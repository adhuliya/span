#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Tests to check correct span analysis results.
Assumes the basic tests were successful.
"""

import unittest
import sys
import subprocess as subp
from typing import List, Dict

import span.util.messages as msg
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


class SpanAnalysisTests(unittest.TestCase):


  def setUp(self):
    # called before every test
    pass


  def tearDown(self):
    # called after every test
    pass


  def test_AABA_analyze(self):
    """Checking analysis results on the given programs."""
    print("\nTesting analysis results now.")
    fileMap = genFileMap(self)

    for cFile, pyFile in fileMap.items():
      pyFileActions: List[TestActionAndResult] = evalTestCaseFile(pyFile)
      for action in pyFileActions:
        if action.action == "analyze":
          print(f"Checking analysis results of {cFile},")
          self.runAndCheckAnalysisResults(cFile, action)


  def runAndCheckAnalysisResults(self,
      cFileName: str,
      action: TestActionAndResult
  ) -> None:
    tUnit: ir.TranslationUnit = genTranslationUnit(cFileName, self)

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
        anNameResults = syn1.getAnalysisResults(anName)
        assert anNameResults, f"{anName}"
        if self.compareAnalysisResults(anNameResults,
                                       action.results["analysis.results"][anName][func.name],
                                       cFileName):
          print(f"    {cFileName}: {anName} on {func.name} is correct.")
          print(f"        analyses={action.analyses}")


  def compareAnalysisResults(self,
      results: Dict[graph.CfgNodeId, dfv.NodeDfvL],
      expectedResults: Dict[graph.CfgNodeId, dfv.NodeDfvL],
      cFileName: str,
  ) -> bool:
    nodeIds = set(results.keys())
    givenNodeIds = set(expectedResults.keys())
    self.assertEqual(nodeIds >= givenNodeIds, True,
                     f"{nodeIds} is not a superset of {givenNodeIds}.")

    for nid in givenNodeIds:
      self.assertEqual(results[nid], expectedResults[nid],
                       (f"({cFileName}) Node {nid}: Result: {results[nid]}"
                        f" and expected is {expectedResults[nid]}."))

    # self.assertEqual(results, givenResults)
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
