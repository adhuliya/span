#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Constant propagation analysis.

This (and every) analysis subclasses,

  * `span.sys.lattice.DataLT` (to define its lattice)
  * `span.api.analysis.AnalysisAT` (to define the analysis)
  * `span.api.analysis.SimAT` (to define the simplifications)
"""

import logging

from span.ir.conv import Forward

LOG = logging.getLogger(__name__)
from typing import Tuple, Set, Dict, List, Optional as Opt,\
  Callable, cast

from span.util.util import LS

import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.ir as ir

from span.api.lattice import ChangedT, Changed, DataLT
import span.api.dfv as dfv
from span.api.dfv import DfvPairL
import span.api.lattice as lattice
import span.api.analysis as analysis
from span.api.analysis import SimFailed, SimPending, BoolValue, \
  NumValue, ValueTypeT, AnalysisAT

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
  ) -> Tuple['ComponentL', ChangedT]:
    """For documentation see: `span.api.lattice.LatticeLT.meet`"""
    tup = lattice.basicMeetOp(self, other)
    if tup:
      return tup
    elif self.val == other.val:
      return self, not Changed
    else:
      return ComponentL(self.func, bot=True), Changed


  def isConstant(self):
    """Returns True if self.val is a constant."""
    return self.val is not None  # a simple check


  def __lt__(self, other: 'ComponentL') -> bool:
    """For documentation see: span.api.lattice.LatticeLT.__lt__.__doc__"""
    lt = lattice.basicLessThanTest(self, other)
    return self.val == other.val if lt is None else lt


  def __eq__(self, other) -> bool:
    """For documentation see: `span.api.lattice.LatticeLT.__eq__`"""
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = lattice.basicEqualsTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    return hash((self.val, self.top, self.bot))


  def getCopy(self) -> 'ComponentL':
    if self.top: ComponentL(self.func, top=True)
    if self.bot: ComponentL(self.func, bot=True)
    return ComponentL(self.func, self.val)  # since val is immutable


  def isTrue(self) -> Opt[bool]:
    """Returns the boolean equivalent of the constant value."""
    if self.top or self.bot:
      return None
    return self.val != 0


  def __str__(self):
    s = lattice.getBasicString(self)
    return s if s else f"{self.val}"


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
    super().__init__(func, val, top, bot, ComponentL, "ConstA")
    # self.componentTop = ComponentL(self.func, top=True)
    # self.componentBot = ComponentL(self.func, bot=True)


  def countConstants(self) -> int:
    """Gives the count of number of constant in the data flow value."""
    if self.top or self.bot: return 0
    assert self.val, f"{self}"
    return sum(1 for val in self.val.values()
               if val.isConstant()) # ok val.isConst..


  def getNamesWithConstValue(self) -> Set[types.VarNameT]:
    """Gives the variable names which are known to be constant."""
    if self.top or self.bot: return set()
    assert self.val, f"{self}"
    return set(vName for vName, val in self.val.items()
                if val.isConstant()) # ok val.isConst..

################################################
# BOUND END  : Const_lattice
################################################

################################################
# BOUND START: Const_analysis
################################################

class ConstA(analysis.ValueAnalysisAT):
  """Constant Propagation Analysis."""
  __slots__ : List[str] = []
  L: type = OverallL  # the lattice ConstA uses
  # direction of the analysis
  D: Opt[types.DirectionT] = Forward


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func, ComponentL, OverallL)


  ################################################
  # BOUND START: Special_Instructions
  ################################################
  # uses default implementation in analysis.ValueAnalysisAT class
  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################

  # def Ptr_Assign_Instr(self,
  #     nodeId: types.NodeIdT,
  #     insn: instr.AssignI,
  #     nodeDfv: NodeDfvL,
  #     calleeBi: Opt[NodeDfvL] = None,  #IPA
  # ) -> NodeDfvL:
  #   return self.Nop_Instr(nodeId, insn, nodeDfv)

  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Simplifiers
  ################################################

  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[types.NumericT]] = None,
  ) -> Opt[Set[types.NumericT]]:
    # STEP 1: tell the system if the expression can be evaluated
    if not e.type.isNumeric():
      return SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return SimPending # tell that sim my be possible if nodeDfv given

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, NumValue) # filter the values

    # STEP 4: If here, eval the expression
    exprVal = self.getExprDfv(e, dfvIn)
    if exprVal.top: return SimPending  # can be evaluated, needs more info
    if exprVal.bot: return SimFailed  # cannot be evaluated
    return {exprVal.val}


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[types.NumericT]] = None,
  ) -> Opt[Set[types.NumericT]]:
    # STEP 1: tell the system if the expression can be evaluated
    if (not e.type.isNumeric()
        or not e.arg1.type.isNumeric()
        or not e.arg2.type.isNumeric()):
      return SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return SimPending # tell that sim my be possible if nodeDfv given

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, NumValue) # filter the values

    # STEP 4: If here, eval the expression
    arg1, arg2 = e.arg1, e.arg2
    vals = []
    for arg in (arg1, arg2):
      if isinstance(arg, expr.VarE):
        val = dfvIn.getVal(arg.name)
      else: # a literal (can be possible)
        assert isinstance(arg, expr.LitE), f"{e}"
        assert isinstance(arg.val, (int, float)), f"{arg}"
        val = ComponentL(self.func, val=arg.val)
      if val.top: return SimPending
      if val.bot: return SimFailed
      vals.append(val)

    val1, val2 = vals[0], vals[1]
    assert val1.val and val2.val, f"{val1}, {val2}"
    opCode = e.opr.opCode
    if opCode == op.BO_ADD_OC:
      return {val1.val + val2.val}
    elif opCode == op.BO_SUB_OC:
      return {val1.val - val2.val}
    elif opCode == op.BO_MUL_OC:
      return {val1.val * val2.val}
    elif opCode == op.BO_DIV_OC:
      if val2.val == 0:
        if LS: LOG.critical("DivideByZero: expr: %s, dfv: %s", e, dfvIn)
        return SimFailed
      else:
        return {val1.val / val2.val}
    elif opCode == op.BO_MOD_OC:
      return {val1.val % val2.val}
    elif opCode == op.BO_GT_OC:
      return {1 if val1.val > val2.val else 0}
    elif opCode == op.BO_GE_OC:
      return {1 if val1.val >= val2.val else 0}
    elif opCode == op.BO_LT_OC:
      return {1 if val1.val < val2.val else 0}
    elif opCode == op.BO_LE_OC:
      return {1 if val1.val <= val2.val else 0}
    elif opCode == op.BO_EQ_OC:
      return {1 if val1.val == val2.val else 0}
    elif opCode == op.BO_NE_OC:
      return {1 if val1.val != val2.val else 0}
    return SimFailed


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[bool]] = None,
  ) -> Opt[Set[bool]]:
    # STEP 1: tell the system if the expression can be evaluated
    if not e.type.isNumeric():
      return SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return SimPending # tell that sim my be possible if nodeDfv given

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, BoolValue) # filter the values

    # STEP 4: If here, eval the expression
    val = dfvIn.getVal(e.name)
    if val.top: return SimPending  # can be evaluated but needs more info
    if val.bot: return SimFailed  # cannot be evaluated
    assert val.val is not None, f"{e}, {val}"
    if val.val != 0:
      return {True}
    else:
      return {False}


  def filterTest(self,
      exprVal: ComponentL,
      valueType: ValueTypeT = NumValue,
  ) -> Callable[[types.T], bool]:
    if valueType == NumValue:
      def valueTestNumeric(val) -> bool:
        if exprVal.top: return False
        if exprVal.bot: return True
        return exprVal.val == val
      return valueTestNumeric

    elif valueType == BoolValue:
      def valueTestBoolean(val) -> bool:
        if exprVal.top: return False
        if exprVal.bot: return True
        return exprVal.isTrue() == val
      return valueTestBoolean

    raise ValueError(f"{exprVal}, {valueType}")

  ################################################
  # BOUND END  : Simplifiers
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def getExprDfvLitE(self,
      e: expr.LitE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> ComponentL:
    assert isinstance(e.val, (int, float)), f"{e}"
    return ComponentL(self.func, val=e.val)


  def getExprDfvCastE(self,
      e: expr.CastE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    assert isinstance(e.arg, expr.VarE), f"{e}"
    if self.L.isAcceptedType(e.arg.type):
      value = dfvInGetVal(e.arg.name)
      if value.top or value.bot:
        return value
      else:
        assert self.L.isAcceptedType(e.to) and value.val, f"{e}, {value}"
        value.val = e.to.castValue(value.val)
        return value
    else:
      return self.componentBot


  def getExprDfvUnaryE(self,
      e: expr.UnaryE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> ComponentL:
    assert isinstance(e.arg, expr.VarE), f"{e}"
    value = dfvInGetVal(e.arg.name)
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
      else:
        raise ValueError(f"{e}")
      return value
    raise TypeError(f"{type(value)}: {value}")


  def getExprDfvBinaryE(self,
      e: expr.BinaryE,
      dfvIn: dfv.OverallL,
  ) -> dfv.ComponentL:
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
        if val2.val == 0:
          return self.componentBot
        val = val1.val / val2.val
      elif rhsOpCode == op.BO_MOD_OC:
        if val2.val == 0:
          return self.componentBot
        val = val1.val % val2.val
      else:
        val = None

      if val is not None:
        return ComponentL(self.func, val=val)
      else:
        return self.componentBot


  def calcFalseTrueDfv(self,
      arg: expr.SimpleET,
      dfvIn: OverallL,
  ) -> Tuple[OverallL, OverallL]:  # dfvFalse, dfvTrue
    """Conditionally propagate data flow values."""
    assert isinstance(arg, expr.VarE), f"{arg}"
    argInDfvVal = dfvIn.getVal(arg.name)
    if not (argInDfvVal.top or argInDfvVal.bot): # i.e. arg is a constant
      return dfvIn, dfvIn

    argName = arg.name
    zeroDfv = ComponentL(self.func, 0)  # always zero on false branch

    dfvValTrue: Dict[types.VarNameT, ComponentL] = {}
    dfvValFalse: Dict[types.VarNameT, ComponentL] = {}
    dfvValFalse[argName] = zeroDfv

    tmpExpr = ir.getTmpVarExpr(self.func, arg.name)
    if tmpExpr and isinstance(tmpExpr, expr.BinaryE):
      arg1, arg2 = tmpExpr.arg1, tmpExpr.arg2
      assert isinstance(arg1, expr.VarE), f"{tmpExpr}"
      opCode = tmpExpr.opr.opCode
      arg1Dfv = self.getExprDfv(arg1, dfvIn)
      if arg1Dfv.bot and opCode == op.BO_EQ_OC:
        dfvValTrue[arg1.name] = self.getExprDfv(arg2, dfvIn)  # equal dfv
      elif arg1Dfv.bot and opCode == op.BO_NE_OC:
        dfvValFalse[arg1.name] = self.getExprDfv(arg2, dfvIn) # equal dfv

    return dfv.updateDfv(dfvValFalse, dfvIn), dfv.updateDfv(dfvValTrue, dfvIn)

  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : Const_analysis
################################################


