#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The analysis' simplification(Sim)/evaluation interface."""

import logging

LOG = logging.getLogger("span")

from typing import List, Optional as Opt, Any, Dict, Set, Tuple
from span.util.logger import LS
import span.ir.types as types
from span.api.lattice import Changed, NoChange, ChangeL, LatticeLT
import span.ir.expr as expr
import span.api.dfv as dfv

import span.util.messages as msg

# simplification function names (that contain '__to__' in their name)
SimNameT = str


################################################
# BOUND START: Simplification_lattice.
################################################

class SimL(LatticeLT):
  """Base class for all simplification results."""
  _theTop: Opt['SimL'] = None  # SimPending
  _theBot: Opt['SimL'] = None  # SimFailed

  __slots__ : List[str] = ["val"]

  def __init__(self,
      val: Opt[Any] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if val is None and not (bot or top):
      msg = "Invalid SimL object creation arguments."
      if LS: LOG.error(msg)
      raise ValueError(msg)
    super().__init__(top, bot)
    self.val = val


  def meet(self,
      other: 'SimL'
  ) -> Tuple['SimL', ChangeL]:
    if self.bot: return self, NoChange
    if other.bot: return other, Changed
    if other.top: return self, NoChange
    if self.top: return other, Changed

    if self.val == other.val: return self, NoChange
    return self.getBot(), Changed


  def join(self,
      other: 'SimL'
  ) -> Tuple['SimL', ChangeL]:
    if self.top: return self, NoChange
    if other.top: return other, Changed
    if other.bot: return self, NoChange
    if self.bot: return other, Changed

    if self.val == other.val: return self, NoChange
    return self.getBot(), Changed


  def __lt__(self,
      other: 'SimL'
  ) -> bool:
    if self.bot: return True
    if other.bot: return False
    if other.top: return True
    if self.top: return False
    assert self.val is not None and other.val is not None, \
      "Value set must have valid value."
    if self.val == other.val: return True
    return False


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, SimL):
      return NotImplemented
    if self.top and other.top: return True
    if self.bot and other.bot: return True
    if self.val is not None or other.val is not None:
      return self.val == other.val
    return False


  def __hash__(self):
    return hash((self.top, self.bot))


  @classmethod
  def getTop(cls) -> 'SimL':
    if cls._theTop is None:
      cls._theTop = SimL(top=True)
    return cls._theTop


  @classmethod
  def getBot(cls) -> 'SimL':
    if cls._theBot is None:
      cls._theBot = SimL(bot=True)
    return cls._theBot


SimPending = SimL.getTop()
SimFailed = SimL.getBot()


class SimToVarL(SimL):
  """For simplification to a set of vars (increasing set size)."""
  _theTop: Opt['SimToVarL'] = None  # SimToVarPending
  _theBot: Opt['SimToVarL'] = None  # SimToVarFailed

  __slots__ : List[str] = []

  def __init__(self,
      val: Opt[Set[types.VarNameT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if val is None and not (bot or top):
      msg = "Invalid SimToVarL object creation arguments."
      if LS: LOG.error(msg)
      raise ValueError(msg)
    super().__init__(val, top, bot)
    self.val: Opt[Set[types.VarNameT]] = val


  def meet(self, other) -> Tuple['SimToVarL', ChangeL]:
    assert isinstance(other, SimToVarL), f"{other}"
    if self.bot: return self, NoChange
    if other.bot: return other, Changed
    if other.top: return self, NoChange
    if self.top: return other, Changed

    assert self.val is not None and other.val is not None
    if len(self.val) > len(other.val):
      if self.val > other.val:
        return self, NoChange
    else:
      if self.val <= other.val:
        return other, Changed

    return self.getBot(), Changed


  def join(self, other) -> Tuple['SimToVarL', ChangeL]:
    assert isinstance(other, SimToVarL), f"{other}"
    if self.top: return self, NoChange
    if other.bot: return self, NoChange
    if other.top: return other, Changed
    if self.bot: return other, Changed

    assert self.val is not None and other.val is not None
    if len(self.val) > len(other.val):
      if self.val > other.val:
        return other, Changed
    else:
      if self.val <= other.val:
        return self, NoChange

    return self.getTop(), Changed


  def __lt__(self, other) -> bool:
    assert isinstance(other, SimToVarL), f"{other}"
    if self.bot: return True
    if other.bot: return False
    if other.top: return True
    if self.top: return False
    assert self.val and other.val, "Value set must have valid value."
    if other.val <= self.val: return True
    return False


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, SimToVarL):
      return NotImplemented
    if self.top and other.top: return True
    if self.bot and other.bot: return True
    if self.top or self.bot or other.top or other.bot: return False
    assert self.val and other.val, "Value set must have valid value."
    return self.val == other.val


  def __hash__(self):
    return hash((self.top, self.bot))


  @classmethod
  def getTop(cls) -> 'SimToVarL':
    if cls._theTop is None:
      cls._theTop = SimToVarL(top=True)
    return cls._theTop


  @classmethod
  def getBot(cls) -> 'SimToVarL':
    if cls._theBot is None:
      cls._theBot = SimToVarL(bot=True)
    return cls._theBot


  def __str__(self):
    if self.top: return "SimToVarPending"
    if self.bot: return "SimToVarFailed"
    return f"SimToVarL({self.val})"


  def __repr__(self):
    return self.__str__()


SimToVarPending = SimToVarL.getTop()
SimToVarFailed = SimToVarL.getBot()


class SimToLiveL(SimL):
  """For simplification to a set of vars (increasing set size)."""
  _theTop: Opt['SimToLiveL'] = None  # SimToVarPending
  _theBot: Opt['SimToLiveL'] = None  # SimToVarFailed

  __slots__ : List[str] = []

  def __init__(self,
      val: Opt[Set[types.VarNameT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if val is None and not (bot or top):
      msg = "Invalid SimToLiveL object creation arguments."
      if LS: LOG.error(msg)
      raise ValueError(msg)
    super().__init__(val, top, bot)


  def meet(self, other) -> Tuple['SimToLiveL', ChangeL]:
    assert isinstance(other, SimToLiveL), f"{other}"
    if self.bot: return self, NoChange
    if other.bot: return other, Changed
    if other.top: return self, NoChange
    if self.top: return other, Changed

    assert self.val is not None and other.val is not None
    if len(self.val) > len(other.val):
      if self.val > other.val:
        return self, NoChange
    else:
      if self.val <= other.val:
        return other, Changed

    return self.getBot(), Changed


  def join(self, other) -> Tuple['SimToLiveL', ChangeL]:
    assert isinstance(other, SimToLiveL), f"{other}"
    if self.top: return self, NoChange
    if other.bot: return self, NoChange
    if other.top: return other, Changed
    if self.bot: return other, Changed

    assert self.val is not None and other.val is not None
    if len(self.val) > len(other.val):
      if self.val > other.val:
        return other, Changed
    else:
      if self.val <= other.val:
        return self, NoChange

    return self.getTop(), Changed


  def __lt__(self, other) -> bool:
    assert isinstance(other, SimToLiveL), f"{other}"
    if self.bot: return True
    if other.bot: return False
    if other.top: return True
    if self.top: return False

    assert self.val is not None and other.val is not None
    if self.val >= other.val: return True
    return False


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, SimToLiveL):
      return NotImplemented
    if self.top and other.top: return True
    if self.bot and other.bot: return True
    if self.top or self.bot or other.top or other.bot: return False
    assert self.val and other.val, "Value set must have valid value."
    return self.val == other.val


  @classmethod
  def getTop(cls) -> 'SimToLiveL':
    if cls._theTop is None:
      cls._theTop = SimToLiveL(top=True)
    return cls._theTop


  @classmethod
  def getBot(cls) -> 'SimToLiveL':
    if cls._theBot is None:
      cls._theBot = SimToLiveL(bot=True)
    return cls._theBot


  def __str__(self):
    if self.top: return "SimToLivePending"
    if self.bot: return "SimToLiveFailed"
    return f"SimToLiveL({self.val})"


  def __repr__(self):
    return self.__str__()


SimToLivePending = SimToLiveL.getTop()
SimToLiveFailed = SimToLiveL.getBot()


class SimToNumL(SimL):
  """For simplification to a single value.

  Sim to bools has a separate lattice (SimToBoolL).
  """
  _theTop: Opt['SimToNumL'] = None  # SimToNumPending
  _theBot: Opt['SimToNumL'] = None  # SimToNumFailed

  __slots__ : List[str] = []

  def __init__(self,
      val: Opt[types.NumericT] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if val is None and not (bot or top):
      msg = "Invalid SimToNumL object creation arguments."
      if LS: LOG.error(msg)
      raise ValueError(msg)
    super().__init__(val, top, bot)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, SimToNumL):
      return NotImplemented
    if self.top and other.top: return True
    if self.bot and other.bot: return True
    if self.top or self.bot or other.top or other.bot: return False
    assert self.val and other.val, "Value set must have valid value."
    return self.val == other.val


  def __str__(self):
    if self.top: return "SimToNumPending"
    if self.bot: return "SimToNumFailed"
    return f"SimToNumL({self.val})"


  def __repr__(self):
    return self.__str__()


  @classmethod
  def getTop(cls) -> 'SimToNumL':
    if cls._theTop is None:
      cls._theTop = SimToNumL(top=True)
    return cls._theTop


  @classmethod
  def getBot(cls) -> 'SimToNumL':
    if cls._theBot is None:
      cls._theBot = SimToNumL(bot=True)
    return cls._theBot


SimToNumPending = SimToNumL.getTop()
SimToNumFailed = SimToNumL.getBot()


class SimToNumSetL(SimL):
  """For simplification to a set of values.
  This is a better alternative to SimToNumL.

  Sim to bools has a separate lattice (SimToBoolL).
  """
  _theTop: Opt['SimToNumSetL'] = None  # SimToNumSetPending
  _theBot: Opt['SimToNumSetL'] = None  # SimToNumSetFailed
  _maxSize: int = 5  # the max size for the set of values

  __slots__ : List[str] = []

  def __init__(self,
      val: Opt[Set[types.NumericT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if val is None and not (bot or top):
      msg = "Invalid SimToNumSetL object creation arguments."
      if LS: LOG.error(msg)
      raise ValueError(msg)
    super().__init__(val, top, bot)


  def __str__(self):
    if self.top: return "SimToNumSetPending"
    if self.bot: return "SimToNumSetFailed"
    return f"SimToNumSetL({self.val})"


  def __repr__(self):
    return self.__str__()


  @classmethod
  def getTop(cls) -> 'SimToNumSetL':
    if cls._theTop is None:
      cls._theTop = SimToNumSetL(top=True)
    return cls._theTop


  @classmethod
  def getBot(cls) -> 'SimToNumSetL':
    if cls._theBot is None:
      cls._theBot = SimToNumSetL(bot=True)
    return cls._theBot


SimToNumSetPending = SimToNumSetL.getTop()
SimToNumSetFailed = SimToNumSetL.getBot()


class SimToNilL(SimL):
  """For simplification to a Nil value."""
  _theTop: Opt['SimToNilL'] = None  # SimToNilPending
  _theNil: Opt['SimToNilL'] = None  # SimToNilSuccessful
  _theBot: Opt['SimToNilL'] = None  # SimToNilFailed

  __slots__ : List[str] = ["nil"]

  def __init__(self,
      nil: Opt[bool] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if nil is None and not (bot or top):
      msg = "Invalid SimToNilL object creation arguments."
      if LS: LOG.error(msg)
      raise ValueError(msg)
    super().__init__(nil, top, bot)
    self.nil = nil


  def __str__(self):
    if self.top:
      return "SimToNilPending."
    if self.bot:
      return "SimToNilFailed."
    return "SimToNilSuccessful."


  @classmethod
  def getTop(cls) -> 'SimToNilL':
    if cls._theTop is None:
      cls._theTop = SimToNilL(top=True)
    return cls._theTop


  @classmethod
  def getNil(cls) -> 'SimToNilL':
    if cls._theNil is None:
      cls._theNil = SimToNilL(nil=True)
    return cls._theNil


  @classmethod
  def getBot(cls) -> 'SimToNilL':
    if cls._theBot is None:
      cls._theBot = SimToNilL(bot=True)
    return cls._theBot


SimToNilPending = SimToNilL.getTop()
SimToNilSuccessful = SimToNilL.getNil()
SimToNilFailed = SimToNilL.getBot()


class SimToBoolL(SimL):
  """For simplification to a boolean value."""
  _theTop: Opt['SimToBoolL'] = None  # SimToBoolPending
  _theTrue: Opt['SimToBoolL'] = None  # SimToTrueSuccess
  _theFalse: Opt['SimToBoolL'] = None  # SimToFalseSuccess
  _theBot: Opt['SimToBoolL'] = None  # SimToBoolFailed

  __slots__ : List[str] = []

  def __init__(self,
      val: Opt[bool] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    if val is None and not (bot or top):
      msg = "Invalid SimToBoolL object creation arguments."
      if LS: LOG.error(msg)
      raise ValueError(msg)
    super().__init__(val, top, bot)


  def __str__(self):
    if self.top: return "SimToBoolPending."
    if self.bot: return "SimToBoolFailed."
    if self.val == True: return "SimToTrueSuccessful"
    if self.val == False: return "SimToFalseSuccessful"
    assert False, msg.CONTROL_HERE_ERROR


  def __repr__(self):
    return self.__str__()


  @classmethod
  def getTop(cls) -> 'SimToBoolL':
    if cls._theTop is None:
      cls._theTop = SimToBoolL(top=True)
    return cls._theTop


  @classmethod
  def getTrue(cls) -> 'SimToBoolL':
    if cls._theTrue is None:
      cls._theTrue = SimToBoolL(val=True)
    return cls._theTrue


  @classmethod
  def getFalse(cls) -> 'SimToBoolL':
    if cls._theFalse is None:
      cls._theFalse = SimToBoolL(val=False)
    return cls._theFalse


  @classmethod
  def getBot(cls) -> 'SimToBoolL':
    if cls._theBot is None:
      cls._theBot = SimToBoolL(bot=True)
    return cls._theBot


SimToBoolPending = SimToBoolL.getTop()
SimToTrueSuccessful = SimToBoolL.getTrue()
SimToFalseSuccessful = SimToBoolL.getFalse()
SimToBoolFailed = SimToBoolL.getBot()


################################################
# BOUND END  : Simplification_lattice.
################################################

################################################
# BOUND START: Simplification_base_class.
################################################

class SimAT:
  """Simplification functions to be (optionally) overridden.

  For convenience, analysis.AnalysisAT inherits this class.
  So the user may only inherit AnalysisAT class, and
  override functions in this class only if the
  analysis works as a simplifier too.

  The second argument, nodeDfv, if its None,
  means that the return value should be either
  Pending if the expression provided
  can be possibly simplified by the analysis,
  or Failed if the expression cannot be simplified
  given any data flow value.
  """

  __slots__ : List[str] = []

  def Node__to__Nil(self,
      node: types.NodeIdT,
      nodeDfv: Opt[dfv.NodeDfvL] = None,
  ) -> SimToNilL:
    """Node is simplified to Nil if its basically unreachable."""
    raise NotImplementedError()


  def LhsVar__to__Nil(self,
      e: expr.VarE,
      nodeDfv: Opt[dfv.NodeDfvL] = None,
  ) -> SimToLiveL:
    """Returns a set of live variables at out of the node."""
    raise NotImplementedError()


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[dfv.NodeDfvL] = None
  ) -> SimToNumL:
    """Simplify to a single literal if the expr can take that value."""
    raise NotImplementedError()


  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[dfv.NodeDfvL] = None
  ) -> SimToNumL:
    """Simplify to a single literal if the variable can take that value."""
    raise NotImplementedError()


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[dfv.NodeDfvL] = None
  ) -> SimToBoolL:
    """Simplify conditional jump to unconditional jump."""
    raise NotImplementedError()


  def Deref__to__Vars(self,
      e: expr.VarE,
      nodeDfv: Opt[dfv.NodeDfvL] = None
  ) -> SimToVarL:
    """Simplify a deref expr de-referencing varName
    to a set of var pointees."""
    raise NotImplementedError()


################################################
# BOUND END  : Simplification_base_class.
################################################

def extractSimNames() -> Set[str]:
  """returns set of expr simplification func names (these names have `__to__` in them)."""
  tmp = set()
  for memberName in SimAT.__dict__:
    if memberName.find("__to__") >= 0:
      tmp.add(memberName)
  return tmp


simNames: Set[str] = extractSimNames()

Node__to__Nil__Name: str = SimAT.Node__to__Nil.__name__
LhsVar__to__Nil__Name: str = SimAT.LhsVar__to__Nil.__name__
Num_Var__to__Num_Lit__Name: str = SimAT.Num_Var__to__Num_Lit.__name__
Cond__to__UnCond__Name: str = SimAT.Cond__to__UnCond.__name__
Num_Bin__to__Num_Lit__Name: str = SimAT.Num_Bin__to__Num_Lit.__name__
Deref__to__Vars__Name: str = SimAT.Deref__to__Vars.__name__

# maps the simplification names to their failed values
failedSimValueMap: Dict[str, SimL] = {
  Node__to__Nil__Name:        SimToNilFailed,
  LhsVar__to__Nil__Name:      SimToLiveFailed,
  Num_Var__to__Num_Lit__Name: SimToNumFailed,
  Cond__to__UnCond__Name:     SimToBoolFailed,
  Num_Bin__to__Num_Lit__Name: SimToNumFailed,
  Deref__to__Vars__Name:      SimToVarFailed,
}

pendingSimValueMap: Dict[str, SimL] = {
  Node__to__Nil__Name:        SimToNilPending,
  LhsVar__to__Nil__Name:      SimToLivePending,
  Num_Var__to__Num_Lit__Name: SimToNumPending,
  Cond__to__UnCond__Name:     SimToBoolPending,
  Num_Bin__to__Num_Lit__Name: SimToNumPending,
  Deref__to__Vars__Name:      SimToVarPending,
}

simDirnMap = {  # the IN/OUT information needed for the sim
  Node__to__Nil__Name:        types.Forward,  # means dfv at IN is needed
  Num_Var__to__Num_Lit__Name: types.Forward,
  Cond__to__UnCond__Name:     types.Forward,
  Num_Bin__to__Num_Lit__Name: types.Forward,
  Deref__to__Vars__Name:      types.Forward,
  LhsVar__to__Nil__Name:      types.Backward, # means dfv at OUT is needed
}
