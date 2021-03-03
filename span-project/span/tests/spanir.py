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
from span.ir import conv
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
import span.tests.common as common #IMPORTANT
from span.tests.common import \
  (genFileMap,
   genFileMapSpanir,
   genTranslationUnit,
   TestActionAndResult,
   evalTestCaseFile, )
import span.sys.host as host
import span.ir.cfg as cfg
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
    if not common.SPAN_LLVM_AVAILABLE:
      print("\nClang/LLVM with SPAN support not present !!!!!!!!!!!!!!!!!!!!\n")
      return

    print("\nSTART: Testing spanir generation now.\n")

    fileMap = genFileMapSpanir(self)

    for cFile, irFile in fileMap.items():
      print(f"CheckingSpanirOf: {cFile}.")
      if self.checkSpanirConversion(cFile, irFile):
        print("  Correct.")
      else:
        print("  NotCorrect.")

    print("\nEND  : Testing spanir generation now.\n")


  def test_AACA_ir_attributes(self):
    """Checking the correctness of SpanIr meta attributes on given programs."""
    if not common.SPAN_LLVM_AVAILABLE:
      print("\nClang/LLVM with SPAN support not present !!!!!!!!!!!!!!!!!!!!\n")
      return

    print("\nSTART: Testing spanir attributes now.\n")
    fileMap = genFileMap(self)
    fileMapIr = genFileMapSpanir(self)

    for cFileName, pyFile in fileMap.items():
      print(f"CheckingAttributes: {cFileName}: ")
      pyFileActions: List[TestActionAndResult] = evalTestCaseFile(pyFile)
      for action in pyFileActions:
        if action.action == "ir.checks":
          tUnit: ir.TranslationUnit = genTranslationUnit(cFileName)
          self.checkAttributesAll(action.results, tUnit, cFileName)
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

    print("\nEND  : Testing spanir attributes now.\n")


  def checkAttributesAll(self,
      results: Dict,
      tUnit: tunit.TranslationUnit,
      cFileName: str,
  ) -> None:

    # STEP 1: check the names api
    for key in results.keys():
      if key == "tunit":
        self.checkAttributesTUnit(results[key], tUnit, cFileName)
      elif conv.isFuncName(key):
        self.checkAttributesFunc(key, results[key], tUnit, cFileName)

      if key.startswith("ir.names"):
        tup = results[key]
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


  def checkAttributesTUnit(self,
      results: Dict,
      tUnit: tunit.TranslationUnit,
      cFileName: str,
  ) -> None:
    propName = "ir.names.global"
    res = results.get(propName, None)
    if res:
      globalNames = tUnit.getNamesGlobal(res[0])
      self.assertEqual(globalNames, res[1],
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {globalNames}, Correct: {res[1]}"))

    propName = "ir.var.real.count"
    res = results.get(propName, None)
    if res:
      count = len(tUnit.allVars)
      self.assertEqual(count, res,
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.var.abs.count"
    res = results.get(propName, None)
    if res:
      count = len(tUnit._nameInfoMap)
      self.assertEqual(count, res,
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.func.count"
    res = results.get(propName, None)
    if res:
      count = len(tUnit.allFunctions)
      self.assertEqual(count, res,
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.func.def.count"
    res = results.get(propName, None)
    if res:
      count = len(list(tUnit.yieldFunctionsWithBody()))
      self.assertEqual(count, res,
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.func.decl.count"
    res = results.get(propName, None)
    if res:
      count = len(list(func for func in tUnit.yieldFunctions() if not func.hasBody()))
      self.assertEqual(count, res,
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.record.count"
    res = results.get(propName, None)
    if res:
      count = len(tUnit.allRecords)
      self.assertEqual(count, res,
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))


  def checkAttributesFunc(self,
      funcName: types.FuncNameT,
      results: Dict,
      tUnit: tunit.TranslationUnit,
      cFileName: str,
  ) -> None:
    funcObj = tUnit.getFuncObj(funcName)

    propName = "ir.cfg.node.count"
    res = results.get(propName, None)
    if res:
      count = len(funcObj.cfg.nodeMap)
      self.assertEqual(count, res,
                       msg=(f"{propName}({funcName}): {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))


  def checkSpanirConversion(self,
      cFileName: str,
      irFileName: str,
  ) -> bool:
    tUnit: ir.TranslationUnit = genTranslationUnit(cFileName)
    tUnitTest: ir.TranslationUnit = ir.readSpanIr(irFileName)

    self.assertTrue(tUnit.isEqual(tUnitTest),
                    msg=f"Newly generated spanir file, '{cFileName}.spanir.py'"
                        f"doesn't match against the test file '{irFileName}'")
    return True


def _runTests():
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
  _runTests()


