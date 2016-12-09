# -*- coding: utf-8 -*-

import os
import logging
import time

import tqdm
import click
import numpy as np
import matplotlib.path
import matplotlib.pyplot as plt

import bmi.wrapper

from .depth import depth_images, calibrated_depth_images
from .plots import Visualization
from .sandbox_fm import (
    update_delft3d_initial_vars,
    update_delft3d_vars,
    compute_affines
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    pass

@cli.command()
@click.option(
    '--calibrated/--raw',
    default=False,
    help='Maximum number of iterations (0=no limit)'
)
def view(calibrated):
    """view raw kinect images"""
    if calibrated:
        images = calibrated_depth_images()
        origin = 'bottom'
    else:
        images = depth_images()
        origin = 'top'
    fig, ax = plt.subplots()
    im = ax.imshow(next(images), origin=origin, cmap='terrain')
    plt.ion()
    plt.show()
    for img in tqdm.tqdm(images):
        im.set_data(img)
        fig.canvas.draw()




@cli.command()
@click.argument('image', type=click.File('rb'))
@click.argument('schematization', type=click.File('rb'))
@click.option(
    '--max-iterations',
    default=0,
    help='Maximum number of iterations (0=no limit)'
)
@click.option(
    '--random-bathy',
    default=0.0,
    help='Raise or lower the bathymetry every 30 timesteps by at most x meter at random locations'
)
def run(image, schematization, max_iterations, random_bathy):
    """Console script for sandbox_fm"""
    click.echo("Make sure you start the SARndbox first")
    vis = Visualization()
    # load model library
    images = depth_images(os.path.abspath(image.name))

    model = bmi.wrapper.BMIWrapper('dflowfm')
    img = next(images)
    data = dict(
        kinect_0=img.copy(),
        kinect=img
    )

    # initialize model schematization, changes directory
    model.initialize(schematization.name)

    dt = model.get_time_step()
    update_delft3d_initial_vars(data, model)

    # coordinates of the image in the model
    img_in_model = np.array([
        [7.10000000e+04,   4.49500000e+05],
        [7.44420895e+04,   4.53660772e+05],
        [7.16682419e+04,   4.55955498e+05],
        [6.82261523e+04,   4.51794726e+05]
    ])

    # compute the transformation
    img2model, model2img = compute_affines(img_in_model, img.shape)

    # create xy1 matrices for model and img
    xy1_model = np.c_[
        data['xzw'],
        data['yzw'],
        np.ones_like(data['xzw'])
    ]

    img_in_model_path = matplotlib.path.Path(img_in_model)
    in_sandbox = img_in_model_path.contains_points(xy1_model[:, :2])
    data['in_sandbox'] = in_sandbox

    Y_img, X_img = np.mgrid[:img.shape[0], :img.shape[1]]
    xy1_img = np.c_[X_img.ravel(), Y_img.ravel(), np.ones_like(X_img.ravel())]
    data['xy1_img'] = xy1_img

    # image in model coordinates
    data['xy1_img_in_model'] = np.dot(xy1_img, img2model.T)
    # multiply [x, y, 1] with affine' gives [xt, yt, 1] (B'A' = (AB)')
    data['xy1_model_in_img'] = np.dot(xy1_model, model2img.T)

    vis.initialize(data)

    change = 0
    s = np.s_[0:0, 0:0]

    for i, img in enumerate(images):
        update_delft3d_vars(data, model)
        print(i)
        if max_iterations and i > max_iterations:
            break
        data["kinect"] = img

        if random_bathy :
            # generate a random slice
            if ((i % 30) == 0):
                i_0 = np.random.randint(img.shape[0])
                i_1 = np.random.randint(i_0, img.shape[0])
                j_0 = np.random.randint(img.shape[1])
                j_1 = np.random.randint(j_0, img.shape[1])
                s = np.s_[i_0:i_1, j_0:j_1]
                change = np.random.uniform(-random_bathy, random_bathy)
            data["kinect"][s] = change
            is_wet = data['bl'] < data['s1']

            is_selected = np.random.random(size=data['bl'].shape[0]) > 1/100.0
            idx = np.logical_and(is_wet, is_selected)

        # comput if wet
        data['bl'][idx] += change

        img_diff = diff = data["kinect_0"] - data["kinect"]

        # diff = img - imgprevious
        # bathydiff = interp(diff)
        # data["bathydiff"] = bathydiff
        vis.update(data)
        tic = time.time()
        model.update(dt)
        toc = time.time()
        print(toc - tic)

if __name__ == "__main__":
    main()
