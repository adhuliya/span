#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""Detect the unreachable code."""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.api import dfv
from span.ir import instr
from span.ir.expr import ExprET, ArrayE
from span.ir.tunit import TranslationUnit
from span.sys.ipa import IpaHost, ipaAnalyzeCascade

from typing import (
  Optional as Opt, Dict, List, Type, Any, cast,
)

import span.util.ff as ff
from span.util import util
from span.api.analysis import AnalysisNameT, AnalysisAT, AnalysisAClassT, ValueAnalysisAT
from span.api.dfv import DfvPairL
from span.ir.constructs import Func
from span.ir.types import (
  NodeIdT, AnNameT, FuncNameT, Type as SpanType, ConstSizeArray, Ptr,
)
from span.api.dfv import AnResult # replacing span.sys.common.AnResult

from span.api.diagnosis import (
  DiagnosisRT, ClangReport,
  MethodT, PlainMethod, CascadingMethod, LernerMethod,
  SpanMethod, UseAllMethods, AllMethods, MethodDetail,
)


class UnreachableCodeR(DiagnosisRT):
  """Detect unreachable code."""

  MethodSequence: List[MethodDetail] = [
    MethodDetail(
      name=PlainMethod,
      anNames=["IntervalA"],
    ),
    MethodDetail(
      name=CascadingMethod,
      anNames=["IntervalA", "PointsToA"],
    ),
    MethodDetail(
      name=LernerMethod,
      anNames=["IntervalA", "PointsToA"],
    ),
    MethodDetail(
      name=SpanMethod,
      anNames=["IntervalA", "PointsToA"],
    ),
  ]


  def __init__(self, tUnit: TranslationUnit):
    super().__init__(name="UnreachableCode", category="Count", tUnit=tUnit)


  def computeResults(self,
      method: MethodDetail,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    anName1  = "IntervalA"
    anClass1 = anClassMap[anName1]

    total = 0

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      # anObj1 = cast(ValueAnalysisAT, anClass1(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        if self.isUnreachable(nid, anResMap[anName1]):
          total += 1

    return (total,)


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAClassT]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalUnreachableNodes: {result[0]}")


  def isUnreachable(self,
      nid: NodeIdT,
      anResult: AnResult,
  ):
    """Returns true if the nid is unreachable."""
    dfv = anResult.get(nid, None)
    if dfv is None:
      return True
    elif dfv.top or dfv.dfvIn.top:
      return True
    return False
