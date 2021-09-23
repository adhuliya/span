#!/usr/bin/env python3

# MIT License
# Copyright (c) 2021 Anshuman Dhuliya

"""The number of definitions reaching variables use."""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.ir.instr import InstrIT, AssignI

from span.api import dfv
from span.ir import instr, expr, ir, conv
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


class DefUseR(DiagnosisRT):
  """The number of definitions reaching variables use."""

  MethodSequence: List[MethodDetail] = [
    MethodDetail(
      name=PlainMethod,
      anNames=["ReachingDefA"],
    ),
    MethodDetail(
      name=CascadingMethod,
      anNames=["PointsToA", "ReachingDefA"],
    ),
    MethodDetail(
      name=LernerMethod,
      anNames=["ReachingDefA", "PointsToA"],
    ),
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
    totalDefsReaching = 0
    totalDefsReachingFuncEnd = 0
    totalUses = 0
    lastNid = -1

    for fName in sorted(dfvs.keys()):
      anResMap = dfvs[fName]
      func = self.tUnit.getFuncObj(fName)

      allVars = self.tUnit.getNamesEnv(func)
      nonTmpVars = self.removeTmp(allVars)
      nonTmpVarRatio = len(nonTmpVars)/len(allVars)

      # anObj1 = cast(ValueAnalysisAT, anClass1(func))
      # anObj2 = cast(ValueAnalysisAT, anClass2(func))

      for nid, insn in func.yieldNodeIdInstrTupleSeq():
        lastNid = nid
        totalNodes += 1
        ptsAnResult = anResMap[anName2] if method.name != PlainMethod else None

        directUse, indirectUse = self.getVarNamesUsed(func, nid, insn, ptsAnResult,
                                                      method.name == SpanMethod)
        directUse = self.removeTmp(directUse)
        indirectUse = self.removeTmp(indirectUse)

        if not (directUse or indirectUse):
          continue # no variable used, goto next insn

        totalUses += len(directUse) + len(indirectUse)

        useDfvMap = self.getVarDefsDfvMap(nid, directUse, anResMap[anName1])
        useDfvMap.update(self.getVarDefsDfvMap(nid, indirectUse, anResMap[anName1]))

        allDefPoints = 0
        for vName, dfv in useDfvMap.items():
          if dfv.top:
            totalDefsReaching += 1 # assume uninitialized
          elif dfv.bot:
            allDefPoints += 100 # a lower approximation when #defs > 100.
            # assert False, f"{vName}, {dfv}, {dfv.func.name}"
          else:
            allDefPoints += len(dfv.val)

        totalDefsReaching += allDefPoints

      totalDefsReachingFuncEnd = self.getAllReachingDefs(
        lastNid, func, anResMap[anName1])

    return totalNodes, totalDefsReaching, totalDefsReachingFuncEnd, totalUses


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> None:
    print(f"AnalysisType: {self.__class__.__name__}")
    print(f"Method: {method}")
    print(f"  TotalNodes              : {result[0]}")
    print(f"  TotalDefsReaching       : {result[1]}")
    print(f"  TotalDefsReachingFuncEnd: {result[2]}")
    print(f"  TotalUses               : {result[3]}")


  def getVarNamesUsed(self,
      func: Func,
      nid: NodeIdT,
      insn: InstrIT,
      ptsAnResult: Opt[AnResult] = None,
      spanMethod: bool = False,
  ) -> Tuple[Set[VarNameT], Set[VarNameT]]:
    """Returns var names possibly used in an expression."""
    names = instr.getNamesUsedInInstrSyntactically(insn, True, False)
    de = instr.getDerefExpr(insn, includeLhs=False)

    if not de:
      return names, set()

    # return names, self.tUnit.getNamesEnv(func, de.type)

    # if here, there is a deref expression as rvalue
    if not ptsAnResult: # in case of plain method
      return names, self.removeTmp(self.tUnit.getNamesEnv(func, de.type))
    else:
      derefVar = expr.getDereferencedVar(de)
      dfv, ptsRes = None, ptsAnResult.get(nid)
      if ptsRes:
        dfv = ptsRes.dfvIn.getVal(derefVar.name)

      if not dfv or dfv.bot:
        return names, self.removeTmp(self.tUnit.getNamesEnv(func, de.type))
      elif dfv.top:
        return names, set()
      else:
        # if len(dfv.val) > 1 and not spanMethod:
        #   return names, self.tUnit.getNamesEnv(func, de.type)
        # else:
        return names, self.removeTmp(dfv.val) # taking points-to set of non-tmp vars


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


  def getAllReachingDefs(self,
      nid: NodeIdT,
      func: Func,
      anResult: AnResult,
  ) -> int:
    resMap, nidRes = {}, anResult.get(nid)
    allDefs = 0
    dfvIn = nidRes.dfvIn
    for vName in self.tUnit.getNamesEnv(func):
      val = dfvIn.getVal(vName)
      if val.val:
        allDefs = len(val.val)
      elif val.bot:
        allDefs += 100

    return allDefs


  def removeTmp(self, varNameSet: Set[VarNameT]) -> Set[VarNameT]:
    nonTmpVars = set()
    for vName in varNameSet:
      if not conv.isTmpVar(vName):
        nonTmpVars.add(vName)
    return nonTmpVars
