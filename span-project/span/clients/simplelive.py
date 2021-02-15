#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Strong Liveness analysis."""

import logging

from ..ir.conv import Backward

LOG = logging.getLogger("span")
from typing import Optional as Opt, Set, Tuple, List, Callable, cast

import span.ir.types as types
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as obj
import span.ir.ir as ir

from span.api.lattice import DataLT
from span.api.dfv import NodeDfvL
from span.api.analysis import AnalysisAT, BackwardD, SimPending, SimFailed

################################################
# BOUND START: LiveVars lattice
################################################

# Borrow the lattice related definitions from stronglive specification
from .stronglive import Live, Dead, OverallL


################################################
# BOUND END  : LiveVars lattice
################################################

################################################
# BOUND START: LiveVars analysis
################################################

class LiveVarsA(AnalysisAT):
  """Simple Live Variables Analysis."""
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
    startBi = self.overallTop

    if inBi is None:
      # all globals are live at end/exit node
      endBi: OverallL = OverallL(self.func, val=ir.getNamesGlobal(self.func))
    else:
      endBi = OverallL(self.func, val=ir.getNamesGlobal(self.func))  # TODO

    return startBi, endBi


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


  def Num_Assign_Var_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_UnaryArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_BinArith_Instr(self,
      hello: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Deref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Array_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_CastVar_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Member_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_Select_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Var_SizeOf_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Deref_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Deref_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Member_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Member_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Array_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Num_Assign_Array_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Deref_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Deref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfVar_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Array_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Array_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Deref_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Member_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Member_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfArray_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfFunc_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_AddrOfMember_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Array_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_BinArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_CastArr_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_CastVar_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_FuncName_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Member_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Var_Select_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ):
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    oldOut = nodeDfv.dfvOut

    if oldOut.bot:
      return NodeDfvL(oldOut, oldOut)

    varNames = ir.getNamesUsedInExprSyntactically(insn.arg) | \
               ir.getNamesInExprMentionedIndirectly(self.func, insn.arg)

    return self._killGen(nodeDfv, gen=varNames)


  def Conditional_Instr(self,
      nodeId: types.NodeIdT,
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


  def Return_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    assert isinstance(insn.arg, expr.VarE)
    return self._killGen(nodeDfv, gen={insn.arg.name})


  def CondRead_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    lName = insn.lhs
    rNames = insn.rhs

    lhsIsLive = cast(OverallL, nodeDfv.dfvOut).getVal(lName)
    if lhsIsLive:
      return self._killGen(nodeDfv, kill={lName}, gen=rNames)

    return self.Nop_Instr(nodeId, nodeDfv)


  def _killGen(self,
      nodeDfv: NodeDfvL,
      kill: Opt[Set[types.VarNameT]] = None,
      gen: Opt[Set[types.VarNameT]] = None,
  ) -> NodeDfvL:
    # FIXME: Optimize me.
    oldOut = cast(OverallL, nodeDfv.dfvOut)

    newIn = oldOut.getCopy()
    if kill:
      newIn.setValDead(kill)
    if gen:
      newIn.setValLive(gen)

    return NodeDfvL(newIn, oldOut)


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


  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    dfvOut = cast(OverallL, nodeDfv.dfvOut)  # dfv at OUT of a node
    rhsNamesAreLive: bool = True  # its simple liveness

    lhsNames = ir.getNamesLValuesOfExpr(self.func, lhs)
    assert len(lhsNames) >= 1, f"{lhs}: {lhsNames}"

    rhsNames = ir.getNamesUsedInExprSyntactically(rhs) | \
               ir.getNamesInExprMentionedIndirectly(self.func, rhs)

    # at least one side should name only one location (a SPAN IR check)
    assert len(lhsNames) == 1 or len(rhsNames) == 1

    if len(lhsNames) == 1:
      return self._killGen(nodeDfv, kill=set(lhsNames), gen=rhsNames)
    else:
      return self._killGen(nodeDfv, gen=rhsNames)

################################################
# BOUND END  : LiveVars analysis
################################################
