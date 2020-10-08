#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""All instructions of IR

Note: use names in this module with module name: e.g. instr.UseI...
"""
import logging

LOG = logging.getLogger("span")
from typing import Set, List
from typing import Optional as Opt

from span.util.logger import LS
import span.ir.expr as expr
import span.ir.types as types
import span.util.util as util
from span.util.util import AS

InstrCodeT = types.InstrCodeT

################################################
# BOUND START: instr_codes
################################################

# the order and ascending sequence may be important
NOP_INSTR_IC: InstrCodeT = 0

BARRIER_INSTR_IC: InstrCodeT = 1
USE_INSTR_IC: InstrCodeT = 2
COND_READ_INSTR_IC: InstrCodeT = 3
UNDEF_VAL_INSTR_IC: InstrCodeT = 4
FILTER_INSTR_IC: InstrCodeT = 5  # new name for liveness
EX_READ_INSTR_IC: InstrCodeT = 6

ASSIGN_INSTR_IC: InstrCodeT = 10
RETURN_INSTR_IC: InstrCodeT = 20
CALL_INSTR_IC: InstrCodeT = 30
COND_INSTR_IC: InstrCodeT = 40
GOTO_INSTR_IC: InstrCodeT = 50

PAR_INSTR_IC: InstrCodeT = 60

################################################
# BOUND END  : instr_codes
################################################

# set of artificial instruction codes
ARTIFICIAL_INSTR_CODES: Set[InstrCodeT] = {
  NOP_INSTR_IC, BARRIER_INSTR_IC, USE_INSTR_IC,
  COND_READ_INSTR_IC, UNDEF_VAL_INSTR_IC, FILTER_INSTR_IC,
  EX_READ_INSTR_IC
}


class InstrIT:
  """Base type for all instructions."""

  __slots__ : List[str] = ["instrCode", "info", "type"]

  def __init__(self,
      instrCode: InstrCodeT,
      info: Opt[types.Info] = None,
  ) -> None:
    if self.__class__ is InstrIT: raise TypeError()
    self.type = types.Void  # default instruction type
    self.instrCode = instrCode
    self.info = info


  def checkInvariants(self, level: int = 0):
    """Runs some invariant checks on self.
    Args:
      level: An argument to help invoke specific checks in future.
    """
    if level == 0:
      assert self.instrCode is not None, f"{self}"
      assert self.type is not None, f"{self}"


  def isArtificial(self) -> bool:
    """Returns True if the instruction is artificial."""
    return self.instrCode in ARTIFICIAL_INSTR_CODES


  def isEqual(self,
      other: 'InstrIT'
  ) -> bool:
    """Used in place of __eq__, for testing purposes."""
    equal = True
    if not isinstance(other, self.__class__):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.instrCode == other.instrCode:
      if LS: LOG.error("InstrCodesDiffer: %s, %s",
                       self.instrCode, other.instrCode)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash(self.instrCode) + hash(self.type)


class AssignI(InstrIT):
  """Assignment statement.
  Two forms only: (runtime checked)
    VarE    = ExprET
           or
    DerefET = SimpleET
  """

  __slots__ : List[str] = ["lhs", "rhs"]

  def __init__(self,
      lhs: expr.LocationET,
      rhs: expr.ExprET,
      info: Opt[types.Info] = None
  ) -> None:
    # invariant check
    if not isinstance(lhs, expr.LocationET) \
        or (isinstance(lhs, expr.DerefET)
            and not isinstance(rhs, expr.SimpleET)):
      raise ValueError(f"{lhs} = {rhs}")
    super().__init__(ASSIGN_INSTR_IC, info)
    self.lhs = lhs
    self.rhs = rhs


  def checkInvariants(self, level: int = 0):
    super().checkInvariants(level)
    if level == 0:
      self.lhs.checkInvariants(level)
      self.rhs.checkInvariants(level)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, AssignI):
      return NotImplemented
    equal = True
    if not self.lhs == other.lhs:
      equal = False
    elif not self.rhs == other.rhs:
      equal = False
    elif not self.type == other.type:
      equal = False
    elif not self.info == other.info:
      equal = False
    return True


  def isEqual(self,
      other: 'InstrIT'
  ) -> bool:
    equal = True
    if not isinstance(other, AssignI):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.lhs.isEqual(other.lhs):
      if LS: LOG.error("LHSsDiffer:")
      equal = False
    if not self.rhs.isEqual(other.rhs):
      if LS: LOG.error("RHSsDiffer:")
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash(self.lhs) + hash(self.rhs)


  def __str__(self):
    return f"{self.lhs} = {self.rhs}"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.AssignI({repr(self.lhs)},\n" \
           f"    {repr(self.rhs)}," \
           f" {repr(self.info)})"


FAILED_INSN_SIM = AssignI(expr.VarE("SAME_INSN"), expr.VarE("SAME_INSN"))

class GotoI(InstrIT):
  """goto xyz; instruction
  This instruction is only used in the IR taken as input by SPAN.
  This instruction is not included in the BB representation.
  """

  __slots__ : List[str] = ["label"]

  def __init__(self,
      label: types.LabelNameT = None,
      info: Opt[types.Info] = None
  ) -> None:
    # invariant check
    if not isinstance(label, types.LabelNameT):
      raise ValueError(f"{label}")
    super().__init__(GOTO_INSTR_IC, info)
    self.label = label


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, GotoI):
      return NotImplemented
    equal = True
    if not self.label == other.label:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'InstrIT'
  ) -> bool:
    equal = True
    if not isinstance(other, GotoI):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.label == other.label:
      if LS: LOG.error("LabelsDiffer: %s, %s", self.label, other.label)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __str__(self):
    return f"goto {self.label}"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.GotoI({repr(self.label)}, {repr(self.info)})"


class LabelI(InstrIT):
  """label xyz: instruction
  This instruction is only used in the IR taken as input by SPAN.
  This instruction is not included in the BB representation.
  """

  __slots__ : List[str] = ["label"]

  def __init__(self,
      label: types.LabelNameT,
      info: Opt[types.Info] = None
  ) -> None:
    # invariant check
    if not isinstance(label, types.LabelNameT):
      raise ValueError(f"{label}")
    super().__init__(GOTO_INSTR_IC, info)
    self.label = label


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, LabelI):
      return NotImplemented
    equal = True
    if not self.label == other.label:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def isEqual(self,
      other: 'InstrIT'
  ) -> bool:
    equal = True
    if not isinstance(other, LabelI):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.label == other.label:
      if LS: LOG.error("LabelsDiffer: %s, %s", self.label, other.label)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __str__(self):
    return f"label {self.label}"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.LabelI({repr(self.label)}, {repr(self.info)})"


class CondI(InstrIT):
  """A conditional instruction.
  The self.trueLabel and self.falseLabel become irrelevant
  once BB or CFG is formed.
  """

  __slots__ : List[str] = ["arg", "trueLabel", "falseLabel"]

  def __init__(self,
      arg: expr.SimpleET,
      trueLabel: types.LabelNameT = None,
      falseLabel: types.LabelNameT = None,
      info: Opt[types.Info] = None
  ) -> None:
    # invariant check
    if not isinstance(arg, expr.SimpleET):
      raise ValueError(f"{arg}")
    super().__init__(COND_INSTR_IC, info)
    self.arg = arg
    self.trueLabel = trueLabel
    self.falseLabel = falseLabel


  def checkInvariants(self, level: int = 0):
    super().checkInvariants(level)
    if level == 0:
      assert isinstance(self.arg, expr.VarE), f"{self}"
      self.arg.checkInvariants(level)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, CondI):
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
      other: 'InstrIT'
  ) -> bool:
    equal = True
    if not isinstance(other, CondI):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.arg.isEqual(other.arg):
      if LS: LOG.error("ArgumentsDiffer:")
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash(self.arg) + hash(self.instrCode)


  def __str__(self):
    return f"if ({self.arg}) {self.trueLabel} {self.falseLabel}"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.CondI({repr(self.arg)}, {repr(self.trueLabel)}, " \
           f"{repr(self.falseLabel)}, {repr(self.info)})"


class ReturnI(InstrIT):
  """Return statement."""

  __slots__ : List[str] = ["arg"]

  def __init__(self,
      arg: Opt[expr.SimpleET] = None,
      info: Opt[types.Info] = None
  ) -> None:
    # invariant check
    if not isinstance(arg, expr.SimpleET) and arg is not None:
      raise ValueError(f"{arg}")
    super().__init__(RETURN_INSTR_IC, info)
    self.arg = arg


  def checkInvariants(self, level: int = 0):
    super().checkInvariants(level)
    if level == 0:
      assert self.arg is None \
             or isinstance(self.arg, (expr.VarE, expr.LitE)), f"{self}"
      if self.arg: self.arg.checkInvariants(level)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, ReturnI):
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
      other: 'InstrIT'
  ) -> bool:
    equal = True
    if not isinstance(other, ReturnI):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if self.arg is None and other.arg is not None:
      if LS: LOG.error("ArgumentsDiffer:")
      equal = False
    if self.arg is not None and other.arg is None:
      if LS: LOG.error("ArgumentsDiffer:")
      equal = False
    if self.arg and other.arg and not self.arg.isEqual(other.arg):
      if LS: LOG.error("ArgumentsDiffer:")
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash(self.arg) + hash(self.instrCode)


  def __str__(self):
    return f"return {self.arg}"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.ReturnI({repr(self.arg)}, {repr(self.info)})"


class CallI(InstrIT):
  """Call statement."""

  __slots__ : List[str] = ["arg"]

  def __init__(self,
      arg: expr.CallE,
      info: Opt[types.Info] = None
  ) -> None:
    # invariant check
    if not isinstance(arg, expr.CallE):
      raise ValueError(f"{arg}")
    super().__init__(CALL_INSTR_IC, info)
    self.arg = arg


  def checkInvariants(self, level: int = 0):
    super().checkInvariants(level)
    if level == 0:
      assert self.arg is not None, f"{self}"
      self.arg.checkInvariants(level)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, CallI):
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
      other: 'InstrIT'
  ) -> bool:
    equal = True
    if not isinstance(other, CallI):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.arg.isEqual(other.arg):
      if LS: LOG.error("ArgumentsDiffer:")
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash(self.arg)


  def __str__(self):
    return f"{self.arg}"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.CallI({repr(self.arg)}, {repr(self.info)})"


class ParallelI(InstrIT):
  """
  Holds the set of instructions which are assumed to be
  parallel in their execution semantics.
  These instructions should never have function calls in them.
  """

  __slots__ : List[str] = ["insns"]

  def __init__(self,
      insns: List[InstrIT],
      info: Opt[types.Info] = None,
  ) -> None:
    # invariant check
    if AS:
      for insn in insns:
        if not isinstance(insn, InstrIT) \
            or getCallExpr(insn):  # insn must not contain a call expression
          raise ValueError(f"{insn} in {insns}")
    super().__init__(PAR_INSTR_IC, info)
    self.insns = insns


  def yieldInstructions(self):
    yield from self.insns


  def addInstr(self, insn: InstrIT):
    self.insns.append(insn)


  @staticmethod
  def genPrallelMultiAssign(lhs: expr.LocationET,
      rhsList: List[expr.ExprET]
  ) -> 'ParallelI':
    """
    A convenience function to generate an object of PrallelI
    such that the lhs is the same and is being assigned multiple
    rhs expressions (more than one).
    """
    assert len(rhsList) > 1, f"rhsList"

    insns: List[InstrIT] = []
    for rhs in rhsList:
      insn = AssignI(lhs=lhs, rhs=rhs, info=lhs.info)
      insns.append(insn)

    return ParallelI(insns=insns, info=lhs.info)


  def __eq__(self, other):
    if self is other:
      return True
    if not isinstance(other, ParallelI):
      return NotImplemented
    equal = True
    if not len(self.insns) == len(other.insns):
      equal = False
    elif not self.insns == other.insns:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __hash__(self):
    insn = self.insns[-1] if self.insns else None
    return hash(("ParallelI", len(self.insns), insn))


  def isEqual(self,
      other: 'InstrIT'
  ) -> bool:
    equal = True
    if not isinstance(other, ParallelI):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not len(self.insns) == len(other.insns):
      if LS: LOG.error("InstrCountsDiffer:")
    if not self.insns == other.insns:
      if LS: LOG.error("InstrsDiffer:")
    if not self.type.isEqual(other.type):
      equal = False
    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __str__(self):
    insnList = [str(insn) for insn in self.insns]
    insns = "//".join(insnList)
    return f"ParallelI({insns})"


  def __repr__(self):
    return f"ParallelI({self.insns})"


################################################
# BOUND START: Special_Instructions
# These special instructions are used internally,
# but can be used in toy programs for testability.
################################################

class UseI(InstrIT):
  """Value of the variable is used."""

  __slots__ : List[str] = ["vars"]

  def __init__(self,
      vars: Set[types.VarNameT],
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(USE_INSTR_IC, info)
    self.vars: Set[types.VarNameT] = vars


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, UseI):
      return NotImplemented
    equal = True
    if not self.vars == other.vars:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __str__(self):
    return f"use({self.vars})"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.UseI({repr(self.vars)})"


class ExReadI(InstrIT):
  """Only the given vars are exclusively read.

  All other vars are considered marked unread before this instruction.
  """

  __slots__ : List[str] = ["vars"]

  def __init__(self,
      vars: Set[types.VarNameT],
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(EX_READ_INSTR_IC, info)
    self.vars: Set[types.VarNameT] = vars


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, ExReadI):
      return NotImplemented
    equal = True
    if not self.vars == other.vars:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __str__(self):
    return f"exRead({self.vars})"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.ExReadI({repr(self.vars)})"


class CondReadI(InstrIT):
  """Use of vars in rhs in lhs assignment.

  It implicitly blocks all forward/backward information flow,
  if not implemented by an analysis.
  """

  __slots__ : List[str] = ["lhs", "rhs"]

  def __init__(self,
      lhs: types.VarNameT,
      rhs: Set[types.VarNameT],
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(COND_READ_INSTR_IC, info)
    self.lhs = lhs
    self.rhs = rhs


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, CondReadI):
      return NotImplemented
    equal = True
    if not self.lhs == other.lhs:
      equal = False
    elif not self.rhs == other.rhs:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __hash__(self):
    return hash(self.lhs)


  def __str__(self):
    return f"condRead({self.lhs}, {self.rhs})"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.CondReadI({repr(self.lhs)}, {repr(self.rhs)})"


class FilterI(InstrIT):
  """Set of vars dead at current program point."""

  __slots__ : List[str] = ["varNames"]

  def __init__(self,
      varNames: Set[types.VarNameT],
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(FILTER_INSTR_IC, info)
    self.varNames = varNames


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, FilterI):
      return NotImplemented
    equal = True
    if not self.varNames == other.varNames:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __hash__(self):
    return hash(self.varNames)


  def __str__(self):
    return f"filter({self.varNames})"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.FilterI({repr(self.varNames)})"


class UnDefValI(InstrIT):
  """Variable takes a user input, i.e. an unknown/undefined value."""

  __slots__ : List[str] = ["lhsName"]

  def __init__(self,
      lhsName: types.VarNameT,  # deliberately named lhs
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(UNDEF_VAL_INSTR_IC, info)
    self.lhsName: types.VarNameT = lhsName  # deliberately named lhs


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, UnDefValI):
      return NotImplemented
    equal = True
    if not self.lhsName == other.lhsName:
      equal = False
    elif not self.info == other.info:
      equal = False
    return equal


  def __str__(self):
    return f"input({self.lhsName})"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.UnDefValI({repr(self.lhsName)})"


class BarrierI(InstrIT):
  """Creates a barrier between IN and OUT.
  Data flow information doesn't travel from IN to OUT or vice versa.
  """


  def __init__(self,
      info: types.Info = None
  ) -> None:
    super().__init__(BARRIER_INSTR_IC, info)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, BarrierI):
      return NotImplemented
    if not self.info == other.info:
      return False
    return True


  def __str__(self):
    return f"barrier()"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.BarrierI()"


class NopI(InstrIT):
  """A no operation instruction, for dummy nodes.

  For EmptyI, Host calls the identity transfer function of an analysis.
  """


  def __init__(self,
      info: Opt[types.Info] = None
  ) -> None:
    super().__init__(NOP_INSTR_IC, info)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, NopI):
      return NotImplemented
    if not self.info == other.info:
      return False
    return True


  def __hash__(self):
    return 0


  def __str__(self):
    return "nop()"


  def __repr__(self):
    return f"# {str(self)}\n" \
           f"instr.NopI()"


################################################
# BOUND END  : Special_Instructions
################################################

def getCallExpr(insn: InstrIT) -> Opt[expr.CallE]:
  """Get the call expr if present in the instruction."""
  if isinstance(insn, AssignI):
    if isinstance(insn.rhs, expr.CallE):
      return insn.rhs
  elif isinstance(insn, CallI):
    return insn.arg

  return None


def getCalleeFuncName(insn: InstrIT) -> Opt[types.FuncNameT]:
  """Get the callee name if its a proper function."""
  callE = getCallExpr(insn)
  return callE.getCalleeFuncName() if callE else None


def getDerefExpr(insn: InstrIT) -> Opt[expr.ExprET]:
  if not isinstance(insn, AssignI):
    return None  # DerefE can occur only in AssignI instructions
  return expr.getDerefExpr(insn.lhs) or expr.getDerefExpr(insn.rhs)


