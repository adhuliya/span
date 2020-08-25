#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The number of constants detected."""

import logging

LOG = logging.getLogger("span")

from typing import List, Optional as Opt, Dict, Set, cast
import io

import span.api.analysis as analysis
import span.api.dfv as dfv
import span.api.diagnosis as diagnosis

import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.tunit as irTUnit
import span.ir.constructs as obj
import span.ir.ir as ir

from span.api.diagnosis import Report, Message

# import the analysis classes
from span.clients.stronglive import StrongLiveVarsA
from span.clients.pointsto import PointsToA
import span.clients.const as const
import span.clients.pointsto as pointsto
import span.clients.stronglive as liveness
import span.clients as clients


class ConstantsCountR(diagnosis.DiagnosisRT):
  """Counts the constants detected."""
  Needs = [const.ConstA]
  OptionalNeeds = [PointsToA]
  AnalysesSeqCascading = [["ConstA"]]
  # AnalysesSeqCascading  = [["ConstA"], ["PointsToA"],
  #                        ["ConstA"], ["EvenOddA"], ["ConstA"]]
  # AnalysesSeqLerner    = [["ConstA", "PointsToA", "EvenOddA"]]
  AnalysesSeqLerner = [["ConstA", "PointsToA"]]


  def __init__(self):
    self.name = "Constants"
    self.category = "Count"


  def handleResults(self,
      results: Opt[Dict[analysis.AnalysisNameT,
                             Dict[types.Nid, dfv.NodeDfvL]]],
      func: obj.Func,
  ) -> Opt[List[Report]]:
    reports: List[Report] = []

    assert results, f"{func}: {results}"
    constVars = results[const.ConstA.__name__]

    assert func.cfg, f"{func}"
    count = 0
    for nodeId, node in func.cfg.nodeMap.items():
      constDfv = cast(const.OverallL, constVars[nodeId].dfvOut)
      count += constDfv.countConstants()

    print(f"Count: {count}, Func: {func.name}")

    return reports
