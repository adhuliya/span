#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

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


class NullDerefR(DiagnosisRT):
  """Computes the average number of pointees of deref expressions."""

  MethodSequence: List[MethodDetail] = [
    MethodDetail(
      PlainMethod,
      [0],
      ["PointsToA"],
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
    # holds the result, as it is used between methods
    self.res = None


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
    elif method.name == CascadingMethod:
      res = self.computeDfvsUsingCascadingMethod(method, config, anClassMap)
    elif method.name == LernerMethod:
      res = self.computeDfvsUsingLernerMethod(method, config, anClassMap)
    elif method.name == SpanMethod:
      res = self.computeDfvsUsingSpanMethod(method, config, anClassMap)

    return res


  def computeResults(self,
      method: MethodDetail,
      config: int,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    anName1 = "PointsToA"
    anClass1 = anClassMap[anName1]

    totalDerefs = 0
    totalSafeDerefs = 0
    totalBotDerefs = 0 # where pointees are bots

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

    return totalDerefs, totalSafeDerefs, totalBotDerefs


  def handleResults(self,
      method: MethodDetail,
      config: int,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAClassT]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalDerefs    : {result[0]}")
    print(f"  TotalSafeDerefs: {result[1]}")
    print(f"  TotalBotDerefs : {result[2]}")


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
    res = ipaHost.analyze()

    return res


  def computeDfvsUsingLernerMethod(self,
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
      useTransformation=True, # this induces lerner's method
    )
    res = ipaHost.analyze()

    return res


  def computeDfvsUsingCascadingMethod(self,
      method: MethodDetail,
      config: int,
      anClassMap: Dict[AnNameT, Type[AnalysisAClassT]],
  ) -> Dict[FuncNameT, Dict[AnNameT, AnResult]]:
    assert len(anClassMap) == 2, f"{anClassMap}, {config}"

    res = ipaAnalyzeCascade(self.tUnit, method.anNames)
    return res


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


