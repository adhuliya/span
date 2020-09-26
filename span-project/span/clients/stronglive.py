#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Strong Liveness analysis."""

import logging

LOG = logging.getLogger("span")
from typing import Optional as Opt, Set, Tuple, List, Callable, cast

from span.util.logger import LS

import span.ir.types as types
from span.ir.conv import getSuffixes, simplifyName
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as obj
import span.ir.ir as ir
from span.ir.ir import \
  (getNamesEnv, getNamesGlobal, getExprRValueNames,
   getExprLValueNames, getNamesUsedInExprSyntactically,
   getNamesUsedInExprNonSyntactically, inferTypeOfVal)
from span.api.lattice import \
  (ChangeL, Changed, NoChange, DataLT, basicEqualTest, basicLessThanTest,
   getBasicString)
from span.api.dfv import NodeDfvL
from span.api.analysis import AnalysisAT, BackwardD, SimFailed, SimPending

################################################
# BOUND START: StrongLiveVars lattice
################################################

IsLiveT = bool
Live: IsLiveT = True
Dead: IsLiveT = False


class OverallL(DataLT):


  def __init__(self,
      func: obj.Func,
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


  def meet(self, other) -> Tuple['OverallL', ChangeL]:
    """Returns glb of self and other, WITHOUT MODIFYING EITHER."""
    assert isinstance(other, OverallL), f"{other}"
    if self is other: return self, NoChange
    if self < other: return self, NoChange
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


  def __lt__(self, other) -> bool:
    lt = basicLessThanTest(self, other)
    return self.val >= other.val if lt is None else lt


  def __eq__(self, other) -> bool:
    if not isinstance(other, OverallL):
      return NotImplemented
    equal = basicEqualTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    val = set() if self.val is None else self.val
    hashThisVal = frozenset(val)
    return hash(self.func) ^ hash((hashThisVal, self.top, self.bot))


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
  D: type = BackwardD
  simNeeded: List[Callable] = [AnalysisAT.Deref__to__Vars,
                               AnalysisAT.Cond__to__UnCond,
                               AnalysisAT.Node__to__Nil,
                              ]


  def __init__(self,
      func: obj.Func,
  ) -> None:
    super().__init__(func)
    self.overallTop: OverallL = OverallL(self.func, top=True)
    self.overallBot: OverallL = OverallL(self.func, bot=True)


  def getBoundaryInfo(self,
      nodeDfv: Opt[NodeDfvL] = None,
      ipa: bool = False,
  ) -> NodeDfvL:
    """Must generate a valid boundary info."""
    if ipa and not nodeDfv:
      raise ValueError(f"{ipa}, {nodeDfv}")

    inBi = self.overallTop
    outBi = OverallL(self.func, val=getNamesGlobal(self.func))

    if ipa:
      dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
      dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())
      dfvIn.func = dfvOut.func = self.func

      vNames: Set[types.VarNameT] = self.getAllVars()

      if dfvIn.val: dfvIn.val = dfvIn.val & vNames
      if dfvOut.val: dfvOut.val = dfvOut.val & vNames
      return NodeDfvL(dfvIn, dfvOut)

    if nodeDfv: inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
    return NodeDfvL(inBi, outBi)  # good to create a copy


  def getAllVars(self) -> Set[types.VarNameT]:
    """Gets all the variables of the accepted type."""
    return ir.getNamesEnv(self.func)


  def isAcceptedType(self) -> bool:
    return True  # liveness accepts all types

  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def Nop_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """An identity backward transfer function."""
    nodeOut = nodeDfv.dfvOut
    nodeIn = nodeDfv.dfvIn
    if nodeIn is nodeOut:
      return nodeDfv  # to avoid making a fresh object
    else:
      return NodeDfvL(nodeOut, nodeOut)


  def ExRead_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ExReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    newIn = OverallL(self.func, top=True)
    newIn.setValLive(insn.vars)
    return NodeDfvL(newIn, nodeDfv.dfvOut)


  def UnDefVal_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self._killGen(nodeDfv, kill={insn.lhsName})


  def Use_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UseI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self._killGen(nodeDfv, gen=insn.vars)


  def CondRead_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
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

  def Num_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: lhs = rhs.
    Convention:
      Type of lhs and rhs is numeric.
    """
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: lhs = rhs.
    Convention:
      Type of lhs and rhs is a record.
    """
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: record: lhs = rhs.
    Convention:
      Type of lhs and rhs is a record.
    """
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    dfvOut = nodeDfv.dfvOut
    if dfvOut.bot: return NodeDfvL(dfvOut, dfvOut)
    varNames = self.processCallE(insn.arg)
    return self._killGen(nodeDfv, gen=varNames)


  def Conditional_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self._killGen(nodeDfv, gen={insn.arg.name})


  def Return_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self._killGen(nodeDfv, gen={insn.arg.name})

  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Simplifiers
  ################################################

  def LhsVar__to__Nil(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
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
      nodeDfv: NodeDfvL,
      kill: Opt[Set[types.VarNameT]] = None,
      gen: Opt[Set[types.VarNameT]] = None,
  ) -> NodeDfvL:
    dfvOut = nodeDfv.dfvOut
    assert isinstance(dfvOut, OverallL), f"{dfvOut}"

    if LS: LOG.debug(f"StrongLiveVarsA: Kill={kill}, Gen={gen}")

    if dfvOut.bot and not kill: return NodeDfvL(dfvOut, dfvOut)
    if dfvOut.top and not gen: return NodeDfvL(dfvOut, dfvOut)

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
    return NodeDfvL(newIn, dfvOut)


  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Processes all kinds of assignment instructions.
    The record types are also handled without any special treatment."""
    dfvOut = nodeDfv.dfvOut  # dfv at OUT of a node
    assert isinstance(dfvOut, OverallL), f"{dfvOut}"
    rhsNamesAreLive: bool = False
    rhsIsCallExpr: bool = isinstance(rhs, expr.CallE)

    # Find out: should variables be marked live?
    if dfvOut.bot or rhsIsCallExpr:
      rhsNamesAreLive = True

    lhsNames = getExprLValueNames(self.func, lhs)
    assert len(lhsNames) >= 1, f"{lhsNames}: {lhs}, {nodeDfv}"
    if dfvOut.val and set(lhsNames) & dfvOut.val:
      rhsNamesAreLive = True

    if LS: LOG.debug(f"lhsNames = {lhsNames} (live={rhsNamesAreLive})")

    # Now take action
    if not rhsNamesAreLive:
      return NodeDfvL(dfvOut, dfvOut)

    if rhsIsCallExpr:
      rhsNames = self.processCallE(rhs)
    else:
      rhsNames = getNamesUsedInExprNonSyntactically(self.func, rhs)\
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
  ) -> Set[types.VarNameT]:
    assert isinstance(e, expr.CallE), f"{e}"
    names = getNamesGlobal(self.func)
    names |= getNamesUsedInExprSyntactically(e)
    return names

  ################################################
  # BOUND END  : Helper_Functions
  ################################################


################################################
# BOUND END  : StrongLiveVars analysis
################################################
