#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Collecting statistics of the system."""

import logging

LOG = logging.getLogger("span")

from typing import Dict, Tuple, Set, List, Callable
from typing import Optional as Opt
from collections import deque
import time
import io

import span.ir.types as types
import span.ir.expr as expr
import span.api.analysis as analysis
from span.api.analysis import AnalysisNameT
import span.util.common_util as cutil

# simplification names
Node__to__Nil__Name: str = analysis.AnalysisAT.Node__to__Nil.__name__
LhsVar__to__Nil__Name: str = analysis.AnalysisAT.LhsVar__to__Nil.__name__
Num_Var__to__Num_Lit__Name: str = analysis.AnalysisAT.Num_Var__to__Num_Lit.__name__
Cond__to__UnCond__Name: str = analysis.AnalysisAT.Cond__to__UnCond.__name__
Num_Bin__to__Num_Lit__Name: str = analysis.AnalysisAT.Num_Bin__to__Num_Lit.__name__
Deref__to__Vars__Name: str = analysis.AnalysisAT.Deref__to__Vars.__name__


class HostStat:
  def __init__(self, host, totalCfgNodes=0):
    self.host = host
    self.simChangeCacheHits = cutil.CacheHits("SimUnChanged")
    self.cachedInstrSimHits = cutil.CacheHits("SimInstrs")
    self.nodeVisitCount = 0  # count the visits to nodes
    self.totalCfgNodes = totalCfgNodes
    self.simTimer = cutil.Timer("Simplification", start=False)
    self.anSwitchTimer = cutil.Timer("AnalysisSwitching", start=False)
    self.instrAnTimer = cutil.Timer("InstrAnalysis", start=False)
    self.idInstrAnTimer = cutil.Timer("IdInstrAnalysis", start=False)
    self.funcSelectionTimer = cutil.Timer("FunctionSelectionTime", start=False)
    self.nodeMapUpdateTimer = cutil.Timer("NodeWorkListUpdateTime", start=False)


  def incrementNodeVisitCount(self):
    self.nodeVisitCount += 1


  def __str__(self):
    l1 = [f"{self.simChangeCacheHits}"]
    l1.append(f"{self.cachedInstrSimHits}")
    l1.append(f"NumOfNodesVisited: {self.nodeVisitCount} (total {self.totalCfgNodes})")
    l1.append(f"{self.simTimer}")
    l1.append(f"{self.anSwitchTimer}")
    l1.append(f"{self.instrAnTimer}")
    l1.append(f"{self.idInstrAnTimer}")
    l1.append(f"{self.funcSelectionTimer}")
    l1.append(f"{self.nodeMapUpdateTimer}")
    l1.append(f"HostResultSize: {cutil.getSize2(self.host.anWorkDict)}")
    return "\n".join(l1)


class GlobalStats:
  """
  Collects various global statistics in span.sys package in one place.
  """

  def __init__(self):
    # sim name to count map
    self.simCountMap: Dict[str, int] = dict()
    for simName in analysis.simNames:
      self.simCountMap[simName] = 0

  def print(self):
    print("GLOBAL_STATS")
    print("=" * 64)
    for simName in sorted(analysis.simNames):
      print(f"{simName}: {self.simCountMap[simName]}")

"""import this object into other modules in the span.sys module"""
GST = GlobalStats()


