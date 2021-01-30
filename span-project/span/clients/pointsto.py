#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Points-to analysis.

This (and every) analysis subclasses,
* span.sys.lattice.LatticeLT (to define its lattice)
* span.sys.analysis.AnalysisAT (to define the analysis)
"""

import logging
LOG = logging.getLogger("span")

from typing import Tuple, Dict, List, Optional as Opt, Set, Callable, cast

from span.util.util import LS

import span.ir.ir as ir
import span.ir.types as types
import span.ir.conv as irConv
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs

from span.api.lattice import (ChangedT, Changed, basicLessThanTest,
                              basicEqualTest, getBasicString)
import span.api.dfv as dfv
from span.api.dfv import NodeDfvL
import span.api.analysis as analysis
from span.api.analysis import SimFailed, SimPending, ValueTypeT, \
  NumValue, NameValue, BoolValue, AnalysisAT

################################################
# BOUND START: Points-to lattice.
################################################

HasPointeesT = bool
HasPointees: HasPointeesT = True
NoPointees: HasPointeesT = False


class ComponentL(dfv.ComponentL):

  __slots__ : List[str] = []


  def __init__(self,
      func: constructs.Func,
      val: Opt[Set[types.VarNameT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    # correct the state and type
    self.val: Opt[Set[types.VarNameT]] = val
    if self.val is not None and len(self.val) == 0:
      raise ValueError(f"{self}")


  def meet(self, other) -> Tuple['ComponentL', ChangedT]:
    assert isinstance(other, ComponentL), f"{other}"
    tup = self.basicMeetOp(other)
    if tup:
      return tup
    else:
      assert self.val and other.val, f"{self}, {other}"
      new = self.getCopy()
      new.val.update(other.val)
      return new, Changed


  def getCopy(self) -> 'ComponentL':
    if self.top: return ComponentL(self.func, top=True)
    if self.bot: return ComponentL(self.func, bot=True)

    assert self.val, f"{self}"
    return ComponentL(self.func, self.val.copy())


  def __len__(self):
    if self.top: return 0
    if self.bot: return 0x7FFFFFFF  # a large number

    assert self.val, f"Pointees should be one or more: {self}"
    return len(self.val)


  def __contains__(self, varName: types.VarNameT):
    return self.isPointee(varName)


  def isPointee(self,
      varName: types.VarNameT
  ) -> bool:
    """Given a valid varName, returns True if its a possible pointee."""
    if self.top:
      return False
    if self.bot:
      return True  # this is C, a pointer can point to anything

    assert self.val, f"{self}"
    return varName in self.val


  def addPointee(self,
      varName: types.VarNameT
  ) -> None:
    """Adds a given pointee."""
    if self.top:
      self.top = False
      self.val = set()
      self.val.add(varName)

    elif self.bot:
      pass  # bot includes varName

    else:
      assert self.val, f"{self}"
      self.val.add(varName)


  def addPointees(self,
      varNames: Set[types.VarNameT]
  ) -> None:
    """Adds the given set of pointees."""
    if self.top:
      self.top = False
      self.val = set(varNames)  # copy forced

    elif self.bot:
      pass  # bot includes varName

    else:
      assert self.val is not None
      self.val.update(varNames)


  # def removePointee(self, varName) .... cannot be implemented because,
  #   If the value is self.bot, this class has no type information
  #   to populate self.val with appropriate values.
  #   Given the nature of C pointers, they can point to anything.
  #   Moreover, removePointee() doesn't make sense in pointer analysis.


  def __lt__(self, other) -> bool:
    assert isinstance(other, ComponentL), f"{other}"
    lt = basicLessThanTest(self, other)
    return self.val >= other.val if lt is None else lt  # other should be a subset


  def __eq__(self, other) -> bool:
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = basicEqualTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    val = frozenset(self.val) if self.val else None
    return hash((val, self.top))


  def __str__(self):
    s = getBasicString(self)
    if s: return s
    simpleName = {irConv.simplifyName(name) for name in self.val}
    return f"{simpleName}"


  def __repr__(self):
    return self.__str__()


class OverallL(dfv.OverallL):
  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[types.VarNameT, ComponentL]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot, ComponentL, "PointsToA")  # type: ignore
    self.val: Opt[Dict[types.VarNameT, ComponentL]] = val  # type: ignore


  def getAllVars(self) -> Set[types.VarNameT]:
    """Return a set of vars the analysis is tracking.
    One must override this method if variables are other
    than numeric.
    """
    return ir.getNamesEnv(self.func, pointer=True)


################################################
# BOUND END  : Points-to lattice.
################################################

################################################
# BOUND START: Points-to Analysis.
################################################

class PointsToA(analysis.ValueAnalysisAT):
  """Points-to Analysis."""
  __slots__ : List[str] = []

  L: type = OverallL
  D: Opt[types.DirectionT] = irConv.Forward


  needsRhsDerefToVarsSim: bool = False
  needsLhsDerefToVarsSim: bool = False
  needsNumVarToNumLitSim: bool = False
  needsNumBinToNumLitSim: bool = False
  needsCondToUnCondSim:   bool = True
  needsLhsVarToNilSim:    bool = True
  needsNodeToNilSim:      bool = False


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func, ComponentL, OverallL)


  def isAcceptedType(self, t: types.Type) -> bool:
    return t.isPointer()

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

  def Num_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.Nop_Instr(nodeId, insn, nodeDfv)

  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Simplifiers
  ################################################

  def Deref__to__Vars(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[Set[types.VarNameT]] = None,
  ) -> Opt[Set[types.VarNameT]]:
    varName = e.name

    # STEP 1: check if the expression can be evaluated
    varType = ir.inferTypeOfVal(self.func, varName)

    if not isinstance(varType, (types.Ptr, types.ArrayT)):
      return SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return SimPending

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, NameValue) # filter the values

    # STEP 4: If here, eval the expression
    # special case (deref of array is the array itself)
    if isinstance(varType, types.ArrayT):
      if LS: LOG.info("WARN: Deref_of_Array: %s, %s", e, varType)
      return {varName}

    val = dfvIn.getVal(varName)
    if val.top: return SimPending
    if val.bot:
      return SimFailed
    return val.val


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[Set[bool]] = None,
  ) -> Opt[Set[bool]]:
    # STEP 1: check if the expression can be evaluated
    nameType = ir.inferTypeOfVal(self.func, e.name)
    if not isinstance(nameType, types.Ptr):
      return SimFailed  # i.e. no eval possible for the expression

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return SimPending  # i.e. given a dfv, eval may be possible

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, BoolValue) # filter the values

    # STEP 4: If here, eval the expression
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    val = cast(ComponentL, dfvIn.getVal(e.name))

    if val.bot: return SimFailed  # cannot be evaluated
    if val.top: return SimPending  # can be evaluated, needs more info

    if val.val and len(val.val) == 1 and irConv.NULL_OBJ_NAME in val.val:
      return {False}
    else:
      return SimFailed


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[types.NumericT]] = None,
  ) -> Opt[List[types.NumericT]]:
    """Specifically for expressions: x == y, x != y"""
    # STEP 1: check if the expression can be evaluated
    opCode = e.opr.opCode
    if opCode not in (op.BO_NE_OC, op.BO_EQ_OC):
      return SimFailed
    if not isinstance(e.arg1.type, types.Ptr):
      return SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return SimPending

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, NumValue) # filter the values

    # STEP 4: If here, eval the expression
    leftArgDfv = cast(ComponentL, self.getExprDfv(e.arg1, dfvIn))
    rightArgDfv = cast(ComponentL, self.getExprDfv(e.arg2, dfvIn))

    if leftArgDfv.top or rightArgDfv.top: return SimPending
    if leftArgDfv.bot or rightArgDfv.bot: return SimFailed
    assert leftArgDfv.val and rightArgDfv.val, f"{leftArgDfv}, {rightArgDfv}"

    retVal: Opt[int] = None
    if leftArgDfv == rightArgDfv and len(leftArgDfv.val) == 1:  # equal
      retVal = 1 if opCode == op.BO_EQ_OC else 0
    elif len(leftArgDfv.val & rightArgDfv.val) == 0:  # not equal
        retVal = 0 if opCode == op.BO_EQ_OC else 1

    return [retVal] if retVal is not None else SimFailed


  def filterTest(self,
      exprVal: dfv.ComponentL,
      valueType: ValueTypeT = NumValue,
  ) -> Callable[[types.T], bool]:
    assert isinstance(exprVal, ComponentL), f"{exprVal}"
    if valueType == NumValue:
      def valueTestNumeric(numVal: types.NumericT) -> bool:
        return True
      return valueTestNumeric  # return the test function

    elif valueType == BoolValue:
      def valueTestBoolean(boolVal: bool) -> bool:
        return True
      return valueTestBoolean  # return the test function

    elif valueType == NameValue:
      def valueTestName(nameVal: types.VarNameT) -> bool:
        if exprVal.top: return False
        if exprVal.bot: return True
        return nameVal in exprVal.val
      return valueTestName  # return the test function
    raise ValueError(f"{exprVal}, {valueType}")


  ################################################
  # BOUND END  : Simplifiers
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def namesPossiblyModifiedInCallE(self,
      e: expr.CallE,
      dfvIn: OverallL,
  ) -> Set[types.VarNameT]:
    """Pointers that may be modified in a call (conservative)."""
    names = PointsToA.getNamesUsedInExprNonSyntactically(self.func, e, dfvIn)
    names = ir.filterNamesPointer(self.func, names)
    return names


  def getExprDfv(self,
      rhs: expr.ExprET,
      dfvIn: OverallL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> dfv.ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects the rhs to be pointer type or an array type."""
    value: dfv.ComponentL = self.componentTop
    rhsType = rhs.type
    # assert isinstance(rhsType, (types.Ptr, types.ArrayT, types.FuncSig)), \
    #   f"{type(rhs)}: {rhsType}, {rhs}"
    if not isinstance(rhsType, (types.Ptr, types.ArrayT, types.FuncSig)): # FIXME
      return self.componentBot  #FIXME: safe approximation

    if isinstance(rhs, expr.LitE):
      if rhs.isString():
        return ComponentL(self.func, val={rhs.name})
      elif rhs.val == 0:
        return ComponentL(self.func, val={ir.NULL_OBJ_NAME})
      else:
        return self.componentBot  # a sound over-approximation

    elif isinstance(rhs, expr.AddrOfE):
      arg = rhs.arg
      if isinstance(arg, expr.VarE):  # handles PseudoVarE too
        return ComponentL(self.func, val={arg.name})
      elif isinstance(arg, (expr.ArrayE, expr.MemberE, expr.DerefE)):
        names = PointsToA.getNamesOfLValuesInExpr(self.func, arg, dfvIn)
        return ComponentL(self.func, val=names) if names else self.componentTop

    elif isinstance(rhs, expr.VarE):  # handles PseudoVarE too
      if isinstance(rhsType, types.Ptr):
        return dfvIn.getVal(rhs.name)
      elif isinstance(rhsType, (types.ArrayT, types.FuncSig)):
        return ComponentL(self.func, val={rhs.name})
      else:  # for all other types
        if LS: LOG.error("%s", rhsType)
        return self.componentBot

    elif isinstance(rhs, expr.SizeOfE):
      return self.componentBot

    elif isinstance(rhs, expr.CastE):
      #return self.componentBot
      if isinstance(rhsType, types.Ptr):
        return self.getExprDfv(rhs.arg, dfvIn)
      else:
        return self.componentBot

    elif isinstance(rhs, expr.DerefE):
      names = PointsToA.getNamesUsedInExprNonSyntactically(self.func, rhs, dfvIn)
      names = ir.filterNamesPointer(self.func, names)
      for name in names:
        value, _ = value.meet(dfvIn.getVal(name))
      return value if names else self.componentTop

    elif isinstance(rhs, expr.UnaryE):
      return self.componentBot

    elif isinstance(rhs, expr.BinaryE):
      return self.getExprDfvBinArith(rhs, dfvIn)

    elif isinstance(rhs, expr.SelectE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      value, _ = val1.meet(val2)
      return value

    elif isinstance(rhs, (expr.ArrayE, expr.MemberE)):
      names = PointsToA.getNamesOfLValuesInExpr(self.func, rhs, dfvIn)
      for name in names:
        value, _ = value.meet(dfvIn.getVal(name))
      return value

    elif isinstance(rhs, expr.CallE):
      return self.getExprDfvCallE(rhs, calleeBi)

    raise ValueError(f"{rhs}")


  def getExprDfvBinArith(self,
      binExpr: expr.BinaryE,
      dfvIn: OverallL
  ) -> dfv.ComponentL:
    """Processes binary expressions with ptr type."""
    if not isinstance(binExpr.type, types.Ptr):
      return self.componentBot

    arg1 = binExpr.arg1
    arg2 = binExpr.arg2
    ptrVarName: Opt[str] = None
    isArray = False

    # Assuming only one of the args is a pointer/array variable
    # Note: binary subtraction between two pointers results in an integer
    if isinstance(arg1, expr.VarE):
      ptrVarName = arg1.name
      if isinstance(arg1.type, types.ArrayT):
        isArray = True
    elif isinstance(arg2, expr.VarE):
      ptrVarName = arg2.name
      if isinstance(arg2.type, types.ArrayT):
        isArray = True

    assert ptrVarName is not None

    if isArray:  # arr + 1 etc. results in ptr to an element of arr
      return ComponentL(self.func, val={ptrVarName})

    # if here: no array is used in the expression
    newVal: dfv.ComponentL = self.componentTop

    pointees = dfvIn.getVal(ptrVarName)
    if pointees.top:
      newVal = self.componentTop
    elif pointees.bot:
      newVal = self.componentBot
    else:
      # Check if all the pointees are arrays.
      assert pointees.val
      for pointee in pointees.val:
        if not isinstance(ir.inferTypeOfVal(self.func, pointee), types.ArrayT):
          # return bot even if one pointee is not an array
          newVal = self.componentBot
          break
      else:
        # if here: all pointees are arrays
        newVal = pointees

    return newVal


  @staticmethod
  def getNamesOfLValuesInExpr(func: constructs.Func,
      e: expr.ExprET,
      dfvIn: OverallL = None
  ) -> Set[types.VarNameT]:
    """Returns the locations that may be modified,
    if this expression was on the LHS of an assignment."""
    if dfvIn is None:  # become conservative
      return set(ir.getExprLValueNames(func, e))

    names = set()

    if isinstance(e, expr.VarE):
      names.add(e.name)
      return names

    elif isinstance(e, expr.DerefE):
      assert isinstance(e.arg, expr.VarE), f"{e}"
      names.update(PointsToA.getNamesOfPointees(func, e.arg.name, dfvIn))
      return names

    elif isinstance(e, expr.ArrayE):
      if e.hasDereference():
        names.update(PointsToA.getNamesOfPointees(func, e.getArrayName(), dfvIn))
      else:
        names.add(e.getArrayName())
      return names

    elif isinstance(e, expr.MemberE):
      assert e.hasDereference(), f"{e}"
      pointeeNames = PointsToA.getNamesOfPointees(func, e.of.name, dfvIn)
      for name in pointeeNames:
        names.add(f"{name}.{e.name}")
      return names

    raise ValueError(f"{e}")


  def getExprLValueNames(self,
      func: constructs.Func,
      lhs: expr.ExprET,
      dfvIn: dfv.OverallL
  ) -> Set[types.VarNameT]:
    """Points-to analysis overrides this function."""
    names = PointsToA.getNamesUsedInExprNonSyntactically(func, lhs, dfvIn)
    if not names:
      return super().getExprLValueNames(func, lhs, dfvIn)
    else:
      return names


  @staticmethod
  def getNamesUsedInExprNonSyntactically(
      func: constructs.Func,
      e: expr.ExprET,
      dfvIn: OverallL = None,
  ) -> Set[types.VarNameT]:
    """
    This function returns the possible locations used in a DerefET/CallE
    expression conservatively/using the given points-to information.

    The function is designed in a way such that it can be called
    by other modules. The func arg has been specially added for this.
    """
    if dfvIn is None:  # default to conservative behavior
      return ir.getNamesUsedInExprNonSyntactically(func, e)

    varNames = set()

    if isinstance(e, expr.LitE) and e.isString():  # a string literal
      varNames.add(e.name)
      return varNames

    elif isinstance(e, expr.DerefE):
      assert isinstance(e.arg, expr.VarE), f"{e}"
      varNames.update(PointsToA.getNamesOfPointees(func, e.arg.name, dfvIn))
      return varNames

    elif isinstance(e, expr.ArrayE):
      if e.hasDereference():
        varNames.update(PointsToA.getNamesOfPointees(func, e.of.name, dfvIn))
      return varNames

    elif isinstance(e, expr.MemberE):
      assert e.hasDereference(), f"{e}"
      pointeeNames = PointsToA.getNamesOfPointees(func, e.of.name, dfvIn)
      for name in pointeeNames:
        varNames.add(f"{name}.{e.name}")
      return varNames

    elif isinstance(e, expr.CallE):  # FIXME: check the logic
      for arg in e.args:  # iterate over the call arguments
        argType = arg.type
        if isinstance(argType, types.ArrayT):
          argType = argType.getElementTypeFinal()
        if isinstance(argType, types.Ptr): # only ptr arguments matter
          if isinstance(arg, expr.AddrOfE):
            assert isinstance(arg.arg, expr.VarE), f"{arg}"
            varNames.add(arg.arg.name)
            continue
          assert isinstance(arg, expr.VarE), f"{arg}"
          names: Set[types.VarNameT] = set()
          PointsToA._getNamesOfArgPointeesPtr(func, arg.name, names, dfvIn)
          varNames.update(names)
      varNames.update(ir.getNamesGlobal(func))  # non-pointer vars included
      return varNames

    return varNames


  @staticmethod
  def _getNamesOfArgPointeesPtr(func,
      varName: types.VarNameT,
      names: Set[types.VarNameT],
      dfvIn: OverallL = None,
  ) -> None:
    """
    Don't call this directly. Use:
    getNamesUsedInExprNonSyntactically()
    """
    assert names is not None
    pointeeNames = PointsToA.getNamesOfPointees(func, varName, dfvIn)
    ptrPointeeNames = ir.filterNamesPointer(func, pointeeNames)
    for ptrName in ptrPointeeNames:
      PointsToA._getNamesOfArgPointeesPtr(func, ptrName, names, dfvIn)
    names.update(ptrPointeeNames)


  @staticmethod
  def getNamesOfPointees(
      func: constructs.Func,
      varName: types.VarNameT,
      dfvIn: OverallL = None
  ) -> Set[types.VarNameT]:
    """Returns the pointee names of the given pointer name,
    if dfvIn is None it returns conservative value."""

    # Step 1: what type is the given name?
    varType = ir.inferTypeOfVal(func, varName)
    if isinstance(varType, types.ArrayT):
      varType = varType.getElementTypeFinal()

    if not isinstance(varType, types.Ptr):
      raise ValueError(f"{varName}: {varType}")

    # Step 2: if here its a pointer, get its pointees
    pointeeType = varType.getPointeeType()

    if dfvIn is None:  # become conservative
      return ir.getNamesEnv(func, pointeeType)

    varDfv = dfvIn.getVal(varName)
    if varDfv.top:        # no result
      return set()
    elif varDfv.bot:      # conservative result
      return ir.getNamesEnv(func, pointeeType)
    else:                 # precise result
      assert varDfv.val, f"{varDfv}"
      return varDfv.val - irConv.NULL_OBJ_SET

  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : Points-to Analysis.
################################################
