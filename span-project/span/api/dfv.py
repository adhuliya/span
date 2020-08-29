#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The analysis' common data flow value declarations."""

from typing import Tuple, Optional as Opt, Dict, Any, Set,\
                   Type, TypeVar, List, cast, Callable
import logging
import io

LOG = logging.getLogger("span")

from span.util.logger import LS
from span.api.lattice import LatticeLT, DataLT, ChangeL, Changed, NoChange, BoundLatticeLT
from span.util.util import AS
import span.ir.constructs as constructs
import span.ir.types as types
import span.ir.conv as irConv
import span.ir.ir as ir


################################################
# BOUND START: Node dfv related lattice
################################################

class NewOldL(LatticeLT):
  """Flags a change in data flow values."""
  _new_in_obj: Opt['NewOldL'] = None
  _new_out_obj: Opt['NewOldL'] = None
  _new_inout_obj: Opt['NewOldL'] = None
  _old_inout_obj: Opt['NewOldL'] = None

  __slots__ : List[str] = ["_newIn", "_newOut"]

  def __init__(self,
      newIn: ChangeL,
      newOut: ChangeL
  ) -> None:
    top = not (newIn or newOut)
    bot = bool(newIn and newOut)
    super().__init__(top=top, bot=bot)

    self._newIn = newIn
    self._newOut = newOut


  def meet(self, other) -> Tuple['NewOldL', ChangeL]:
    assert isinstance(other, NewOldL), f"{other}"
    if self.bot: return self, NoChange
    if other.bot: return other, Changed
    if other.top: return self, NoChange
    if self.top: return other, Changed
    if self == other: return self, NoChange

    return self.getNewInOut(), Changed


  def __lt__(self, other) -> bool:
    assert isinstance(other, NewOldL), f"{other}"
    if self.bot:  return True
    if other.bot: return False
    if other.top: return True
    if self.top:  return False
    return self == other


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, NewOldL):
      return NotImplemented
    return self._newIn == other._newIn and self._newOut == other._newOut


  def __str__(self):
    return f"(IN={self._newIn}, OUT={self._newOut})"


  def __repr__(self):
    return self.__str__()


  @classmethod
  def getNewOldObj(cls, isNewIn=False, isNewOut=False) -> 'NewOldL':
    if not isNewIn and not isNewOut:
      return cls.getOldInOut()
    elif not isNewIn and isNewOut:
      return cls.getNewOut()
    elif isNewIn and not isNewOut:
      return cls.getNewIn()
    elif isNewIn and isNewOut:
      return cls.getNewInOut()
    raise ValueError()


  @property
  def isNewIn(self) -> bool:
    return bool(self._newIn)


  @property
  def isNewOut(self) -> bool:
    return bool(self._newOut)


  @property
  def isNewInOut(self) -> bool:
    return bool(self._newIn and self._newIn)


  @property
  def isOldInOut(self) -> bool:
    return not (self._newIn or self._newOut)


  def __bool__(self) -> bool:
    return bool(self._newIn or self._newOut)


  @classmethod
  def getNewIn(cls) -> 'NewOldL':
    if not cls._new_in_obj:
      cls._new_in_obj = NewOldL(Changed, NoChange)
    return cls._new_in_obj


  @classmethod
  def getNewOut(cls) -> 'NewOldL':
    if not cls._new_out_obj:
      cls._new_out_obj = NewOldL(NoChange, Changed)
    return cls._new_out_obj


  @classmethod
  def getNewInOut(cls) -> 'NewOldL':
    new_inout_obj = cls._new_inout_obj
    if new_inout_obj is not None:
      return new_inout_obj
    new_inout_obj = NewOldL(Changed, Changed)
    cls._new_inout_obj = new_inout_obj
    return new_inout_obj


  @classmethod
  def getOldInOut(cls) -> 'NewOldL':
    if not cls._old_inout_obj:
      cls._old_inout_obj = NewOldL(NoChange, NoChange)
    return cls._old_inout_obj


  @classmethod
  def make(cls,
      new_in: ChangeL,
      new_out: ChangeL
  ) -> 'NewOldL':
    if new_in:
      if new_out:
        return cls.getNewInOut()
      return cls.getNewIn()
    else:
      if new_out:
        return cls.getNewOut()
      return cls.getOldInOut()


OLD_INOUT = NewOldL.getOldInOut()
NEW_IN = NewOldL.getNewIn()
NEW_OUT = NewOldL.getNewOut()
NEW_INOUT = NewOldL.getNewInOut()


class NodeDfvL(LatticeLT):
  """
  Stores the data flow value at IN and OUT of a node.

  Since IN and OUT are objects of (respective analysis') lattices,
  this object also behaves like a lattice.
  """
  __slots__ : List[str] = ["dfvIn", "dfvOut", "dfvOutTrue", "dfvOutFalse"]


  def __init__(self,
      dfvIn: DataLT,
      dfvOut: Opt[DataLT] = None,
      dfvOutTrue: Opt[DataLT] = None,
      dfvOutFalse: Opt[DataLT] = None,
  ) -> None:
    self.dfvIn: DataLT = dfvIn
    # only used for out of conditional (i.e. if) nodes
    if dfvOutFalse is None or dfvOutTrue is None:
      assert dfvOutFalse is None and dfvOutTrue is None,\
        f"{dfvOutFalse}, {dfvOutTrue}"
      assert dfvOut is not None, f"{dfvIn}"
      self.dfvOut: DataLT = dfvOut
      self.dfvOutFalse: DataLT = dfvOut
      self.dfvOutTrue: DataLT = dfvOut
    elif dfvOut is None:
      assert dfvOutFalse is not None and dfvOutTrue is not None
      self.dfvOut, _ = dfvOutFalse.meet(dfvOutTrue)
      self.dfvOutFalse = dfvOutFalse
      self.dfvOutTrue = dfvOutTrue
    else:
      self.dfvOut = dfvOut
      self.dfvOutFalse = dfvOutFalse
      self.dfvOutTrue = dfvOutTrue

    assert self.dfvIn and self.dfvOut, f"{self}"
    super().__init__(top=bool(self.dfvIn.top and self.dfvOut.top),
                     bot=bool(self.dfvIn.bot and self.dfvOut.bot))


  def meet(self, other) -> Tuple['NodeDfvL', ChangeL]:
    assert isinstance(other, NodeDfvL), f"{other}"
    if self is other:
      return self, NoChange

    chOut = NoChange
    chIn = NoChange

    if self.dfvIn is other.dfvIn:  # since data flow values are treated immutable
      dfvIn = self.dfvIn
    else:
      dfvIn, chIn = self.dfvIn.meet(other.dfvIn)

    # dfvOut = dfvOutTrue = dfvOutFalse = None
    # if self.dfvOut is not None:
    if self.dfvOut is other.dfvOut:
      dfvOut = self.dfvOut
    else:
      dfvOut, chOutTmp = self.dfvOut.meet(other.dfvOut)
      chOut, _ = chOut.meet(chOutTmp)

    if other.dfvOut is other.dfvOutTrue:
      dfvOutTrue = dfvOut
    else:
      dfvOutTrue, chOutTmp = self.dfvOutTrue.meet(other.dfvOutTrue)
      chOut, _ = chOut.meet(chOutTmp)

    if other.dfvOut is other.dfvOutFalse:
      dfvOutFalse = dfvOut
    else:
      dfvOutFalse, chOutTmp = self.dfvOutFalse.meet(other.dfvOutFalse)
      chOut, _ = chOut.meet(chOutTmp)

    if LS: LOG.debug("NodeDfv (meet with prev nodeDfv): In: %s, Out: %s.", chIn, chOut)
    return NodeDfvL(dfvIn, dfvOut, dfvOutTrue, dfvOutFalse), chIn.meet(chOut)[0]


  def getCopy(self):
    dfvInCopy = self.dfvIn.getCopy()
    dfvOutCopy = self.dfvOut.getCopy()
    if self.dfvOut is self.dfvOutTrue:
      assert self.dfvOut is self.dfvOutFalse
      dfvOutTrueCopy, dfvOutFalseCopy = dfvOutCopy, dfvOutCopy
    else:
      dfvOutTrueCopy = self.dfvOutTrue.getCopy()
      dfvOutFalseCopy = self.dfvOutFalse.getCopy()

    return NodeDfvL(dfvInCopy, dfvOutCopy, dfvOutTrueCopy, dfvOutFalseCopy)


  def __lt__(self, other: 'NodeDfvL') -> bool:
    if self.dfvIn < other.dfvIn and self.dfvOut < other.dfvOut:
      return True
    return False


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, NodeDfvL):
      raise NotImplemented
    return self.dfvIn == other.dfvIn and self.dfvOut == other.dfvOut


  def __hash__(self):
    return hash(self.dfvIn) ^ hash(self.dfvOut)


  def __str__(self):
    if self.dfvOutTrue is self.dfvOutFalse and self.dfvOut is self.dfvOutTrue:
      if self.dfvIn is self.dfvOut:
        return f"IN == OUT: {self.dfvIn}"
      else:
        return f"IN: {self.dfvIn}, OUT: {self.dfvOut}"
    else:
      return f"IN: {self.dfvIn}, OUT: {self.dfvOut}, TRUE: {self.dfvOutTrue}, FALSE: {self.dfvOutFalse}"


  def __repr__(self):
    return self.__str__()

################################################
# BOUND END  : Node dfv related lattice
################################################

################################################
# BOUND START: Common_OverallL
################################################

class ComponentL(DataLT):
  __slots__ : List[str] = []


  def __init__(self,
      func: constructs.Func,
      val: Any = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val: Opt[Any] = val

  def meet(self, other) -> Tuple['ComponentL', ChangeL]:
    raise NotImplementedError()


class OverallL(DataLT):
  """Common OverallL for numeric/value analyses."""
  __slots__ : List[str] = ["componentTop", "componentBot", "name"]


  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[types.VarNameT, ComponentL]] = None,
      top: bool = False,
      bot: bool = False,
      componentL: Type[ComponentL] = ComponentL,
      name: str = "",
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val: Opt[Dict[types.VarNameT, ComponentL]] = val
    assert componentL is not ComponentL, f"{func} {name}"
    self.componentTop = componentL(self.func, top=True)
    self.componentBot = componentL(self.func, bot=True)
    self.name = name


  def meet(self, other) -> Tuple['OverallL', ChangeL]:
    assert isinstance(other, OverallL), f"{other}"
    if self is other: return self, NoChange
    if self.bot: return self, NoChange
    if other.top: return self, NoChange
    if other.bot: return other, Changed
    if self.top: return other, Changed

    assert self.val and other.val
    if self.val == other.val: return self, NoChange

    # take meet of individual entities (variables)
    meet_val: Dict[types.VarNameT, ComponentL] = {}
    vars_set = {vName for vName in self.val.keys()}
    vars_set.update({vName for vName in other.val.keys()})
    bot = self.componentBot
    for vName in vars_set:
      dfv1: ComponentL = self.val.get(vName, bot)
      dfv2: ComponentL = other.val.get(vName, bot)
      if not (dfv1.bot or dfv2.bot): # do not store bot, as it is the default
        dfv3, _ = dfv1.meet(dfv2)
        if not dfv3.bot:
          meet_val[vName] = dfv3

    if meet_val:
      value = self.__class__(self.func, val=meet_val)
    else:
      value = self.__class__(self.func, bot=True)

    return value, Changed


  def __lt__(self,
      other: 'OverallL'
  ) -> bool:
    if self.bot: return True
    if other.top: return True
    if other.bot: return False
    if self.top: return False

    assert self.val and other.val, f"{self}, {other}"
    vNames = {vName for vName in self.val}
    vNames.update({vName for vName in other.val})
    bot = self.componentBot
    for vName in vNames:
      dfv1 = self.val.get(vName, bot)
      dfv2 = other.val.get(vName, bot)
      if not dfv1 < dfv2: return False
    return True


  def __eq__(self, other) -> bool:
    """strictly equal check."""
    if self is other:
      return True
    if not isinstance(other, self.__class__):
      return NotImplemented

    sTop, sBot, oTop, oBot = self.top, self.bot, other.top, other.bot
    if sTop and oTop: return True
    if sBot and oBot: return True
    if sTop or sBot or oTop or oBot: return False

    # self and other are proper values
    assert self.val and other.val, f"{self.val}, {other.val}"
    vNames = {var for var in self.val}
    vNames.update(var for var in other.val)
    selfGetVal, otherGetVal = self.val.get, other.val.get
    bot = self.componentBot
    for vName in vNames:
      dfv1 = selfGetVal(vName, bot)
      dfv2 = otherGetVal(vName, bot)
      if not dfv1 == dfv2: return False
    return True


  def __hash__(self):
    val = {} if self.val is None else self.val
    hashThisVal = frozenset(val.items())
    return hash((self.func, hashThisVal, self.top, self.bot))


  def getVal(self,
      varName: types.VarNameT
  ) -> ComponentL:
    """returns entity lattice value."""
    if self.top: return self.componentTop
    if self.bot: return self.componentBot

    assert self.val, f"{self}"
    return self.val.get(varName, self.componentBot)


  def setVal(self,
      vName: types.VarNameT,
      val: ComponentL
  ) -> None:
    """Mutates current object."""
    if self.top and val.top: return
    if self.bot and val.bot: return

    if self.val is None: self.val = {}
    if self.top:
      for varName in self.getAllVars():
        self.val[varName] = self.componentTop

    self.top = self.bot = False  # if it was top/bot, then certainly its no more.
    if val.bot:
      if vName in self.val:
        del self.val[vName]  # since default is bot
        if not self.val:
          self.top, self.bot, self.val = False, True, None
    else:
      self.val[vName] = val


  def getCopy(self) -> 'OverallL':
    if self.top:
      return self.__class__(self.func, top=True)
    if self.bot:
      return self.__class__(self.func, bot=True)

    assert self.val is not None, f"{self}"
    return self.__class__(self.func, self.val.copy())


  def getAllVars(self) -> Set[types.VarNameT]:
    """Return a set of vars the analysis is tracking.
    One must override this method if variables are other
    than numeric.
    """
    return ir.getNamesEnv(self.func, numeric=True)


  def filterVals(self, varNames: Set[types.VarNameT]) -> None:
    """Mutates the self object.
    All variable names in varNames are set to Top.
    """
    if self.top or not varNames:
      return None

    if self.getAllVars() == varNames:
      self.top, self.bot, self.val = True, False, None
      return None

    self.val = self.val if self.val else {}
    if self.bot:
      self.bot = False

    val = self.val
    for vName in varNames:
      val[vName] = self.componentTop
    return None


  def __str__(self):
    if self.top: return "Top"
    if self.bot: return "Bot"

    assert self.val, f"{self.val}"
    string = io.StringIO()
    string.write("{")
    prefix = None
    for key in self.val:
      # if not irConv.isUserVar(key): # added for ACM Winter School
      #   continue
      # if irConv.isDummyVar(key):  # skip printing dummy variables
      #   continue
      if prefix: string.write(prefix)
      prefix = ", "
      name = irConv.simplifyName(key)
      string.write(f"{name}: {self.val[key]}")
    string.write("}")
    return string.getvalue()


  def __repr__(self):
    if self.top: return f"{self.name}.OverallL({self.func}, top=True)"
    if self.bot: return f"{self.name}.OverallL({self.func}, bot=True)"

    string = io.StringIO()
    string.write("{self.name}.OverallL({")
    prefix = ""
    for key in self.val:
      string.write(prefix)
      prefix = ", "
      string.write(f"{key!r}: {self.val[key]!r}")
    string.write("})")
    return string.getvalue()



################################################
# BOUND END  : Common_OverallL
################################################

################################################
# BOUND START: Convenience_Functions
################################################

def getIpaBoundaryInfo(
    func: constructs.Func,
    nodeDfv: NodeDfvL,
    componentBot: ComponentL,
    getAllVars: Callable[[], Set[types.VarNameT]],
) -> NodeDfvL:
  """Returns the IPA boundary info for the func.
  It removes the variables that are not in the env
  of func."""
  dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
  dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())
  dfvIn.func, dfvOut.func = func, func

  vNames: Set[types.VarNameT] = getAllVars()

  if dfvIn.val:
    for value in dfvIn.val.values():
      value.func = func
    for key in list(dfvIn.val.keys()):
      if key not in vNames:
        dfvIn.setVal(key, componentBot) # remove key
  if dfvOut.val:
    for value in dfvOut.val.values():
      value.func = func
    for key in list(dfvOut.val.keys()):
      if key not in vNames:
        dfvOut.setVal(key, componentBot) # remove key

  return NodeDfvL(dfvIn, dfvOut)


def Filter_Vars(
    func: constructs.Func,
    varNames: Set[types.VarNameT],
    nodeDfv: NodeDfvL
) -> NodeDfvL:
  dfvIn = cast(OverallL, nodeDfv.dfvIn)

  if not varNames or dfvIn.top:  # i.e. nothing to filter or no DFV to filter == Nop
    return NodeDfvL(dfvIn, dfvIn)  # = NopI

  newDfvOut = dfvIn.getCopy()
  newDfvOut.filterVals(ir.filterNamesNumeric(func, varNames))
  return NodeDfvL(dfvIn, newDfvOut)


################################################
# BOUND END  : Convenience_Functions
################################################


