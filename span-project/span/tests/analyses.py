#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Tests to check correct span analysis results.
Assumes the basic tests were successful.
"""

import unittest
from typing import List, Dict, Optional as Opt

import span.ir.ir as ir
from span.tests.common import \
  (genFileMap,
   genFileMapSpanir,
   genTranslationUnit,
   TestActionAndResult,
   evalTestCaseFile, )
import span.sys.host as host
import span.ir.cfg as cfg
import span.api.dfv as dfv
from span.api.analysis import AnalysisNameT
import span.sys.clients as clients
import span.sys.driver as driver


class SpanAnalysisTests(unittest.TestCase):


  def setUp(self):
    # called before every test
    pass


  def tearDown(self):
    # called after every test
    pass


  def test_AABA_analyze(self):
    """Checking analysis results on the given programs."""
    print("\nTesting analysis results now. START.\n")
    fileMap = genFileMap(self)
    irFileMap = genFileMapSpanir(self)

    for cFile, pyFile in fileMap.items():
      irFile = irFileMap[cFile] if cFile in irFileMap else None
      pyFileActions: List[TestActionAndResult] = evalTestCaseFile(pyFile)
      for action in pyFileActions:
        if action.action == "analyze":
          print(f"Checking analysis results of: {cFile},")
          self.runAndCheckAnalysisResults(cFile, irFile, action)
    print("\nTesting analysis results now. END.\n")


  def allAnalysesPresent(self, analyses: List[AnalysisNameT]):
    """Returns True if all the given analyses are present in the system."""
    allPresent = True
    for anName in analyses:
      if not clients.isAnalysisPresent(anName):
        print("  NOTE: AnalysisNotPresent:", anName)
        allPresent = False
    return allPresent


  def runAndCheckAnalysisResults(self,
      cFileName: str,
      irFileName: Opt[str],
      action: TestActionAndResult
  ) -> None:
    """Runs the analyses and checks their results."""
    if irFileName:
      tUnit: ir.TranslationUnit = ir.readSpanIr(irFileName)
    else:
      tUnit: ir.TranslationUnit = genTranslationUnit(cFileName)

    if not self.allAnalysesPresent(action.analyses):
      print(f"  SkippingTest(AnalysesNotPresent):", action.analyses)
      return None

    mainAnalysis = action.analyses[0]
    otherAnalyses = action.analyses[1:]
    analysisCount = len(action.analyses)
    avoidAnalyses = None

    for func in tUnit.yieldFunctionsWithBody():
      syn1 = host.Host(func=func,
                       mainAnName=mainAnalysis,
                       otherAnalyses=otherAnalyses,
                       avoidAnalyses=avoidAnalyses,
                       maxNumOfAnalyses=analysisCount)
      syn1.analyze()  # do the analysis
      for anName in action.analyses:
        if anName not in action.results["analysis.results"]: continue
        if func.name not in action.results["analysis.results"][anName]: continue
        anNameResults = syn1.getAnalysisResults(anName).nidNdfvMap
        assert anNameResults, f"{anName}"
        if self.compareAnalysisResults(anNameResults,
                                       action.results["analysis.results"][anName][func.name],
                                       cFileName):
          print(f"    {cFileName}: {anName} on {func.name} is correct.")
          print(f"        analyses={action.analyses}")


  def compareAnalysisResults(self,
      results: Dict[cfg.CfgNodeId, dfv.NodeDfvL],
      expectedResults: Dict[cfg.CfgNodeId, dfv.NodeDfvL],
      cFileName: str,
  ) -> bool:
    nodeIds = set(results.keys())
    givenNodeIds = set(expectedResults.keys())
    self.assertEqual(nodeIds >= givenNodeIds, True,
                     f"{nodeIds} is not a superset of {givenNodeIds}.")

    for nid in givenNodeIds:
      self.assertEqual(results[nid], expectedResults[nid],
                       f"({cFileName}) Node {nid}")

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
