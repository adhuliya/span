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
    tup = lattice.basicMeetOp(self, other)
    if tup:
      return tup
    elif self.val == other.val:
      return self, NoChange
    else:
      return ComponentL(self.func, bot=True), Changed


  def __lt__(self, other: 'ComponentL') -> bool:
    """For documentation see: span.api.lattice.LatticeLT.__lt__.__doc__"""
    lt = lattice.basicLessThanTest(self, other)
    return self.val == other.val if lt is None else lt


  def __eq__(self, other) -> bool:
    """For documentation see: `span.api.lattice.LatticeLT.__eq__`"""
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = lattice.basicEqualTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    return hash(self.func.name) ^ hash((self.val, self.top, self.bot))


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

class ConstA(analysis.ValueAnalysisAT):
  """Constant Propagation Analysis."""
  __slots__ : List[str] = []
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
  # uses default implementation in analysis.ValueAnalysisAT class
  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Simplifiers
  ################################################

  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[types.NumericT]] = None,
  ) -> Opt[List[types.NumericT]]:
    # STEP 1: check if the expression can be evaluated
    varType = e.type
    if not varType.isNumeric():
      return sim.SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimPending

    # STEP 3: If here, either eval or filter the evals
    if values is None: # eval
      exprVal = self.getExprDfv(e, cast(OverallL, nodeDfv.dfvIn))
      if exprVal.bot: return sim.SimFailed  # cannot be evaluated
      if exprVal.top: return sim.SimPending  # can be evaluated, needs more info
      return [exprVal.val]
    else: # filter the values
      if not values: return values  # returns an empty list
      exprVal = self.getExprDfv(e, cast(OverallL, nodeDfv.dfvIn))
      if exprVal.bot:
        return values
      elif exprVal.top:
        return sim.SimPending
      else:
        assert exprVal.val is not None, f"{e}, {exprVal}, {nodeDfv.dfvIn}"
        testFunc = lambda val: exprVal.val == val
        return list(filter(testFunc, values))


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
      arg1Dfv = self.getExprDfv(tmpExpr.arg1, dfvIn)
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


