#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
This is the driver module of the testing facility.
"""

import unittest

import span.tests.basic as basictest
import span.tests.spanir as testspanir
import span.tests.analyses as testanalyses


def runTests(testType: str):
  """Call this function to start tests."""
  # always run basic tests
  suite = unittest.TestSuite()

  # always add the basic tests
  basictest.addTests(suite)

  if testType in {"all", "ir", "spanir"}:
    testspanir.addTests(suite)

  if testType in {"all", "analyses", "analysis"}:
    testanalyses.addTests(suite)

  runner = unittest.TextTestRunner()
  runner.run(suite)
