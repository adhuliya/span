#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Tests to check correct spanir conversion.
Assumes the basic tests were successful.
"""

import unittest
import sys
import subprocess as subp
from typing import Dict, List

# IMPORTANT imports for eval() to work
from span.ir.types import Loc
import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.tunit as tunit

import span.util.common_util as cutil
import span.ir.constructs as constructs
import span.ir.ir as ir
from span.tests.common import \
  (genFileMap,
   genTranslationUnit,
   TestActionAndResult,
   evalTestCaseFile, )
import span.sys.host as host
import span.ir.graph as graph
import span.api.dfv as dfv


class SpanIrTests(unittest.TestCase):


  def setUp(self):
    # called before every test
    pass


  def tearDown(self):
    # called after every test
    pass


  def test_AABA_c2Spanir(self):
    """Checking the correctness of SpanIr on given programs."""
    print("\nTesting spanir now.")
    fileMap = genFileMap(self)

    for cFile, pyFile in fileMap.items():
      spanirActionPresent = False
      print(f"Checking spanir of {cFile}.")
      pyFileActions: List[TestActionAndResult] = evalTestCaseFile(pyFile)
      for action in pyFileActions:
        if action.action == "c2spanir":
          spanirActionPresent = True
          if self.checkSpanirConversion(cFile, action):
            print("    Correct.")
      if not spanirActionPresent:
        print("    OK. (spanir check not requested)")


  def test_AACA_ir_attributes(self):
    """Checking the correctness of SpanIr meta attributes on given programs."""
    print("\nTesting spanir now (its attributes).")
    fileMap = genFileMap(self)

    for cFileName, pyFile in fileMap.items():
      pyFileActions: List[TestActionAndResult] = evalTestCaseFile(pyFile)
      for action in pyFileActions:
        if action.action == "c2spanir":
          print(f"Checking attributes: {cFileName}: ")
          tUnit: ir.TranslationUnit = genTranslationUnit(cFileName)
          # Now check for the various attributes.
          # STEP 1: check the names api
          for key in action.results.keys():
            if key.startswith("ir.names"):
              tup = action.results[key]
              if tup[0] == "global":  # i.e. all the global variables
                self.assertEqual(tUnit.getNamesGlobal(tup[1]), tup[2],
                                 msg=(f"{cFileName}: {pyFile}: Got: {tUnit.getNamesGlobal(tup[1])}"
                                      f"Exptected: {tup[2]}"))
              elif tup[0].startswith("f:"):
                tmp = tUnit.getNamesEnv(tUnit.allFunctions[tup[0]], tup[1])
                self.assertEqual(tmp, tup[2],
                                 msg=(f"{cFileName}: {pyFile}: Got: {tmp}"
                                      f"Exptected: {tup[2]}"))
              else:
                self.assertTrue(False, "Should not reach here.")

          print("   Correct.")


  def checkSpanirConversion(self,
      cFileName: str,
      action: TestActionAndResult
  ) -> bool:
    tUnit: ir.TranslationUnit = genTranslationUnit(cFileName)

    self.assertTrue(action.results["ir.tunit"].isEqual(tUnit), msg=f"For {cFileName}")
    return True


def runTests():
  """Call this function to start tests."""
  suite = unittest.TestSuite()
  for name, nameType in SpanIrTests.__dict__.items():
    if callable(nameType) and name.startswith("test_"):
      suite.addTest(SpanIrTests(name))
  runner = unittest.TextTestRunner()
  runner.run(suite)
  # unittest.main(SpanTestBasic())


def addTests(suite: unittest.TestSuite) -> None:
  """Call this function to add tests."""
  for name, nameType in SpanIrTests.__dict__.items():
    if callable(nameType) and name.startswith("test_"):
      suite.addTest(SpanIrTests(name))
  return None


if __name__ == "__main__":
  # unittest.main()
  runTests()
