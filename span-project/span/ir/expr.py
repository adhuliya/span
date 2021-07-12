#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""
All possible expressions used in an instruction.
"""

import logging
LOG = logging.getLogger(__name__)
LER = LOG.error

from typing import List, Set, Any, Optional as Opt

import span.util.util as util
import span.util.consts as consts
import span.ir.types as types
import span.ir.conv as irConv
import span.ir.op as op

ExprCodeT = types.ExprCodeT

################################################
# BOUND START: expr_codes
################################################

# the order and ascending sequence may be important
VAR_EXPR_EC: ExprCodeT = 11
LIT_EXPR_EC: ExprCodeT = 12
FUNC_EXPR_EC: ExprCodeT = 13

UNARY_EXPR_EC: ExprCodeT = 20
CAST_EXPR_EC: ExprCodeT = 21
# BASIC_EXPR_EC:      ExprCodeT = 22
ADDROF_EXPR_EC: ExprCodeT = 23
DEREF_EXPR_EC: ExprCodeT = 24
SIZEOF_EXPR_EC: ExprCodeT = 25
BINARY_EXPR_EC: ExprCodeT = 30
ARR_EXPR_EC: ExprCodeT = 31

CALL_EXPR_EC: ExprCodeT = 40
# PTRCALL_EXPR_EC:    ExprCodeT = 41
MEMBER_EXPR_EC: ExprCodeT = 45
PHI_EXPR_EC: ExprCodeT = 50
SELECT_EXPR_EC: ExprCodeT = 60
ALLOC_EXPR_EC: ExprCodeT = 70


################################################
# BOUND END  : expr_codes
################################################

class ExprET:
  """Base class for all expressions."""

  __slots__: List[str] = ['exprCode', 'info', 'type']


  def __init__(self,
      exprCode: ExprCodeT,
      info: Opt[types.Info] = None,
  ) -> None:
    if self.__class__ is ExprET: raise TypeError()
    self.exprCode = exprCode
    self.info = info
    self.type: types.Type = types.Void


  def getRValueNames(self) -> Set[types.VarNameT]: return set()


  def getDereferencedVarE(self) -> Opt['VarE']:
    return None


  def hasDereference(self) -> bool:
    return False


  def getFormalStr(self) -> types.FormalStrT:
    raise NotImplementedError()


  def checkInvariants(self):
    """Runs some invariant checks on self. """
    if util.CC1:
      assert self.exprCode is not None
      assert self.type is not None


  def __eq__(self, other) -> bool:
    if not isinstance(other, ExprET):
      return NotImplemented
    if self is other:
      return True
    equal = True
    if not isinstance(other, ExprET):
      equal = False
    elif not self.exprCode == other.exprCode:
      equal = False
    elif not self.type == other.type:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __hash__(self) -> int:
    return hash((self.exprCode, self.type))


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    """Used in place of __eq__, for testing purposes."""
    equal = True
    if not isinstance(other, self.__class__):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.exprCode == other.exprCode:
      if util.LL1: LER("ExprCodesDiffer: %s, %s",
                       self.exprCode, other.exprCode)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def hasVarExpr(self) -> bool: return False

  def hasNumVarExpr(self) -> bool: return False

  def hasDerefExpr(self) -> bool: return False

  def hasArrayDerefExpr(self) -> bool: return False

  def hasMemDerefExpr(self) -> bool: return False

  def hasNumBinaryExpr(self) -> bool: return False

  def hasNumUnaryExpr(self) -> bool: return False

  def hasPtrCall(self) -> bool: return False


class SimpleET(ExprET):
  """A simple (non-divisible) expressions.
  Like, var 'x',
        'x.y' without dereference,
        a literal value '12.3'."""

  __slots__: List[str] = []


  def __init__(self,
      exprCode: ExprCodeT,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(exprCode, info)


class LitE(SimpleET):
  """A single numeric literal. Bools are also numeric."""

  __slots__: List[str] = ["val", "name"]


  def __init__(self,
      val: types.LitT,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(LIT_EXPR_EC, info)
    self.val: types.LitT = val
    # String literals are given special (constant) variable names.
    # its type is ConstantArray of characters
    # name of the string literal is set in tunit.processStringLiteral()
    self.name: types.VarNameT = ""


  def getFormalStr(self) -> types.FormalStrT:
    return consts.LIT_E_STR


  def checkInvariants(self):
    super().checkInvariants()
    if util.CC1:
      assert isinstance(self.val, (int, float, str)), f"{self}"
      if self.name:
        assert isinstance(self.val, str), f"{self}"


  def isNumeric(self) -> bool:
    """Returns True if self.val is numeric.
    Characters are also numeric."""
    if isinstance(self.val, (int, float)):
      return True
    elif isinstance(self.val, str):
      return False
    assert False, f"{self.val}: {type(self.val)}"


  def isString(self) -> bool:
    if isinstance(self.val, str):
      assert self.name, f"{self}, {self.name}, {self.info}"
      return True
    else:
      assert not self.name, f"{self}, {self.name}"
      return False


  def __eq__(self, other) -> bool:
    if not isinstance(other, LitE):
      return NotImplemented
    if self is other:
      return True
    equal = True
    if not self.val == other.val:
      equal = False
    elif not self.name == other.name:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, LitE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.val == other.val:
      if util.LL1: LER("ValuesDiffer: %s, %s", self.val, other.val)
      equal = False
    if not self.name == other.name:
      if util.LL1: LER("NamesDiffer: %s, %s", self.name, other.name)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash(self.val)


  def __str__(self):
    if isinstance(self.val, str):
      newVal = repr(repr(self.val))
      newVal = newVal[1:-1]
      return f"{newVal}"
    return f"{self.val}"


  def __repr__(self):
    return f"expr.LitE({repr(self.val)}, {repr(self.info)})"


class LocationET(ExprET):
  """Expressions (could be a compound expressions)
  that represent a location (which can appear on the lhs).
  This is an empty class to make use of is-a relation,
  and to also satisfy cython in the future.
  """
  pass


class VarE(SimpleET, LocationET):
  """Holds a location name, that has no pointer dereference.
  E.g. x, x.y.z, ...
  """

  __slots__: List[str] = ["name"]


  def __init__(self,
      name: types.VarNameT,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(VAR_EXPR_EC, info)
    self.name: types.VarNameT = name
    if self.hasFunctionName():
      self.exprCode = FUNC_EXPR_EC


  def getRValueNames(self) -> Set[types.VarNameT]:
    return {self.name}


  def getFullName(self) -> types.VarNameT:
    return self.name


  def getFormalStr(self) -> types.FormalStrT:
    return consts.VAR_E_STR


  def checkInvariants(self):
    super().checkInvariants()
    if util.CC1:
      assert self.name, f"{self}"
      if self.hasFunctionName():
        assert self.exprCode == FUNC_EXPR_EC, f"{self}"


  def hasFunctionName(self):
    return irConv.isFuncName(self.name)


  def isFunctionVar(self):
    return isinstance(self.type, types.FuncSig)


  def hasVarExpr(self) -> bool: return True


  def hasNumVarExpr(self) -> bool: return self.type.isNumeric()


  def __eq__(self, other) -> bool:
    if not isinstance(other, VarE):
      return NotImplemented
    if self is other:
      return True
    equal = True
    if not isinstance(other, VarE):
      equal = False
    if not self.name == other.name:
      equal = False
    if not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, VarE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.name == other.name:
      if util.LL1: LER("NamesDiffer: %s, %s", self.name, other.name)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    return hash(self.name)


  def __str__(self):
    name = self.name if util.DD3 else self.name.split(":")[-1]
    return f"{name}"


  def __repr__(self):
    return f"expr.VarE({repr(self.name)}, {repr(self.info)})"


class PpmsVarE(VarE):
  """Holds a single PPMS variable name.
  Pseudo variables are used to name line
  and type based heap locations etc.

  Note: to avoid circular dependency avoid any operation on
  SPAN IR instructions in this module.
  """

  __slots__: List[str] = ["insn", "sizeExpr"]


  def __init__(self,
      name: types.VarNameT,
      info: Opt[types.Info] = None,
      insn: Opt[Any] = None, # a single `InstrIT` object (with memory allocation)
  ) -> None:
    super().__init__(name, info)
    # First insn is always the memory alloc instruction
    # The second is optionally a cast assignment.
    self.insn = insn


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, PpmsVarE):
      return NotImplemented
    equal = True
    if not self.name == other.name:
      equal = False
    if not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, PpmsVarE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.name == other.name:
      if util.LL1: LER("NamesDiffer: %s, %s", self.name, other.name)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    return hash(self.name)


  def __str__(self):
    name = self.name.split(":")[-1]
    return f"{name}"


  def __repr__(self):
    return (f"expr.PpmsVarE({repr(self.name)}, {repr(self.info)},"
           f"  insn= {repr(self.insn)})")


class UnaryET(ExprET):
  """A generic unary expression base class."""


  def __init__(self,
      exprCode: ExprCodeT,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(exprCode, info)


class DerefET(LocationET):
  """Expressions involving dereference.
  E.g. *x, x->y, a[y], ..."""


  def __init__(self,
      exprCode: ExprCodeT,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(exprCode, info)


class DerefE(UnaryET, DerefET):
  """A (unary) dereference expression."""

  __slots__: List[str] = ["arg"]


  def __init__(self,
      arg: VarE,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(DEREF_EXPR_EC, info)
    assert isinstance(arg, VarE), f"{arg}, {info}"
    self.arg = arg


  def hasDerefExpr(self) -> bool: return True


  def getFormalStr(self) -> types.FormalStrT:
    return consts.DEREF_E_STR


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, DerefE):
      return NotImplemented
    equal = True
    if not self.arg == other.arg:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, DerefE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.arg.isEqual(other.arg):
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def hasDereference(self):
    return True


  def getDereferencedVarE(self) -> Opt['VarE']:
    return self.arg


  def __hash__(self) -> int:
    return hash((self.arg, self.exprCode))


  def __str__(self):
    return f"*{self.arg}"


  def __repr__(self):
    return f"expr.DerefE({repr(self.arg)}, {repr(self.info)})"


class ArrayE(DerefET):
  """An array expression."""

  __slots__: List[str] = ["index", "of", "_hasPtrDeref"]


  def __init__(self,
      index: SimpleET,
      of: 'LocationET',
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(ARR_EXPR_EC, info)
    self.index = index
    self.of = of
    self._hasPtrDeref: Opt[bool] = None


  def hasArrayDerefExpr(self) -> bool:
    return self.hasDereference()


  def getFormalStr(self) -> types.FormalStrT:
    return consts.ARRAY_E_STR


  def getArrayName(self) -> types.VarNameT:
    if isinstance(self.of, VarE):
      return self.of.name
    raise ValueError(f"{self}")


  def getIndexName(self) -> Opt[types.VarNameT]:
    if isinstance(self.index, VarE):
      return self.index.name
    return None


  def getFullName(self) -> types.VarNameT:
    """Checks and returns the name of the array."""
    return self.getArrayName()


  def hasDereference(self) -> bool:
    """Is the array expression used on a pointer variable?"""
    if self._hasPtrDeref is None:
      # Not considering Void as Pointer here
      self._hasPtrDeref = self.of.type.isPointer()
    return self._hasPtrDeref


  def getDereferencedVarE(self) -> Opt['VarE']:
    if self.hasDereference():
      assert isinstance(self.of, VarE), f"{self}, {self.info}"
      return self.of
    return None


  def checkInvariants(self):
    if util.CC1:
      assert self.isCanonical(), f"{self}, {self.info}"


  def isCanonical(self) -> bool:
    """a[], ptr[] are canonical forms.
    a[][], a.y[] are non canonical forms.
    C program is always converted to a canonical SpanIr."""
    if isinstance(self.of, VarE):
      return True
    return False


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, ArrayE):
      return NotImplemented
    equal = True
    if not self.index == other.index:
      equal = False
    elif not self.of == other.of:
      equal = False
    elif not self.type == other.type:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, ArrayE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.index == other.index:
      if util.LL1: LER("IndicesDiffer: %s, %s", self.index, other.index)
      equal = False
    if not self.of.isEqual(other.of):
      if util.LL1: LER("OfsDiffer: %s, %s", self.of, other.of)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash((self.of, self.index))


  def __str__(self):
    return f"{self.of}[{self.index}]"


  def __repr__(self):
    return f"expr.ArrayE({repr(self.index)}, {repr(self.of)}, {repr(self.info)})"


class MemberE(DerefET):
  """A member access expressions with deref: e.g. x->f
  If it denotes expressions of form x.f that don't
  have dereference (i.e. x is not a pointer to a record),
  then it is replaced by VarE expressions
  before the analysis begins..."""

  __slots__: List[str] = ["index", "of"]


  def __init__(self,
      name: types.MemberNameT,
      of: VarE,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(MEMBER_EXPR_EC, info)
    self.name = name
    self.of = of


  def getFormalStr(self) -> types.FormalStrT:
    return consts.MEMBER_E_STR


  def hasMemDerefExpr(self) -> bool:
    assert isinstance(self.of.type, types.Ptr), f"{self}, {self.of.type}"
    return True


  def checkInvariants(self):
    super().checkInvariants()
    if util.CC1:
      assert self.hasDereference(), f"{self}"
      assert isinstance(self.of, VarE), f"{self}"
      assert self.of and self.name, f"{self}"
      assert not irConv.isMemberName(self.name), f"{self}"
      assert not irConv.isMemberName(self.of.name), f"{self}"


  def getFullName(self) -> types.VarNameT:
    """Returns a name that can be used by analyses."""
    if not self.hasDereference():
      return f"{self.of.name}.{self.name}"
    raise ValueError(f"Member deref expression has no name.")


  def hasDereference(self) -> bool:
    """Does this member expressions as "->" in it?"""
    return isinstance(self.of.type, types.Ptr)


  def getDereferencedVarE(self) -> Opt['VarE']:
    if self.hasDereference():
      return self.of
    return None


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, MemberE):
      return NotImplemented
    equal = True
    if not self.name == other.name:
      equal = False
    elif not self.of == other.of:
      equal = False
    elif not self.type == other.type:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, MemberE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.name == other.name:
      if util.LL1: LER("NamesDiffer: %s, %s", self.name, other.name)
      equal = False
    if not self.of.isEqual(other.of):
      if util.LL1: LER("OfsDiffer: %s, %s", self.of, other.of)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash((self.name, self.of))


  def __str__(self):
    sep = "->" if self.hasDereference() else "."
    return f"{self.of}{sep}{self.name}"


  def __repr__(self):
    return f"expr.MemberE({repr(self.name)}, {repr(self.of)}, {repr(self.info)})"


class BinaryE(ExprET):
  """A binary expression."""

  __slots__: List[str] = ["arg1", "opr", "arg2"]


  def __init__(self,
      arg1: SimpleET,
      opr: op.BinaryOp,
      arg2: SimpleET,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(BINARY_EXPR_EC, info)
    self.arg1 = arg1
    self.opr = opr
    self.arg2 = arg2


  def getRValueNames(self) -> Set[types.VarNameT]:
    return self.arg1.getRValueNames() | self.arg2.getRValueNames()


  def getFormalStr(self) -> types.FormalStrT:
    return consts.BINARYARITH_E_STR


  def hasNumBinaryExpr(self) -> bool:
    return self.type.isNumeric()


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, BinaryE):
      return NotImplemented
    equal = True
    if not self.arg1 == other.arg1:
      equal = False
    elif not self.opr == other.opr:
      equal = False
    elif not self.arg2 == other.arg2:
      equal = False
    elif not self.type == other.type:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, BinaryE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.arg1.isEqual(other.arg1):
      equal = False
    if not self.opr.isEqual(other.opr):
      equal = False
    if not self.arg2.isEqual(other.arg2):
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def isRelational(self):
    return self.opr.isRelationalOp()


  def __hash__(self) -> int:
    return hash((self.arg1, self.arg2, self.opr))


  def __str__(self):
    return f"{self.arg1} {self.opr} {self.arg2}"


  def __repr__(self):
    return f"expr.BinaryE({repr(self.arg1)}, {repr(self.opr)}, " \
           f"{repr(self.arg2)}, {repr(self.info)})"


class UnaryE(UnaryET):
  """A unary arithmetic expression."""

  __slots__: List[str] = ["opr", "arg"]


  def __init__(self,
      opr: op.UnaryOp,
      arg: SimpleET,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(UNARY_EXPR_EC, info)
    self.opr = opr
    self.arg = arg


  def getRValueNames(self) -> Set[types.VarNameT]:
    return self.arg.getRValueNames()


  def getFormalStr(self) -> types.FormalStrT:
    return consts.UNARYARITH_E_STR


  def hasNumUnaryExpr(self) -> bool:
    return self.type.isNumeric()


  def checkInvariants(self):
    super().checkInvariants()
    if util.CC1:
      assert not isinstance(self.arg, LitE), f"{self}"


  def computeExpr(self) -> LitE:
    """Compute expr if argument is a literal.
    The argument should be literal.
    """
    if isinstance(self.arg, LitE):
      val = self.arg.val
      opCode = self.opr.opCode
      newVal = val
      if opCode == op.UO_BIT_NOT:
        newVal = ~int(val)
      elif opCode == op.UO_LNOT_OC:
        newVal = not int(val)
      elif opCode == op.UO_MINUS_OC:
        newVal = -1 * val
      else:
        assert False, f"{self}"
      return LitE(newVal, info=self.info)
    raise TypeError(f"{self}")


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, UnaryE):
      return NotImplemented
    equal = True
    if not self.opr == other.opr:
      equal = False
    elif not self.arg == other.arg:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, UnaryE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.opr.isEqual(other.opr):
      equal = False
    if not self.arg.isEqual(other.arg):
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash((self.arg, self.opr))


  def __str__(self):
    return f"{self.opr}{self.arg}"


  def __repr__(self):
    return f"expr.UnaryE({repr(self.opr)}, " \
           f"{repr(self.arg)}, {repr(self.info)})"


class AddrOfE(UnaryET):
  """A (unary) address-of expression."""

  __slots__: List[str] = ["arg"]


  def __init__(self,
      arg: LocationET,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(ADDROF_EXPR_EC, info)
    self.arg = arg


  def getFormalStr(self) -> types.FormalStrT:
    if isinstance(self.arg, VarE):
      fstr = consts.ADDROFVAR_E_STR
    elif isinstance(self.arg, DerefE):
      fstr = consts.ADDROFDEREF_E_STR
    elif isinstance(self.arg, MemberE):
      fstr = consts.ADDROFMEMBER_E_STR
    elif isinstance(self.arg, ArrayE):
      fstr = consts.ADDROFARRAY_E_STR
    else:
      assert False, f"{self}, {self.arg}"
    return fstr


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, AddrOfE):
      return NotImplemented
    equal = True
    if not self.arg == other.arg:
      equal = False
    elif not self.type == other.type:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, AddrOfE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.arg.isEqual(other.arg):
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def hasDereference(self):
    return self.arg.hasDereference()


  def getDereferencedVarE(self) -> Opt['VarE']:
    return self.arg.getDereferencedVarE()


  def __hash__(self) -> int:
    return hash((self.arg, self.exprCode))


  def __str__(self):
    return f"&{self.arg}"


  def __repr__(self):
    return f"expr.AddrOfE({repr(self.arg)}, {repr(self.info)})"


class CastE(UnaryET):
  """A unary type cast expression."""

  __slots__: List[str] = ["arg", "to"]


  def __init__(self,
      arg: LocationET,
      to: types.Type,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(CAST_EXPR_EC, info)
    self.arg = arg
    self.to = to  # it is same as self.type (don't set it here)


  def getFormalStr(self) -> types.FormalStrT:
    if isinstance(self.arg, VarE):
      fstr = consts.CASTVAR_E_STR
    elif isinstance(self.arg, ArrayE):
      fstr = consts.CASTARR_E_STR
    else:
      assert False, f"{self}"
    return fstr


  def checkInvariants(self):
    super().checkInvariants()
    if util.CC1:
      assert isinstance(self.arg, LocationET), f"{self}"


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, CastE):
      return NotImplemented
    equal = True
    if not self.to == other.to:
      equal = False
    elif not self.arg == other.arg:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, CastE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.arg.isEqual(other.arg):
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash((self.to, self.arg, self.exprCode))


  def __str__(self):
    return f"({self.to}) {self.arg}"


  def __repr__(self):
    return f"expr.CastE({repr(self.arg)}, {repr(self.to)}, {repr(self.info)})"


class AllocE(UnaryET):
  """A stack allocator instruction.

  It allocates size * sizeof(self.type) on the stack,
  and returns the pointer to it.
  """

  __slots__: List[str] = ["arg"]


  def __init__(self,
      arg: SimpleET,
      info: types.Info,
  ) -> None:
    super().__init__(ALLOC_EXPR_EC, info)
    self.arg = arg


  def getFormalStr(self) -> types.FormalStrT:
    return consts.ALLOC_E_STR


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, AllocE):
      return NotImplemented
    equal = True
    if not self.arg == other.arg:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, AllocE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.arg.isEqual(other.arg):
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash((self.arg, self.exprCode))


  def __str__(self):
    return f"alloca {self.arg}"


  def __repr__(self):
    return f"expr.AllocE({repr(self.arg)}, {repr(self.info)})"


class SizeOfE(UnaryET):
  """Calculates size of the argument type in bytes at runtime."""

  __slots__: List[str] = ["arg"]


  def __init__(self,
      arg: VarE,  # var of types.VarArray type only
      info: Opt[types.Info] = None,
  ) -> None:
    super().__init__(SIZEOF_EXPR_EC, info)
    self.arg = arg


  def getFormalStr(self) -> types.FormalStrT:
    return consts.SIZEOF_E_STR


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, SizeOfE):
      return NotImplemented
    equal = True
    if not self.arg == other.arg:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, SizeOfE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.arg.isEqual(other.arg):
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash((self.arg, self.exprCode))


  def __str__(self):
    return f"sizeof {self.arg}"


  def __repr__(self):
    return f"expr.SizeOfE({repr(self.arg)}, {repr(self.info)})"


class CallE(ExprET):
  """A function call expression.
  If callee is a types.VarE then its a function pointer.
  """

  __slots__: List[str] = ["callee", "args"]


  def __init__(self,
      callee: VarE,
      args: Opt[List[SimpleET]] = None,
      info: Opt[types.Info] = None,
  ) -> None:
    super().__init__(CALL_EXPR_EC, info)
    self.callee = callee
    self.args: List[SimpleET] = [] if args is None else args


  def getFormalStr(self) -> types.FormalStrT:
    return consts.CALL_E_STR


  def hasPtrCall(self) -> bool:
    return self.hasDereference()


  def getDereferencedVarE(self) -> Opt['VarE']:
    if self.hasDereference():
      return self.callee
    return None


  def checkInvariants(self):
    super().checkInvariants()
    if util.CC1:
      assert isinstance(self.callee, VarE), f"{self}"
      self.callee.checkInvariants()
      if self.args:
        for arg in self.args:
          assert isinstance(arg, (VarE, LitE)), f"{self}: {arg}"
          arg.checkInvariants()


  def isPointerCall(self) -> bool:
    """Is this a pointer variable based call?"""
    return isinstance(self.callee.type, types.Ptr)


  def getCalleeSignature(self) -> types.FuncSig:
    """Returns the signature of the called function."""
    calleeType = self.callee.type
    if isinstance(calleeType, types.Ptr):
      return calleeType.to  # type: ignore
    elif isinstance(calleeType, types.FuncSig):
      return calleeType
    assert False, f"{self}: {calleeType}"


  def hasDereference(self) -> bool:
    return isinstance(self.callee.type, types.Ptr)


  def getFuncName(self) -> Opt[types.FuncNameT]:
    """Get the callee name if its a proper function."""
    if not self.isPointerCall():
      return self.callee.name
    return None


  def getFuncPtrName(self) -> Opt[types.VarNameT]:
    """Returns the name of the function pointer if present."""
    if self.isPointerCall():
      return self.callee.name
    return None


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, CallE):
      return NotImplemented
    equal = True
    if not self.callee == other.callee:
      equal = False
    elif not self.args == other.args:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, CallE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.callee.isEqual(other.callee):
      equal = False
    if not self.args == other.args:
      if util.LL1: LER("ArgumentsDiffer: %s, %s", self.args, other.args)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash((self.callee, self.exprCode))


  def __str__(self):
    if self.args:
      args = [str(arg) for arg in self.args]
      expr = ",".join(args)
    else:
      expr = ""
    return f"{self.callee}({expr})"


  def __repr__(self):
    return f"expr.CallE({repr(self.callee)}, {repr(self.args)}, {repr(self.info)})"


class SelectE(ExprET):
  """Ternary conditional operator."""

  __slots__: List[str] = ["cond", "arg1", "arg2"]


  def __init__(self,
      cond: VarE,  # use as a boolean value
      arg1: SimpleET,
      arg2: SimpleET,
      info: Opt[types.Info] = None,
  ) -> None:
    super().__init__(SELECT_EXPR_EC, info)
    # assert isinstance(cond, VarE), f"{cond}" # FIXME
    assert isinstance(arg1, SimpleET), f"{arg1}"
    assert isinstance(arg2, SimpleET), f"{arg2}"
    self.cond = cond
    self.arg1 = arg1
    self.arg2 = arg2


  def getFormalStr(self) -> types.FormalStrT:
    return consts.SELECT_E_STR


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, SelectE):
      return NotImplemented
    equal = True
    if not self.cond == other.cond:
      equal = False
    elif not self.arg1 == other.arg1:
      equal = False
    elif not self.arg2 == other.arg2:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __hash__(self) -> int:
    return hash((self.cond, self.arg1, self.arg2))


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, SelectE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.cond.isEqual(other.cond):
      equal = False
    if not self.arg1.isEqual(other.arg1):
      equal = False
    if not self.arg2.isEqual(other.arg2):
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __str__(self):
    return f"{self.cond} ? {self.arg1} : {self.arg2}"


  def __repr__(self):
    return f"expr.SelectE({repr(self.cond)}, {repr(self.arg1)}, " \
           f"{repr(self.arg2)}, {repr(self.info)})"


class PhiE(ExprET):
  """A phi expression. For a possible future SSA form."""

  __slots__: List[str] = ["args"]


  def __init__(self,
      args: Set[types.VarNameT],
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(PHI_EXPR_EC, info)
    self.args = args


  def getFormalStr(self) -> types.FormalStrT:
    return consts.PHI_E_STR


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, PhiE):
      return NotImplemented
    equal = True
    if not self.args == other.args:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __hash__(self) -> int:
    return hash((self.args, self.exprCode))


  def isEqual(self,
      other: 'ExprET'
  ) -> bool:
    equal = True
    if not isinstance(other, PhiE):
      if util.LL1: LER("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.args == other.args:
      if util.LL1: LER("ArgumentsDiffer: %s, %s", self.args, other.args)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and util.LL1:
      LER("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __str__(self):
    return f"phi({self.args})"


  def __repr__(self):
    return f"expr.PhiE({repr(self.args)}, {repr(self.info)})"


def getDefaultInitExpr(objType: types.Type) -> Opt[ExprET]:
  """Returns the default global initialization
  of variables as per their types."""
  e: Opt[ExprET] = None

  if objType.isNumeric():
    e = LitE(val=0)
  elif objType.isPointer():
    e = AddrOfE(arg=VarE(name=irConv.NULL_OBJ_NAME))

  return e


def getDerefExpr(e: ExprET) -> Opt[ExprET]:
  if isinstance(e, AddrOfE):
    e = e.arg
  if e.hasDereference():
    return e
  return None


def getDereferencedVar(e: ExprET) -> VarE:
  """Returns the variable de-referenced in the given expression."""
  assert e.hasDereference(), f"{e}"

  varE = None
  if isinstance(e, DerefE):
    varE = e.arg
  elif isinstance(e, ArrayE):
    varE = e.of
  elif isinstance(e, MemberE):
    varE = e.of
  elif isinstance(e, CallE):
    varE = e.callee

  assert varE and isinstance(varE, VarE), f"{e}, {varE}"
  return varE


def getVarExprs(e: ExprET) -> List[VarE]:
  """Returns the list of VarE in the given expression."""
  if isinstance(e, LitE):
    return []  # i.e. empty list
  if isinstance(e, VarE):
    return [e]

  if isinstance(e, (UnaryE, DerefE, CastE, SizeOfE, AllocE)):
    return getVarExprs(e.arg)
  if isinstance(e, (BinaryE, SelectE)):
    l1 = getVarExprs(e.arg1)
    l1.extend(getVarExprs(e.arg2))
    return l1
  if isinstance(e, ArrayE):
    l1 = getVarExprs(e.of)
    l1.extend(getVarExprs(e.index))
    return l1
  if isinstance(e, MemberE):
    return getVarExprs(e.of)
  else:
    raise ValueError(f"{e}")


def getNamesUsedInExprSyntactically(
    e: ExprET,
    forLiveness=True,
    addLValue=True,
) -> Set[types.VarNameT]:
  """Returns the names syntactically present in the expression.
  If forLiveness is False, the return set will also include,
    1. The function name in a call.
    2. The name of variable whose address is taken.
  """
  thisFunction = getNamesUsedInExprSyntactically

  if isinstance(e, LitE):
    return set()
  if isinstance(e, VarE):  # covers PseudoVarE too
    return {e.name} if addLValue else set()

  if isinstance(e, (DerefE, UnaryE, CastE, SizeOfE, AllocE)):
    return thisFunction(e.arg, forLiveness)
  if isinstance(e, (MemberE, ArrayE)):
    l1 = thisFunction(e.of, forLiveness)
    if isinstance(e, ArrayE): l1.update(thisFunction(e.index, forLiveness))
    return l1
  if isinstance(e, (BinaryE, SelectE)):
    l1 = thisFunction(e.arg1, forLiveness)
    l1.update(thisFunction(e.arg2, forLiveness))
    if isinstance(e, SelectE): l1.update(thisFunction(e.cond, forLiveness))
    return l1

  if isinstance(e, AddrOfE):
    if forLiveness and isinstance(e.arg, VarE):  # forLiveness
      return set()  # i.e. in '&a' discard 'a'
    return thisFunction(e.arg, forLiveness)
  if isinstance(e, CallE):
    if forLiveness and not e.hasDereference():  # forLiveness
      varNames = set()  # i.e. in 'f(a,b)' don't include 'f'
    else:
      varNames = thisFunction(e.callee, forLiveness)  # i.e. in 'f(a,b)' include 'f'
    for arg in e.args:
      varNames |= thisFunction(arg, forLiveness)
    return varNames
  raise ValueError(f"{e}")


def evalExpr(e: ExprET) -> LitE:
  """Converts: 5 + 6, 6 > 7, -5, +6, !7, ~9, ... to a single literal."""
  newExpr = e  # default value on return

  if isinstance(e, BinaryE):
    arg1 = e.arg1
    arg2 = e.arg2
    opCode = e.opr.opCode

    if isinstance(arg1, LitE) and isinstance(arg2, LitE):
      if opCode == op.BO_ADD_OC:
        newExpr = LitE(arg1.val + arg2.val, info=arg1.info)  # type: ignore
      elif opCode == op.BO_SUB_OC:
        newExpr = LitE(arg1.val - arg2.val, info=arg1.info)  # type: ignore
      elif opCode == op.BO_MUL_OC:
        newExpr = LitE(arg1.val * arg2.val, info=arg1.info)  # type: ignore
      elif opCode == op.BO_DIV_OC:
        newExpr = LitE(arg1.val / arg2.val, info=arg1.info)  # type: ignore
      elif opCode == op.BO_MOD_OC:
        newExpr = LitE(arg1.val % arg2.val, info=arg1.info)  # type: ignore

      elif opCode == op.BO_LT_OC:
        newExpr = LitE(int(arg1.val < arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_LE_OC:
        newExpr = LitE(int(arg1.val <= arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_EQ_OC:
        newExpr = LitE(int(arg1.val == arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_NE_OC:
        newExpr = LitE(int(arg1.val != arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_GE_OC:
        newExpr = LitE(int(arg1.val >= arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_GT_OC:
        newExpr = LitE(int(arg1.val > arg2.val), info=arg1.info)  # type: ignore

      elif opCode == op.BO_BIT_OR_OC:
        newExpr = LitE(int(arg1.val | arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_BIT_AND_OC:
        newExpr = LitE(int(arg1.val & arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_RSHIFT_OC:
        newExpr = LitE(int(arg1.val >> arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_LSHIFT_OC:
        newExpr = LitE(int(arg1.val << arg2.val), info=arg1.info)  # type: ignore
      elif opCode == op.BO_BIT_XOR_OC:
        newExpr = LitE(int(arg1.val ^ arg2.val), info=arg1.info)  # type: ignore

      if newExpr is e:
        print(f"ExprNotEvaluated: {e}, {e.info}, {e.type}")

  elif isinstance(e, UnaryE):
    arg, opCode = e.arg, e.opr.opCode

    if isinstance(arg, LitE):
      if opCode == op.UO_PLUS_OC:
        newExpr = arg
      elif opCode == op.UO_MINUS_OC:
        newExpr = LitE(arg.val * -1, info=arg.info)  # type: ignore
      elif opCode == op.UO_LNOT_OC:
        newExpr = LitE(int(not (bool(arg.val))), info=arg.info)
      elif opCode == op.UO_BIT_NOT_OC:
        newExpr = LitE(~arg.val, info=arg.info)  # type: ignore

  elif isinstance(e, CastE):
    if isinstance(e.arg, LitE):
      newExpr = e.arg
      if isinstance(e.arg.val, (int, float)):
        newVal = e.type.castValue(e.arg.val)
        newExpr = LitE(newVal, info=e.arg.info)

  return newExpr


