#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Constant propagation analysis.

This (and every) analysis subclasses,

  * `span.sys.lattice.DataLT` (to define its lattice)
  * `span.api.analysis.AnalysisAT` (to define the analysis)
  * `span.api.analysis.SimAT` (to define the simplifications)
"""

import logging

LOG = logging.getLogger("span")
from typing import Tuple, Set, Dict, List, Optional as Opt,\
  Callable, cast, Iterable
import io

import span.util.util as util
from span.util.util import LS

import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.ir as ir

from span.api.lattice import ChangeL, Changed, NoChange, DataLT
import span.api.dfv as dfv
from span.api.dfv import NodeDfvL
import span.api.sim as sim
import span.api.lattice as lattice
import span.api.analysis as analysis
import span.ir.tunit as irTUnit

import span.util.messages as msg


################################################
# BOUND START: Const_lattice
################################################

class ComponentL(dfv.ComponentL):
  """The lattice of an entity (a numeric variable)."""

  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[types.NumericT] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val: Opt[types.NumericT] = val


  def meet(self,
      other: 'ComponentL'
  ) -> Tuple['ComponentL', ChangeL]:
    """For documentation see: `span.api.lattice.LatticeLT.meet`"""
    if self is other: return self, NoChange
    if self.bot: return self, NoChange
    if other.top: return self, NoChange
    if other.bot: return other, Changed
    if self.top: return other, Changed

    if other.val == self.val:
      return self, NoChange
    else:
      return ComponentL(self.func, bot=True), Changed


  def __lt__(self, other: 'ComponentL') -> bool:
    """For documentation see: span.api.lattice.LatticeLT.__lt__.__doc__"""
    if self.bot: return True
    if other.top: return True
    if other.bot: return False
    if self.top: return False

    if self.val == other.val: return True
    return False


  def __eq__(self, other) -> bool:
    """For documentation see: `span.api.lattice.LatticeLT.__eq__`"""
    if self is other:
      return True
    if not isinstance(other, ComponentL):
      return NotImplemented

    sTop, sBot, oTop, oBot = self.top, self.bot, other.top, other.bot
    if sTop and oTop: return True
    if sBot and oBot: return True
    if sTop or sBot or oTop or oBot: return False

    return self.val == other.val


  def __hash__(self):
    return hash(self.func.name) ^ hash((self.val, self.top, self.bot))


  def getCopy(self) -> 'ComponentL':
    if self.top: ComponentL(self.func, top=True)
    if self.bot: ComponentL(self.func, bot=True)
    return ComponentL(self.func, self.val)  # since val is immutable


  def __str__(self):
    if self.bot: return "Bot"
    if self.top: return "Top"
    return f"{self.val}"


  def __repr__(self):
    return self.__str__()


class OverallL(dfv.OverallL):
  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[types.VarNameT, dfv.ComponentL]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot, ComponentL, "const")
    # self.componentTop = ComponentL(self.func, top=True)
    # self.componentBot = ComponentL(self.func, bot=True)


  def countConstants(self) -> int:
    """Gives the count of number of constant in the data flow value."""
    if self.top or self.bot:
      return 0

    assert self.val, f"{self}"
    count = 0
    for var, val in self.val.items():
      if val.val is not None:
        count += 1
    return count


################################################
# BOUND END  : Const_lattice
################################################

################################################
# BOUND START: Const_analysis
################################################

class ConstA(analysis.AnalysisAT):
  """Constant Propagation Analysis."""
  __slots__ : List[str] = ["componentTop", "componentBot"]
  L: type = OverallL  # the lattice ConstA uses
  D: type = analysis.ForwardD  # its a forward flow analysis
  simNeeded: List[Callable] = [sim.SimAT.Num_Var__to__Num_Lit,
                               sim.SimAT.Deref__to__Vars,
                               sim.SimAT.Num_Bin__to__Num_Lit,
                               sim.SimAT.LhsVar__to__Nil,
                               sim.SimAT.Cond__to__UnCond,
                               #sim.SimAT.Node__to__Nil,
                               ]


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func)
    self.componentTop: ComponentL = ComponentL(self.func, top=True)
    self.componentBot: ComponentL = ComponentL(self.func, bot=True)
    self.overallTop: OverallL = OverallL(self.func, top=True)
    self.overallBot: OverallL = OverallL(self.func, bot=True)


  def getIpaBoundaryInfo(self,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return dfv.getIpaBoundaryInfo(self.func, nodeDfv,
                                  self.componentBot, self.getAllVars)


  def getAllVars(self) -> Set[types.VarNameT]:
    return ir.getNamesEnv(self.func, numeric=True)

  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def Filter_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return dfv.Filter_Vars(self.func, insn.varNames, nodeDfv)


  def UnDefVal_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if not insn.type.isNumeric():
      return self.Nop_Instr(nodeId, nodeDfv)

    oldIn = nodeDfv.dfvIn
    newOut = cast(OverallL, oldIn.getCopy())
    newOut.setVal(insn.lhs, self.componentBot)
    return NodeDfvL(oldIn, newOut)


  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################

  def Num_Assign_Var_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Deref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_CastVar_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_SizeOf_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_UnaryArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_BinArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Select_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Array_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Member_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.rhs, nodeDfv.dfvIn)


  def Record_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Deref_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Deref_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Array_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Array_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Member_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Member_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Record_Assign_Array_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    raise NotImplementedError()


  def Record_Assign_Deref_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    raise NotImplementedError()


  def Record_Assign_Member_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    raise NotImplementedError()


  def Record_Assign_Var_Array_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    raise NotImplementedError()


  def Record_Assign_Var_Deref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    raise NotImplementedError()


  def Record_Assign_Var_Member_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    raise NotImplementedError()


  def Record_Assign_Var_Select_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    raise NotImplementedError()


  def Record_Assign_Var_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    raise NotImplementedError()


  def Conditional_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    oldIn = cast(OverallL, nodeDfv.dfvIn)
    if isinstance(insn.arg.type, types.Ptr): # special case
      return NodeDfvL(oldIn, oldIn)
    dfvFalse, dfvTrue = self.calcTrueFalseDfv(insn.arg, oldIn)
    return NodeDfvL(oldIn, None, dfvTrue, dfvFalse)


  def Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.arg, nodeDfv.dfvIn)


  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Simplifiers
  ################################################

  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
  ) -> sim.SimToNumL:
    # STEP 1: check if the expression can be evaluated
    varType = e.type
    if not varType.isNumeric():
      return sim.SimToNumFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToNumPending

    val = cast(OverallL, nodeDfv.dfvIn).getVal(e.name)
    if val.bot: return sim.SimToNumFailed  # cannot be evaluated
    if val.top: return sim.SimToNumPending  # can be evaluated, needs more info
    return sim.SimToNumL(val.val)


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[NodeDfvL] = None,
  ) -> sim.SimToNumL:
    # STEP 1: check if the expression can be evaluated
    exprType = e.type
    arg1Type = e.arg1.type
    arg2Type = e.arg2.type

    if not exprType.isNumeric():
      return sim.SimToNumFailed
    if not arg1Type.isNumeric() or not arg2Type.isNumeric():
      return sim.SimToNumFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToNumPending

    if isinstance(e.arg1, expr.VarE):
      val1 = cast(OverallL, nodeDfv.dfvIn).getVal(e.arg1.name)
    else: # a literal
      assert isinstance(e.arg1, expr.LitE), f"{e}"
      assert isinstance(e.arg1.val, (int, float)), f"{e.arg1}"
      val1 = ComponentL(self.func, val=e.arg1.val)

    if val1.bot: return sim.SimToNumFailed
    if val1.top: return sim.SimToNumPending

    if isinstance(e.arg2, expr.VarE):
      val2 = cast(OverallL, nodeDfv.dfvIn).getVal(e.arg2.name)
    else:  # a literal
      assert isinstance(e.arg2, expr.LitE), f"{e}"
      assert isinstance(e.arg2.val, (int, float)), f"{e.arg1}"
      val2 = ComponentL(self.func, val=e.arg2.val)

    if val2.bot: return sim.SimToNumFailed
    if val2.top: return sim.SimToNumPending

    assert val1.val and val2.val, f"{val1}, {val2}"
    opCode = e.opr.opCode
    if opCode == op.BO_ADD_OC:
      return sim.SimToNumL(val1.val + val2.val)
    elif opCode == op.BO_SUB_OC:
      return sim.SimToNumL(val1.val - val2.val)
    elif opCode == op.BO_MUL_OC:
      return sim.SimToNumL(val1.val * val2.val)
    elif opCode == op.BO_DIV_OC:
      if val2.val == 0:
        if LS: LOG.critical("DivideByZero: expr: %s, dfv: %s",
                            e, nodeDfv.dfvIn)
        return sim.SimToNumFailed
      else:
        return sim.SimToNumL(val1.val / val2.val)
    elif opCode == op.BO_MOD_OC:
      return sim.SimToNumL(val1.val % val2.val)
    elif opCode == op.BO_GT_OC:
      val = 1 if val1.val > val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_GE_OC:
      val = 1 if val1.val >= val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_LT_OC:
      val = 1 if val1.val < val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_LE_OC:
      val = 1 if val1.val <= val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_EQ_OC:
      val = 1 if val1.val == val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_NE_OC:
      val = 1 if val1.val != val2.val else 0
      return sim.SimToNumL(val)

    return sim.SimToNumFailed


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None
  ) -> sim.SimToBoolL:
    # STEP 1: check if the expression can be evaluated
    exprType = e.type
    if not exprType.isNumeric():
      return sim.SimToBoolFailed

    # STEP 2: If here, eval may be possible
    if nodeDfv is None:
      return sim.SimToBoolPending

    # STEP 3: attempt evaluation
    val = cast(OverallL, nodeDfv.dfvIn).getVal(e.name)
    if val.bot: return sim.SimToBoolFailed  # cannot be evaluated
    if val.top:
      nameType = ir.inferTypeOfVal(self.func, e.name)
      if isinstance(nameType, types.Ptr):
        return sim.SimToBoolFailed
      else:
        return sim.SimToBoolPending  # can be evaluated but needs more info
    if val.val != 0:
      return sim.SimToBoolL(True)
    else:
      return sim.SimToBoolL(False)


  ################################################
  # BOUND END  : Simplifiers
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      dfvIn: DataLT,
  ) -> NodeDfvL:
    """A common function to handle various assignment instructions."""
    assert isinstance(dfvIn, OverallL), f"{type(dfvIn)}"

    if isinstance(lhs.type, types.RecordT):
      return self.processLhsRhsRecordType(lhs, rhs, dfvIn)

    lhsVarNames = ir.getExprLValuesWhenInLhs(self.func, lhs)
    assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"

    rhsDfv = self.getExprDfv(rhs, dfvIn)

    dfvInGetVal = dfvIn.getVal
    outDfvValues = {}  # a temporary store of out dfvs
    if len(lhsVarNames) == 1:  # a must update
      for name in lhsVarNames:  # this loop is entered once only
        newVal = rhsDfv
        if ir.nameHasArray(self.func, name):  # may update arrays
          oldVal = cast(ComponentL, dfvInGetVal(name))
          newVal, _ = oldVal.meet(rhsDfv)
        if dfvInGetVal(name) != newVal:
          outDfvValues[name] = newVal
    else:
      for name in lhsVarNames:  # do may updates (take meet)
        oldDfv = cast(ComponentL, dfvIn.getVal(name))
        updatedDfv, changed = oldDfv.meet(rhsDfv)
        if dfvInGetVal(name) != updatedDfv:
          outDfvValues[name] = updatedDfv

    if isinstance(rhs, expr.CallE):  # over-approximate
      names = ir.getNamesUsedInExprNonSyntactically(self.func, rhs)
      names = ir.filterNamesInteger(self.func, names)
      for name in names:
        if dfvInGetVal(name) != self.componentBot:
          outDfvValues[name] = self.componentBot

    newOut = dfvIn
    if outDfvValues:
      newOut = cast(OverallL, dfvIn.getCopy())
      for name, value in outDfvValues.items():
        newOut.setVal(name, value)
    return NodeDfvL(dfvIn, newOut)


  def getExprDfv(self,
      e: expr.ExprET,
      dfvIn: OverallL
  ) -> ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects that the rhs is non-record type.
    (Record type expressions are handled separately.)
    """
    value = self.componentTop

    if isinstance(e, expr.LitE):
      assert isinstance(e.val, (int, float)), f"{e}"
      return ComponentL(self.func, val=e.val)

    elif isinstance(e, expr.VarE):  # handles PseudoVarE too
      return cast(ComponentL, dfvIn.getVal(e.name))

    elif isinstance(e, expr.DerefE):
      names = ir.getNamesUsedInExprNonSyntactically(self.func, e)
      for name in names:
        value, _ = value.meet(cast(ComponentL, dfvIn.getVal(name)))
      return value

    elif isinstance(e, expr.CastE):
      if e.arg.type.isNumeric():
        value, _ = value.meet(self.getExprDfv(e.arg, dfvIn))
        assert isinstance(value, ComponentL)
        if value.top or value.bot:
          return value
        else:
          assert e.to.isNumeric() and value.val
          value.val = e.to.castValue(value.val)
          return value
      else:
        return self.componentBot

    elif isinstance(e, expr.SizeOfE):
      return self.componentBot

    elif isinstance(e, expr.UnaryE):
      value, _ = value.meet(self.getExprDfv(e.arg, dfvIn))
      if value.top or value.bot:
        return value
      elif value.val is not None:
        rhsOpCode = e.opr.opCode
        if rhsOpCode == op.UO_MINUS_OC:
          value.val = -value.val  # not NoneType... pylint: disable=E
        elif rhsOpCode == op.UO_BIT_NOT_OC:
          assert isinstance(value.val, int), f"{value}"
          value.val = ~value.val  # not NoneType... pylint: disable=E
        elif rhsOpCode == op.UO_LNOT_OC:
          value.val = int(not bool(value.val))
        return value
      else:
        assert False, f"{type(value)}: {value}"

    elif isinstance(e, expr.BinaryE):
      val1 = self.getExprDfv(e.arg1, dfvIn)
      val2 = self.getExprDfv(e.arg2, dfvIn)
      if val1.top or val2.top:
        return self.componentTop
      elif val1.bot or val2.bot:
        return self.componentBot
      else:
        assert val1.val and val2.val, f"{val1}, {val2}"
        rhsOpCode = e.opr.opCode
        if rhsOpCode == op.BO_ADD_OC:
          val: Opt[float] = val1.val + val2.val
        elif rhsOpCode == op.BO_SUB_OC:
          val = val1.val - val2.val
        elif rhsOpCode == op.BO_MUL_OC:
          val = val1.val * val2.val
        elif rhsOpCode == op.BO_DIV_OC:
          if val2.val == 0: return self.componentBot
          val = val1.val / val2.val
        elif rhsOpCode == op.BO_MOD_OC:
          if val2.val == 0: return self.componentBot
          val = val1.val % val2.val
        else:
          val = None

        if val is not None:
          return ComponentL(self.func, val=val)
        else:
          return self.componentBot

    elif isinstance(e, expr.SelectE):
      val1 = self.getExprDfv(e.arg1, dfvIn)
      val2 = self.getExprDfv(e.arg2, dfvIn)
      value, _ = val1.meet(val2)
      return value

    elif isinstance(e, (expr.ArrayE, expr.MemberE)):
      varNames = ir.getExprLValuesWhenInLhs(self.func, e)
      for name in varNames:
        value, _ = value.meet(cast(ComponentL, dfvIn.getVal(name)))
      return value

    elif isinstance(e, expr.CallE):
      return self.componentBot

    raise ValueError(f"{e}")


  def processLhsRhsRecordType(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      dfvIn: DataLT,
  ) -> NodeDfvL:
    """Processes assignment instruction with RecordT"""
    instrType = lhs.type
    assert isinstance(instrType, types.RecordT), f"{lhs}, {rhs}: {instrType}"
    assert isinstance(dfvIn, OverallL), f"{type(dfvIn)}"

    lhsVarNames = ir.getExprLValuesWhenInLhs(self.func, lhs)
    assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
    strongUpdate: bool = len(lhsVarNames) == 1

    rhsVarNames = ir.getExprLValuesWhenInLhs(self.func, rhs)
    assert len(rhsVarNames) >= 1, f"{lhs}: {rhsVarNames}"

    allMemberInfo = instrType.getNamesOfType(None)

    tmpDfv: Dict[types.VarNameT, ComponentL] = dict()
    for memberInfo in allMemberInfo:
      if memberInfo.type.isNumeric():
        for lhsName in lhsVarNames:
          fullLhsVarName = f"{lhsName}.{memberInfo.name}"
          oldLhsDfv = dfvIn.getVal(fullLhsVarName)
          rhsDfv = lattice.mergeAll(
            dfvIn.getVal(f"{rhsName}.{memberInfo.name}")
            for rhsName in rhsVarNames)
          if not strongUpdate:
            rhsDfv, _ = oldLhsDfv.meet(rhsDfv)
          if oldLhsDfv != rhsDfv:
            tmpDfv[fullLhsVarName] = rhsDfv

    newOut = dfvIn
    if tmpDfv:
      newOut = dfvIn.getCopy()
      for varName, val in tmpDfv.items():
        newOut.setVal(varName, val)

    return NodeDfvL(dfvIn, newOut)


  def processCallE(self,
      e: expr.ExprET,
      dfvIn: DataLT,
  ) -> NodeDfvL:
    assert isinstance(e, expr.CallE), f"{e}"
    assert isinstance(dfvIn, OverallL), f"{type(dfvIn)}"

    newOut = dfvIn.getCopy()
    names = ir.getNamesUsedInExprNonSyntactically(self.func, e)
    names = ir.filterNamesNumeric(self.func, names)
    for name in names:
      newOut.setVal(name, self.componentBot)
    return NodeDfvL(dfvIn, newOut)


  def calcTrueFalseDfv(self,
      arg: expr.SimpleET,
      dfvIn: OverallL,
  ) -> Tuple[OverallL, OverallL]:  # dfvFalse, dfvTrue
    """Conditionally propagate data flow values."""
    assert isinstance(arg, expr.VarE), f"{arg}"
    argInDfvVal = dfvIn.getVal(arg.name)
    if not (argInDfvVal.top or argInDfvVal.bot): # i.e. arg is a constant
      return dfvIn, dfvIn

    varDfvTrue = varDfvFalse = None

    tmpExpr = ir.getTmpVarExpr(self.func, arg.name)
    argDfvFalse = ComponentL(self.func, 0)  # always true

    varName = arg.name
    if tmpExpr and isinstance(tmpExpr, expr.BinaryE):
      opCode = tmpExpr.opr.opCode
      varDfv = self.getExprDfv(tmpExpr.arg1, dfvIn)
      if opCode == op.BO_EQ_OC and varDfv.bot:
        varDfvTrue = self.getExprDfv(tmpExpr.arg2, dfvIn)
      elif opCode == op.BO_NE_OC and varDfv.bot:
        varDfvFalse = self.getExprDfv(tmpExpr.arg2, dfvIn)

    if argDfvFalse or varDfvFalse:
      dfvFalse = cast(OverallL, dfvIn.getCopy())
      if argDfvFalse:
        dfvFalse.setVal(arg.name, argDfvFalse)
      if varDfvFalse:
        dfvFalse.setVal(varName, varDfvFalse)
    else:
      dfvFalse = dfvIn

    if varDfvTrue:
      dfvTrue = cast(OverallL, dfvIn.getCopy())
      dfvTrue.setVal(varName, varDfvTrue)
    else:
      dfvTrue = dfvIn

    return dfvFalse, dfvTrue

  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : Const_analysis
################################################
