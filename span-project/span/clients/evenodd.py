#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Even-Odd Analysis.

This (and every) analysis subclasses,
* span.sys.lattice.LatticeLT (to define its lattice)
* span.sys.analysis.AnalysisAT (to define the analysis)
"""

import logging

from span.ir.conv import Forward

LOG = logging.getLogger("span")
from typing import Tuple, Dict, Set, List, Optional as Opt, Callable, cast

import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs

from span.api.lattice import DataLT, ChangedT, Changed,\
  basicMeetOp, basicLessThanTest, basicEqualTest, getBasicString
import span.api.dfv as dfv
from span.api.dfv import NodeDfvL
import span.api.analysis as analysis
from span.api.analysis import SimFailed, SimPending, BoolValue, \
  NumValue, ValueTypeT, AnalysisAT

Even = True
Odd = False


################################################
# BOUND START: evenodd_lattice
################################################

class ComponentL(dfv.ComponentL):
  """
      Top
     /   \
   Even Odd
     \   /
      Bot
  """

  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[bool] = None,  # True/False if Even/Odd
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val: Opt[bool] = val


  def meet(self,
      other: 'ComponentL'
  ) -> Tuple['ComponentL', ChangedT]:
    tup = basicMeetOp(self, other)
    if tup:
      return tup
    elif self.val == other.val:
      return self, not Changed
    else:
      return ComponentL(self.func, bot=True), Changed


  def __lt__(self,
      other: 'ComponentL'
  ) -> bool:
    """A non-strict weaker-than test. See doc of super class."""
    lt = basicLessThanTest(self, other)
    return self.val == other.val if lt is None else lt


  def __eq__(self, other) -> bool:
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = basicEqualTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    return hash((self.val, self.top, self.bot))


  def getCopy(self) -> 'ComponentL':
    if self.top: ComponentL(self.func, top=True)
    if self.bot: ComponentL(self.func, bot=True)
    return ComponentL(self.func, self.val)


  def __str__(self):
    #return f"{self.top}, {self.bot}, {self.val}"
    s = getBasicString(self)
    return s if s else f"{'Even' if self.val else 'Odd'}"


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
    super().__init__(func, val, top, bot, ComponentL, "EvenOddA")
    # self.componentTop = ComponentL(self.func, top=True)
    # self.componentBot = ComponentL(self.func, bot=True)


################################################
# BOUND END  : evenodd_lattice
################################################

################################################
# BOUND START: evenodd_analysis
################################################

class EvenOddA(analysis.ValueAnalysisAT):
  """Even-Odd (Parity) Analysis."""
  __slots__ : List[str] = ["componentEven", "componentOdd"]
  L: type = OverallL
  # direction of the analysis
  D: Opt[types.DirectionT] = Forward


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func, ComponentL, OverallL)
    self.componentEven: ComponentL = ComponentL(self.func, val=Even)
    self.componentOdd: ComponentL = ComponentL(self.func, val=Odd)


  ################################################
  # BOUND START: Special_Instructions
  ################################################
  # uses default implementation in analysis.ValueAnalysisAT class
  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: normal_instructions
  ################################################

  def Ptr_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.Nop_Instr(nodeId, insn, nodeDfv)

  ################################################
  # BOUND END  : normal_instructions
  ################################################

  ################################################
  # BOUND START: simplifiers
  ################################################

  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[Set[types.NumericT]] = None,
  ) -> Opt[Set[types.NumericT]]:
    # STEP 1: tell the system if the expression can be evaluated
    if not e.type.isNumeric() or e.type.isArray():
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
    return SimFailed  # even-odd cannot really simplify


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[Set[types.NumericT]] = None,
  ) -> Opt[Set[types.NumericT]]:
    """Specifically for expression: 'var % 2'."""
    arg1, arg2 = e.arg1, e.arg2
    # STEP 1: check if the expression can be evaluated
    if not e.opr is op.BO_MOD: return SimFailed
    if isinstance(arg2, expr.VarE): return SimFailed
    if isinstance(arg2, expr.LitE) and arg2.val != 2: return SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return SimPending

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, NumValue) # filter the values

    # STEP 4: If here, eval the expression
    assert isinstance(arg1, expr.VarE), f"{e}"
    varDfv = dfvIn.getVal(arg1.name)
    if varDfv.top: return SimPending
    if varDfv.bot: return SimFailed
    if varDfv.val is Even: return {0}
    if varDfv.val is Odd: return {1}

    raise ValueError(f"{e}: {varDfv} {nodeDfv}")


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
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
    if val.top: return SimPending  # can be evaluated, needs more info
    if val.bot: return SimFailed  # cannot be evaluated
    assert val.val is not None, f"{e}, {val}"
    if val.val is Odd: return {True}  # take true edge
    return SimFailed


  def filterTest(self,
      exprVal: ComponentL,
      valueType: ValueTypeT = NumValue,
  ) -> Callable[[types.T], bool]:
    if valueType == NumValue:
      def valueTestNumeric(numVal: types.NumericT) -> bool:
        if exprVal.top: return False
        if exprVal.bot: return True
        assert exprVal.val is not None, f"{exprVal}, {numVal}"
        if exprVal.val: return not bool(numVal % 2) # even
        if not exprVal.val: return bool(numVal % 2) # odd
        assert False, f"{exprVal}, {numVal}"
      return valueTestNumeric  # return the test function

    elif valueType == BoolValue:
      def valueTestBoolean(boolVal: bool) -> bool:
        if exprVal.top: return False
        if exprVal.bot: return True
        assert exprVal.val, f"{exprVal}, {boolVal}"
        if not boolVal: return exprVal.val # False i.e. 0 must be even
        # True i.e. non-0 can be even or odd
        return True # default fallback
      return valueTestBoolean  # return the test function

    raise ValueError(f"{exprVal}, {valueType}")

  ################################################
  # BOUND END  : simplifiers
  ################################################

  ################################################
  # BOUND START: helper_functions
  ################################################

  def getExprDfvLitE(self,
      e: expr.LitE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    if int(e.val) == e.val:  # an integer
      return self.componentOdd if e.val % 2 else self.componentEven
    else:  # a floating point number
      return self.componentBot


  def getExprDfvUnaryE(self,
      e: expr.UnaryE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    value = dfvInGetVal(e.arg.name)
    if value.top or value.bot:
      return value
    else:
      rhsOpCode = e.opr.opCode
      if rhsOpCode == op.UO_MINUS_OC:
        return value
      elif rhsOpCode in (op.UO_BIT_NOT_OC, op.UO_LNOT_OC):  # reverse the result
        return self.componentOdd if value.val is Even else self.componentEven
      else:
        return self.componentBot


  def getExprDfvBinaryE(self,
      e: expr.BinaryE,
      dfvIn: dfv.OverallL,
  ) -> dfv.ComponentL:
    val1 = self.getExprDfv(e.arg1, dfvIn)
    val2 = self.getExprDfv(e.arg2, dfvIn)
    if val1.top or val2.top: return self.componentTop
    if val1.bot or val2.bot: return self.componentBot
    else:
      same: bool = val1.val is val2.val
      rhsOpCode = e.opr.opCode
      if rhsOpCode is op.BO_ADD_OC:
        return self.componentEven if same else self.componentOdd
      if rhsOpCode is op.BO_SUB_OC:
        return self.componentEven if same else self.componentOdd
      if rhsOpCode is op.BO_MUL_OC:
        oneEven: bool = True if val1.val or val2.val else False
        return self.componentEven if oneEven else self.componentOdd
      if rhsOpCode is op.BO_MOD_OC:
        if same and val1.val is Even:
          return self.componentEven
        if not same and val2.val is Even:
          return self.componentOdd
        return self.componentBot

      return self.componentBot  # conservative

  ################################################
  # BOUND END  : helper_functions
  ################################################

################################################
# BOUND END  : evenodd_analysis
################################################
