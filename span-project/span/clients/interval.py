#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Interval (Range) Analysis."""

import logging
LOG = logging.getLogger(__name__)
LDB, LER = LOG.debug, LOG.error

from typing import Tuple, Dict, Set, List, Optional as Opt, cast, Callable, Type

from span.ir.tunit import TranslationUnit
import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.ir as ir
from span.ir.conv import Forward

from span.api.lattice import \
  (ChangedT,
   Changed,
   basicEqualsTest,
   basicLessThanTest,
   basicMeetOp,
   getBasicString,
   DataLT, )
import span.api.dfv as dfv
from span.api.dfv import DfvPairL
import span.api.analysis as analysis
from span.api.analysis import SimFailed, SimPending, BoolValue, \
  NumValue, ValueTypeT, AnalysisAT

from span.util.util import LS
import span.util.util as util


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
    if val and val[0] == float("-inf") \
        and val[1] == float("+inf"):
      self.top, self.bot, self.val = False, True, None


  def meet(self,
      other: 'ComponentL'
  ) -> Tuple['ComponentL', ChangedT]:
    tup = basicMeetOp(self, other)
    if tup:
      return tup
    else:
      assert self.val and other.val, f"{self}, {other}"
      lowerLim = min(self.val[0], other.val[0])
      upperLim = max(self.val[1], other.val[1])
      return ComponentL(self.func, val=(lowerLim, upperLim)), Changed


  def widen(self,
      other: Opt['ComponentL'] = None,
      ipa: bool = False,  # special case #IPA
  ) -> Tuple['ComponentL', ChangedT]:
    """For docs see base class method."""
    if other is None: return self, not Changed

    if other.top:        # no widening needed
      return self, not Changed
    elif self.top:        # no widening needed
      return (self, not Changed) if other.top else (other, Changed)
    elif self.bot:        # no widening needed
      return self, not Changed
    elif self != other:  # WIDEN-WIDEN # return self it its weaker
      if self < other:
        return self, not Changed
      elif self.isBooleanRange() and other.isBooleanRange():
        return self.meet(other)
      else:
        wide = ComponentL(self.func, bot=True)
        if LS and util.VV3: LDB(" Widened: %s (w.r.t. %s) to %s ",
                                self, other, wide)
        return wide, Changed
    else:                 # no widening needed
      return self, not Changed


  def __lt__(self,
      other: 'ComponentL'
  ) -> bool:
    """A non-strict weaker-than test. See doc of super class."""
    lt = basicLessThanTest(self, other)
    return lt if lt is not None else \
      (self.val[0] <= other.val[0] and self.val[1] >= other.val[1])


  def __eq__(self, other) -> bool:
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = basicEqualsTest(self, other)
    return equal if equal is not None else self.val == other.val


  def __hash__(self):
    return hash((self.val, self.top))


  def checkInvariants(self, level: int = 0):
    if level >= 0:
      if self.top: assert not self.bot, f"{self.func.name}: {self}"
      if self.bot: assert not self.top, f"{self.func.name}: {self}"
      if not (self.top or self.bot):
        assert self.val is not None, f"{self.func.name}: {self}"


  def getCopy(self) -> 'ComponentL':
    if self.top: return ComponentL(self.func, top=True)
    if self.bot: return ComponentL(self.func, bot=True)
    return ComponentL(self.func, val=self.val)


  def isExactZero(self) -> bool:
    return self.val and self.val[0] == 0 == self.val[1]


  def getNegatedRange(self) -> 'ComponentL':
    if self.top: return self
    if self.bot: return self
    assert self.val, f"{self}"
    return ComponentL(self.func, val=(-self.val[1], -self.val[0]))


  def bitNotRange(self) -> 'ComponentL':
    """Optimistically assumes bit-not is done on an integer."""
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

    assert self.val and other.val, f"{self}, {other}"
    v1 = self.val[0] * other.val[0]
    v2 = self.val[1] * other.val[1]

    return ComponentL(self.func, val=(min(v1,v2), max(v1,v2)))


  def modRange(self,
      other: 'ComponentL',
  ) -> 'ComponentL':
    """Call this function for an expression: `other % self`.
    Mod operation in C is only possible between two integers (unlike Python).
    """
    if self.top: return self
    if self.bot: return self # over-approx (can add precision w.r.t. other)
    if other.top: return other

    assert self.val, f"self: {self}, other: {other}"
    selfUpper = abs(self.val[1])

    neg = -1 if other.hasNegatives() else 0
    pos = 1 if other.hasPositives() else 0

    lower, upper = neg * (selfUpper - 1), pos * (selfUpper - 1)

    if other.isConstant():
      pass # over-approx (can add precision here)

    return ComponentL(self.func, val=(lower, upper))


  def isBooleanRange(self) -> bool:
    if self.val:
      lo, up = self.val
      return lo in (0,1) and up in (0,1)
    return False


  def isPositive(self) -> bool:
    """Returns True if the complete range is on the positive side."""
    return self.val and self.val[0] > 0


  def hasPositives(self) -> bool:
    """Returns True if the range contains positive values (zero is not positive)."""
    return self.bot or (self.val and self.val[1] > 0)


  def isNegative(self) -> bool:
    """Returns True if the complete range is on the negative side."""
    return self.val and self.val[1] < 0


  def hasNegatives(self) -> bool:
    """Returns True if the range contains negative values."""
    return self.bot or (self.val and self.val[0] < 0)


  def isPositiveOrZero(self) -> bool:
    return self.val and self.val[0] >= 0


  def isNegativeOrZero(self) -> bool:
    return self.val and self.val[1] <= 0


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


  def inIndexRange(self, value: float) -> bool:
    """"Returns true if the range is within [0, value]."""
    if self.top: return False
    if self.bot: return False
    assert self.val, f"{self}"
    return 0 <= self.val[0] and self.val[1] <= value


  def isConstant(self):
    return self.val and self.val[0] == self.val[1]


  def getValuesSet(self,
      intType: bool = False
  ) -> Opt[Set[int]]:
    """Returns a set of integer values if they can cover the range."""
    if intType and self.val:
      low, high = self.val
      if high - low < 10: # FIXME: defined a named constant
        return set(i for i in range(int(low), int(high)+1))  # FIXME: remove int()
    return None


  def cutLimit(self,
      other: 'ComponentL',
      lessThanOther: bool = True,
      equalToOther: bool = True,
      intType: bool = True,
  ) -> 'ComponentL':
    """Limits the upper/lower value w.r.t. the relation to 'other'.
    Returns Top value if the cut is non-meaningful.
    """
    topVal = ComponentL(self.func, top=True) # can't compute
    if self.top: return self
    if other.bot: return self
    if other.top: return topVal

    def newVal(val):
      nonlocal self
      return ComponentL(self.func, val=val)

    assert other.val, f"{other}"
    otherLower, otherUpper = other.val
    if self.bot:
      if lessThanOther:
        upper = otherUpper if equalToOther else \
          (otherUpper - 1 if intType else otherUpper)
        return newVal((float("-inf"), upper))
      else: # greaterThanOther
        lower = otherLower if equalToOther else \
          (otherLower + 1 if intType else otherLower)
        return newVal((lower, float("+inf")))

    assert self.val, f"{self}"
    selfLower, selfUpper = self.val

    if lessThanOther:
      if otherUpper < selfLower: return topVal
      if selfUpper < otherLower: return self
      if selfUpper == otherLower:
        upper = otherLower if equalToOther else \
          (otherLower - 1 if intType else otherLower)
        return newVal((selfLower, upper)) if selfLower <= upper else topVal
      if selfUpper >= otherUpper: # certainly selfUpper > otherLower
        upper = otherUpper if equalToOther else \
          (otherUpper - 1 if intType else otherUpper)
        return newVal((selfLower, upper)) if selfLower <= upper else topVal
      if selfUpper < otherUpper:
        return self
    else: # greaterThanOther
      if otherLower > selfUpper: return topVal
      if selfLower > otherUpper: return self
      if selfLower == otherUpper:
        lower = otherUpper if equalToOther else \
          (otherUpper + 1 if intType else otherUpper)
        return newVal((lower, selfUpper)) if lower <= selfUpper else topVal
      if selfLower <= otherLower: # obviously otherUpper > selfLower
        lower = otherLower if equalToOther else \
          (otherLower + 1 if intType else otherLower)
        return newVal((lower, selfUpper)) if lower <= selfUpper else topVal
      if selfLower > otherLower:
        return self

    assert False, f"{self}, {other}"


  def getIntersectRange(self, other: 'ComponentL') -> 'ComponentL':
    """self and other must intersect"""
    #assert self.overlaps(other), f"NoOverlap: {self} and {other}"
    if not self.overlaps(other): # return Top if no overlap (i.e. no intersection)
      return ComponentL(self.func, top=True)

    if self < other: return self
    if other < self:  return other

    assert self.val and other.val , f"{self}, {other}"
    lower = max(self.val[0], other.val[0])
    upper = min(self.val[1], other.val[1])

    return ComponentL(self.func, val=(lower, upper))


  def getDisjointRange(self,
      other: 'ComponentL',
      intType: bool = False,  # TODO: make use of
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


  def isStrictlyLowerThan(self,
      other: 'ComponentL',
      intType: bool = False,  # TODO: make use of
  ) -> bool:
    """Self's complete range is strictly lower than other"""
    if self < other or other < self:
      return False

    assert self.val and other.val , f"{self}, {other}"
    return self.val[1] < other.val[0]


  def __str__(self):
    valStr = getBasicString(self)
    idStr = f"(id:{id(self)})" if util.DD5 else ""

    def getSafeStr(val: types.NumericT):
      if isinstance(val, float):
        if val in (float("+inf"), float("-inf")):
          return f"'{val}'" # put value in quotes

      return f"{val}" # default: return the value as it is.

    if not valStr:
      if self.isConstant():
        valStr = getSafeStr(self.val[0])
      else:
        valStr = f"({getSafeStr(self.val[0])}, {getSafeStr(self.val[1])})"

    return f"{valStr}{idStr}"


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
    super().__init__(func, val, top, bot, ComponentL, "IntervalA")


  def countConstants(self) -> int:
    """Gives the count of number of constant in the data flow value."""
    if self.top or self.bot:
      return 0

    assert self.val, f"{self}"
    return sum(1 for v in self.val.values() if v.isConstant())  # type: ignore


  def widen(self,
      other: Opt['OverallL'] = None,
      ipa: bool = False,  # special case #IPA
  ) -> Tuple['OverallL', ChangedT]:
    if other is None: return self, not Changed

    if other.top:         # no widening needed
      return self, not Changed
    elif self.top:        # no widening needed
      return (self, not Changed) if other.top else (other, Changed)
    elif self.bot:        # no widening needed
      return self, not Changed
    elif self != other:   # WIDENing needed!
      if other.bot:
        return other, Changed
      else:
        pass # continues to the widening logic below...
    else:                 # no widening needed
      return self, not Changed

    # If here, then widen individual entities (variables).
    widened_val: Dict[types.VarNameT, ComponentL] = {}
    vNames = set(self.val.keys())
    vNames.update(other.val.keys())
    selfValGet, otherValGet = self.val.get, other.val.get
    changed = False
    for vName in vNames:
      defaultVal = self.getDefaultVal(vName)
      dfv1: ComponentL = selfValGet(vName, defaultVal)
      dfv2: ComponentL = otherValGet(vName, defaultVal)
      dfv3, _changed = dfv1.widen(dfv2)  # attempt widening here
      changed = changed or _changed
      if not dfv3 == defaultVal:
        widened_val[vName] = dfv3

    if not changed:
      return self, not Changed

    value = OverallL(self.func, val=widened_val)
    return value, Changed


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
  L: Type[dfv.OverallL] = OverallL
  # direction of the analysis
  D: types.DirectionT = Forward


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func, ComponentL, OverallL)
    dfv.initTopBotOverall(func, IntervalA.__name__, IntervalA.L)


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
  # BOUND START: simplifiers
  ################################################

  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[types.NumericT]] = None,
  ) -> Opt[Set[types.NumericT]]:
    # STEP 1: tell the system if the expression can be evaluated
    eType = e.type
    if not eType.isNumericOrVoid() or eType.isArrayOrVoid():
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
    exprVal = cast(ComponentL, self.getExprDfv(e, dfvIn))
    if exprVal.top: return SimPending  # can be evaluated, needs more info
    if exprVal.bot: return SimFailed  # cannot be evaluated
    simVals = exprVal.getValuesSet(e.type.isInteger()) # type: ignore
    if simVals: return simVals
    return SimFailed


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[types.NumericT]] = None,
  ) -> Opt[Set[types.NumericT]]:
    """Specifically for expression: '_ <relop> _'."""
    # STEP 1: tell the system if the expression can be evaluated
    arg1, arg2 = e.arg1, e.arg2
    if (not e.type.isNumeric()
        # or not e.opr.isRelationalOp()
        or not arg1.type.isNumeric()
        or not arg2.type.isNumeric()):
      return SimFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return SimPending # tell that sim my be possible if nodeDfv is given

    # STEP 3: If here, either eval or filter the values
    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    if values is not None:
      assert len(values), f"{e}, {values}"
      filtered = self.filterValues(e, values, dfvIn, NumValue) # filter the values
      return filtered # if filtered else SimPending

    # STEP 4: If here, eval the expression
    exprVal = cast(ComponentL, self.getExprDfvBinaryE(e, dfvIn))
    if util.LL5: LDB(f"EXPR_VAL: {e} ({e.info}): {exprVal},"
                     f"arg1: {self.getExprDfv(e.arg1, dfvIn)}, "
                     f"arg2: {self.getExprDfv(e.arg2, dfvIn)}")
    if exprVal.top: return SimPending  # can be evaluated, needs more info
    if exprVal.bot: return SimFailed  # cannot be evaluated
    simVals = exprVal.getValuesSet(e.type.isInteger()) # type: ignore
    if simVals: return simVals
    return SimFailed


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[Set[bool]] = None,
  ) -> Opt[Set[bool]]:
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
      return self.filterValues(e, values, dfvIn, BoolValue) # filter the values

    # STEP 4: If here, eval the expression
    val = cast(ComponentL, dfvIn.getVal(e.name))
    if val.top: return SimPending  # can be evaluated but needs more info
    if val.bot: return SimFailed  # cannot be evaluated
    assert val.val is not None, f"{e}, {val}"
    if val.isExactZero():
      return {False}  # take false edge
    elif not val.inRange(0):
      return {True}   # take true edge
    else:
      return SimFailed  # both edges are possible


  def filterTest(self,
      exprVal: ComponentL,
      valueType: ValueTypeT = NumValue,
  ) -> Callable[[types.T], bool]:
    if valueType == NumValue:
      def valueTestNumeric(numVal: types.NumericT) -> bool:
        if exprVal.top: return False
        if exprVal.bot: return True
        return exprVal.inRange(numVal)
      return valueTestNumeric  # return the test function

    elif valueType == BoolValue:
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


  def genNodeDfvL(self,
      outDfvValues: Dict[types.VarNameT, dfv.ComponentL],
      nodeDfv: DfvPairL,
      callNode: bool = False, #IPA maybe True if a callE present.
  ) -> DfvPairL:
    """A convenience function to create and return the NodeDfvL."""
    dfvIn = newOut = cast(OverallL, nodeDfv.dfvIn)
    if callNode: #IPA modify the current dfvOut
      newOut = nodeDfv.dfvOut
      if outDfvValues:
        newOutSetVal = newOut.setVal
        for name, value in outDfvValues.items():
            newOutSetVal(name, value)  # modify dfvOut in-place
    else: #INTRA transfer current dfvIn to replace current dfvOut
      dfvOutGetVal = nodeDfv.dfvOut.getVal  # the node's current dfvOut
      if outDfvValues:
        newOut = cast(dfv.OverallL, dfvIn.getCopy())
        newOutSetVal = newOut.setVal
        for name, value in outDfvValues.items():
          oldOutValue: ComponentL = dfvOutGetVal(name)
          newValue, _ = oldOutValue.widen(value)
          newOutSetVal(name, newValue)
    return DfvPairL(dfvIn, newOut)


  def getExprDfvLitE(self,
      e: expr.LitE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation for Constant Propagation."""
    assert isinstance(e.val, (int, float)), f"{e}"
    return ComponentL(self.func, val=(e.val, e.val))


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
        eTo, val = e.to, value.val
        assert self.L.isAcceptedType(eTo) and value.val, f"{e}, {value}"
        newValue = ComponentL(self.func,
                              val=(eTo.castValue(val[0]), eTo.castValue(val[1])))
        return newValue
    else:
      return self.componentBot


  def getExprDfvUnaryE(self,
      e: expr.UnaryE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    assert isinstance(e.arg, expr.VarE), f"{e}"
    value = cast(ComponentL, dfvInGetVal(e.arg.name))
    if not e.arg.type.isNumericOrVoid():
      return self.componentBot
    elif value.top or value.bot:
      return value
    elif value.val is not None:
      rhsOpCode = e.opr.opCode
      if rhsOpCode == op.UO_MINUS_OC:
        value = value.getNegatedRange()  # not NoneType... pylint: disable=E
      elif rhsOpCode == op.UO_BIT_NOT_OC:
        if util.LL1 and (isinstance(value.val[0], float)
                         or isinstance(value.val[1], float)):
          LER(f"{value}, {type(value.val)}")
        value = value.bitNotRange()  # not NoneType... pylint: disable=E
      elif rhsOpCode == op.UO_LNOT_OC:
        value = value.logicalNotRange()
      else:
        raise ValueError(f"{e}")
      return value
    raise TypeError(f"{type(value)}: {value}")


  def getExprDfvBinaryE(self,
      e: expr.BinaryE,
      dfvIn: dfv.OverallL,
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    val1 = cast(ComponentL, self.getExprDfv(e.arg1, dfvIn))
    val2 = cast(ComponentL, self.getExprDfv(e.arg2, dfvIn))
    opr, rhsOpCode  = e.opr, e.opr.opCode

    if val1.isConstant() and val2.isConstant():
      newExpr: expr.LitE = expr.evalExpr(
        expr.BinaryE(expr.LitE(val1.val[0]), opr, expr.LitE(val2.val[0])))
      # try: #delit
      return ComponentL(self.func, val=(newExpr.val, newExpr.val))
      # except Exception as ex: #delit
      #   print(f"SPAN: BinaryE: {e}, {opr}") #delit
      #   raise ex #delit
    if val1.top or val2.top:
      return self.componentTop
    elif rhsOpCode == op.BO_MOD_OC:
      return val2.modRange(val1)
    elif val1.bot or val2.bot:
      return ComponentL(self.func, val=(0,1))\
        if opr.isRelationalOp() else self.componentBot
    else:
      if rhsOpCode == op.BO_ADD_OC:
        return val1.addRange(val2)
      elif rhsOpCode == op.BO_SUB_OC:
        return val1.subtractRange(val2)
      elif rhsOpCode == op.BO_MUL_OC:
        return val1.multiplyRange(val2)
      elif opr.isRelationalOp():
        return self.getExprDfvBinaryRelE(e, dfvIn)
      else:
        return self.componentBot  # conservative


  def getExprDfvBinaryRelE(self,
      e: expr.BinaryE,
      dfvIn: dfv.OverallL,
  ) -> dfv.ComponentL:
    arg1, arg2, opr = e.arg1, e.arg2, e.opr
    assert opr.isRelationalOp(), f"{self.func.name}: {e}, {e.info}"

    arg1Val = cast(ComponentL, self.getExprDfv(arg1, dfvIn))
    arg2Val = cast(ComponentL, self.getExprDfv(arg2, dfvIn))

    if arg1Val.top or arg2Val.top: return self.componentTop

    arg1isInt, arg2isInt = arg1.type.isInteger(), arg2.type.isInteger()
    overlaps = arg1Val.overlaps(arg2Val)
    constArg1 = arg1Val.isConstant()
    constArg2 = arg2Val.isConstant()
    lowerArg1 = arg1Val.isStrictlyLowerThan(arg2Val, arg1isInt)
    lowerArg2 = arg2Val.isStrictlyLowerThan(arg1Val, arg2isInt)
    isEqual = arg1Val == arg2Val

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
      if lowerArg1:
        result = True
      elif lowerArg2 or (isEqual and constArg1):
        result = False
    elif opCode == op.BO_GE_OC:
      if overlaps and constArg1 and constArg2:
        result = True
      elif lowerArg1:
        result = False
      elif lowerArg2:
        result = True
    elif opCode == op.BO_GT_OC:
      if lowerArg1 or (isEqual and constArg1):
        result = False
      elif lowerArg2:
        result = True

    val = (1, 1) if result else ((0, 1) if result is None else (0, 0))
    return ComponentL(self.func, val=val)


  def calcFalseTrueDfv(self,
      arg: expr.SimpleET,
      dfvIn: dfv.OverallL,
  ) -> Tuple[OverallL, OverallL]:  # dfvFalse, dfvTrue
    """Conditionally propagate data flow values."""
    assert isinstance(arg, expr.VarE), f"{arg}"

    argName = arg.name
    zeroDfv = ComponentL(self.func, (0, 0))  # always zero on false branch

    dfvValTrue: Dict[types.VarNameT, ComponentL] = {}
    dfvValFalse: Dict[types.VarNameT, ComponentL] = {}
    dfvValFalse[argName] = zeroDfv

    tmpExpr = ir.getTmpVarExpr(self.func, arg.name)
    true1 = true2 = false1 = false2 = None # 1 and 2 are for arg 1 and 2
    if tmpExpr and isinstance(tmpExpr, expr.BinaryE):
      arg1, arg2 = tmpExpr.arg1, tmpExpr.arg2
      arg1isInt, arg2isInt = arg1.type.isInteger(), arg2.type.isInteger()
      assert isinstance(arg1, expr.VarE), f"{tmpExpr}"
      dfv1, dfv2 = cast(ComponentL, self.getExprDfv(arg1, dfvIn)), \
                   cast(ComponentL, self.getExprDfv(arg2, dfvIn))
      opCode = tmpExpr.opr.opCode
      if opCode == op.BO_EQ_OC:
        true1 = true2 = dfv1.getIntersectRange(dfv2)  # equal dfv
        false1, false2 = dfv1.getDisjointRange(dfv2, arg1isInt)
      elif opCode == op.BO_NE_OC:
        true1, true2 = dfv1.getDisjointRange(dfv2, arg1isInt)
        false1 = false2 = dfv1.getIntersectRange(dfv2)  # equal dfv
      else:
        cutLimit1, cutLimit2 = dfv1.cutLimit, dfv2.cutLimit
        if opCode == op.BO_LT_OC:
          true1 = cutLimit1(dfv2, True, False, arg1isInt)
          true2 = cutLimit2(dfv1, False, False, arg2isInt)
          false1 = cutLimit1(dfv2, False, True, arg1isInt)
          false2 = cutLimit2(dfv1, True, True, arg2isInt)
        elif opCode == op.BO_LE_OC:
          true1 = cutLimit1(dfv2, True, True, arg1isInt)
          true2 = cutLimit2(dfv1, False, True, arg2isInt)
          false1 = cutLimit1(dfv2, False, False, arg1isInt)
          false2 = cutLimit2(dfv1, True, False, arg2isInt)
        elif opCode == op.BO_GT_OC:
          true1 = cutLimit1(dfv2, False, False, arg1isInt)
          true2 = cutLimit2(dfv1, True, False, arg2isInt)
          false1 = cutLimit1(dfv2, True, True, arg1isInt)
          false2 = cutLimit2(dfv1, False, True, arg2isInt)
        elif opCode == op.BO_GE_OC:
          true1 = cutLimit1(dfv2, False, True, arg1isInt)
          true2 = cutLimit2(dfv1, True, True, arg2isInt)
          false1 = cutLimit1(dfv2, True, False, arg1isInt)
          false2 = cutLimit2(dfv1, False, False, arg2isInt)

      arg2IsVarE = isinstance(arg2, expr.VarE)
      if true1 and true2:
        dfvValTrue[arg1.name] = true1
        if arg2IsVarE: dfvValTrue[arg2.name] = true2
      if false1 and false2:
        dfvValFalse[arg1.name] = false1
        if arg2IsVarE: dfvValFalse[arg2.name] = false2

    return dfv.updateDfv(dfvValFalse, dfvIn), dfv.updateDfv(dfvValTrue, dfvIn)


  @staticmethod
  def countSimCondToUncond(
      func: constructs.Func,
      dfvDict: Dict[types.NodeIdT, DfvPairL]
  ) -> int:
    tUnit: TranslationUnit = func.tUnit
    count = 0

    for nid, node in func.cfg.nodeMap.items():
      insn = node.insn

      if nid not in dfvDict: # unreachable nodes might not be present
        if isinstance(insn, instr.CondI):
          count += 1 # count unreachable cond nodes as well
        continue

      if isinstance(insn, instr.CondI):
        vName = insn.arg.name # must be a variable
        dfvIn = dfvDict[nid].dfvIn
        vDfv: ComponentL = dfvIn.getVal(vName)
        if vDfv.isConstant():
          count += 1

    return count


  @staticmethod
  def test_dfv_assertion(
      computed: DataLT,
      strVal: str,  # a short string representation of the assertion (see tests)
  ) -> bool:
    """Returns true if assertion is correct.
    strVal Examples,
    "is: bot", "is: top", "has: {'v:main:b': 'top'}"
    """

    if strVal.startswith("any"):
      return True

    if strVal.startswith("is:"):
      strVal = strVal[3:]
      if strVal.strip() in {"bot", "Bot", "BOT"}:
        return computed.bot
      elif strVal.strip() in {"top", "Top", "TOP"}:
        return computed.top
      else: # must be of type computed.val
        mapOfVarNames = eval(strVal)
        return computed.val == mapOfVarNames

    if strVal.startswith("has:"):
      strVal = strVal[4:]
      mapOfVarNames = eval(strVal)
      for vName, val in mapOfVarNames.items():
        cputed = computed.getVal(vName)
        correct = IntervalA.test_dfv_assertion(cputed, f"is: {val}")
        if not correct: return False
      return True

    raise ValueError()
  ################################################
  # BOUND END  : helper_functions
  ################################################

################################################
# BOUND END  : interval_analysis
################################################


