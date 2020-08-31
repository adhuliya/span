#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Interval (Range) Analysis."""

import logging

LOG = logging.getLogger("span")
from typing import Tuple, Dict, Set, List, Optional as Opt, cast, Callable, Type
import io

import span.util.util as util
import span.util.messages as msg

import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.ir as ir

from span.api.lattice import DataLT, ChangeL, Changed, NoChange
import span.api.dfv as dfv
import span.api.lattice as lattice
from span.api.dfv import NodeDfvL
import span.api.sim as sim
import span.api.analysis as analysis
import span.ir.tunit as irTUnit


################################################
# BOUND START: interval_lattice
################################################

class ComponentL(dfv.ComponentL):
  __slots__ : List[str] = []


  def __init__(self,
      func: constructs.Func,
      val: Opt[Tuple[float, float]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val: Opt[Tuple[float, float]] = val


  def meet(self,
      other: 'ComponentL'
  ) -> Tuple['ComponentL', ChangeL]:
    tup = lattice.basicMeetOp(self, other)
    if tup:
      return tup
    elif self.val == other.val:
      return self, NoChange
    else:
      assert self.val and other.val, f"{self}, {other}"
      lowerLim = min(self.val[0], other.val[0])
      upperLim = max(self.val[1], other.val[1])
      return ComponentL(self.func, val=(lowerLim, upperLim)), Changed


  def __lt__(self,
      other: 'ComponentL'
  ) -> bool:
    """A non-strict weaker-than test. See doc of super class."""
    lt = lattice.basicLessThanTest(self, other)
    return (self.val[0] <= other.val[0] and self.val[1] >= other.val[1]) \
             if lt is None else lt


  def __eq__(self, other) -> bool:
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = lattice.basicEqualTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    return hash((self.func.name, self.val, self.top, self.bot))


  def getCopy(self) -> 'ComponentL':
    if self.top: ComponentL(self.func, top=True)
    if self.bot: ComponentL(self.func, bot=True)
    return ComponentL(self.func, self.val)


  def isExactZero(self) -> bool:
    return self.val and self.val[0] == 0 == self.val[1]


  def getNegatedRange(self) -> 'ComponentL':
    if self.top: return self
    if self.bot: return self
    assert self.val, f"{self}"
    return ComponentL(self.func, val=(-self.val[1], -self.val[0]))


  def bitNotRange(self) -> 'ComponentL':
    if self.isConstant():
      assert self.val, f"{self}"
      bitNotValue = ~int(self.val[0])
      return ComponentL(self.func, val=(bitNotValue, bitNotValue))
    else:
      return ComponentL(self.func, bot=True)


  def logicalNotRange(self) -> 'ComponentL':
    if self.isExactZero():
      return ComponentL(self.func, val=(1, 1))
    elif not self.inRange(0):
      return ComponentL(self.func, val=(0, 0))
    else:
      return ComponentL(self.func, val=(0, 1))


  def addRange(self, other: 'ComponentL') -> 'ComponentL':
    """when two ranges are added '+'"""
    if self.bot:  return self
    if self.top:  return self
    if other.bot: return other
    if other.top: return other

    assert self.val and other.val , f"{self}, {other}"
    lower = self.val[0] + other.val[0]
    upper = self.val[1] + other.val[1]

    return ComponentL(self.func, val=(lower, upper))


  def subtractRange(self, other: 'ComponentL') -> 'ComponentL':
    """when two ranges are subtracted '-'"""
    if self.bot:  return self
    if self.top:  return self
    if other.bot: return other
    if other.top: return other

    assert self.val and other.val , f"{self}, {other}"
    lower = self.val[0] - other.val[1]
    upper = self.val[1] - other.val[0]

    return ComponentL(self.func, val=(lower, upper))


  def multiplyRange(self, other: 'ComponentL') -> 'ComponentL':
    if self.bot:  return self
    if self.top:  return self
    if other.bot: return other
    if other.top: return other

    assert self.val and other.val , f"{self}, {other}"
    v1 = self.val[0] * other.val[0]
    v2 = self.val[1] * other.val[1]

    return ComponentL(self.func, val=(min(v1,v2), max(v1,v2)))


  def modRange(self) -> 'ComponentL':
    if self.top: return self

    upper = float("+inf")
    if not self.bot:
      assert self.val, f"{self}"
      upper = self.val[1] if 0 < self.val[1] else upper

    return ComponentL(self.func, val=(0, upper))


  def isPositive(self) -> bool:
    return self.val and self.val[0] > 0


  def isNegative(self) -> bool:
    return self.val and self.val[0] < 0


  def isPositiveOrZero(self) -> bool:
    return self.val and self.val[0] >= 0


  def isNegativeOrZero(self) -> bool:
    return self.val and self.val[0] <= 0


  def overlaps(self, other: 'ComponentL') -> bool:
    if self.top or other.top: return False
    if self.bot or other.bot: return True

    assert self.val and other.val , f"{self}, {other}"
    if self.inRange(other.val[0]) or self.inRange(other.val[1]):
      return True
    return False


  def inRange(self, value: float) -> bool:
    if self.top: return False
    if self.bot: return True
    assert self.val, f"{self}"
    return self.val[0] <= value <= self.val[1]


  def isConstant(self):
    return self.val and self.val[0] == self.val[1]


  # TODO: cutUpper/cutLower
  # def cutUpper(self, val: types.NumericT) -> 'ComponentL':
  #   """limit the upper if possible"""
  #   if self.top: return self
  #   if self < other: return self
  #   if other < self:  return other

  #   assert self.val and other.val , f"{self}, {other}"
  #   lower = max(self.val[0], other.val[0])
  #   upper = min(self.val[1], other.val[1])

  #   return ComponentL(self.func, val=(lower, upper))


  def getIntersectRange(self, other: 'ComponentL') -> 'ComponentL':
    """self and other must intersect"""
    assert self.overlaps(other), f"NoOverlap: {self} and {other}"

    if self < other: return self
    if other < self:  return other

    assert self.val and other.val , f"{self}, {other}"
    lower = max(self.val[0], other.val[0])
    upper = min(self.val[1], other.val[1])

    return ComponentL(self.func, val=(lower, upper))


  def getDisjointRange(self, other: 'ComponentL'
  ) -> Tuple['ComponentL', 'ComponentL']:
    """Returns two disjoint ranges with the given range.
    Its the opposite of the intersection of range.
    It maintains the order of self and other in the output.
    """
    if not self.overlaps(other):
      return self, other  # no overlap hence return the same

    if self < other or other < self:
      return self, other  # full overlap has no disjoint

    assert self.val and other.val , f"{self}, {other}"
    swap, lower, upper = False, self.val, other.val
    if lower[0] > upper[0]:
      swap, lower, upper = True, upper, lower  # swap

    # partial overlap can be computed
    disjoint1 = ComponentL(self.func, val=(lower[0], upper[0]))
    disjoint2 = ComponentL(self.func, val=(lower[1], upper[1]))

    return (disjoint2, disjoint1) if swap else (disjoint1, disjoint2)


  def isLowerRangeThan(self, other: 'ComponentL') -> bool:
    """Self's complete range is lower than other (may be overlapped)"""
    if self < other or other < self:
      return False

    assert self.val and other.val , f"{self}, {other}"
    return self.val[0] < other.val[0] and self.val[1] < other.val[0]


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
    super().__init__(func, val, top, bot, ComponentL, "interval")
    # self.componentTop = ComponentL(self.func, top=True)
    # self.componentBot = ComponentL(self.func, bot=True)


  def countConstants(self) -> int:
    """Gives the count of number of constant in the data flow value."""
    if self.top or self.bot: return 0
    assert self.val, f"{self}"
    return sum(1 for val in self.val.values() if val.isConstant())  # type: ignore

################################################
# BOUND END  : interval_lattice
################################################

################################################
# BOUND START: interval_analysis
################################################

class IntervalA(analysis.ValueAnalysisAT):
  """Even-Odd (Parity) Analysis."""
  __slots__ : List[str] = []
  # concrete lattice class of the analysis
  L: Opt[Type[dfv.DataLT]] = OverallL
  # concrete direction class of the analysis
  D: Opt[Type[analysis.DirectionDT]] = analysis.ForwardD
  simNeeded: List[Callable] = [sim.SimAT.Num_Var__to__Num_Lit,
                               sim.SimAT.Num_Bin__to__Num_Lit,
                               sim.SimAT.Deref__to__Vars,
                               sim.SimAT.LhsVar__to__Nil,
                               sim.SimAT.Cond__to__UnCond
                               ]

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

  def Ptr_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.Nop_Instr(nodeId, nodeDfv)

  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: simplifiers
  ################################################

  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[types.NumericT]] = None,
  ) -> Opt[List[types.NumericT]]:
    """Specifically for expression: '_ <relop> _'."""
    # STEP 1: tell the system if the expression can be evaluated
    arg1, arg2 = e.arg1, e.arg2
    if (not e.type.isNumeric()
        or not e.opr.isRelationalOp()
        or not arg1.type.isNumeric()
        or not arg2.type.isNumeric()):
      return sim.SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimPending # tell that sim my be possible if nodeDfv given

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, sim.NumValue) # filter the values

    # STEP 4: If here, eval the expression
    arg1Val = self.getExprDfv(arg1, dfvIn)
    arg2Val = self.getExprDfv(arg2, dfvIn)

    if arg1Val.top or arg2Val.top:
      return sim.SimPending

    overlaps = arg1Val.overlaps(arg2Val)
    constArg1 = arg1Val.isConstant()
    constArg2 = arg2Val.isConstant()
    lowerArg1 = arg1Val.isLowerRangeThan(arg2Val)
    lowerArg2 = arg2Val.isLowerRangeThan(arg1Val)

    result: Opt[bool] = None  # None means don't know
    opCode = e.opr.opCode
    if opCode == op.BO_EQ_OC:
      if overlaps and constArg1 and constArg2:
        result = True
      elif not overlaps:
        result = False
    elif opCode == op.BO_NE_OC:
      if overlaps and constArg1 and constArg2:
        result = False
      elif not overlaps:
        result = True
    elif opCode == op.BO_LE_OC:
      if overlaps and constArg1 and constArg2:
        result = True
      elif not overlaps and lowerArg1:
        result = True
      elif not overlaps and lowerArg2:
        result = False
    elif opCode == op.BO_LT_OC:
      if not overlaps and lowerArg1:
        result = True
      elif not overlaps and lowerArg2:
        result = False
    elif opCode == op.BO_GE_OC:
      if overlaps and constArg1 and constArg2:
        result = True
      elif not overlaps and lowerArg2:
        result = True
      elif not overlaps and lowerArg1:
        result = False
    elif opCode == op.BO_GT_OC:
      if not overlaps and lowerArg2:
        result = True
      elif not overlaps and lowerArg1:
        result = False

    if result is not None:
      return [1 if result else 0]
    else:
      return sim.SimFailed


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[bool]] = None,
  ) -> Opt[List[bool]]:
    # STEP 1: tell the system if the expression can be evaluated
    if not e.type.isNumeric():
      return sim.SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimPending # tell that sim my be possible if nodeDfv given

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, sim.BoolValue) # filter the values

    # STEP 4: If here, eval the expression
    val = cast(ComponentL, dfvIn.getVal(e.name))
    if val.top: return sim.SimPending  # can be evaluated but needs more info
    if val.bot: return sim.SimFailed  # cannot be evaluated
    assert val.val is not None, f"{e}, {val}"
    if val.isExactZero():
      return [False]  # take false edge
    elif not val.inRange(0):
      return [True]  # take true edge
    else:
      return sim.SimFailed  # both edges are possible


  def filterTest(self,
      exprVal: ComponentL,
      valueType: sim.ValueTypeT = sim.NumValue,
  ) -> Callable[[types.T], bool]:
    if valueType == sim.NumValue:
      def valueTestNumeric(numVal: types.NumericT) -> bool:
        if exprVal.top: return False
        if exprVal.bot: return True
        return exprVal.inRange(numVal)
      return valueTestNumeric  # return the test function

    elif valueType == sim.BoolValue:
      def valueTestBoolean(boolVal: bool) -> bool:
        if exprVal.top: return False
        if exprVal.bot: return True
        return exprVal.inRange(0) if not boolVal else not exprVal.inRange(0)
      return valueTestBoolean  # return the test function

    raise ValueError(f"{exprVal}, {valueType}")

  ################################################
  # BOUND END  : simplifiers
  ################################################

  ################################################
  # BOUND START: helper_functions
  ################################################


  def getExprDfv(self,
      rhs: expr.ExprET,
      dfvIn: OverallL
  ) -> ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects the rhs to be numeric."""
    value = self.componentTop

    if isinstance(rhs, expr.LitE):
      assert isinstance(rhs.val, (int, float)), f"{rhs.val}"
      return ComponentL(self.func, val=(rhs.val, rhs.val))

    elif isinstance(rhs, expr.VarE):  # handles ObjectE, PseudoVarE
      return cast(ComponentL, dfvIn.getVal(rhs.name))

    elif isinstance(rhs, expr.DerefE):
      return self.componentBot

    elif isinstance(rhs, expr.CastE):
      return cast(ComponentL, dfvIn.getVal(rhs.arg.name))

    elif isinstance(rhs, expr.SizeOfE):
      return self.componentBot

    elif isinstance(rhs, expr.UnaryE):
      value = self.getExprDfv(rhs.arg, dfvIn)
      if value.top or value.bot:
        return value
      else:
        rhsOpCode = rhs.opr.opCode
        if rhsOpCode == op.UO_MINUS_OC:
          return value.getNegatedRange()
        elif rhsOpCode == op.UO_BIT_NOT_OC:  # reverse the result
          return value.bitNotRange()
        elif rhsOpCode == op.UO_LNOT_OC:
          return value.logicalNotRange()
        assert False, msg.CONTROL_HERE_ERROR

    elif isinstance(rhs, expr.BinaryE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      rhsOpCode = rhs.opr.opCode
      if val1.top or val2.top:
        return self.componentTop
      elif rhsOpCode == op.BO_MOD_OC:
        return val2.modRange()
      elif val1.bot or val2.bot:
        return self.componentBot
      else:
        if rhsOpCode == op.BO_ADD_OC:
          return val1.addRange(val2)
        elif rhsOpCode == op.BO_SUB_OC:
          return val1.subtractRange(val2)
        elif rhsOpCode == op.BO_MUL_OC:
          return val1.multiplyRange(val2)
        else:
          return self.componentBot  # conservative

    elif isinstance(rhs, expr.SelectE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      value, _ = val1.meet(val2)
      return value

    elif isinstance(rhs, (expr.ArrayE, expr.MemberE)):
      names = ir.getExprLValueNames(self.func, rhs)
      for name in names:
        value, _ = value.meet(cast(ComponentL, dfvIn.getVal(name)))
      return value

    elif isinstance(rhs, expr.CallE):
      return self.componentBot

    # control should not reach here
    assert False, f"class: {rhs.__class__} rhs: {rhs}, dfvIn: {dfvIn}"


  def calcTrueFalseDfv(self,
      arg: expr.SimpleET,
      dfvIn: OverallL,
  ) -> Tuple[OverallL, OverallL]:  # dfvFalse, dfvTrue
    """Conditionally propagate data flow values."""
    assert isinstance(arg, expr.VarE), f"{arg}"

    argName = arg.name
    argInDfvVal = dfvIn.getVal(arg.name)
    zeroDfv = ComponentL(self.func, (0, 0))  # always zero on false branch

    dfvValTrue: Dict[types.VarNameT, ComponentL] = {}
    dfvValFalse: Dict[types.VarNameT, ComponentL] = {}
    dfvValFalse[argName] = zeroDfv

    tmpExpr = ir.getTmpVarExpr(self.func, arg.name)
    true1 = true2 = false1 = false2 = None
    if tmpExpr and isinstance(tmpExpr, expr.BinaryE):
      arg1, arg2 = tmpExpr.arg1, tmpExpr.arg2
      assert isinstance(arg1, expr.VarE), f"{tmpExpr}"
      arg1Dfv, arg2Dfv = self.getExprDfv(arg1, dfvIn), self.getExprDfv(arg2, dfvIn)
      opCode = tmpExpr.opr.opCode
      if opCode == op.BO_EQ_OC:
        true1 = true2 = arg1Dfv.getIntersectRange(arg2Dfv)  # equal dfv
        false1, false2 = arg1Dfv.getDisjointRange(arg2Dfv)
      elif opCode == op.BO_NE_OC:
        true1, true2 = arg1Dfv.getDisjointRange(arg2Dfv)
        false1 = false2 = arg1Dfv.getIntersectRange(arg2Dfv)  # equal dfv
      elif opCode in (op.BO_LT_OC, op.BO_LE_OC):
        true1, true2 = arg1Dfv.cutUpper(arg2Dfv), arg2Dfv.cutLower(arg1Dfv)
        false1, false2 = arg1Dfv.cutLower(arg2Dfv), arg2Dfv.cutUpper(arg1Dfv)
      elif opCode in (op.BO_GT_OC, op.BO_GE_OC):
        true1, true2 = arg1Dfv.cutLower(arg2Dfv), arg2Dfv.cutUpper(arg1Dfv)
        false1, false2 = arg1Dfv.cutUpper(arg2Dfv), arg2Dfv.cutLower(arg1Dfv)

      arg2IsVarE = isinstance(arg2, expr.VarE)
      if true1 and true2:
        dfvValTrue[arg1.name] = true1
        if arg2IsVarE: dfvValTrue[arg2.name] = true2
      if false1 and false2:
        dfvValFalse[arg1.name] = true1
        if arg2IsVarE: dfvValFalse[arg2.name] = true2

    return dfv.updateDfv(dfvValFalse, dfvIn), dfv.updateDfv(dfvValTrue, dfvIn)

  ################################################
  # BOUND END  : helper_functions
  ################################################

################################################
# BOUND END  : interval_analysis
################################################
