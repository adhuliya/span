#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""The number of uninitialized variables used."""

import logging

from span.ir.instr import InstrIT, AssignI

LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.api import dfv
from span.ir import instr, expr, ir
from span.ir.expr import ExprET, ArrayE
from span.ir.tunit import TranslationUnit
from span.sys.ipa import IpaHost, ipaAnalyzeCascade

from typing import (
  Optional as Opt, Dict, List, Type, Any, cast, Set,
)

import span.util.ff as ff
from span.util import util
from span.api.analysis import AnalysisNameT, AnalysisAT, AnalysisAClassT, ValueAnalysisAT
from span.api.dfv import DfvPairL, ComponentL
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


class UninitializedVarsR(DiagnosisRT):
  """The number of uninitialized variables used."""

  MethodSequence: List[MethodDetail] = [
    MethodDetail(
      PlainMethod,
      [0],
      ["ReachingDefA"],
    ),
    # MethodDetail(
    #   CascadingMethod,
    #   [0],
    #   ["ReachingDefA", "PointsToA"],
    # ),
    # MethodDetail(
    #   LernerMethod,
    #   [0],
    #   ["ReachingDefA", "PointsToA"],
    # ),
    MethodDetail(
      SpanMethod,
      [0],
      ["ReachingDefA", "PointsToA"],
    ),
  ]


  def __init__(self, tUnit: TranslationUnit):
    super().__init__(name="IndexOutOfBounds", category="Count", tUnit=tUnit)


  def computeResults(self,
      method: MethodDetail,
      config: int,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    # Logic for all the methods is here
    anName1, anName2  = "ReachingDefA", "PointsToA"
    # anClass1, anClass2 = anClassMap[anName1], anClassMap[anName2]

    totalUses = 0 # total use points
    totalUsesUninitMust = 0 # total uninit uses (must)
    totalUsesInitMust = 0 # total init uses (must)

    for fName, anResMap in dfvs.items():
      func = self.tUnit.getFuncObj(fName)
      # anObj1 = cast(ValueAnalysisAT, anClass1(func))
      # anObj2 = cast(ValueAnalysisAT, anClass2(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        ptsAnResult = None if method.name == PlainMethod else anResMap[anName2]

        varNamesUsed = self.getVarNamesUsed(func, nid, insn, ptsAnResult)

        if not varNamesUsed:
          continue # no variable used, goto next insn

        varDefsDfvMap = self.getVarDefsDfvMap(nid, varNamesUsed, anResMap[anName1])

        totalUses += len(varNamesUsed)

        for vName, dfv in varDefsDfvMap.items():
          if dfv is None: # None if nid is unreachable
            totalUsesInitMust += 1 # unreachable code is assumed initialized
          elif dfv.isInitialized(must=True):
            totalUsesInitMust += 1
          elif not dfv.isInitialized(must=False):
            totalUsesUninitMust += 1

    return totalUses, totalUsesInitMust, totalUsesUninitMust


  def handleResults(self,
      method: MethodDetail,
      config: int,
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


  def getVarNamesUsed(self,
      func: Func,
      nid: NodeIdT,
      insn: InstrIT,
      ptsAnResult: Opt[AnResult] = None,
  ) -> Set[VarNameT]:
    """Returns var names possibly used in an expression."""
    names = instr.getNamesUsedInExprSyntactically(insn)
    de = instr.getDerefExpr(insn, includeLhs=False)

    if not de:
      return names

    # if here, there is a deref expression as rvalue
    if not ptsAnResult: # in case of plain method
      return names | self.tUnit.getNamesEnv(func, de.type)
    else:
      derefName = expr.getDereferencedVar(de)
      dfv, ptsRes = None, ptsAnResult.get(nid)
      if ptsRes:
        dfv = ptsRes.dfvIn.getVal(derefName)

      if not dfv or dfv.bot:
        return names | self.tUnit.getNamesEnv(func, de.type)
      elif dfv.top:
        return names
      else:
        return names | dfv.val


  def getVarDefsDfvMap(self,
      nid,
      varNamesUsed: Set[VarNameT],
      anResult: AnResult,
  ) -> Dict[VarNameT, ComponentL]:
    resMap, nidRes = {}, anResult.get(nid)
    for vName in varNamesUsed:
      resMap[vName] = None if nidRes is None else nidRes.dfvIn.getVal(vName)
    return resMap


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


