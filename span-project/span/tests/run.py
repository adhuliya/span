#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""
This is the driver module of the testing facility.
"""

import unittest

import span.tests.basic as basicTests
import span.tests.spanir as spanIrTests
import span.tests.analyses as analysisTests


def runTests(testType: str):
  """Call this function to start tests."""
  suite = unittest.TestSuite()

  # always add the basic tests
  basicTests.addTests(suite)

  # conditionally add ir tests
  if testType in {"all", "ir", "spanir"}:
    spanIrTests.addTests(suite)

  # conditionally add analysis tests
  if testType in {"all", "analyses", "analysis"}:
    analysisTests.addTests(suite)

  runner = unittest.TextTestRunner()
  runner.run(suite)


