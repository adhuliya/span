#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Strong Liveness analysis."""

import logging

LOG = logging.getLogger("span")
from typing import Optional as Opt, Set, Tuple, List, Callable

import span.util.util as util
from span.util.logger import LS
import span.util.messages as msg

import span.ir.types as types
import span.ir.conv as irConv
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as obj
import span.ir.ir as ir

from span.api.lattice import ChangeL, Changed, NoChange, DataLT
from span.api.dfv import NodeDfvL
import span.api.sim as sim
import span.api.analysis as analysis
import span.ir.tunit as irTunit

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

    # if here, elements are incomparable.
    # Both are neither top nor bot.
    assert other.val is not None
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
    if liveness == Live:
      self.setValLive(varNames)
    else:
      self.setValDead(varNames)


  def setValLive(self,
      varNames: Set[types.VarNameT]
  ) -> None:
    if self.bot or \
        (self.val and self.val >= varNames):
      return  # varNames already live

    self.top = False  # no more a top value (if it was)
    self.val = self.val if self.val is not None else set()

    for varName in varNames:
      self.val.update(ir.getPrefixes(varName))

    if self.val == ir.getNamesEnv(self.func):
      self.val, self.top, self.bot = None, False, True


  def setValDead(self,
      varNames: Set[types.VarNameT],
  ) -> None:
    if self.top or \
        (self.val and len(varNames & self.val) == 0):
      return  # varNames already dead

    self.bot = False  # no more a bot value (if it was)
    self.val = self.val if self.val is not None else ir.getNamesEnv(self.func).copy()

    for varName in varNames:
      for name in ir.getSuffixes(self.func, varName):
        self.val.remove(name)  # FIXME: kill all suffixes

    if not self.val:
      self.val, self.top, self.bot = None, True, False


  def __lt__(self, other) -> bool:
    assert isinstance(other, OverallL), f"{other}"
    if self.bot: return True
    if other.top: return True
    if other.bot: return False
    if self.top: return False

    # self is weaker if its a superset
    assert self.val is not None and other.val is not None
    return self.val >= other.val


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, OverallL):
      return NotImplemented
    sTop, sBot, oTop, oBot = self.top, self.bot, other.top, other.bot
    if sTop and oTop: return True
    if sBot and oBot: return True
    if sTop or oBot or sBot or oTop: return False

    assert self.val and other.val, f"{self}, {other}"
    return self.val == other.val


  def __hash__(self):
    val = set() if self.val is None else self.val
    hashThisVal = frozenset(val)
    return hash(self.func) ^ hash((hashThisVal, self.top, self.bot))


  def __str__(self):
    if self.top:
      return "Top"
    elif self.bot:
      # added isUserVar(name) for ACM Winter School 2019
      # vnames = {types.simplifyName(name)
      #          for name in ir.getNamesEnv(self.func) if ir.isUserVar(name)}
      return "Bot"
    else:
      # added isUserVar(name) for ACM Winter School 2019
      # vnames = {types.simplifyName(name) for name in self.val if ir.isUserVar(name)}
      vnames = {irConv.simplifyName(name) for name in self.val}  # if not ir.isDummyVar(name)}
    if vnames:
      return f"{vnames}"
    else:
      return "{}"


  def __repr__(self):
    return self.__str__()


################################################
# BOUND END  : StrongLiveVars lattice
################################################

################################################
# BOUND START: StrongLiveVars analysis
################################################

class StrongLiveVarsA(analysis.AnalysisAT):
  """Strongly Live Variables Analysis."""
  # liveness lattice
  L: type = OverallL
  D: type = analysis.BackwardD
  # blocking expression methods
  simNeeded: List[Callable] = [sim.SimAT.Deref__to__Vars,
                               sim.SimAT.Cond__to__UnCond,
                               sim.SimAT.Node__to__Nil,
                              ]


  def __init__(self,
      func: obj.Func,
  ) -> None:
    super().__init__(func)
    self.overallTop: OverallL = OverallL(self.func, top=True)
    self.overallBot: OverallL = OverallL(self.func, bot=True)


  def getBoundaryInfo(self,
      inBi: Opt[DataLT] = None,
      outBi: Opt[DataLT] = None,
  ) -> Tuple[OverallL, OverallL]:
    """
    The boundary information at start/end node.

    Returns:
      startBi: boundary data flow value at IN of start node
      endBi: boundary data flow value at OUT of end node
    """
    # No boundary information at IN of start node
    # since this analysis is backward only.
    startBi: OverallL = self.overallTop

    if inBi is None:
      # all globals are live at end/exit node
      endBi = OverallL(self.func, val=ir.getNamesGlobal(self.func))
    else:
      endBi = OverallL(self.func, val=ir.getNamesGlobal(self.func))  # TODO

    return startBi, endBi


  def Nop_Instr(self,
      nodeId: types.Nid,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """An identity backward transfer function."""
    nodeOut = nodeDfv.dfvOut
    nodeIn = nodeDfv.dfvIn
    if nodeIn is nodeOut:
      return nodeDfv  # to avoid making a fresh object
    else:
      return NodeDfvL(nodeOut, nodeOut)


  def Num_Assign_Var_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_UnaryArith_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_BinArith_Instr(self,
      hello: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Deref_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Array_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_CastVar_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Member_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Select_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_SizeOf_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Deref_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Deref_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Member_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Member_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Array_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Array_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Deref_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Deref_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfVar_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Array_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Array_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Deref_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Member_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Member_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfArray_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfDeref_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfFunc_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfMember_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Array_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_BinArith_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_CastArr_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_CastVar_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_FuncName_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Member_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Select_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Array_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Deref_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Member_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Var_Array_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Var_Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Var_Deref_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Var_Member_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Var_Select_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Var_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    oldOut = nodeDfv.dfvOut

    if oldOut.bot:
      return NodeDfvL(oldOut, oldOut)

    varNames = ir.getNamesUsedInExprSyntactically(insn.arg) | \
               ir.getNamesUsedInExprNonSyntactically(self.func, insn.arg)

    return self._killGen(nodeDfv, gen=varNames)


  def Conditional_Instr(self,
      nodeId: types.Nid,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    names = ir.getNamesUsedInExprSyntactically(insn.arg)

    if names:
      assert len(names) == 1
      return self._killGen(nodeDfv, gen=names)
    else:
      return self.Nop_Instr(nodeId, nodeDfv)


  def ExRead_Instr(self,
      nodeId: types.Nid,
      insn: instr.ExReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    newIn = OverallL(self.func, top=True)
    newIn.setValLive(insn.vars)

    return NodeDfvL(newIn, nodeDfv.dfvOut)


  def UnDefVal_Instr(self,
      nodeId: types.Nid,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self._killGen(nodeDfv, kill={insn.lhs})


  def Use_Instr(self,
      nodeId: types.Nid,
      insn: instr.UseI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self._killGen(nodeDfv, gen=insn.vars)


  def Return_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    assert isinstance(insn.arg, expr.VarE)
    return self._killGen(nodeDfv, gen={insn.arg.name})


  def CondRead_Instr(self,
      nodeId: types.Nid,
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

    return self.Nop_Instr(nodeId, nodeDfv)


  def _killGen(self,
      nodeDfv: NodeDfvL,
      kill: Opt[Set[types.VarNameT]] = None,
      gen: Opt[Set[types.VarNameT]] = None,
  ) -> NodeDfvL:
    # FIXME: Optimize me.
    oldOut = nodeDfv.dfvOut
    assert isinstance(oldOut, OverallL), f"{oldOut}"

    if LS: LOG.debug(f"StrongLiveVarsA: Kill={kill}, Gen={gen}")

    newIn = oldOut.getCopy()
    if kill:
      newIn.setValDead(kill)
    if gen:
      newIn.setValLive(gen)

    return NodeDfvL(newIn, oldOut)


  def LhsVar__to__Nil(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None
  ) -> sim.SimToLiveL:
    if nodeDfv is None:
      return sim.SimToLivePending

    dfvOut = nodeDfv.dfvOut
    if dfvOut.top: return sim.SimToLivePending
    if dfvOut.bot: return sim.SimToLiveFailed
    return sim.SimToLiveL(dfvOut.val)  # return the set of variables live


  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    dfvOut = nodeDfv.dfvOut  # dfv at OUT of a node
    assert isinstance(dfvOut, OverallL), f"{dfvOut}"
    rhsNamesAreLive: bool = False

    # Find out: should variables be marked live?
    if dfvOut.bot or isinstance(rhs, expr.CallE):
      rhsNamesAreLive = True

    lhsNames = set(ir.getExprLValuesWhenInLhs(self.func, lhs))
    assert len(lhsNames) >= 1, f"{msg.INVARIANT_VIOLATED}: {lhs}"
    if dfvOut.val and set(lhsNames) & dfvOut.val:
      rhsNamesAreLive = True

    if LS: LOG.debug(f"lhsNames = {lhsNames} (live={rhsNamesAreLive})")

    # Now take action
    if not rhsNamesAreLive:
      return NodeDfvL(dfvOut, dfvOut)

    rhsNames = ir.getNamesUsedInExprSyntactically(rhs) | \
               ir.getNamesUsedInExprNonSyntactically(self.func, rhs)

    # at least one side should names only one location (a SPAN IR check)
    assert len(lhsNames) >= 1 and len(rhsNames) >= 0, \
      f"{lhs} ({lhsNames}) = {rhs} ({rhsNames}) {rhs.info}"

    if len(lhsNames) == 1:
      return self._killGen(nodeDfv, kill=lhsNames, gen=rhsNames)
    else:
      return self._killGen(nodeDfv, gen=rhsNames)

################################################
# BOUND END  : StrongLiveVars analysis
################################################
