#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Defines the base lattice class."""

import logging

from span.ir import constructs

LOG = logging.getLogger("span")

from typing import Tuple, Any, List, TypeVar, Optional as Opt, Sequence as Seq, Iterable

import span.ir.constructs as obj

import span.ir.types as types

ChangedT = bool  # is the value changed?
Changed: ChangedT = True  # for unchanged use `not Changed`

BoundLatticeLT = TypeVar('BoundLatticeLT', bound='LatticeLT')


class LatticeLT:
  """Base class for all Lattices."""

  __slots__ : List[str] = ["top", "bot"]


  def __init__(self,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if bot and top:
      raise ValueError(f"{top}, {bot}")
    self.top = top
    self.bot = bot


  def meet(self, other) -> Tuple['LatticeLT', ChangedT]:
    """Calculates glb of the self and the other data flow value.

    Default implementation, assuming only top and bot exist (binary lattice).

    Args:
      other: the data flow value to calculate `meet` with.

    Returns:
      (Lattice, Changed): glb of self and dfv, and True if glb != self
    """
    return NotImplemented


  def widen(self,  #for #IPA and for infinite lattice heights
      other: Opt['LatticeLT'] = None,
      ipa: bool = False,  # special case #IPA FIXME: is this needed?
  ) -> Tuple['LatticeLT', ChangedT]:
    """Apply widening w.r.t. the prev value.
    MUST override this function if widening is needed.
    """
    raise NotImplementedError()


  def getCopy(self) -> 'LatticeLT':
    """Return a copy of this lattice element.
    In the least, it should be a deep copy of mutable elements,
    and a shallow copy of the immutable elements.
    """
    raise NotImplementedError()


  def __lt__(self, other) -> bool:
    """Emulates non-strict weaker-than partial order,

    Default implementation, assuming only top and bot exist (binary lattice).

    Salient properties:
    if: x <= y and y <= x, then x and y are equal.
    if: not x <= y and not y <= x, then x and y are incomparable.
    for all other cases,
    not x <= y should-be-equal-to y <= x.
    """
    res = basicLessThanTest(self, other)
    assert res is not None, f"{res}, {self}, {other}"
    return res


  def __eq__(self, other) -> bool:
    """returns True if equal, False if not equal or incomparable.

    Default implementation, assuming only top and bot exist (binary lattice).
    """
    if not isinstance(other, LatticeLT):
      return NotImplemented
    res = basicEqualsTest(self, other)
    assert res is not None, f"{res}, {self}, {other}"
    return res


  def __gt__(self, other):
    """Never use `>` or `>=` operator. Don't Override this method."""
    raise NotImplementedError()


BoundDataLT = TypeVar('BoundDataLT', bound='DataLT')


class DataLT(LatticeLT):
  """The abstract Lattice type for analyses.

  One should always subclass this to form lattice.
  Directly creating objects of this class will lead to a TypeError().
  """

  __slots__ : List[str] = ["func", "val"]


  def __init__(self,
      func: obj.Func,
      val: Opt[Any] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if self.__class__.__name__.endswith("T"): raise TypeError()
    super().__init__(top, bot)
    # if not (self.top or self.bot):  # safety check (moved to subclasses)
    #   assert val is not None
    self.func = func
    self.val = val
    if self.top or self.bot:  # top and bot get priority
      self.val = None


  def meet(self, other) -> Tuple['DataLT', ChangedT]:
    """Calculates glb of the self and the other data flow value.

    Note: It never modifies the 'self' or the 'other' data flow value.

    Args:
      other: the data flow value to calculate `meet` with.

    Returns:
      (Lattice, ChangedT): glb of self and dfv, and 'Changed' if glb != self
    """
    raise NotImplementedError()


  def widen(self,
      other: Opt['DataLT'] = None,
      ipa: bool = False,  # special case #IPA FIXME: is this needed?
  ) -> Tuple['DataLT', ChangedT]:
    """Apply widening w.r.t. the prev value.
    MUST override this function if widening is needed.
    """
    if self != other:
      return other, Changed
    else:
      return self, not Changed


  def checkInvariants(self, level: int = 0):
    """Checks necessary invariants."""
    pass


  def localize(self, #IPA
      forFunc: constructs.Func,
      keepParams: bool = False,
  ) -> 'DataLT':
    """Returns self's copy localized for the given forFunc."""
    raise NotImplementedError


  def updateFuncObj(self, funcObj: constructs.Func): #IPA #Mutates 'self'.
    """Updates the self.func object reference (for all sub-objects too).
    Modifies self object."""
    raise NotImplementedError


  def addLocals(self, #IPA #Mutates 'self'
      fromDfv: 'DataLT',
  ) -> None:
    """Adds the value of strictly local variables in self.func
    in fromDfv to self. It modifies self object.
    Modifies self object.
    """
    raise NotImplementedError


  def basicMeetOp(self, other: types.T) -> Opt[Tuple[types.T, ChangedT]]:
    assert self.__class__ == other.__class__, f"{self}, {other}"
    tup = basicMeetOp(self, other)
    if tup: return tup

    #assert self.val and other.val, f"self: {self.val}, other: {other.val}"
    return None  # can't compute


  def basicLessThanTest(self, other: 'DataLT') -> Opt[bool]:
    """A basic less than test common to all lattices.
    If this fails the lattices can do more complicated tests.
    This function does some common assertion tests to ensure correctness.
    """
    assert self.__class__ == other.__class__, f"{self}, {other}"
    lt = basicLessThanTest(self, other)
    if lt is not None: return lt

    #assert self.val and other.val, f"{self}, {other}"
    return None  # i.e. can't decide


  def basicEqualTest(self, other: 'DataLT') -> Opt[bool]:
    """A basic equality test common to all lattices.
    If this fails the lattices can do more complicated tests.
    """
    assert self.__class__ == other.__class__, f"{self}, {other}"
    equal = basicEqualsTest(self, other)
    if equal is not None: return equal

    #assert self.val and other.val, f"{self}, {other}"
    return None  # i.e. can't decide


  def __lt__(self, other):
    raise NotImplementedError()


  def __eq__(self, other):
    raise NotImplementedError()


  def __hash__(self):
    raise NotImplementedError()


  def getCopy(self) -> 'DataLT':
    raise NotImplementedError()


  def __str__(self):
    if self.top: return "Top"
    if self.bot: return "Bot"
    return f"DataLT({self.val})"


  def __repr__(self):
    return self.__str__()


def mergeAll(values: Iterable[BoundLatticeLT]) -> BoundLatticeLT:
  """Takes meet of all the values of LatticeLT type.
  All values must be the same type."""
  assert values, f"{values}"
  result = None
  for val in values:
    if result is not None:
      result, _ = result.meet(val)
    else:
      result = val
    if result.bot: break  # an optimization
  return result  # type: ignore


def basicMeetOp(first: types.T, second: types.T) -> Opt[Tuple[types.T, ChangedT]]:
  """A basic meet operation common to all lattices.
  If this fails the lattices can do more complicated operations.
  """
  if first is second: return first, not Changed
  if first.bot: return first, not Changed
  if second.top: return first, not Changed
  if second.bot: return second, Changed
  if first.top: return second, Changed
  if first < second: return first, not Changed
  if second < first: return second, Changed
  return None  # i.e. can't compute


def basicLessThanTest(first: LatticeLT, second: LatticeLT) -> Opt[bool]:
  """A basic less than test common to all lattices.
  If this fails the lattices can do more complicated tests.
  """
  if first.bot: return True
  if second.top: return True
  if second.bot: return False
  if first.top: return False
  # assert first.val and second.val, f"{first}, {second}"
  return None  # i.e. can't decide


def basicEqualsTest(first: LatticeLT, second: LatticeLT) -> Opt[bool]:
  """A basic equality test common to all lattices.
  If this fails the lattices can do more complicated tests.
  """
  if first is second: return True
  fTop, fBot, sTop, sBot = first.top, first.bot, second.top, second.bot
  if fTop and sTop: return True
  if fBot and sBot: return True
  if fTop or fBot or sTop or sBot: return False
  # assert first.val and second.val, f"{first}, {second}"
  return None  # i.e. can't decide


def getBasicString(obj: LatticeLT) -> Opt[str]:
  """Utility function to convert Top/Bot lattice values to a readable string."""
  if obj.bot: return "Bot"
  if obj.top: return "Top"
  return None


