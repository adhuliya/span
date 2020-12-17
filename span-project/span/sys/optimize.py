#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Optimize C program."""

import logging
LOG = logging.getLogger("span")
from typing import Optional as Opt, Dict, Set, List

from span.api.analysis import SimNameT, AnalysisNameT, SimFailed, SimPending, AnalysisAT
from span.api.dfv import NodeDfvL
from span.ir import cfg, expr, instr
from span.ir.constructs import Func
from span.ir.conv import TRANSFORM_INFO_FILE_NAME
from span.ir.types import FuncNameT, Loc
from span.sys import clients
from span.util.common_util import Verbosity
from span.util.util import LS

from span.ir.tunit import TranslationUnit
from span.sys.host import Host
from span.sys.ipa import IpaHost


class TrInfo: # TransformationInfo
  """This class represents the transformation information."""
  __slots__ = ["value", "loc", "trType"]

  def __init__(self, value, loc: Loc, trType: SimNameT):
    self.value: str = str(value)
    self.loc: Loc = loc
    self.trType: SimNameT = trType # transformation type (sim name)


  def dumpStr(self):
    return f"VALUE {self.value}\nLINE {self.loc.line}" \
           f"\nCOL {self.loc.col}\nTRTYPE {self.trType}"


  def __lt__(self, other):
    """To sort objects based on the location in the source code."""
    return self.loc <= other.loc


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
    self.trInfoList: List[TrInfo] = [] # all results accumulated here


  # mainentry
  def transform(self):
    """Invoke this function to do all things necessary."""
    self.analyze()
    self.genTransformInfo_All()
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
    if Verbosity >= 2:
      ipaHostSpan.printFinalResults()


  def genTransformInfo_All(self) -> None:
    """Generate the whole transformation information."""
    assert self.ipaHost or self.intraHosts, f"No analysis results"
    if self.ipaEnabled:
      assert self.ipaHost, f"No analysis results"
    else:
      assert self.intraHosts, f"No analysis results"

    host = self.ipaHost if self.ipaEnabled else self.intraHosts
    for func in self.tUnit.yieldFunctionsForAnalysis():
      funcResults = host.finalResult[func.name]
      self.genTransformInfo_Func(func, funcResults)


  def genTransformInfo_Func(self, func: Func, funcResults: Dict) -> None:
    """Generate the transformation information for a function."""
    for node in func.cfg.yieldNodes():
      trInfo = self.genTransformInfo_Instr(node, func, funcResults)
      if trInfo: self.trInfoList.append(trInfo)


  def genTransformInfo_Instr(self,
      node: cfg.CfgNode,
      func: Func,
      funcResults: Dict[AnalysisNameT, Dict[cfg.CfgNodeId, NodeDfvL]],
  ) -> Opt[TrInfo]:
    """Generate the transformation info for a statement."""
    nid, insn = node.id, node.insn
    if insn.needsCondInstrSim():
      trInfo = self.genTransformInfo_CondInstr(insn, node, func, funcResults)
    elif insn.needsRhsNumVarSim():
      trInfo = self.genTransformInfo_RhsVar(insn, node, func, funcResults)
    elif insn.needsRhsNumBinaryExprSim():
      trInfo = self.genTransformInfo_RhsNumBinary(insn, node, func, funcResults)
    else:
      trInfo = None

    return trInfo


  def genTransformInfo_CondInstr(self,
      insn: instr.CondI,
      node: cfg.CfgNode,
      func: Func,
      funcResults: Dict[AnalysisNameT, Dict[cfg.CfgNodeId, NodeDfvL]],
  ) -> Opt[TrInfo]:
    assert insn.needsCondInstrSim(), f"{insn}, {node}, {func}"
    simName = AnalysisAT.Cond__to__UnCond.__name__
    res = collectAndMergeResults(simName, insn.arg, node, func, funcResults)
    if res and len(res) == 1:
      for value in res: # this loop runs only once
        return TrInfo(value, insn.arg.info.loc, simName)
    return None


  def genTransformInfo_RhsVar(self,
      insn: instr.AssignI,
      node: cfg.CfgNode,
      func: Func,
      funcResults: Dict[AnalysisNameT, Dict[cfg.CfgNodeId, NodeDfvL]],
  ) -> Opt[TrInfo]:
    assert insn.needsRhsNumVarSim(), f"{insn}, {node}, {func}"
    simName = AnalysisAT.Num_Var__to__Num_Lit.__name__
    res = collectAndMergeResults(simName, insn.rhs, node, func, funcResults)
    if res and len(res) == 1:
      for value in res: # this loop runs only once
        return TrInfo(value, insn.rhs.info.loc, simName)
    return None


  def genTransformInfo_RhsNumBinary(self,
      insn: instr.AssignI,
      node: cfg.CfgNode,
      func: Func,
      funcResults: Dict[AnalysisNameT, Dict[cfg.CfgNodeId, NodeDfvL]],
  ) -> Opt[TrInfo]:
    assert insn.needsRhsNumBinaryExprSim(), f"{insn}, {node}, {func}"
    simName = AnalysisAT.Num_Bin__to__Num_Lit.__name__
    res = collectAndMergeResults(simName, insn.rhs, node, func, funcResults)
    if res and len(res) == 1:
      for value in res: # this loop runs only once
        return TrInfo(value, insn.rhs.info.loc, simName)
    return None


  def dumpTransformInfo(self) -> None:
    """Output the transform info to a file."""
    fileName = TRANSFORM_INFO_FILE_NAME.format(cFileName=self.tUnit.name)
    with open(fileName, "w") as fw:
      for trInfo in sorted(self.trInfoList):
        fw.write(trInfo.dumpStr())
        fw.write("\n\n")


def collectAndMergeResults(
    simName: SimNameT,
    e: Opt[expr.ExprET],
    node: cfg.CfgNode,
    func: Func,
    funcResults: Dict[AnalysisNameT, Dict[cfg.CfgNodeId, NodeDfvL]],
) -> Opt[Set]:  # A None value indicates failed sim
  """Collects and merges the simplification by various analyses.
  Step 1: Select one working simplification from any one analysis.
  Step 2: Refine the simplification.
  """
  anNames = set(funcResults.keys())
  anNames = anNames & clients.simSrcMap[simName]

  if not anNames:
    return SimFailed  # no sim analyses -- hence fail

  # Step 0: Get analyses objects.
  anObjs = {anName: clients.analyses[anName](func) for anName in anNames}

  # Step 1: Find the first useful result
  values: Opt[Set] = SimFailed
  if LS: LOG.debug("SimAnalyses for %s: %s", simName, anNames)
  for anName in anNames:    # loop to select the first working sim
    nDfv = funcResults[anName][node.id]
    values = calculateSimValue(anObjs[anName], anName, simName, node, nDfv, e)
    if values:
      break  # break at the first useful value
  if values in (SimPending, SimFailed):
    return values  # failed/pending values can never be refined

  # Step 2: Refine the simplification
  assert values not in (SimPending, SimFailed), f"{values}"
  if LS: LOG.debug("Refining(Start): %s", values)
  for anName in anNames:
    nDfv = funcResults[anName][node.id]
    tmpValues = calculateSimValue(anObjs[anName], anName, simName, node, nDfv, e, values)
    values = values if tmpValues is SimFailed else tmpValues
    if values == SimPending:
      break  # no use to continue
  if LS: LOG.debug("Refining(End): Refined value is %s", values)
  return values  # a refined result


def calculateSimValue(
    simAnObj,
    simAnName: AnalysisNameT,
    simName: SimNameT,
    node: cfg.CfgNode,
    nDfv: NodeDfvL,
    e: Opt[expr.ExprET] = None,
    values: Opt[Set] = None,
) -> Opt[Set]:
  """Calculates the simplification value for the given parameters."""
  assert hasattr(simAnObj, simName), f"{simAnName}, {simName}"
  nid, simFunction = node.id, getattr(simAnObj, simName)

  if LS: LOG.debug("SimOfExpr: '%s' isAttemptedBy %s withDfv %s.", e, simAnName, nDfv)
  # Note: if e is None, it assumes sim works on node id
  newValues = simFunction(e if e else nid, nDfv, values)
  if LS: LOG.debug("SimOfExpr: '%s' is %s, by %s.", e, newValues, simAnName)
  return newValues


