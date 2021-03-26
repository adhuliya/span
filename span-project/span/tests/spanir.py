#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Tests to check correct spanir conversion.
"""

import unittest
import sys
import subprocess as subp
from typing import Dict, List, Any, Optional as Opt

# IMPORTANT imports for eval() to work
from span.ir import conv, callgraph
from span.ir.callgraph import CallGraph
from span.ir.conv import FalseEdge, TrueEdge, UnCondEdge
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
          self.checkAttributesAll(action.results, tUnit, cFileName, pyFile)
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
      pyFile: str,
  ) -> None:

    self.checkAttributesCallGraph(results, tUnit, cFileName)

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


  def checkAttributesCallGraph(self,
      results: Dict,
      tUnit: tunit.TranslationUnit,
      cFileName: str,
  ) -> None:
    callGraph: Opt[CallGraph] = None

    propName = "callgraph.edges.count"
    res = results.get(propName, None)
    if res:
      callGraph = callgraph.generateCallGraph(tUnit) if not callGraph else callGraph
      count = callGraph.getCountEdges()
      self.assertEqual(count, res,
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "callgraph.nodes.count"
    res = results.get(propName, None)
    if res:
      callGraph = callgraph.generateCallGraph(tUnit) if not callGraph else callGraph
      count = callGraph.getCountNodes()
      self.assertEqual(count, res,
                       msg=(f"{propName}: {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))


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
    funcCfg = funcObj.cfg
    bbEdges = funcObj.bbEdges

    propName = "ir.cfg.node.count" # node count: all
    res = results.get(propName, None)
    if res:
      count = len(funcCfg.nodeMap)
      self.assertEqual(count, res,
                       msg=(f"{propName}({funcName}): {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.cfg.bb.edge.count" # edge count: all
    res = results.get(propName, None)
    if res:
      count = len(bbEdges)
      self.assertEqual(count, res,
                       msg=(f"{propName}({funcName}): {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.cfg.bb.edge.false.true.pair.count" # edge count: false
    res = results.get(propName, None)
    if res:
      countFalse = len(list(1 for _,_,l in bbEdges if l == FalseEdge))
      self.assertEqual(countFalse, res,
                       msg=(f"{propName}({funcName}): {cFileName}: (FalseEdge) Computed:"
                            f" {countFalse}, Correct: {res}"))
      countTrue = len(list(1 for _,_,l in bbEdges if l == TrueEdge))
      self.assertEqual(countTrue, res,
                       msg=(f"{propName}({funcName}): {cFileName}: (TrueEdge) Computed:"
                            f" {countTrue}, Correct: {res}"))

    propName = "ir.cfg.bb.edge.true.count" # edge count: true
    res = results.get(propName, None)
    if res:
      count = len(list(1 for _,_,l in bbEdges if l == TrueEdge))

    propName = "ir.cfg.bb.edge.uncond.count" # edge count: uncond
    res = results.get(propName, None)
    if res:
      count = len(list(1 for _,_,l in bbEdges if l == UnCondEdge))
      self.assertEqual(count, res,
                       msg=(f"{propName}({funcName}): {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.cfg.bb.has.edges" # contains the given edges
    res = results.get(propName, None)
    if res:
      hasEdges = res <= set(bbEdges)
      self.assertEqual(hasEdges, True,
                       msg=(f"{propName}({funcName}): {cFileName}: Computed:"
                            f" {bbEdges}, Correct: {res}"))

    propName = "ir.cfg.bb.insn.count"  # count instructions in given BBs
    res = results.get(propName, None)
    if res:
      for bbId, correctCount in res.items():
        count = len(funcObj.basicBlocks[bbId])
        self.assertEqual(count, correctCount,
                         msg=(f"{propName}({funcName}): {cFileName}:"
                              f" (BBId: {bbId}) Computed:"
                              f" {count}, Correct: {correctCount}"))

    propName = "ir.cfg.insn.nop.count" # count on NopI in the ir
    res = results.get(propName, None)
    if res:
      count = len(list(1 for insn in funcObj.yieldInstrSeq() if isinstance(insn, instr.NopI)))
      self.assertEqual(count, res,
                       msg=(f"{propName}({funcName}): {cFileName}: Computed:"
                            f" {count}, Correct: {res}"))

    propName = "ir.cfg.start.end.node.is.insn.nop" # start, end node must be NopI
    res = results.get(propName, None)
    if res is not None:
      startNop = isinstance(funcCfg.start.insn, instr.NopI)
      self.assertEqual(startNop, res,
                       msg=(f"{propName}({funcName}): {cFileName}: (StartNode) Computed:"
                            f" {startNop}, Correct: {res}"))
      endNop = isinstance(funcCfg.end.insn, instr.NopI)
      self.assertEqual(endNop, res,
                       msg=(f"{propName}({funcName}): {cFileName}: (EndNode) Computed:"
                            f" {endNop}, Correct: {res}"))


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


