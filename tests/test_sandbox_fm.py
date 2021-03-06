#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_sandbox_fm
----------------------------------

Tests for `sandbox_fm` module.
"""

import pytest

import logging

from contextlib import contextmanager
from click.testing import CliRunner

from sandbox_fm import sandbox_fm
from sandbox_fm import cli

logger = logging.getLogger(__name__)


def log_ex(ex):
    try:
        raise ex
    except:
        logger.exception("exception raised")



class TestSandbox_fm(object):

    @classmethod
    def setup_class(cls):
        pass

    def test_something(self):
        pass

    def test_command_line_interface(self):
        runner = CliRunner()

        # run with test input
        result = runner.invoke(cli.main, [
            'tests/depthimage.png',
            'tests/zandmotor/zm_tide.mdu',
            '--max-iterations=1'
        ])
        logger.info(result.output)
        log_ex(result.exception)
        assert result.exit_code == 0, (result)
        assert 'sandbox_fm.cli.main' in result.output

        # run help
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output

    @classmethod
    def teardown_class(cls):
        pass
