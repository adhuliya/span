#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""The number of array index out-of-bounds or in-bounds detected."""

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


class ArrayIndexOutOfBoundsR(DiagnosisRT):
  """The number of array index out-of-bounds or in-bounds detected."""

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
    if method.name == PlainMethod:
      return self.computeResultsUsingPlainMethod(method, dfvs, anClassMap)

    # Logic for all the methods is here (except the PlainMethod)
    anName1, anName2  = "IntervalA", "PointsToA"
    anClass1, anClass2 = anClassMap[anName1], anClassMap[anName2]

    total = 0
    inRangeTotal = 0
    outOfRangeTotal = 0
    unknownTotal = 0 # couldn't determine

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      anObj1 = cast(ValueAnalysisAT, anClass1(func))
      anObj2 = cast(ValueAnalysisAT, anClass2(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        arrayE = instr.getArrayE(insn)

        if not arrayE: continue   # goto next instruction in sequence
        total += 1

        indexDfv, arrType, arrIndex = None, arrayE.of.type, arrayE.index

        size = self.getArraySize(arrayE, nid, anResMap[anName2], anObj2)
        indexDfv = self.getExprDfv(arrIndex, nid, anResMap[anName1], anObj1)

        if not size or indexDfv.bot:
          unknownTotal += 1
          self.printDebugInfo(nid, arrayE, size, indexDfv, func.name, "Unknown")
        elif indexDfv.top:
          inRangeTotal += 1 # top because of unreachable code, thus any range okay
        else:
          if indexDfv.inIndexRange(size):
            inRangeTotal += 1
            self.printDebugInfo(nid, arrayE, size, indexDfv, func.name, "InRange")
          else:
            outOfRangeTotal += 1
            self.printDebugInfo(nid, arrayE, size, indexDfv, func.name, "OutOfRange")

    return total, inRangeTotal, outOfRangeTotal, unknownTotal


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAClassT]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  Total      : {result[0]}")
    print(f"  InRange    : {result[1]}")
    print(f"  OutOfRange : {result[2]}")
    print(f"  Unknown    : {result[3]}")


  def computeResultsUsingPlainMethod(self,
      method: MethodDetail,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    """Count array indexes, and count out-of-bounds indexes.

    It only uses IntervalA.
    """
    anName1 = "IntervalA"
    anClass1 = anClassMap[anName1]

    total = 0
    inRangeTotal = 0
    outOfRangeTotal = 0
    unknownTotal = 0 # couldn't determine

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      anObj1 = cast(ValueAnalysisAT, anClass1(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        arrayE = instr.getArrayE(insn)

        if not arrayE: continue   # goto next instruction in sequence
        total += 1

        indexDfv, arrType, arrIndex = None, arrayE.of.type, arrayE.index

        size = self.getArraySize(arrayE, nid)
        indexDfv = self.getExprDfv(arrIndex, nid, anResMap[anName1], anObj1)

        if not size or indexDfv.bot:
          unknownTotal += 1
          self.printDebugInfo(nid, arrayE, size, indexDfv, func.name, "Unknown")
        elif indexDfv.top:
          inRangeTotal += 1 # top because of unreachable code, thus any range okay
        else:
          if indexDfv.inIndexRange(size):
            inRangeTotal += 1
            self.printDebugInfo(nid, arrayE, size, indexDfv, func.name, "InRange")
          else:
            outOfRangeTotal += 1
            self.printDebugInfo(nid, arrayE, size, indexDfv, func.name, "OutOfRange")

    return total, inRangeTotal, outOfRangeTotal, unknownTotal


  def getArraySize(self,
      arrayE: ArrayE,
      nid: NodeIdT,
      anResult: Opt[AnResult] = None,
      anObj : Opt[ValueAnalysisAT] = None,
  ) -> Opt[int]:
    arrType, arrIndex = arrayE.of.type, arrayE.index

    size = None
    if isinstance(arrType, ConstSizeArray):
      size = arrType.size
    elif anResult and anObj and isinstance(arrType, Ptr):
      pointeesDfv = self.getExprDfv(arrayE.of, nid, anResult, anObj)
      if pointeesDfv and not pointeesDfv.bot and not pointeesDfv.top:
        minSize = ff.LARGE_INT_VAL
        for vName in pointeesDfv.val: # find minimum size
          vType = self.tUnit.inferTypeOfVal(vName)
          if isinstance(vType, ConstSizeArray):
            minSize = vType.size if minSize > vType.size else minSize
          else: # a pointee is not a ConstSizeArray, no benefit to continue
            minSize = ff.LARGE_INT_VAL
            break
        if minSize != ff.LARGE_INT_VAL:
          size = minSize

    return size


  def getExprDfv(self,
      e: ExprET,
      nid: NodeIdT,
      anResult: AnResult,
      anObj : ValueAnalysisAT,
  ) -> Opt[dfv.ComponentL]:
    dfvPair = anResult.get(nid)
    if dfvPair:
      return anObj.getExprDfv(e, cast(dfv.OverallL, dfvPair.dfvIn))


  def printDebugInfo(self,
      nid: NodeIdT,
      arrayE: ArrayE,
      size: int,
      indexDfv: Opt[dfv.ComponentL],
      funcName: FuncNameT,
      msg: str,
  ) -> None:
    print(f"  {msg}({nid}): {indexDfv},"
          f" {arrayE} (size:{size}, {arrayE.info}), {funcName}.")


