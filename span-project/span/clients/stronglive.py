#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""Strong Liveness analysis."""

import logging

from span.util import util

LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.ir.constructs import Func
from span.ir.tunit import TranslationUnit

from typing import Optional as Opt, Set, Tuple, List, Callable, cast, Any

from span.util.util import LS

import span.ir.types as types
from span.ir.conv import getSuffixes, simplifyName, Backward, nameHasPpmsVar
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.ir as ir
from span.ir.ir import \
  (getNamesEnv, getNamesGlobal, getExprRValueNames,
   getNamesLValuesOfExpr, getNamesUsedInExprSyntactically,
   getNamesInExprMentionedIndirectly, inferTypeOfVal)
from span.api.lattice import \
  (ChangedT, Changed, DataLT, basicEqualsTest, basicLessThanTest,
   getBasicString)
from span.api.dfv import DfvPairL
from span.api.analysis import AnalysisAT, BackwardD, SimFailed, SimPending

################################################
# BOUND START: StrongLiveVars lattice
################################################

IsLiveT = bool
Live: IsLiveT = True
Dead: IsLiveT = False


class OverallL(DataLT):


  def __init__(self,
      func: Func,
      val: Opt[Set[types.VarNameT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val: Opt[Set[types.VarNameT]] = val
    if val is not None and len(val) == 0:
      self.val, self.top, self.bot = None, True, False
    elif val is not None and self.func and val == ir.getNamesEnv(self.func):
      self.val, self.top, self.bot = None, False, True


  def meet(self, other) -> Tuple['OverallL', ChangedT]:
    """Returns glb of self and other, WITHOUT MODIFYING EITHER."""
    assert isinstance(other, OverallL), f"{other}"
    if self is other: return self, not Changed
    if self < other: return self, not Changed
    if other < self: return other, Changed

    # if here, elements are incomparable, and neither is top/bot.
    assert self.val and other.val, f"{self}, {other}"
    new = self.getCopy()
    new.setValLive(other.val)
    return new, Changed


  def getCopy(self) -> 'OverallL':
    if self.top: return OverallL(self.func, top=True)
    if self.bot: return OverallL(self.func, bot=True)
    assert self.val is not None
    return OverallL(self.func, self.val.copy())


  def getVal(self,
      varName: types.VarNameT
  ) -> IsLiveT:
    """Returns True if `varName` is live."""
    if self.top: return Dead
    if self.bot: return Live
    assert self.val is not None
    return varName in self.val


  def setVal(self,
      varNames: Set[types.VarNameT],
      liveness: IsLiveT
  ) -> None:
    if liveness is Live:
      self.setValLive(varNames)
    else:
      self.setValDead(varNames)


  def setValLive(self,
      varNames: Set[types.VarNameT]
  ) -> None:
    if self.bot or (self.val and self.val >= varNames):
      return  # varNames already live

    self.top = False  # no more a top value (if it was)
    self.val = set() if not self.val else self.val

    for varName in varNames:
      self.val.update(ir.getPrefixes(varName))

    if self.val == getNamesEnv(self.func):
      self.val, self.top, self.bot = None, False, True


  def setValDead(self,
      varNames: Set[types.VarNameT],
  ) -> None:
    if self.top or \
        (self.val and len(varNames & self.val) == 0):
      return  # varNames already dead

    self.bot = False  # no more a bot value (if it was)
    self.val = self.val if self.val is not None else getNamesEnv(self.func).copy()

    for varName in varNames:
      suffixes = getSuffixes(self.func, varName,
                             inferTypeOfVal(self.func, varName))
      for name in suffixes:
        self.val.remove(name)  # FIXME: kill all suffixes

    if not self.val:
      self.val, self.top, self.bot = None, True, False


  def localize(self, #IPA
      forFunc: Func,
      keepParams: bool = False,
      keepReturnVars: bool = False,
  ) -> 'OverallL':
    """Returns self's copy localized for the given forFunc."""
    localizedDfv = self.getCopy()
    localizedDfvVal, localizedDfvSetValDead = localizedDfv.val, localizedDfv.setValDead

    if localizedDfvVal:
      tUnit: TranslationUnit = self.func.tUnit
      varNames = localizedDfvVal
      keep = tUnit.getNamesGlobal()\
             | ({e.name for e in forFunc.getReturnExprList() if isinstance(e, expr.VarE)}
                if keepReturnVars else set())
      dropNames = varNames - keep
      # essentially removing the variables except the ppms vars
      localizedDfvSetValDead({vName for vName in dropNames if not nameHasPpmsVar(vName)})

    localizedDfv.updateFuncObj(forFunc)
    return localizedDfv


  def updateFuncObj(self, funcObj: Func): #IPA #mutates 'self'
    self.func, selfVal = funcObj, self.val # updating function object here 1


  def addLocals(self, #IPA #mutates 'self'
      fromDfv: 'OverallL',
  ) -> None:
    tUnit: TranslationUnit = self.func.tUnit
    localVars = tUnit.getNamesLocalStrict(self.func)
    if not localVars:
      return

    selfSetValLive, fromDfvGetVal = self.setValLive, fromDfv.getVal

    if fromDfv.bot:
      selfSetValLive(localVars)
    elif fromDfv.top:
      pass # nothing to do
    elif fromDfv.val:
      selfSetValLive(fromDfv.val & localVars)


  def __lt__(self, other) -> bool:
    lt = basicLessThanTest(self, other)
    return self.val >= other.val if lt is None else lt


  def __eq__(self, other) -> bool:
    if not isinstance(other, OverallL):
      return NotImplemented
    equal = basicEqualsTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    val = set() if self.val is None else self.val
    hashThisVal = frozenset(val)
    return hash((hashThisVal, self.top, self.bot))


  def __str__(self):
    s = getBasicString(self)
    return s if s else f"{set(map(simplifyName, self.val))}"


  def __repr__(self):
    return self.__str__()


################################################
# BOUND END  : StrongLiveVars lattice
################################################

################################################
# BOUND START: StrongLiveVars analysis
################################################

class StrongLiveVarsA(AnalysisAT):
  """Strongly Live Variables Analysis."""
  # liveness lattice
  L: type = OverallL
  # direction of the analysis
  D: Opt[types.DirectionT] = Backward


  needsRhsDerefToVarsSim: bool = True
  needsLhsDerefToVarsSim: bool = True
  needsNumVarToNumLitSim: bool = False
  needsNumBinToNumLitSim: bool = False
  needsCondToUnCondSim: bool = True
  needsLhsVarToNilSim: bool = False
  needsNodeToNilSim: bool = False


  def __init__(self,
      func: Func,
  ) -> None:
    super().__init__(func)
    self.overallTop: OverallL = OverallL(self.func, top=True)
    self.overallBot: OverallL = OverallL(self.func, bot=True)


  def getBoundaryInfo(self,
      nodeDfv: Opt[DfvPairL] = None,
      ipa: bool = False,
      entryFunc: bool = False,
      forFunc: Opt[Func] = None,
  ) -> DfvPairL:
    """Must generate a valid boundary info."""
    if ipa and not nodeDfv:
      raise ValueError(f"{ipa}, {nodeDfv}")

    func = forFunc if forFunc else self.func

    overallTop = self.overallTop.getCopy()
    overallTop.func = func # IMPORTANT

    if not ipa or entryFunc: #INTRA or #IPA entryFunc
      if not ipa and nodeDfv: #INTRA but explicit value given
        inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
      else: #IPA with entryFunc or #INTRA with no explicit value
        inBi = overallTop
        outBi = overallTop if entryFunc else \
          OverallL(func, val=getNamesGlobal(func))
        # Mark returned variables as live.
        retVars = set()
        for e in func.getReturnExprList():
          if isinstance(e, expr.VarE):
            retVars.add(e.name)
            if isinstance(e.type, types.RecordT):
              e.type.getNamesOfType(None, prefix=e.name)
        if retVars:
          outBi = outBi.getCopy()
          outBi.setValLive(retVars)
      return DfvPairL(inBi, outBi)  # good to create a copy
    elif ipa: #IPA
      dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
      dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())
      dfvIn.func = dfvOut.func = func

      vNames: Set[types.VarNameT] = self.getAllVars(func)

      if dfvIn.val: dfvIn.val = dfvIn.val & vNames
      if dfvOut.val: dfvOut.val = dfvOut.val & vNames
      return DfvPairL(dfvIn, dfvOut)
    else:
      raise ValueError(f"{func.name}, {ipa}, {nodeDfv}")



  def getLocalizedCalleeBi(self, #IPA
      nodeId: types.NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: DfvPairL,  # caller's node IN/OUT
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    """See base method for doc."""
    assert insn.hasRhsCallExpr(), f"{self.func.name}, {nodeId}, {insn}, {insn.info}"

    calleeName = instr.getCalleeFuncName(insn)
    tUnit: TranslationUnit = self.func.tUnit
    calleeFuncObj = tUnit.getFuncObj(calleeName)

    # In is unchanged in Backward analyses
    if calleeBi:
      inDfv = calleeBi.dfvIn # unchanged In
    else:
      inDfv = self.overallTop.getCopy()
      inDfv.func = calleeFuncObj

    newDfvOut = nodeDfv.dfvOut.localize(calleeFuncObj, keepReturnVars=True)

    localized = DfvPairL(inDfv, newDfvOut)
    localized = self.getBoundaryInfo(localized, ipa=True, forFunc=calleeFuncObj)
    if util.LL1: LDB("CalleeCallSiteDfv(Localized): %s", localized)
    return localized


  def getAllVars(self, func: Opt[Func] = None) -> Set[types.VarNameT]:
    """Gets all the variables of the accepted type."""
    return ir.getNamesEnv(func if func else self.func)


  def isAcceptedType(self,
      t: Opt[types.Type] = None,
      name: Opt[types.VarNameT] = None,
  ) -> bool:
    return True  # liveness accepts all types

  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def Nop_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    """A backward identity transfer function."""
    nodeOut = nodeDfv.dfvOut
    nodeIn = nodeDfv.dfvIn
    if nodeIn is nodeOut:
      return nodeDfv  # to avoid making a fresh object
    else:
      return DfvPairL(nodeOut, nodeOut)


  def ExRead_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ExReadI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    newIn = OverallL(self.func, top=True)
    newIn.setValLive(insn.vars)
    return DfvPairL(newIn, nodeDfv.dfvOut)


  def UnDefVal_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    return self._killGen(nodeDfv, kill={insn.lhsName})


  def Use_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UseI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    return self._killGen(nodeDfv, gen=insn.vars)


  def CondRead_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondReadI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    lName = insn.lhs
    rNames = insn.rhs
    dfvOut = nodeDfv.dfvOut
    assert isinstance(dfvOut, OverallL), f"{dfvOut}"

    lhsIsLive = dfvOut.getVal(lName)
    if lhsIsLive:
      return self._killGen(nodeDfv, kill={lName}, gen=rNames)

    return self.Nop_Instr(nodeId, insn, nodeDfv)

  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################

  def Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    """Instr_Form: numeric: lhs = rhs.
    Convention:
      Type of lhs and rhs is numeric.
    """
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv, calleeBi)


  def Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CallI,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    dfvOut = nodeDfv.dfvOut
    if dfvOut.bot: return DfvPairL(dfvOut, dfvOut)
    varNames = self.processCallE(insn.arg, nodeDfv, calleeBi)
    if not varNames:
      return nodeDfv
    else:
      return self._killGen(nodeDfv, gen=varNames)


  def Conditional_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    return self._killGen(nodeDfv, gen={insn.arg.name})


  # def Return_Var_Instr(self,
  #     nodeId: types.NodeIdT,
  #     insn: instr.ReturnI,
  #     nodeDfv: DfvPairL
  # ) -> DfvPairL:
  #   # Consider return instruction as NopI.
  #   #   In IPA liveness of returned variables is context dependent.
  #   #   In Intra analysis case, mark all returned variables as line at BI.
  #   # return self._killGen(nodeDfv, gen={insn.arg.name})

  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Simplifiers
  ################################################

  def LhsVar__to__Nil(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[types.VarNameT]] = None,
  ) -> Opt[Set[types.VarNameT]]:
    if nodeDfv is None:
      return SimPending

    dfvOut = nodeDfv.dfvOut
    if dfvOut.top: return SimPending
    if dfvOut.bot: return SimFailed
    return dfvOut.val  # return the set of variables live

  ################################################
  # BOUND END  : Simplifiers
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def _killGen(self,
      nodeDfv: DfvPairL,
      kill: Opt[Set[types.VarNameT]] = None,
      gen: Opt[Set[types.VarNameT]] = None,
  ) -> DfvPairL:
    dfvOut = nodeDfv.dfvOut
    assert isinstance(dfvOut, OverallL), f"{dfvOut}"

    if LS: LDB(f"StrongLiveVarsA: Kill={kill}, Gen={gen}")

    if dfvOut.bot and not kill: return DfvPairL(dfvOut, dfvOut)
    if dfvOut.top and not gen: return DfvPairL(dfvOut, dfvOut)

    outVal, newIn = dfvOut.val, dfvOut
    if outVal is None:
      top, bot = dfvOut.top, dfvOut.bot
      if not (top or bot): raise ValueError(f"{dfvOut}")
      outVal = set() if top else getNamesEnv(self.func)

    realKill = kill - gen if gen and kill else kill
    if (realKill and outVal & realKill) or (gen and gen - outVal):
      newIn = dfvOut.getCopy()
      if realKill: newIn.setValDead(kill)
      if gen: newIn.setValLive(gen)
    return DfvPairL(newIn, dfvOut)


  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    """Processes all kinds of assignment instructions.
    The record types are also handled without any special treatment."""
    dfvOut = nodeDfv.dfvOut  # dfv at OUT of a node
    assert isinstance(dfvOut, OverallL), f"{dfvOut}"
    rhsNamesAreLive: bool = False
    rhsIsCallExpr: bool = isinstance(rhs, expr.CallE)

    if rhsIsCallExpr:
      print(f"CallExprRHS: {lhs} = {rhs}")

    # Find out: should variables be marked live?
    if dfvOut.bot or rhsIsCallExpr:
      rhsNamesAreLive = True

    lhsNames = getNamesLValuesOfExpr(self.func, lhs)
    assert len(lhsNames) >= 1, f"{lhsNames}: {lhs}, {nodeDfv}"
    if dfvOut.val and set(lhsNames) & dfvOut.val:
      rhsNamesAreLive = True

    if LS: LDB(f"lhsNames = {lhsNames} (live={rhsNamesAreLive})")

    # Now take action
    if not rhsNamesAreLive:
      return DfvPairL(dfvOut, dfvOut)

    if rhsIsCallExpr:
      rhsNames = self.processCallE(rhs, nodeDfv, calleeBi)
      # Remove lhsName form rhsNames, if it is not global.
      for name in lhsNames: # this loop only runs once
        if name not in getNamesGlobal(self.func):
          rhsNames.remove(name) if name in rhsNames else False
      if not rhsNames:
        return nodeDfv # return the nodeDfv as it is #TODO: check
    else:
      rhsNames = getNamesInExprMentionedIndirectly(self.func, rhs) \
                 | getNamesUsedInExprSyntactically(rhs)

    # at least one side should name only one location (a SPAN IR check)
    assert len(lhsNames) >= 1 and len(rhsNames) >= 0, \
      f"{lhs} ({lhsNames}) = {rhs} ({rhsNames}) {rhs.info}"

    if len(lhsNames) == 1:
      return self._killGen(nodeDfv, kill=lhsNames, gen=rhsNames)
    else:
      return self._killGen(nodeDfv, gen=rhsNames)


  def processCallE(self,
      e: expr.ExprET,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> Set[types.VarNameT]:
    assert isinstance(e, expr.CallE), f"{e}"
    if calleeBi: #IPA
      dfvIn = calleeBi.dfvIn.localize(self.func)
      dfvIn.addLocals(nodeDfv.dfvOut)
      return dfvIn.val
    else: #INTRA
      names = getNamesGlobal(self.func)
      names |= getNamesUsedInExprSyntactically(e)
      return names


  @staticmethod
  def test_dfv_assertion(
      computed: OverallL,
      strVal: str,  # a short string representation of the assertion (see tests)
  ) -> bool:
    """Returns true if assertion is correct."""

    if strVal.startswith("any"):
      return True

    if strVal.startswith("is:"):
      strVal = strVal[3:]
      if strVal.strip() in {"bot", "Bot", "BOT"}:
        return computed.bot
      elif strVal.strip() in {"top", "Top", "TOP"}:
        return computed.top
      else: # must be a set
        setOfVarNames = eval(strVal)
        return computed.val == setOfVarNames

    if strVal.startswith("has:"):
      strVal = strVal[4:]
      setOfVarNames = eval(strVal)
      return setOfVarNames <= computed.val

    raise ValueError()


  @staticmethod
  def evalString(evalThis: str) -> Any:
    """A needed function to automate test cases."""
    return eval(evalThis)

  ################################################
  # BOUND END  : Helper_Functions
  ################################################


################################################
# BOUND END  : StrongLiveVars analysis
################################################
