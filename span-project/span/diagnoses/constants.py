#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""Computes the number of constants at use point."""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.api import dfv
from span.ir import instr
from span.ir.expr import ExprET, ArrayE
from span.ir.tunit import TranslationUnit
from span.sys.ipa import IpaHost, ipaAnalyzeCascade

from typing import (
  Optional as Opt, Dict, List, Type, Any, cast, Set,
)

import span.util.ff as ff
from span.util import util
from span.api.analysis import AnalysisNameT, AnalysisAT, AnalysisAT_T, ValueAnalysisAT
from span.api.dfv import DfvPairL
from span.ir.constructs import Func
from span.ir.types import (
  NodeIdT, AnNameT, FuncNameT, Type as SpanType, ConstSizeArray, Ptr, VarNameT,
)
from span.api.dfv import AnResult # replacing span.sys.common.AnResult

from span.api.diagnosis import (
  DiagnosisRT, ClangReport,
  MethodT, PlainMethod, CascadingMethod, LernerMethod,
  SpanMethod, UseAllMethods, AllMethods, MethodDetail,
)


class ConstantsUsedR(DiagnosisRT):
  """Computes the number of constants at use point."""

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
    # Logic for all the methods is here
    anName1, anName2  = "IntervalA", "PointsToA"
    anClass1, anClass2 = anClassMap[anName1], anClassMap[anName2]

    totalConstantsUsed = 0

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      anObj1 = cast(ValueAnalysisAT, anClass1(func))
      anObj2 = cast(ValueAnalysisAT, anClass2(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        constVarNames = self.getConstVarNames(nid, anResMap[anName1])
        insnVarNames = instr.getNamesUsedInInstrSyntactically(insn)

        names = insnVarNames & constVarNames
        totalConstantsUsed += len(names)

    return (totalConstantsUsed,)


  def handleResults(self,
      method: MethodDetail,
      config: int,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalConstsUsed: {result[0]}")


  def getConstVarNames(self,
      nid: NodeIdT,
      anResult: Opt[AnResult] = None,
  ) -> Opt[Set[VarNameT]]:
    if not anResult:
      return None

    dfvPair = anResult.get(nid)
    if dfvPair:
      return dfvPair.dfvIn.getNamesWithConstValue()
    else:
      return None


  def computeDfvsUsingPlainMethod(self,
      method: MethodDetail,
      config: int,
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
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
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
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
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
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
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
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


