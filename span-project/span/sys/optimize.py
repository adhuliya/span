#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Optimize C program."""

import logging

from itertools import chain
from span.api.analysis import SimNameT, AnalysisNameT, SimFailed, SimPending
from span.api.dfv import NodeDfvL
from span.ir import graph, expr
from span.ir.constructs import Func
from span.ir.types import FuncNameT
from span.sys import clients
from span.util.util import LS

LOG = logging.getLogger("span")
from typing import Optional as Opt, Dict, Set

from span.ir.tunit import TranslationUnit
from span.sys.host import Host
from span.sys.ipa import IpaHost


class TrInfo: # TransformationInfo
  """This class represents the transformation information."""
  def __init__(self, value):
    self.trType = None # transformation type
    self.loc = None
    self.value = value


  def __str__(self):
    return f"TrInfo({self.trType}, {self.value}, {self.loc})"


  def __repr__(self):
    return self.__str__()


class TransformCode:
  """This class analyzes the TranslationUnit and transforms it
  to optimize"""
  def __init__(self,
      tUnit: TranslationUnit,
      ipaEnabled: bool = True
  ):
    self.tUnit = tUnit
    self.ipaEnabled = ipaEnabled
    self.analyses = ["IntervalA", "PointsToA"]
    self.ipaHost: Opt[IpaHost] = None
    self.intraHosts: Opt[Dict[Func, Host]] = None


  # mainentry
  def transform(self):
    self.analyze()
    self.genTransformInfoAll()
    self.dumpTransformInfo()


  def analyze(self):
    """Analyze the C program."""
    mainAnalysis = self.analyses[0]
    otherAnalyses = self.analyses[1:]
    maxNumOfAnalyses = len(self.analyses)

    ipaHostSpan = IpaHost(self.tUnit,
                          mainAnName=mainAnalysis,
                          otherAnalyses=otherAnalyses,
                          maxNumOfAnalyses=maxNumOfAnalyses
                          )
    ipaHostSpan.analyze()
    self.ipaHost = ipaHostSpan


  def genTransformInfoAll(self) -> None:
    """Generate the whole transformation information."""
    assert self.ipaHost or self.intraHosts, f"No analysis results"
    if self.ipaEnabled:
      assert self.ipaHost, f"No analysis results"
    else:
      assert self.intraHosts, f"No analysis results"

    host = self.ipaHost if self.ipaEnabled else self.intraHosts
    for func in self.tUnit.yieldFunctionsForAnalysis():
      funcResults = host.finalResult[func.name]
      self.genTransformInfoFunc(func, funcResults)


  def genTransformInfoFunc(self, func: Func, funcResults: Dict) -> None:
    """Generate the transformation information for a function."""
    intervalRes = funcResults["IntervalA"]
    for node in func.cfg.yieldNodes():
      nid, insn = node.id, node.insn
      pass #TODO


  def dumpTransformInfo(self):
    """Output the transform info to a file."""
    pass


def collectAndMergeResults(
    simName: SimNameT,
    func: Func,
    node: graph.CfgNode,
    e: Opt[expr.ExprET],
    dfvMap: Dict[AnalysisNameT, Dict[graph.CfgNodeId, NodeDfvL]],
) -> Opt[Set]:  # A None value indicates failed sim
  """Collects and merges the simplification by various analyses.
  Step 1: Select one working simplification from any one analysis.
  Step 2: Refine the simplification.
  """
  anNames = set(dfvMap.keys())
  anNames = anNames & clients.simSrcMap[simName]

  if not anNames: return SimFailed  # no sim analyses -- hence fail

  # Step 0: Get analyses objects.
  anObjs = {anName: clients.analyses[anName](func) for anName in anNames}

  # Step 1: Find the first useful result
  values: Opt[Set] = SimFailed
  if LS: LOG.debug("SimAnalyses for %s: %s", simName, anNames)
  for anName in anNames:    # loop to select the first working sim
    nDfv = dfvMap[anName][node.id]
    values = calculateSimValue(anObjs[anName], anName, simName, node, nDfv, e)
    if len(values) >= 1:
      break  # break at the first useful value
  if values in (SimPending, SimFailed):
    return values  # failed/pending values can never be refined

  # Step 2: Refine the simplification
  assert values not in (SimPending, SimFailed), f"{values}"
  if LS: LOG.debug("Refining(Start): %s", values)
  for anName in anNames:
    nDfv = dfvMap[anName][node.id]
    values = calculateSimValue(anObjs[anName], anName, simName, node, nDfv, e, values)
    assert values != SimFailed, f"{anName}, {simName}, {node}, {e}, {values}"
    if values == SimPending:
      break  # no use to continue
  if LS: LOG.debug("Refining(End): Refined value is %s", values)
  return values  # a refined result


def calculateSimValue(
    simAnObj,
    simAnName: AnalysisNameT,
    simName: SimNameT,
    node: graph.CfgNode,
    nDfv: NodeDfvL,
    e: Opt[expr.ExprET] = None,
    values: Opt[Set] = None,
) -> Opt[Set]:
  """Calculates the simplification value for the given parameters."""
  assert hasattr(simAnObj, simName), f"{simAnName}, {simName}"
  nid, simFunction = node.id, getattr(simAnObj, simName)

  if LS: LOG.debug("SimOfExpr: '%s' isAttemptedBy %s withDfv %s.", e, simAnName, nDfv)
  # Note: if e is None, it assumes sim works on node id
  value = simFunction(e if e else nid, nDfv, values)
  if LS: LOG.debug("SimOfExpr: '%s' is %s, by %s.", e, value, simAnName)
  return value


