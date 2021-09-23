#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""Computes the average number of pointees of deref expressions."""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.api import dfv
from span.ir import instr
from span.ir.expr import ExprET, ArrayE
from span.ir.tunit import TranslationUnit
from span.sys.ipa import IpaHost

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


class AvgDerefR(DiagnosisRT):
  """Computes the average number of pointees of deref expressions."""

  MethodSequence: List[MethodDetail] = [
    MethodDetail(
      name=PlainMethod,
      anNames=["PointsToA"],
    ),
    MethodDetail(
      name=SpanMethod,
      anNames=["PointsToA"],
    ),
    MethodDetail(
      name=SpanMethod,
      anNames=["PointsToA", "IntervalA"],
    ),
  ]


  def __init__(self, tUnit: TranslationUnit):
    super().__init__(name="IndexOutOfBounds", category="Count", tUnit=tUnit)
    # holds the result, as it is used between methods
    self.res = None


  def computeDfvs(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Opt[Dict[FuncNameT, Dict[AnNameT, AnResult]]]:
    """Compute the DFVs necessary to detect index out of bounds."""
    if util.LL0: LDB("ComputeDFVs: Method=%s", method)

    if self.res is None:
      self.res = self.computeDfvsUsingPlainMethod(method, anClassMap)

    return self.res


  def computeResults(self,
      method: MethodDetail,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    """Count array indexes, and count out-of-bounds indexes."""

    plainMethod = method.name == PlainMethod

    anName = "PointsToA"
    anClass = anClassMap[anName]

    totalDereferences = 0
    totalPointees = 0

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      # anObj = cast(ValueAnalysisAT, anClass(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        var = instr.getDereferencedVar(insn)

        if not var:
          continue   # goto next instruction in sequence

        totalDereferences += 1

        varDfv = anResMap[anName].get(nid).dfvIn.getVal(var.name) # type is okay

        if not varDfv or varDfv.top: # may be None
          continue     # an unreachable nid has no pointees in its exprs
        elif varDfv.bot:
          pointees = self.tUnit.getNamesEnv(func) #, var.type.getPointeeType())
          totalPointees += len(pointees)
        else:
          if plainMethod:
            if len(varDfv.val) > 1:
              # a plainMethod
              pointees = self.tUnit.getNamesEnv(func) #, var.type.getPointeeType())
              totalPointees += len(pointees)
              # if len(pointees) < len(varDfv.val):
              #   print(f"({var}, {var.type}): AllPossiblePointees: {pointees},"
              #         f"\nComputedPointees: {varDfv}")
            else:
              totalPointees += len(varDfv.val)  # i.e. +1
          else:
            totalPointees += len(varDfv.val)

    return totalDereferences, totalPointees


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalDereferences  : {result[0]}")
    print(f"  TotalPointees      : {result[1]}")
    print(f"  AvgDerefs          : {result[1]/result[0]}")


  def computeDfvsUsingPlainMethod(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> Opt[Dict[FuncNameT, Dict[AnNameT, AnResult]]]:
    assert len(anClassMap) == 1, f"{anClassMap}"

    mainAnalysis = method.anNames[0]
    ipaHost = IpaHost(
      self.tUnit,
      mainAnName=mainAnalysis,
      maxNumOfAnalyses=1,
    )
    res = ipaHost.analyze()

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


