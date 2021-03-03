#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The analysis' common data flow value declarations."""

from typing import Tuple, Optional as Opt, Dict, Any, Set,\
                   Type, TypeVar, List, cast, Callable
import logging
import io

from span.ir import tunit, conv
from span.ir.conv import isStringLitName

LOG = logging.getLogger("span")

from span.util.util import LS
import span.util.util as util
from span.api.lattice import\
  (LatticeLT, DataLT, ChangedT, Changed,
   BoundLatticeLT, basicMeetOp, basicLessThanTest,
   basicEqualsTest, getBasicString)
import span.ir.constructs as constructs
import span.ir.types as types
import span.ir.ir as ir
from span.ir.ir import filterNamesNumeric


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
      newIn: ChangedT,
      newOut: ChangedT
  ) -> None:
    top = not (newIn or newOut)
    bot = newIn and newOut
    super().__init__(top=top, bot=bot)

    self._newIn = newIn
    self._newOut = newOut


  def meet(self, other) -> Tuple['NewOldL', ChangedT]:
    assert isinstance(other, NewOldL), f"{other}"
    if self.bot: return self, not Changed
    if other.bot: return other, Changed
    if other.top: return self, not Changed
    if self.top: return other, Changed
    if self == other: return self, not Changed

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


  def orWith(self, other: 'NewOldL'):
    isNewIn = self.isNewIn or other.isNewIn
    isNewOut = self.isNewOut or other.isNewOut
    return self.getNewOldObj(isNewIn, isNewOut)


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
    return self._newIn


  @property
  def isNewOut(self) -> bool:
    return self._newOut


  @property
  def isNewInOut(self) -> bool:
    return self._newIn and self._newOut


  @property
  def isOldInOut(self) -> bool:
    return not (self._newIn or self._newOut)


  def __bool__(self) -> bool:
    return self._newIn or self._newOut


  @classmethod
  def getNewIn(cls) -> 'NewOldL':
    if not cls._new_in_obj:
      cls._new_in_obj = NewOldL(Changed, not Changed)
    return cls._new_in_obj


  @classmethod
  def getNewOut(cls) -> 'NewOldL':
    if not cls._new_out_obj:
      cls._new_out_obj = NewOldL(not Changed, Changed)
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
      cls._old_inout_obj = NewOldL(not Changed, not Changed)
    return cls._old_inout_obj


  @classmethod
  def make(cls,
      new_in: ChangedT,
      new_out: ChangedT
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
  __slots__ : List[str] = ["func", "dfvIn", "dfvOut", "dfvOutTrue", "dfvOutFalse"]


  def __init__(self,
      dfvIn: DataLT,
      dfvOut: Opt[DataLT] = None,
      dfvOutTrue: Opt[DataLT] = None,
      dfvOutFalse: Opt[DataLT] = None,
  ) -> None:
    self.dfvIn: DataLT = dfvIn
    self.func = dfvIn.func
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


  def meet(self, other) -> Tuple['NodeDfvL', ChangedT]:
    assert isinstance(other, NodeDfvL), f"{other}"
    if self is other:
      return self, not Changed

    chOut = not Changed
    chIn = not Changed

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
      chOut = chOut or chOutTmp

    if other.dfvOut is other.dfvOutTrue:
      dfvOutTrue = dfvOut
    else:
      dfvOutTrue, chOutTmp = self.dfvOutTrue.meet(other.dfvOutTrue)
      chOut = chOut or chOutTmp

    if other.dfvOut is other.dfvOutFalse:
      dfvOutFalse = dfvOut
    else:
      dfvOutFalse, chOutTmp = self.dfvOutFalse.meet(other.dfvOutFalse)
      chOut = chOut or chOutTmp

    if LS: LOG.debug("NodeDfv (meet with prev nodeDfv): In: %s, Out: %s.", chIn, chOut)
    return NodeDfvL(dfvIn, dfvOut, dfvOutTrue, dfvOutFalse), chIn or chOut


  def widen(self,
      other: 'NodeDfvL',
      ipa: bool = False,  # special case #IPA FIXME: is this needed?
  ) -> Tuple['NodeDfvL', ChangedT]:
    assert isinstance(other, NodeDfvL), f"{other}"
    if self is other:
      return self, not Changed

    chOut = not Changed
    chIn = not Changed

    if self.dfvIn is other.dfvIn:  # since data flow values are treated immutable
      dfvIn = self.dfvIn
    else:
      dfvIn, chIn = self.dfvIn.widen(other.dfvIn)

    # dfvOut = dfvOutTrue = dfvOutFalse = None
    # if self.dfvOut is not None:
    if self.dfvOut is other.dfvOut:
      dfvOut = self.dfvOut
    else:
      dfvOut, chOutTmp = self.dfvOut.widen(other.dfvOut)
      chOut = chOut or chOutTmp

    if other.dfvOut is other.dfvOutTrue:
      dfvOutTrue = dfvOut
    else:
      dfvOutTrue, chOutTmp = self.dfvOutTrue.widen(other.dfvOutTrue)
      chOut = chOut or chOutTmp

    if other.dfvOut is other.dfvOutFalse:
      dfvOutFalse = dfvOut
    else:
      dfvOutFalse, chOutTmp = self.dfvOutFalse.widen(other.dfvOutFalse)
      chOut = chOut or chOutTmp

    if LS: LOG.debug("NodeDfv (widen with prev nodeDfv): In: %s, Out: %s.", chIn, chOut)
    return NodeDfvL(dfvIn, dfvOut, dfvOutTrue, dfvOutFalse), chIn or chOut


  def checkInvariants(self, level: int = 0):
    self.dfvIn.checkInvariants(level)
    self.dfvOut.checkInvariants(level)


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
    idStr = f"(id:{id(self)})" if util.VV5 else ""
    sep = " ***** "
    if self.dfvOutTrue is self.dfvOutFalse and self.dfvOut is self.dfvOutTrue:
      if self.dfvIn is self.dfvOut:
        return f"{idStr} IN == OUT: {self.dfvIn}"
      else:
        return f"{idStr} IN: {self.dfvIn}, {sep} OUT: {self.dfvOut}"
    else:
      return f"{idStr} IN: {self.dfvIn}, {sep} OUT: {self.dfvOut}," \
             f" {sep} TRUE: {self.dfvOutTrue}, {sep} FALSE: {self.dfvOutFalse}"


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

  def meet(self, other) -> Tuple['ComponentL', ChangedT]:
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
    self.componentTop = componentL(self.func, top=True)
    self.componentBot = componentL(self.func, bot=True)
    if not (self.top or self.bot) and self.isDefaultValBot(): # safety check
      assert val is not None, f"{func}, {val}, {top}, {bot}"
    self.val: Opt[Dict[types.VarNameT, ComponentL]] = val
    assert componentL is not ComponentL,\
      f"Analysis should subclass dfv.ComponentL. Details: {func} {name}"
    self.name = name


  def meet(self, other) -> Tuple['OverallL', ChangedT]:
    assert isinstance(other, OverallL), f"{other}"

    tup = self.basicMeetOp(other)
    if tup: return tup

    # take meet of individual entities (variables)
    meet_val: Dict[types.VarNameT, ComponentL] = {}
    vNames = set(self.val.keys()) | set(other.val.keys())
    selfValGet, otherValGet = self.val.get, other.val.get
    defaultVal = self.getDefaultVal()

    for vName in vNames:
      dfv1: ComponentL = selfValGet(vName, defaultVal)
      dfv2: ComponentL = otherValGet(vName, defaultVal)
      dfv3, _ = dfv1.meet(dfv2)
      if dfv3 != defaultVal:
        meet_val[vName] = dfv3

    if meet_val:
      value = self.__class__(self.func, val=meet_val)
    elif self.isDefaultValBot():
      value = self.__class__(self.func, bot=True)
    elif self.isDefaultValTop():
      value = self.__class__(self.func, top=True)
    else:
      value = self.__class__(self.func, val=None) # useful

    return value, Changed


  def __lt__(self,
      other: 'OverallL'
  ) -> bool:
    lt = self.basicLessThanTest(other)
    if lt is not None: return lt

    vNames = set(self.val.keys()) | set(other.val.keys())
    defaultVal = self.getDefaultVal()
    selfValGet, otherValGet = self.val.get, other.val.get
    for vName in vNames:
      dfv1, dfv2 = selfValGet(vName, defaultVal), otherValGet(vName, defaultVal)
      if not (dfv1 < dfv2): return False
    return True


  @classmethod
  def isAcceptedType(cls,
      t: types.Type,
      name: Opt[types.VarNameT] = None,
  ) -> bool:
    """Returns True if the type of the instruction/variable is
    of interest to the analysis.
    By default it selects only Numeric types.
    """
    check1 = t.isNumeric()
    check2 = not isStringLitName(name) if name else True
    return check1 and check2


  @classmethod
  def getAllVars(cls, func: constructs.Func) -> Set[types.VarNameT]:
    """Gets all the variables of the accepted type."""
    names = ir.getNamesEnv(func)
    return ir.filterNames(func, names, cls.isAcceptedType)


  def __eq__(self, other) -> bool:
    """strictly equal check."""
    if not isinstance(other, self.__class__):
      return NotImplemented

    equal = self.basicEqualTest(other)
    if equal is not None: return equal

    vNames = set(self.val.keys()) | set(other.val.keys())
    defaultVal = self.getDefaultVal()
    selfGetVal, otherGetVal = self.val.get, other.val.get
    for vName in vNames:
      dfv1, dfv2 = selfGetVal(vName, defaultVal), otherGetVal(vName, defaultVal)
      if not dfv1 == dfv2: return False
    return True


  def __hash__(self):
    hashThisVal = None if self.val is None else frozenset(self.val.items())
    return hash((hashThisVal, self.top)) # , self.bot))


  def checkInvariants(self, level: int = 0):
    if level >= 1:
      if self.val:
        for k, v in self.val.items():
          v.checkInvariants()
          assert v is not None, f"{self.func.name}: {k}, {v}"


  def isDefaultValBot(self):
    return self.componentBot == self.getDefaultVal()


  def isDefaultValTop(self):
    return self.componentTop == self.getDefaultVal()


  def getDefaultVal(self,
      varName: Opt[types.VarNameT] = None  # None default is important
  ) -> Opt[ComponentL]:
    """Default value when a variable is not present in the map.
    Override this function if the default implementation is not suitable.
    """
    return self.componentBot


  def isDefaultVal(self,
      val: ComponentL,
      varName: Opt[types.VarNameT] = None,
  ) -> bool:
    return val == self.getDefaultVal(varName)


  def getVal(self,
      varName: types.VarNameT
  ) -> ComponentL:
    """returns entity lattice value."""
    if self.top: return self.componentTop
    if self.bot: return self.componentBot
    selfVal, defVal = self.val, self.getDefaultVal(varName)
    return selfVal.get(varName, defVal) if selfVal else defVal


  def setVal(self,
      varName: types.VarNameT,
      val: ComponentL
  ) -> None:
    """Mutates 'self'."""
    if self.top and val.top: return
    if self.bot and val.bot: return

    if self.val is None:
      if not (self.top or self.bot) and self.isDefaultVal(val, varName):
        return
      self.val = {}

    defaultVal = self.getDefaultVal(varName)
    if self.top and defaultVal != self.componentTop:
      top = self.componentTop
      self.val = {vName: top for vName in self.getAllVars(self.func)}
    if self.bot and defaultVal != self.componentBot:
      bot = self.componentBot
      self.val = {vName: bot for vName in self.getAllVars(self.func)}

    assert self.val is not None, f"{self}"
    self.top = self.bot = False  # if it was top/bot, then certainly its no more.
    topDefVal, botDefVal = self.isDefaultValTop(), self.isDefaultValBot()
    if self.isDefaultVal(val, varName):
      if varName in self.val:
        del self.val[varName]  # since default value
        if not self.val:
          self.val = None
          self.top, self.bot = topDefVal, botDefVal
    else:
      self.val[varName] = val

    if not (topDefVal or botDefVal): # important optimization check
      self.explicateTopBot()


  def explicateTopBot(self):
    """Checks if all values are Top or Bot.
    Useful in cases where default value is not Top or Bot.
    """
    selfVal = self.val
    if not selfVal: return  # nothing to do

    allVars = self.getAllVars(self.func)
    if len(selfVal) != len(allVars): return # nothing to do

    top = bot = True
    selfGetVal = self.getVal
    for vName in allVars:
      vVal = selfGetVal(vName)
      top = top and vVal.top
      bot = bot and vVal.bot
      if not (top or bot): return # nothing to do

    assert top != bot, f"{top}, {bot}, {selfVal}"
    self.top, self.bot, self.val = top, bot, None


  def getCopy(self, newVal: Opt[Dict] = None) -> 'OverallL':
    """Returns a shallow copy of self or a new object with newVal."""
    if newVal: return self.__class__(self.func, val=newVal)

    retTop, retBot = False, False
    if newVal is not None: # empty dict means top/bot depending on the default value
      retTop = bool(self.getDefaultVal().top)
      retBot = bool(self.getDefaultVal().bot)
    if self.top or retTop: return self.__class__(self.func, top=True)
    if self.bot or retBot: return self.__class__(self.func, bot=True)

    if not self.val:
      assert not (self.isDefaultValTop() or self.isDefaultValBot()), f"{self}"
      return self.__class__(self.func, val=None)
    else:
      return self.__class__(self.func, val=self.val.copy())


  def filterVals(self, varNames: Set[types.VarNameT]) -> None:
    """Mutates 'self'.
    All variable names in varNames are set to Top.
    """
    if self.top or not varNames:
      return None

    if self.getAllVars(self.func) == varNames:
      self.top, self.bot, self.val = True, False, None
      return None

    self.val = self.val if self.val else {}
    self.bot = False
    selfSetVal, cTop = self.setVal, self.componentTop
    for vName in varNames:
      selfSetVal(vName, cTop)
    return None


  def localize(self, #IPA
      forFunc: constructs.Func,
      keepParams: bool = False,
  ) -> 'OverallL':
    """Returns self's copy localized for the given forFunc."""
    localizedDfv = self.getCopy()
    localizedDfvVal, localizedDfvSetVal = localizedDfv.val, localizedDfv.setVal

    defaultVal = self.getDefaultVal()
    if localizedDfvVal:
      tUnit: tunit.TranslationUnit = self.func.tUnit
      varNames = set(localizedDfvVal.keys())
      keep = tUnit.getNamesGlobal() | (set(forFunc.paramNames) if keepParams else set())
      dropNames = varNames - keep
      for vName in dropNames:
        localizedDfvSetVal(vName, defaultVal) # essentially removing the values

    localizedDfv.updateFuncObj(forFunc)
    return localizedDfv


  def updateFuncObj(self, funcObj: constructs.Func): #IPA #mutates 'self'
    self.func, selfVal = funcObj, self.val # updating function object here 1
    if not selfVal: return

    for vName in selfVal:
      newVal = selfVal[vName].getCopy()
      newVal.func = funcObj  # updating function object here 2
      selfVal[vName] = newVal


  def addLocals(self, #IPA #mutates 'self'
      fromDfv: 'OverallL',
  ) -> None:
    tUnit: tunit.TranslationUnit = self.func.tUnit
    localVars = tUnit.getNamesEnv(self.func) - tUnit.getNamesGlobal()
    selfSetVal, fromDfvGetVal = self.setVal, fromDfv.getVal
    for vName in localVars:
      selfSetVal(vName, fromDfvGetVal(vName))


  def __str__(self):
    idStr = f"(id:{id(self)})" if util.VV5 else ""

    if self.top: return f"Top{idStr}"
    if self.bot: return f"Bot{idStr}"

    if self.getDefaultVal(): assert self.val, f"{self.val}"
    string = io.StringIO()
    if self.val:
      selfVal = self.val
      string.write("{")
      prefix = ""
      for key in sorted(selfVal.keys()):
        val = selfVal[key]
        if val.top and not util.VV4: continue  # don't write Top values
        string.write(prefix)
        prefix = ", "
        #string.write(f"{simplifyName(key)}: {self.val[key]}")
        string.write(f"{key}: {selfVal[key]}")
      string.write(f"}}{idStr}" if util.VV5 else "}")
    else:
      string.write("Default")
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

def updateFuncObjInDfvs(
    func: constructs.Func,
    nodeDfv: NodeDfvL,
) -> NodeDfvL:
  """It updates function in the values."""
  dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
  dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())
  dfvIn.func = dfvOut.func = func

  if dfvIn.val:
    for value in dfvIn.val.values():
      value.func = func
  if dfvOut.val:
    for value in dfvOut.val.values():
      value.func = func

  return NodeDfvL(dfvIn, dfvOut)


def removeNonEnvVars(
    nodeDfv: NodeDfvL,
    getDefaultVal: Callable[[str], ComponentL],
    getAllVars: Callable[[], Set[types.VarNameT]],
    direction: types.DirectionT = conv.Forward,
) -> NodeDfvL:
  """It removes the variables that are not in the env of func."""
  dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
  dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())

  vNames: Set[types.VarNameT] = getAllVars()

  assert direction != conv.ForwBack

  if dfvIn.val and direction == conv.Backward:
    for key in list(dfvIn.val.keys()):
      if key not in vNames:
        dfvIn.setVal(key, getDefaultVal(key)) # remove key
  if dfvOut.val and direction == conv.Forward:
    for key in list(dfvOut.val.keys()):
      if key not in vNames:
        dfvOut.setVal(key, getDefaultVal(key)) # remove key

  return NodeDfvL(dfvIn, dfvOut)


def Filter_Vars(
    varNames: Set[types.VarNameT],
    nodeDfv: NodeDfvL  # must contain an OverallL
) -> NodeDfvL:
  """A default implementation for value analyses."""
  dfvIn = cast(OverallL, nodeDfv.dfvIn)

  if not varNames or dfvIn.top:  # i.e. nothing to filter or no DFV to filter == Nop
    return NodeDfvL(dfvIn, dfvIn)  # = NopI

  newDfvOut = dfvIn.getCopy()
  newDfvOut.filterVals(varNames)
  return NodeDfvL(dfvIn, newDfvOut)


def updateDfv(
    dfvDict: Dict[types.VarNameT, ComponentL],
    dfvIn: OverallL,
) -> OverallL:
  """Creates a new dfv from `dfvIn` using `newDfv` dict if needed."""
  newDfv = dfvIn
  newDfvGetVal = newDfv.getVal
  for name, val in dfvDict.items():
    if val != newDfvGetVal(name):
      if newDfv is dfvIn:
        newDfv = dfvIn.getCopy()  # creating a copy only when necessary
        newDfvGetVal = newDfv.getVal  # important (since object changed)
      newDfv.setVal(name, val)
  return newDfv

################################################
# BOUND END  : Convenience_Functions
################################################


