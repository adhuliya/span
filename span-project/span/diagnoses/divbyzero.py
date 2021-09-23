#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""The number divisions that are safe (i.e. no-div-by-zero)"""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.api import dfv
from span.ir import instr, op
from span.ir.expr import ExprET, ArrayE, BinaryE
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


class DivByZeroR(DiagnosisRT):
  """The number divisions that are safe (i.e. no-div-by-zero)"""

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
    super().__init__(name="IndexOutOfBounds", category="Count", tUnit=tUnit)


  def computeResults(self,
      method: MethodDetail,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    """Count array indexes, and count out-of-bounds indexes."""
    # if method.name == PlainMethod:
    #   return self.computeResultsUsingPlainMethod(method, config, dfvs, anClassMap)

    # Logic for all the methods is here (except the PlainMethod)
    anName1 = "IntervalA"
    anClass1 = anClassMap[anName1]

    totalNodesTop = 0
    totalDivs = 0
    totalSafeDivs = 0
    totalBotDivs = 0  # the divisor's dfv is Bot

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      anObj1 = cast(ValueAnalysisAT, anClass1(func))
      # anObj2 = cast(ValueAnalysisAT, anClass2(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        if not isinstance(insn, instr.AssignI):
          continue

        rhs = insn.rhs
        if not isinstance(rhs, BinaryE):
          continue
        if rhs.opr != op.BO_DIV:
          continue

        # if here, rhs is a binary expression with division
        totalDivs += 1
        divisorExpr = rhs.arg2
        divisorDfv = self.getExprDfv(divisorExpr, nid, anResMap[anName1], anObj1)

        if divisorDfv.bot:
          print(f"   BOT_DIV: {insn} ({func.name}, {insn.info})")
          totalBotDivs += 1
        elif divisorDfv.top:
          print(f"   TOP_DIV: {insn} ({func.name}, {insn.info})")
          totalNodesTop += 1
          totalSafeDivs += 1 # unreachable code is assumed safe
        elif not divisorDfv.inRange(0):
          print(f"  SAFE_DIV: {insn} ({func.name}, {insn.info})")
          totalSafeDivs += 1

    return totalNodesTop, totalDivs, totalSafeDivs, totalBotDivs


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalNodesTop: {result[0]}")
    print(f"  TotalDivs    : {result[1]}")
    print(f"  TotalSafeDivs: {result[2]}")
    print(f"  TotalBotDivs : {result[3]}")


  def getExprDfv(self,
      e: ExprET,
      nid: NodeIdT,
      anResult: AnResult,
      anObj : ValueAnalysisAT,
  ) -> Opt[dfv.ComponentL]:
    dfvPair = anResult.get(nid)
    if dfvPair:
      return anObj.getExprDfv(e, cast(dfv.OverallL, dfvPair.dfvIn))


