#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021

"""Detect possible null dereferences."""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.api import dfv
from span.ir import instr, conv
from span.ir.expr import ExprET, ArrayE
from span.ir.tunit import TranslationUnit
from span.sys.ipa import IpaHost, ipaAnalyzeCascade

from typing import (
  Optional as Opt, Dict, List, Type, Any, cast,
)

import span.util.ff as ff
from span.util import util
from span.api.analysis import AnalysisNameT, AnalysisAT, AnalysisAT_T, ValueAnalysisAT
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


class NullDerefR(DiagnosisRT):
  """Computes possible null dereferences."""

  MethodSequence: List[MethodDetail] = [
    MethodDetail(
      name=PlainMethod,
      anNames=["PointsToA"],
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
    super().__init__(name="NullDeref", category="Count", tUnit=tUnit)
    # holds the result, as it is used between methods
    self.res = None


  def computeResults(self,
      method: MethodDetail,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    anName1 = "PointsToA"
    anClass1 = anClassMap[anName1]

    totalDerefs = 0
    totalSafeDerefs = 0
    totalBotDerefs = 0 # where pointees are bots
    totalNullDeref = 0

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      # anObj1 = cast(ValueAnalysisAT, anClass1(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        var = instr.getDereferencedVar(insn)

        if not var:
          continue   # goto next instruction in sequence

        totalDerefs += 1

        varDfv = anResMap[anName1].get(nid).dfvIn.getVal(var.name) # type is okay

        if (
            not varDfv
            or varDfv.top
        ): # may be None (if variable is an array then too it may be None)
          totalSafeDerefs += 1
        elif varDfv.bot:
          totalBotDerefs += 1
        elif not conv.NULL_OBJ_NAME in varDfv.val:
          totalSafeDerefs += 1
        elif conv.NULL_OBJ_NAME in varDfv.val and len(varDfv.val) == 1:
          totalNullDeref += 1

    return totalDerefs, totalSafeDerefs, totalBotDerefs, totalNullDeref


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalDerefs    : {result[0]}")
    print(f"  TotalSafeDerefs: {result[1]}")
    print(f"  TotalBotDerefs : {result[2]}")
    print(f"  TotalNullDerefs: {result[3]}")
