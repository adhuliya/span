#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
All operators used in expressions.
"""

import logging

LOG = logging.getLogger("span")

from typing import Dict, List, Tuple

from span.util.logger import LS
import span.ir.types as types

OpCodeT = types.OpCodeT

################################################
# BOUND START: op_codes
# NOTE: Operators &&, || reduce to if() statements in IR
################################################

# BO = BinaryOperator
# UO = UnaryOperator
# OC = OperatorCode
# NamingFormat: <BO|UO>_<opName>_OC

# the order and ascending sequence may be important

# numeric_ops
UO_PLUS_OC: OpCodeT = 101  # +
UO_MINUS_OC: OpCodeT = 102  # -

# unary pointer_ops
# UO_ADDROF_OC: OpCodeT = 103  # &
# UO_DEREF_OC: OpCodeT = 104  # *
# UO_SIZEOF_OC: OpCodeT = 105  # sizeof()

# bitwise_ops
UO_BIT_NOT_OC: OpCodeT = 110  # ~

# logical_ops
UO_LNOT_OC: OpCodeT = 120  # !

# special cast operator
UO_CAST_OC: OpCodeT = 130  # e.g. (int)2.5

# NOTE: all OpCodes less than 200 are unary.

# numeric_ops
BO_NUM_START_OC: OpCodeT = 200  # Numeric binary ops start
BO_ADD_OC: OpCodeT = 201  # +
BO_SUB_OC: OpCodeT = 202  # -
BO_MUL_OC: OpCodeT = 203  # *
BO_DIV_OC: OpCodeT = 204  # /
BO_MOD_OC: OpCodeT = 205  # %

# integer bitwise_ops
BO_BIT_AND_OC: OpCodeT = 300  # &
BO_BIT_OR_OC: OpCodeT = 301  # |
BO_BIT_XOR_OC: OpCodeT = 302  # ^

# integer shift_ops
BO_LSHIFT_OC: OpCodeT = 400  # <<
BO_RSHIFT_OC: OpCodeT = 401  # >>
BO_RRSHIFT_OC: OpCodeT = 402  # >>>
BO_NUM_END_OC: OpCodeT = 499  # Numeric binary ops end

# numeric relational_ops
BO_REL_START_OC: OpCodeT = 500  # relational ops start
BO_LT_OC: OpCodeT = 507  # <
BO_LE_OC: OpCodeT = 508  # <=
BO_EQ_OC: OpCodeT = 509  # ==
BO_NE_OC: OpCodeT = 510  # !=
BO_GE_OC: OpCodeT = 511  # >=
BO_GT_OC: OpCodeT = 512  # >
BO_REL_END_OC: OpCodeT = 520  # relational ops end


# array_index
# BO_INDEX_OC: OpCodeT     = 600 # [] e.g. arr[3]

################################################
# BOUND END  : op_codes
################################################

class OpT:
  """class type for all operators.

  Attributes:
    opCode: opcode of the operator
  """

  __slots__ : List[str] = ["opCode", "opDict"]

  def __init__(self,
      opCode: OpCodeT
  ) -> None:
    # don't call the super().__init__()
    self.opDict: Dict[OpCodeT, Tuple[str, str]] = {
      # UO_ADDROF_OC:  ("&", "op.UO_ADDROF"),
      # UO_DEREF_OC:   ("*", "op.UO_DEREF"),

      UO_MINUS_OC:   ("-", "op.UO_MINUS"),
      UO_PLUS_OC:    ("+", "op.UO_PLUS"),

      UO_BIT_NOT_OC: ("~", "op.UO_BIT_NOT"),
      UO_LNOT_OC:    ("!", "op.UO_LNOT"),

      BO_ADD_OC:     ("+", "op.BO_ADD"),
      BO_SUB_OC:     ("-", "op.BO_SUB"),
      BO_MUL_OC:     ("*", "op.BO_MUL"),
      BO_DIV_OC:     ("/", "op.BO_DIV"),
      BO_MOD_OC:     ("%", "op.BO_MOD"),

      BO_LT_OC:      ("<", "op.BO_LT"),
      BO_LE_OC:      ("<=", "op.BO_LE"),
      BO_EQ_OC:      ("==", "op.BO_EQ"),
      BO_NE_OC:      ("!=", "op.BO_NE"),
      BO_GE_OC:      (">=", "op.BO_GE"),
      BO_GT_OC:      (">", "op.BO_GT"),

      BO_BIT_AND_OC: ("&", "op.BO_BIT_AND"),
      BO_BIT_OR_OC:  ("|", "op.BO_BIT_OR"),
      BO_BIT_XOR_OC: ("^", "op.BO_BIT_XOR"),

      BO_LSHIFT_OC:  ("<<", "op.BO_LSHIFT"),
      BO_RSHIFT_OC:  (">>", "op.BO_RSHIFT"),
      BO_RRSHIFT_OC: (">>>", "op.BO_RRSHIFT"),
      # BO_INDEX_OC:   ("[]",  "op.BO_INDEX"),
    }  # dict end

    if opCode not in self.opDict:
      if LS: LOG.error("InvalidOpCode: %s", opCode)

    self.opCode = opCode


  def isUnaryOp(self) -> bool:
    return UO_PLUS_OC <= self.opCode < BO_ADD_OC


  def isBinaryOp(self) -> bool:
    return self.opCode >= BO_ADD_OC


  def isArithmeticOp(self) -> bool:
    return BO_ADD_OC <= self.opCode <= BO_MOD_OC \
           or UO_PLUS_OC <= self.opCode <= UO_MINUS_OC


  def isRelationalOp(self) -> bool:
    return BO_LT_OC <= self.opCode <= BO_GT_OC


  def isInequalityOp(self) -> bool:
    return BO_EQ_OC <= self.opCode <= BO_NE_OC


  def isCommutative(self) -> bool:
    if self.opCode in {BO_ADD_OC, BO_MUL_OC, BO_EQ_OC, BO_NE_OC,
                       BO_BIT_AND_OC, BO_BIT_OR_OC, BO_BIT_XOR_OC}:
      return True
    return False


  def __eq__(self, other) -> bool:
    """Operator equality is a special case:
    such that at all places it should be the same object.
    This is efficient.
    """
    if not isinstance(other, OpT):
      return NotImplemented
    if self is other:
      return True
    return False


  def __hash__(self):
    return hash(self.opCode)


  def isEqual(self, other: 'OpT') -> bool:
    equal = True
    if not isinstance(other, OpT):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.opCode == other.opCode:
      LOG.error("OpCodesDiffer: %s, %s", self.opCode, other.opCode)
      equal = False
    if self is not other:
      LOG.error("OpObjectsDiffer: %s, %s", id(self), id(other))
      equal = False

    if LS and not equal:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __str__(self):
    return self.opDict[self.opCode][0]


  def __repr__(self):
    """It returns the name of the predefined objects in this module.
    It expects the eval()uator to import this module as follows:
      import span.ir.op as op
    """
    return self.opDict[self.opCode][1]


class BinaryOp(OpT):
  __slots__ : List[str] = []


  def __init__(self,
      opCode: OpCodeT
  ) -> None:
    super().__init__(opCode)


class UnaryOp(OpT):
  __slots__ : List[str] = []

  def __init__(self,
      opCode: OpCodeT
  ) -> None:
    super().__init__(opCode)


################################################
# BOUND START: operator_objects
################################################

UO_PLUS: UnaryOp = UnaryOp(UO_PLUS_OC)
UO_MINUS: UnaryOp = UnaryOp(UO_MINUS_OC)

# These operators are no more used.
# There are dedicated expression types for these operations.
# UO_ADDROF:    UnaryOp = UnaryOp(UO_ADDROF_OC)
# UO_DEREF:     UnaryOp = UnaryOp(UO_DEREF_OC)
# UO_SIZEOF: UnaryOp = UnaryOp(UO_SIZEOF_OC)

UO_BIT_NOT: UnaryOp = UnaryOp(UO_BIT_NOT_OC)
UO_LNOT: UnaryOp = UnaryOp(UO_LNOT_OC)

BO_ADD: BinaryOp = BinaryOp(BO_ADD_OC)
BO_SUB: BinaryOp = BinaryOp(BO_SUB_OC)
BO_MUL: BinaryOp = BinaryOp(BO_MUL_OC)
BO_DIV: BinaryOp = BinaryOp(BO_DIV_OC)
BO_MOD: BinaryOp = BinaryOp(BO_MOD_OC)

BO_LT: BinaryOp = BinaryOp(BO_LT_OC)
BO_LE: BinaryOp = BinaryOp(BO_LE_OC)
BO_EQ: BinaryOp = BinaryOp(BO_EQ_OC)
BO_NE: BinaryOp = BinaryOp(BO_NE_OC)
BO_GE: BinaryOp = BinaryOp(BO_GE_OC)
BO_GT: BinaryOp = BinaryOp(BO_GT_OC)

BO_BIT_AND: BinaryOp = BinaryOp(BO_BIT_AND_OC)
BO_BIT_OR: BinaryOp = BinaryOp(BO_BIT_OR_OC)
BO_BIT_XOR: BinaryOp = BinaryOp(BO_BIT_XOR_OC)

BO_LSHIFT: BinaryOp = BinaryOp(BO_LSHIFT_OC)
BO_RSHIFT: BinaryOp = BinaryOp(BO_RSHIFT_OC)
BO_RRSHIFT: BinaryOp = BinaryOp(BO_RRSHIFT_OC)

# BO_INDEX: UnaryOp = BinaryOp(BO_INDEX_OC)

################################################
# BOUND END  : operator_objects
################################################

# When left and right operands are flipped, operator also flips.
flippedRelOps = {
  BO_EQ_OC: BO_EQ,
  BO_NE_OC: BO_NE,
  BO_LT_OC: BO_GT,
  BO_LE_OC: BO_GE,
  BO_GT_OC: BO_LT,
  BO_GE_OC: BO_LE,
}


def getFlippedRelOp(relOp: OpT) -> OpT:
  """Returns the flipped equivalent to the given operator.
  It is generally called when operators of the operand are swapped.
  """
  opCode = relOp.opCode
  if opCode in flippedRelOps:
    return flippedRelOps[opCode]
  else:
    raise ValueError()


