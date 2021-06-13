#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""The number of array index out of bounds detected."""

import logging

from span.api import dfv
from span.ir import instr
from span.ir.expr import ExprET, ArrayE
from span.ir.tunit import TranslationUnit
from span.sys.ipa import IpaHost

LOG = logging.getLogger(__name__)
LDB = LOG.debug

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
from span.sys.common import AnResult

from span.api.diagnosis import (
  DiagnosisRT, ClangReport,
  MethodT, PlainMethod, CascadingMethod, LernerMethod,
  SpanMethod, UseAllMethods, AllMethods, MethodDetail,
)


class ArrayIndexOutOfBoundsR(DiagnosisRT):
  """Finds array indexes that may go out of bounds."""

  MethodSequence: List[MethodDetail] = [
    MethodDetail(
      PlainMethod,
      [0],
      ["IntervalA"],
    ),
    MethodDetail(
      CascadingMethod,
      [0],
      ["IntervalA", "PointsToA"],
    ),
    MethodDetail(
      LernerMethod,
      [0],
      ["IntervalA", "PointsToA"],
    ),
    MethodDetail(
      SpanMethod,
      [0],
      ["IntervalA", "PointsToA"],
    ),
  ]


  def __init__(self, tUnit: TranslationUnit):
    super().__init__(name="IndexOutOfBounds", category="Count", tUnit=tUnit)


  def computeDfvs(self,
      method: MethodDetail,
      config: int, #IMPORTANT
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Opt[Dict[FuncNameT, Dict[AnNameT, AnResult]]]:
    """Compute the DFVs necessary to detect index out of bounds."""
    if util.LL0: LDB("ComputeDFVs: Method=%s, Config=%s", method, config)

    res = None
    if method.name == PlainMethod:
      res = self.computeDfvsUsingPlainMethod(method, config, anClassMap)
    # elif method == CascadingMethod:
    #   res = self.computeDfvsUsingCascadingMethod(method, config, anClassMap)
    # elif method == LernerMethod:
    #   res = self.computeDfvsUsingLernerMethod(method, config, anClassMap)
    elif method.name == SpanMethod:
      res = self.computeDfvsUsingSpanMethod(method, config, anClassMap)

    return res


  def computeResults(self,
      method: MethodDetail,
      config: int,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    """Count array indexes, and count out-of-bounds indexes."""
    if method.name == PlainMethod:
      return self.computeResultsUsingPlainMethod(method, config, dfvs, anClassMap)

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
        arrayE = instr.extractArrayE(insn)

        if not arrayE: continue   # goto next instruction in sequence
        total += 1

        arrType, arrIndex = arrayE.of.type, arrayE.index

        size = self.getArraySize(arrayE, nid, anResMap[anName2], anObj2)
        if not size:
          unknownTotal += 1
          continue                # goto next instruction in sequence

        indexDfv = self.getExprDfv(arrIndex, nid, anResMap[anName1], anObj1)

        if (not indexDfv.bot) and indexDfv.inIndexRange(size):
          inRangeTotal += 1
        elif (not indexDfv.top) and (not indexDfv.inIndexRange(size)):
          outOfRangeTotal += 1
        else:
          unknownTotal += 1

    return total, inRangeTotal, outOfRangeTotal, unknownTotal


  def handleResults(self,
      method: MethodDetail,
      config: int,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAClassT]],
  ) -> None:
    print(f"Method: {method}")
    print(f"  Total      : {result[0]}")
    print(f"  InRange    : {result[1]}")
    print(f"  OutOfRange : {result[2]}")
    print(f"  Unknown    : {result[3]}")


  def computeResultsUsingPlainMethod(self,
      method: MethodDetail,
      config: int,
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
        arrayE = instr.extractArrayE(insn)

        if not arrayE: continue   # goto next instruction in sequence
        total += 1

        arrType, arrIndex = arrayE.of.type, arrayE.index

        size = self.getArraySize(arrayE, nid)
        if not size:
          unknownTotal += 1
          continue                # goto next instruction in sequence

        indexDfv = self.getExprDfv(arrIndex, nid, anResMap[anName1], anObj1)

        if (not indexDfv.bot) and indexDfv.inIndexRange(size):
          inRangeTotal += 1
        elif (not indexDfv.top) and (not indexDfv.inIndexRange(size)):
          outOfRangeTotal += 1
        else:
          unknownTotal += 1

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


  def computeDfvsUsingPlainMethod(self,
      method: MethodDetail,
      config: int,
      anClassMap: Dict[AnNameT, Type[AnalysisAClassT]],
  ) -> Opt[Dict[FuncNameT, Dict[AnNameT, AnResult]]]:
    assert len(anClassMap) == 1, f"{anClassMap}, {config}"

    mainAnalysis = method.anNames[0]
    ipaHost = IpaHost(
      self.tUnit,
      mainAnName=mainAnalysis,
      maxNumOfAnalyses=1,
    )
    ipaHost.analyze()

    return ipaHost.vci.finalResult


  def computeDfvsUsingSpanMethod(self,
      method: MethodDetail,
      config: int,
      anClassMap: Dict[AnNameT, Type[AnalysisAClassT]],
  ) -> Dict[FuncNameT, Dict[AnNameT, AnResult]]:
    assert len(anClassMap) == 2, f"{anClassMap}, {config}"

    mainAnalysis = method.anNames[0]
    ipaHost = IpaHost(
      self.tUnit,
      mainAnName=mainAnalysis,
      otherAnalyses=method.anNames[1:],
      maxNumOfAnalyses=len(method.anNames),
    )
    ipaHost.analyze()

    return ipaHost.vci.finalResult
