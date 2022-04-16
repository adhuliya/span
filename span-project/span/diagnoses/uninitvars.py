#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021

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
  Optional as Opt, Dict, List, Type, Any, cast, Set, Tuple,
)

import span.util.ff as ff
from span.util import util
from span.api.analysis import AnalysisNameT, AnalysisAT, AnalysisAT_T, ValueAnalysisAT
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
      name=PlainMethod,
      anNames=["ReachingDefA"],
    ),
    # MethodDetail(
    #   name=CascadingMethod,
    #   anNames=["ReachingDefA", "PointsToA"],
    # ),
    # MethodDetail(
    #   name=LernerMethod,
    #   anNames=["ReachingDefA", "PointsToA"],
    # ),
    MethodDetail(
      name=SpanMethod,
      anNames=["ReachingDefA", "PointsToA"],
    ),
  ]


  def __init__(self, tUnit: TranslationUnit):
    super().__init__(name="IndexOutOfBounds", category="Count", tUnit=tUnit)


  def computeResults(self,
      method: MethodDetail,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    # Logic for all the methods is here
    anName1, anName2  = "ReachingDefA", "PointsToA"
    # anClass1, anClass2 = anClassMap[anName1], anClassMap[anName2]

    totalNodes = 0
    totalUsesDirect = 0 # total use points
    totalUsesIndirect = 0 # total use points
    totalUsesInitUnreachMust = 0 # total uninit uses (must)
    totalUsesUninitMust = 0 # total uninit uses (must)
    totalUsesInitMust = 0 # total init uses (must)
    #totalUsesInitMay = 0 # total may uninitialized uses (may)

    for fName in sorted(dfvs.keys()):
      print(f"{fName}")
      anResMap = dfvs[fName]
      func = self.tUnit.getFuncObj(fName)
      # anObj1 = cast(ValueAnalysisAT, anClass1(func))
      # anObj2 = cast(ValueAnalysisAT, anClass2(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        totalNodes += 1
        ptsAnResult = None if method.name == PlainMethod else anResMap[anName2]

        directUse, indirectUse = self.getVarNamesUsed(func, nid, insn, ptsAnResult)

        if not (directUse or indirectUse):
          continue # no variable used, goto next insn

        directDfvMap = self.getVarDefsDfvMap(nid, directUse, anResMap[anName1])
        indirectDfvMap = self.getVarDefsDfvMap(nid, indirectUse, anResMap[anName1])

        totalUsesDirect += len(directDfvMap)
        totalUsesIndirect += len(indirectDfvMap)

        for vName, dfv in directDfvMap.items():
          if dfv is None: # None if nid is unreachable
            totalUsesInitUnreachMust += 1 # unreachable code is assumed initialized
          elif dfv.isInitialized(must=True):
            totalUsesInitMust += 1
          elif dfv.isUnInitialized(must=True):
            print(f"  UNINIT_MUST1: {insn}, {vName}:{dfv}, ({insn.info})")
            totalUsesUninitMust += 1
          # elif dfv.isInitialized(must=False):
          #   totalUsesInitMay += 1 # may uninitialized (excluded must)

        mustInit = mustUninit = True
        for vName, dfv in indirectDfvMap.items():
          if dfv is None: # None if nid is unreachable
            print(f"  INIT_NONE: {insn}, {vName}:{dfv} ({func.name}, {insn.info}")
            continue
          if not dfv.isInitialized(must=True):
            mustInit = False
          if not dfv.isUnInitialized(must=True):
            mustUninit = False

        if mustInit:
          totalUsesInitMust += 1
        elif mustUninit:
          print(f"  UNINIT_MUST2: {insn}, {indirectUse}, ({func.name}, {insn.info})")
          totalUsesUninitMust += 1

    return totalNodes, totalUsesDirect, totalUsesIndirect, totalUsesInitMust,\
           totalUsesUninitMust, 0, totalUsesInitUnreachMust


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalNodes              : {result[0]}")
    print(f"  TotalUsesDirect         : {result[1]}")
    print(f"  TotalUsesIndirect       : {result[2]}")
    print(f"  TotalUsesInitMust       : {result[3]}")
    print(f"  TotalUsesUninitMust     : {result[4]}")
    # print(f"  TotalUsesInitMay        : {result[5]} (does not include must init)")
    print(f"  TotalUsesInitUnreachMust: {result[6]}")


  def getVarNamesUsed(self,
      func: Func,
      nid: NodeIdT,
      insn: InstrIT,
      ptsAnResult: Opt[AnResult] = None,
  ) -> Tuple[Set[VarNameT], Set[VarNameT]]:
    """Returns var names possibly used in an expression."""
    names = instr.getNamesUsedInInstrSyntactically(insn, True, False)
    de = instr.getDerefExpr(insn, includeLhs=False)

    if not de:
      return names, set()

    # if here, there is a deref expression as rvalue
    if not ptsAnResult: # in case of plain method
      return names, self.tUnit.getNamesEnv(func, de.type)
    else:
      derefVar = expr.getDereferencedVar(de)
      dfv, ptsRes = None, ptsAnResult.get(nid)
      if ptsRes:
        dfv = ptsRes.dfvIn.getVal(derefVar.name)

      if not dfv or dfv.bot:
        return names, self.tUnit.getNamesEnv(func, de.type)
      elif dfv.top:
        return names, set()
      else:
        return names, dfv.val


  def getVarDefsDfvMap(self,
      nid,
      varNamesUsed: Set[VarNameT],
      anResult: AnResult,
  ) -> Dict[VarNameT, ComponentL]:
    if not varNamesUsed:
      return dict()

    resMap, nidRes = {}, anResult.get(nid)
    for vName in varNamesUsed:
      resMap[vName] = None if nidRes is None else nidRes.dfvIn.getVal(vName)
    return resMap


