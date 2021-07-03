#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""The interval of numeric variables."""

import logging

from span.ir.cfg import CfgNode

LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.api import dfv
from span.ir import instr
from span.ir.expr import ExprET, ArrayE
from span.ir.tunit import TranslationUnit
from span.sys.ipa import IpaHost

from typing import (
  Optional as Opt, Dict, List, Type, Any, cast, Tuple,
)

import span.util.ff as ff
from span.util import util
from span.api.analysis import AnalysisNameT, AnalysisAT, AnalysisAClassT, ValueAnalysisAT
from span.api.dfv import DfvPairL
from span.ir.constructs import Func
from span.ir.types import (
  NodeIdT, AnNameT, FuncNameT, Type as SpanType, ConstSizeArray, Ptr, VarNameT,
)
from span.api.dfv import AnResult # replacing span.sys.common.AnResult

from span.api.diagnosis import (
  DiagnosisRT, ClangReport,
  MethodT, PlainMethod, CascadingMethod, LernerMethod,
  SpanMethod, UseAllMethods, AllMethods, MethodDetail, CompareAll,
)


class IntervalR(DiagnosisRT):
  """Finds interval of numeric variables."""

  MethodSequence: List[MethodDetail] = [
    MethodDetail( # just to warmup pypy3
      name=CascadingMethod,
      anNames=["IntervalA", "PointsToA"],
    ),
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
    MethodDetail(
      name=CompareAll,
      anNames=[],
    ),
  ]


  def __init__(self, tUnit: TranslationUnit):
    super().__init__(name="IntervalPrecision", category="Count", tUnit=tUnit)
    self.res: Dict[MethodT, Dict[Tuple[CfgNode, VarNameT], dfv.ComponentL]] = dict()


  def computeResults(self,
      method: MethodDetail,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    """Find the range calculated at a numeric use point."""
    self.res[method.name] = dict()

    # Logic for all the methods
    # anName1, anName2  = "IntervalA", "PointsToA"
    anName1 = "IntervalA"
    # anClass1, anClass2 = anClassMap[anName1], anClassMap[anName2]
    anClass1 = anClassMap[anName1]

    totalNodes = 0
    totalNumericNames = 0
    constantValueTotal = 0
    finiteRangeTotal = 0
    posInfOnlyTotal = 0
    negInfOnlyTotal = 0
    unknownTotal = 0 # couldn't determine

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      anObj1 = cast(ValueAnalysisAT, anClass1(func))
      # anObj2 = cast(ValueAnalysisAT, anClass2(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        totalNodes += 1
        names = instr.getNamesUsedInInstrSyntactically(insn, True, False)

        if not names: continue   # goto next instruction in sequence

        for name in names:
          ntype = self.tUnit.inferTypeOfVal(name)
          if not ntype.isNumeric():
            continue

          totalNumericNames += 1

          nameDfv = self.getNameDfv(name, nid, anResMap[anName1])

          if not nameDfv:
            pass # for None value
          elif nameDfv.bot:
            unknownTotal += 1
          elif nameDfv.top:
            print(f"  TOP_VAL: {insn}, ({name}:{nameDfv}), ({func.name},{insn.info})")
            pass # nothing to do for top
          elif nameDfv.isConstant():
            print(f"  CONSTANT: {name}, {nameDfv}, ({insn}, {func.name}, {insn.info})")
            constantValueTotal += 1
          elif nameDfv.isFinite():
            print(f"  FINITE  : {name}, {nameDfv}, ({insn}, {func.name}, {insn.info})")
            finiteRangeTotal += 1
          elif nameDfv.isPositiveOrZero():
            posInfOnlyTotal += 1
          elif nameDfv.isNegativeOrZero():
            negInfOnlyTotal += 1
          else:
            pass
            # raise ValueError(f"{name}, {nameDfv}")

    return (totalNodes, totalNumericNames, constantValueTotal, finiteRangeTotal,
            posInfOnlyTotal, negInfOnlyTotal, unknownTotal)


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAClassT]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalNodes            : {result[0]}")
    print(f"  TotalNumericNames     : {result[1]}")
    print(f"  TotalConstantValues   : {result[2]}")
    print(f"  TotalFiniteRange      : {result[3]}")
    print(f"  TotalPositiveRange    : {result[4]}")
    print(f"  TotalNegativeRange    : {result[5]}")
    print(f"  TotalUnknown          : {result[6]}")


  def getNameDfv(self,
      name: VarNameT,
      nid: NodeIdT,
      anResult: AnResult,
  ) -> Opt[dfv.ComponentL]:
    dfvPair = anResult.get(nid)
    if dfvPair:
      return cast(dfv.OverallL, dfvPair.dfvIn).getVal(name)

