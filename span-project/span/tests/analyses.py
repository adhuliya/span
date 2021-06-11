#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""
Tests to check correct span analysis results.
Assumes the basic tests were successful.
"""

import unittest
from typing import List, Dict, Optional as Opt, Tuple

import span.ir.ir as ir
import span.tests.common as common #IMPORTANT
from span.ir import types
from span.ir.types import FuncNameT, NodeIdT
from span.tests.common import \
  (genFileMap,
   genFileMapSpanir,
   genTranslationUnit,
   TestActionAndResult,
   evalTestCaseFile, )
import span.sys.host as host
import span.ir.cfg as cfg
import span.api.dfv as dfv
from span.api.analysis import AnalysisNameT as AnNameT
import span.sys.clients as clients
import span.sys.driver as driver
import span.util.consts as consts



class SpanAnalysisTests(unittest.TestCase):


  def setUp(self):
    # called before every test
    pass


  def tearDown(self):
    # called after every test
    pass


  def test_AABA_analyze(self):
    """Checking analysis results on the given programs."""
    print("\nSTART: Testing analysis results.\n")
    fileMap = genFileMap(self)
    irFileMap = genFileMapSpanir(self)

    for cFile, pyFile in fileMap.items():
      irFile = irFileMap[cFile] if cFile in irFileMap else None
      pyFileActions: List[TestActionAndResult] = evalTestCaseFile(pyFile)
      for action in pyFileActions:
        if "analyze" in action.action:
          print(f"Checking analysis results of: {cFile},")
          self.runAndCheckAnalysisResultsIntra(cFile, irFile, action)
        elif "ipa" in action.action:
          print(f"Checking analysis results of: {cFile},")
          self.runAndCheckAnalysisResultsIpa(cFile, irFile, action)
    print("\nEND  : Testing analysis results.\n")


  def allAnalysesPresent(self, analysesExpr: str) -> bool:
    """Returns True if all the given analyses are present in the system."""
    import span.sys.driver as driver
    try:
      driver.parseSpanAnalysisExpr(analysesExpr)
    except ValueError as ve:
      msg = str(ve)
      if consts.AN_NOT_PRESENT in msg:
        print(msg)
        return False # all not present
    return True # all present


  def runAndCheckAnalysisResultsIntra(self,
      cFileName: str,
      irFileName: Opt[str],
      action: TestActionAndResult
  ) -> None:
    """Runs the analyses and checks their results."""
    if not common.SPAN_LLVM_AVAILABLE:
      print("\nClang/LLVM with SPAN support not present !!!!!!!!!!!!!!!!!!!!")
      return

    if not self.allAnalysesPresent(action.analysesExpr):
      print(f"  SkippingTest(AnalysesNotPresent):", action.analysesExpr)
      return None

    parser = driver.getParser()
    fileName = irFileName if irFileName else cFileName
    argList = [action.action, action.analysesExpr, fileName]
    print(f"  {cFileName}: Args: span {argList}")
    args = parser.parse_args(args=argList)
    resultsDict: [FuncNameT, host.Host] = args.func(args)

    anRes = action.results["analysis.results"]
    for anName, funcResMap in anRes.items():
      for funcName, correctAnRes in funcResMap.items():
        resHost: host.Host = resultsDict[funcName]
        computedAnRes = resHost.getAnalysisResults(anName).anResult.result
        if self.compareAnResults(anName, computedAnRes, correctAnRes, cFileName):
          print(f"    {anName} on {funcName} is correct.")


  def runAndCheckAnalysisResultsIpa(self,
      cFileName: str,
      irFileName: Opt[str],
      action: TestActionAndResult
  ) -> None:
    """Runs the analyses and checks their results."""
    if not common.SPAN_LLVM_AVAILABLE:
      print("\nClang/LLVM with SPAN support not present !!!!!!!!!!!!!!!!!!!!")
      return

    if not self.allAnalysesPresent(action.analysesExpr):
      print(f"  SkippingTest(AnalysesNotPresent):", action.analysesExpr)
      return None

    parser = driver.getParser()
    fileName = irFileName if irFileName else cFileName
    argList = [action.action, action.analysesExpr, fileName]
    print(f"    {cFileName}: Args: span {argList}")
    args = parser.parse_args(args=argList)
    ipaHost = args.func(args)
    resultsDict: Dict[FuncNameT, Dict[AnNameT, Dict[NodeIdT, dfv.DfvPairL]]] \
      = ipaHost.vci.finalResult

    propName = "analysis.results"
    res = action.results.get(propName, None)
    if res:
      for anName, funcResMap in res.items():
        for funcName, correctAnRes in funcResMap.items():
          computedAnRes = resultsDict[funcName][anName]
          if self.compareAnResults(anName, computedAnRes, correctAnRes, cFileName):
            print(f"    {anName} on {funcName} is correct.")

    # Check the maximum size of the ValueContextMap table.
    propName = "ipa.vc.table.maxsize"
    res = action.results.get(propName, None)
    if res:
      computedRes = ipaHost.vci.maxVcMapSize
      self.assertEqual(computedRes, res,
                       f"({cFileName}) Correct: {res}, Computed: {computedRes}")


  def compareAnResults(self,
      anName: AnNameT,
      computedAnRes: Dict[cfg.CfgNodeId, dfv.DfvPairL],
      correctAnRes: Dict[cfg.CfgNodeId, Tuple],
      cFileName: str,
  ) -> bool:
    anClass = clients.analyses[anName]
    for nid in correctAnRes.keys():
      correctRes, computedRes = correctAnRes[nid], computedAnRes[nid]
      if len(correctRes) >= 1 and correctRes[0] != "any": # i.e. compare the IN
        if not anClass.test_dfv_assertion(computedRes.dfvIn, correctRes[0]):
          self.assertEqual(False, True,
                           f"({cFileName}) Node {nid}: IN: Correct:"
                           f" {correctRes[0]}, Computed: {computedRes.dfvIn}")

      if len(correctRes) >= 2 and correctRes[1] != "any": # i.e. compare the OUT
        if not anClass.test_dfv_assertion(computedRes.dfvOut, correctRes[1]):
          self.assertEqual(False, True,
                           f"({cFileName}) Node {nid}: OUT: Correct:"
                           f" {correctRes[1]}, Computed: {computedRes.dfvOut}")

      if len(correctRes) >= 3 and correctRes[2] != "any": # i.e. compare the OUT(False)
        if not anClass.test_dfv_assertion(computedRes.dfvOutFalse, correctRes[2]):
          self.assertEqual(False, True,
                           f"({cFileName}) Node {nid}: OUT(False): Correct:"
                           f" {correctRes[2]}, Computed: {computedRes.dfvOutFalse}")

      if len(correctRes) >= 4 and correctRes[3] != "any": # i.e. compare the OUT(True)
        if not anClass.test_dfv_assertion(computedRes.dfvOutTrue, correctRes[3]):
          self.assertEqual(False, True,
                           f"({cFileName}) Node {nid}: OUT(True): Correct:"
                           f" {correctRes[4]}, Computed: {computedRes.dfvOutTrue}")

    return True


def runTests():
  """Call this function to start tests."""
  suite = unittest.TestSuite()
  for name, nameType in SpanAnalysisTests.__dict__.items():
    if callable(nameType) and name.startswith("test_"):
      suite.addTest(SpanAnalysisTests(name))
  runner = unittest.TextTestRunner()
  runner.run(suite)
  # unittest.main(SpanTestBasic())


def addTests(suite: unittest.TestSuite) -> None:
  """Call this function to add tests."""
  for name, nameType in SpanAnalysisTests.__dict__.items():
    if callable(nameType) and name.startswith("test_"):
      suite.addTest(SpanAnalysisTests(name))
  return None


if __name__ == "__main__":
  # unittest.main()
  runTests()


