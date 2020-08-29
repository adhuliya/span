#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Defines the base lattice class."""

import logging

LOG = logging.getLogger("span")

from typing import Tuple, Any, List, TypeVar, Optional as Opt, Sequence as Seq, Iterable

from span.util.messages import TOP_BOT_BOTH
import span.ir.constructs as obj

import span.ir.types as types


# This class cannot subclass LatticeT (since LatticeT uses it),
# but it is a proper lattice.
class ChangeL:
  """
  Lattice with two elements only.
  top: change = False, signifies NoChange in value.
  bot: change = True, signifies Change in value.
  """
  _top: Opt['ChangeL'] = None
  _bot: Opt['ChangeL'] = None
  __slots__ : List[str] = ["_change"]


  def __init__(self,
      change: bool = False
  ) -> None:
    self._change = change


  @property
  def bot(self) -> bool:
    return self._change


  @property
  def top(self) -> bool:
    return not self._change


  @classmethod
  def getTop(cls):
    top = cls._top
    if top is not None: return top

    top = ChangeL(False)
    cls._top = top
    return top


  @classmethod
  def getBot(cls):
    bot = cls._bot
    if bot is not None: return bot

    bot = ChangeL(True)
    cls._bot = bot
    return bot


  @classmethod
  def make(cls, change: bool):
    """Create object of this class (avoids creation of redundant objects)."""
    if change: return cls.getBot()
    return cls.getTop()


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, ChangeL):
      return NotImplemented
    return self._change == other._change


  def meet(self,
      other: 'ChangeL'
  ) -> Tuple['ChangeL', 'ChangeL']:
    """change == True is bot."""
    if self is other: return self, NoChange
    if self.bot: return self, NoChange
    if other.bot: return other, Changed
    return self, NoChange


  def __bool__(self) -> bool:
    return self._change


  def __str__(self):
    if self._change: return "Changed"
    return "NoChange"


  def __repr__(self):
    return self.__str__()


NoChange: ChangeL = ChangeL.getTop()
Changed: ChangeL = ChangeL.getBot()


BoundLatticeLT = TypeVar('BoundLatticeLT', bound='LatticeLT')


class LatticeLT:
  """Base class for all Lattice except for lattice.ChangeL."""

  __slots__ : List[str] = ["top", "bot"]


  def __init__(self,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if bot and top:
      raise ValueError(f"{top}, {bot}")
    self.top = top
    self.bot = bot


  def meet(self, other) -> Tuple['LatticeLT', ChangeL]:
    """Calculates glb of the self and the other data flow value.

    Default implementation, assuming only top and bot exist (binary lattice).

    Args:
      other: the data flow value to calculate `meet` with.

    Returns:
      (Lattice, Changed): glb of self and dfv, and True if glb != self
    """
    return NotImplemented


  def getCopy(self) -> 'LatticeLT':
    """Return a copy of this lattice element."""
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
    if self.bot: return True
    if other.bot: return False
    return True  # both are top


  def __eq__(self, other) -> bool:
    """returns True if equal, False if not equal or incomparable.

    Default implementation, assuming only top and bot exist (binary lattice).
    """
    if self is other:
      return True
    if not isinstance(other, LatticeLT):
      return NotImplemented
    if self.top and other.top: return True
    if self.bot and other.bot: return True
    return False


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
    if not (self.top or self.bot):  # safety check
      assert val is not None
    self.func = func
    self.val = val
    if self.top or self.bot:  # top and bot get priority
      self.val = None


  def meet(self, other) -> Tuple['DataLT', ChangeL]:
    """Calculates glb of the self and the other data flow value.

    Note: It never modifies the 'self' or the 'other' data flow value.

    Args:
      other: the data flow value to calculate `meet` with.

    Returns:
      (Lattice, ChangeL): glb of self and dfv, and 'Changed' if glb != self
    """
    raise NotImplementedError()


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


def basicMeetOp(first: types.T, second: types.T) -> Opt[Tuple[types.T, ChangeL]]:
  """A basic meet operation common to all lattices.
  If this fails the lattices can do more complicated operations.
  """
  if first is second: return first, NoChange
  if first.bot: return first, NoChange
  if second.top: return first, NoChange
  if second.bot: return second, Changed
  if first.top: return second, Changed
  return None  # i.e. can't compute


def basicLessThanTest(first: LatticeLT, second: LatticeLT) -> Opt[bool]:
  """A basic less than test common to all lattices.
  If this fails the lattices can do more complicated tests.
  """
  if first.bot: return True
  if second.top: return True
  if second.bot: return False
  if first.top: return False
  return None  # i.e. can't decide


def basicEqualTest(first: LatticeLT, second: LatticeLT) -> Opt[bool]:
  """A basic equality test common to all lattices.
  If this fails the lattices can do more complicated tests.
  """
  if first is second:
    return True

  sTop, sBot, oTop, oBot = first.top, first.bot, second.top, second.bot
  if sTop and oTop: return True
  if sBot and oBot: return True
  if sTop or sBot or oTop or oBot: return False
  return None  # i.e. can't decide


def getBasicString(obj: LatticeLT) -> Opt[str]:
  if obj.bot: return "Bot"
  if obj.top: return "Top"
  return None
