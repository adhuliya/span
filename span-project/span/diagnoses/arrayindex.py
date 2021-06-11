#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""The number of array index out of bounds detected."""

import logging

from span.api.analysis import AnalysisNameT
from span.api.dfv import DfvPairL
from span.ir.constructs import Func
from span.ir.types import NodeIdT

LOG = logging.getLogger(__name__)

from typing import (
  Optional as Opt, Dict, List
)

from span.api.diagnosis import (
  DiagnosisRT,
  PlainMethod, CascadingMethod, LernerMethod, SpanMethod, Report,
)

class ArrayIndexOutOfBoundsR(DiagnosisRT):

  # MethodSequence = [] # use parent defined


  def __init__(self):
    self.name = "ArrayIndexBounds"
    self.category = "Count"


  def computeResults(self,
      method: str = SpanMethod,
      config: int = 0,
  ):
    if method == SpanMethod:
      print()

  def handleResults(self,
      results: Opt[Dict[AnalysisNameT, Dict[NodeIdT, DfvPairL]]],
      func: Func,
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
