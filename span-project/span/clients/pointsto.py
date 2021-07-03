#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Points-to analysis.

This (and every) analysis subclasses,
* span.sys.lattice.DataLT (to define its lattice)
* span.sys.analysis.AnalysisAT (to define the analysis)
"""

import logging
LOG = logging.getLogger(__name__)
LDB, LIN, LER, LWA = LOG.debug, LOG.info, LOG.error, LOG.warning

from typing import Tuple, Dict, List, Optional as Opt, Set, Callable, cast, Type

from span.util.util import LS
from span.util import util #IMPORTANT


from span.ir.tunit import TranslationUnit
import span.ir.ir as ir
from span.ir.types import (
  VarNameT, Type as SpanType, Ptr, ArrayT, FuncSig,
  NodeIdT, NumericT, T, DirectionT,
)
from span.ir.conv import (
  simplifyName, Forward, NULL_OBJ_NAME, NULL_OBJ_SINGLETON_SET
)
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs

from span.api.lattice import (ChangedT, Changed, basicLessThanTest,
                              basicEqualsTest, getBasicString, mergeAll, DataLT, )
import span.api.dfv as dfv
from span.api.dfv import DfvPairL
import span.api.analysis as analysis
from span.api.analysis import (
  SimFailed, SimPending, ValueTypeT,
  NumValue, NameValue, BoolValue,
)

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
      val: Opt[Set[VarNameT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val: Opt[Set[VarNameT]] = val # to charm pycharm
    if self.val is not None and len(self.val) == 0:
      raise ValueError(f"{self}")


  def meet(self, other) -> Tuple['ComponentL', ChangedT]:
    assert isinstance(other, ComponentL), f"{other}"
    tup = self.basicMeetOp(other)
    if tup:
      return tup
    else:
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


  def __contains__(self, varName: VarNameT):
    return self.isPointee(varName)


  def isPointee(self,
      varName: VarNameT
  ) -> bool:
    """Given a valid varName, returns True if its a possible pointee."""
    if self.top: return False
    if self.bot: return True  # this is C, a pointer can point to anything

    assert self.val, f"{self}"
    return varName in self.val


  def addPointee(self,
      varName: VarNameT
  ) -> None:
    """Adds a given pointee. Mutates 'self'."""
    if   self.top: self.top, self.val = False, {varName}
    elif self.bot: pass  # bot includes varName
    else:  self.val.add(varName)


  def addPointees(self,
      varNames: Set[VarNameT]
  ) -> None:
    """Adds the given set of pointees. Mutates 'self'."""
    if self.top: self.top, self.val = False, set(varNames)  # forced copy
    elif self.bot: pass  # bot includes varNames
    else: self.val.update(varNames)


  # def removePointee(self, varName) .... cannot be implemented because,
  #   If the value is self.bot, this class has no type information
  #   to populate self.val with appropriate values.
  #   Given the nature of C pointers, they can point to anything.
  #   Moreover, removePointee() doesn't make sense in pointer analysis.


  def isZero(self) -> Tuple[bool, bool]:
    """Returns,
     * True, True. if NULL_OBJ_NAME is the only pointee.
     * False, True. if NULL_OBJ_NAME is never the pointee.
     * False, False. if can't say.
     """
    selfVal = self.val
    if selfVal:
      if len(selfVal) == 1 and NULL_OBJ_NAME in selfVal:
        return True, True # its zero
      elif NULL_OBJ_NAME not in selfVal:
        return False, True # its never zero
    return False, False # in all other cases it can't say


  def __lt__(self, other) -> bool:
    assert isinstance(other, ComponentL), f"{other}"
    lt = basicLessThanTest(self, other)
    return (self.val >= other.val) if lt is None else lt  # other should be a subset


  def __eq__(self, other) -> bool:
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = basicEqualsTest(self, other)
    return (self.val == other.val) if equal is None else equal


  def __hash__(self):
    val = frozenset(self.val) if self.val else None
    return hash((val, self.top))


  def __str__(self):
    s = getBasicString(self)
    simpleNames = sorted(name if util.DD1 else simplifyName(name)
                         for name in self.val) if self.val else None
    if util.DD5:
      idStr = f"(setId:{id(self.val)})(id:{id(self)})"
      return f"{s}{idStr}" if s else f"{simpleNames}{idStr}"
    else:
      return s if s else f"{simpleNames}"


  def __repr__(self): return self.__str__()


class OverallL(dfv.OverallL):
  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[VarNameT, ComponentL]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot, ComponentL, "PointsToA")  # type: ignore
    self.val: Opt[Dict[VarNameT, ComponentL]] = val  # type: ignore


  @classmethod
  def isAcceptedType(cls,
      t: SpanType,
      name: Opt[VarNameT] = None,
  ) -> bool:
    """Returns True if the type of the instruction/variable is
    of interest to the analysis, i.e. a pointer type.
    """
    check1 = t.isPointerOrVoid()
    check2 = name != NULL_OBJ_NAME
    return check1 and check2


  def getDefaultValForGlobal(self) -> ComponentL:
    return ComponentL(self.func, val=NULL_OBJ_SINGLETON_SET)


#   @classmethod
#   def getAllVars(cls, func: constructs.Func) -> Set[VarNameT]:
#     """Returns all names which the points-to analysis is interested in.
#     All array names and function names are technically pointers,
#     but they are avoided as the associated info is trivial.
#     """
#     return ir.getNamesEnv(func, pointer=True)


################################################
# BOUND END  : Points-to lattice.
################################################

################################################
# BOUND START: Points-to Analysis.
################################################


class PointsToA(analysis.ValueAnalysisAT):
  """Points-to Analysis."""
  __slots__ : List[str] = []

  L: Type[dfv.OverallL] = OverallL
  D: DirectionT = Forward


  needsRhsDerefToVarsSim: bool = False
  needsLhsDerefToVarsSim: bool = False
  needsNumVarToNumLitSim: bool = False
  needsNumBinToNumLitSim: bool = False
  needsCondToUnCondSim:   bool = True
  needsLhsVarToNilSim:    bool = True
  needsNodeToNilSim:      bool = False
  needsFpCallSim:         bool = True


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func, ComponentL, OverallL)
    dfv.initTopBotOverall(func, PointsToA.__name__, PointsToA.L)


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

  # def Num_Assign_Instr(self,
  #     nodeId: NodeIdT,
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

  def Deref__to__Vars(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[VarNameT]] = None,
  ) -> Opt[Set[VarNameT]]:
    varName = e.name

    # STEP 1: check if the expression can be evaluated
    varType = ir.inferTypeOfVal(self.func, varName)

    if not (varType.isPointerOrVoid() or varType.isArrayOrVoid()):
      return SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None: return SimPending

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      return self.filterValues(e, values, dfvIn, NameValue)

    # STEP 4: If here, eval the expression
    # special case (deref of array is the array itself)
    if isinstance(varType, ArrayT):
      if LS: LWA("Deref_of_Array: %s, %s", e, varType)
      return {varName}

    val = dfvIn.getVal(varName)
    if val.top: return SimPending
    if val.bot: return SimFailed
    return val.val


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[bool]] = None,
  ) -> Opt[Set[bool]]:
    # STEP 1: check if the expression can be evaluated
    varType = self.func.tUnit.inferTypeOfVal(e.name)
    if not varType.isPointer():
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

    zero, certain = val.isZero()
    return ({False} if zero else {True}) if certain else SimFailed


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[NumericT]] = None,
  ) -> Opt[Set[NumericT]]:
    """Specifically for expressions: x == y, x != y"""
    # STEP 1: check if the expression can be evaluated
    opCode = e.opr.opCode
    if opCode not in (op.BO_NE_OC, op.BO_EQ_OC):
      return SimFailed
    if not e.arg1.type.isPointer():
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

    return {retVal} if retVal is not None else SimFailed


  def filterTest(self,
      exprVal: dfv.ComponentL,
      valueType: ValueTypeT = NumValue,
  ) -> Callable[[T], bool]:
    assert isinstance(exprVal, ComponentL), f"{exprVal}"
    if valueType == NumValue:
      def valueTestNumeric(numVal: NumericT) -> bool:
        return True
      return valueTestNumeric  # return the test function

    elif valueType == BoolValue:
      def valueTestBoolean(boolVal: bool) -> bool:
        zero, certain = exprVal.isZero()
        same = (not zero) == boolVal
        return (True if same else False) if certain else True
      return valueTestBoolean  # return the test function

    elif valueType == NameValue:
      def valueTestName(nameVal: VarNameT) -> bool:
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

  def getExprDfv(self,
      rhs: expr.ExprET,
      dfvIn: OverallL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
      nodeId: NodeIdT = 0,
  ) -> dfv.ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects the rhs to be pointer type or an array type."""
    value: dfv.ComponentL = self.componentTop
    rhsType, dfvInGetVal = rhs.type, dfvIn.getVal
    # assert isinstance(rhsType, (Ptr, ArrayT, FuncSig)), \
    #   f"{type(rhs)}: {rhsType}, {rhs}"

    if isinstance(rhs, expr.LitE):
      if rhs.isString():
        return ComponentL(self.func, val={rhs.name})
      elif rhs.val == 0:
        return ComponentL(self.func, val=NULL_OBJ_SINGLETON_SET)
      else:
        return self.componentBot  # a sound over-approximation

    if not rhsType.isPointerOrVoid() and \
        not isinstance(rhsType, (ArrayT, FuncSig)):
      return self.componentBot  #FIXME: safe approximation
      #raise ValueError(f"{rhs}, {rhsType}, {rhs.info}")

    if isinstance(rhs, expr.VarE):  # handles PpmsVarE too
      if isinstance(rhsType, Ptr) or rhsType.isVoid():  # don't use isPointer()
        return dfvInGetVal(rhs.name)
      elif isinstance(rhsType, (ArrayT, FuncSig)):
        return ComponentL(self.func, val={rhs.name})
      else:  # for all other types
        raise ValueError(f"{rhs}, {rhsType}, {rhs.info}")

    elif isinstance(rhs, expr.DerefE):
      rhsArgType = rhs.arg.type
      if rhsArgType.isFuncSig():
        value = ComponentL(self.func, val={rhs.arg.name})
      elif rhsType.isFuncSig(): # In *x add 'x' (as its pointees are func names)
        value = dfvInGetVal(rhs.arg.name)
      else:
        names = PointsToA.getNamesLValuesOfExpr(self.func, rhs, dfvIn)
        names = ir.filterNamesPointer(self.func, names, addFunc=True)
        value = mergeAll(dfvInGetVal(name) for name in names) if names else value
      return value

    elif isinstance(rhs, expr.AddrOfE):
      arg = rhs.arg
      if isinstance(arg, expr.VarE):  # handles PseudoVarE, &arr, &func too
        return ComponentL(self.func, val={arg.name})
      elif isinstance(arg, (expr.ArrayE, expr.MemberE, expr.DerefE)):
        names = PointsToA.getNamesLValuesOfExpr(self.func, arg, dfvIn)
        return ComponentL(self.func, val=names) if names else self.componentTop

    elif isinstance(rhs, expr.SizeOfE):
      return self.componentBot

    elif isinstance(rhs, expr.CastE):
      #return self.componentBot
      if rhsType.isPointerOrVoid():
        return self.getExprDfv(rhs.arg, dfvIn)
      else:
        return self.componentBot

    elif isinstance(rhs, expr.UnaryE):
      return self.componentBot

    elif isinstance(rhs, expr.BinaryE):
      val = self.getExprDfvBinArith(rhs, dfvIn)
      return val

    elif isinstance(rhs, expr.SelectE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      value, _ = val1.meet(val2)
      return value

    elif isinstance(rhs, (expr.ArrayE, expr.MemberE)):
      names = PointsToA.getNamesLValuesOfExpr(self.func, rhs, dfvIn)
      if rhsType.isArray(): # e.g. 3t=s->inUse; where s->inUse is an array.
        if names: # else value stays Top
          value = ComponentL(self.func, val=names)
      else:
        for name in names:
          value, _ = value.meet(dfvInGetVal(name))
      return value

    elif isinstance(rhs, expr.CallE):
      return self.getExprDfvCallE(rhs, calleeBi)

    raise ValueError(f"{rhs}")


  def getExprDfvBinArith(self,
      binExpr: expr.BinaryE,
      dfvIn: OverallL
  ) -> dfv.ComponentL:
    """Processes binary expressions with ptr type."""
    if not isinstance(binExpr.type, Ptr):
      return self.componentBot

    arg1, arg2 = binExpr.arg1, binExpr.arg2
    arg1Type, arg2Type = arg1.type, arg2.type
    arg1IsArr, arg2IsArr = arg1Type.isArray(), arg2Type.isArray()
    arg1IsPtr, arg2IsPtr = arg1Type.isPointer(), arg2Type.isPointer()

    # Assuming only one of the args is a pointer/array variable
    # Note: binary subtraction between two pointers results in an integer
    if arg1IsArr or arg1IsPtr:
      ptrVarName = arg1.name # must be a VarE arg
    else:
      ptrVarName = arg2.name # must be a VarE arg of Ptr or Arr type

    assert ptrVarName is not None

    if arg1IsArr or arg2IsArr:  # arr + 1 etc. results in ptr to an element of arr
      return ComponentL(self.func, val={ptrVarName})
    else: # must be a Ptr
      return dfvIn.getVal(ptrVarName)


  def namesPossiblyModifiedInCallE(self,
      e: expr.CallE,
      dfvIn: OverallL,
  ) -> Set[VarNameT]:
    """Pointers that may be modified in a call (conservative)."""
    names = PointsToA.getNamesInExprMentionedIndirectly(self.func, e, dfvIn)
    names = ir.filterNamesPointer(self.func, names)
    return names


  @staticmethod
  def getNamesLValuesOfExpr(func: constructs.Func,
      e: expr.ExprET,
      dfvIn: OverallL = None
  ) -> Set[VarNameT]:
    """Returns the locations that may be modified,
    if this expression was on the LHS of an assignment."""
    if dfvIn is None:  # become conservative
      return set(ir.getNamesLValuesOfExpr(func, e))

    names = set()

    if isinstance(e, expr.VarE):
      names.add(e.name)
      return names

    elif isinstance(e, expr.DerefE):
      names.update(PointsToA.getNamesOfPointees(func, e.arg.name, dfvIn))
      return names

    elif isinstance(e, expr.ArrayE):
      if e.hasDereference():
        names.update(PointsToA.getNamesOfPointees(func, e.getArrayName(), dfvIn))
      else:
        names.add(e.getArrayName())
      return names

    elif isinstance(e, expr.MemberE):
      pointeeNames = PointsToA.getNamesOfPointees(func, e.of.name, dfvIn)
      for name in pointeeNames:
        names.add(f"{name}.{e.name}")
      return names

    raise ValueError(f"{e}")


  def getExprLValueNames(self,
      func: constructs.Func,
      lhs: expr.ExprET,
      dfvIn: dfv.OverallL
  ) -> Set[VarNameT]:
    return PointsToA.getNamesLValuesOfExpr(func, lhs, dfvIn)


  @staticmethod
  def getNamesInExprMentionedIndirectly(
      func: constructs.Func,
      e: expr.ExprET,
      dfvIn: OverallL = None,
  ) -> Set[VarNameT]:
    """
    This function returns the possible locations used in a DerefET/CallE
    expression conservatively/using the given points-to information.

    The function is designed in a way such that it can be called
    by other modules. The func arg has been specially added for this.
    """
    if dfvIn is None:  # default to conservative behavior
      return ir.getNamesInExprMentionedIndirectly(func, e)

    varNames = set()

    if isinstance(e, expr.LitE) and e.isString():  # a string literal
      varNames.add(e.name)

    elif isinstance(e, expr.DerefE):
      varNames.update(PointsToA.getNamesOfPointees(func, e.arg.name, dfvIn))

    elif isinstance(e, expr.ArrayE):
      if e.hasDereference():
        varNames.update(PointsToA.getNamesOfPointees(func, e.of.name, dfvIn))

    elif isinstance(e, expr.MemberE):
      pointeeNames = PointsToA.getNamesOfPointees(func, e.of.name, dfvIn)
      for name in pointeeNames:
        varNames.add(f"{name}.{e.name}")

    elif isinstance(e, expr.CallE): #INTRA
      for arg in e.args:  # iterate over the call arguments
        argType = arg.type
        if isinstance(argType, ArrayT):
          argType = argType.getElementTypeFinal()
        if isinstance(argType, Ptr): # only ptr arguments matter
          if isinstance(arg, expr.AddrOfE):
            assert isinstance(arg.arg, expr.VarE), f"{arg}"
            varNames.add(arg.arg.name)
            arg = arg.arg
            if not isinstance(arg, Ptr): continue
          assert isinstance(arg, expr.VarE), f"{arg}"
          names: Set[VarNameT] = set()
          PointsToA._getNamesOfArgPointeesPtr(func, arg.name, names, dfvIn)
          varNames.update(names)
      varNames.update(ir.getNamesGlobal(func))  # non-pointer vars included

    return varNames


  @staticmethod
  def _getNamesOfArgPointeesPtr(func,
      varName: VarNameT,
      names: Set[VarNameT],
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
      PointsToA._getNamesOfArgPointeesPtr(func, ptrName, names, dfvIn) #recurse
    names.update(ptrPointeeNames)


  @staticmethod
  def getNamesOfPointees(
      func: constructs.Func,
      varName: VarNameT,
      dfvIn: OverallL = None
  ) -> Set[VarNameT]:
    """Returns the pointee names of the given pointer name,
    if dfvIn is None it returns a conservative value."""

    # Step 1: what type is the given name?
    varType = ir.inferTypeOfVal(func, varName)
    if isinstance(varType, ArrayT):
      varType = varType.getElementTypeFinal()

    if not isinstance(varType, Ptr):
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
      return varDfv.val - NULL_OBJ_SINGLETON_SET


  @staticmethod
  def test_dfv_assertion(
      computed: DataLT,
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
      else: # must be a tuple
        givenVal = eval(strVal)
        return computed.val == givenVal

    if strVal.startswith("has:"):
      strVal = strVal[4:]
      mapOfVarNames = eval(strVal)
      for vName, val in mapOfVarNames.items():
        cputed = computed.getVal(vName)
        correct = PointsToA.test_dfv_assertion(cputed, f"is: {val}")
        if not correct: return False
      return True

    raise ValueError()
  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : Points-to Analysis.
################################################
