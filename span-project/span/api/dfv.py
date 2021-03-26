#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The analysis' common data flow value declarations."""

import logging

from span.ir.tunit import TranslationUnit
from span.util import ff

LOG = logging.getLogger("span")
LDB = LOG.debug

from typing import Tuple, Optional as Opt, Dict, Any, Set,\
                   Type, TypeVar, List, cast, Callable
import io

from span.ir import tunit, conv
from span.ir.conv import isStringLitName, nameHasPpmsVar, isLocalVarName

from span.util.util import LS
import span.util.util as util
from span.api.lattice import\
  (LatticeLT, DataLT, ChangedT, Changed,
   BoundLatticeLT, basicMeetOp, basicLessThanTest,
   basicEqualsTest, getBasicString)
import span.ir.constructs as constructs
import span.ir.types as types
from span.ir.types import (
  FuncNameT, VarNameT
)

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

    if util.LL4: LDB("NodeDfv (meet with prev nodeDfv): In: %s, Out: %s.", chIn, chOut)
    return NodeDfvL(dfvIn, dfvOut, dfvOutTrue, dfvOutFalse), chIn or chOut


  def widen(self,
      other: Opt['NodeDfvL'] = None,
      ipa: bool = False,  # special case #IPA FIXME: is this needed?
  ) -> Tuple['NodeDfvL', ChangedT]:
    assert isinstance(other, NodeDfvL), f"{self.dfvIn.func}, {self}, {other}"
    if self is other:
      return self, not Changed

    chOut = not Changed
    chIn = not Changed

    if self.dfvIn is other.dfvIn:  # since data flow values are treated immutable
      dfvIn = self.dfvIn
    else:
      dfvIn, chIn = self.dfvIn.widen(other.dfvIn)

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

    if util.LL4: LDB("NodeDfv (widened with prev nodeDfv): In: %s, Out: %s.", chIn, chOut)
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
  __slots__ : List[str] = ["name"]

  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[VarNameT, ComponentL]] = None,
      top: bool = False,
      bot: bool = False,
      componentL: Type[ComponentL] = ComponentL,
      name: str = "", # unique analysis name
  ) -> None:
    super().__init__(func, val, top, bot)
    initTopBotComp(func, name, componentL)
    self.val: Opt[Dict[VarNameT, ComponentL]] = val
    assert componentL is not ComponentL,\
      f"Analysis should subclass dfv.ComponentL. Details: {func} {name}"
    self.name = name


  def meet(self, other) -> Tuple['OverallL', ChangedT]:
    assert isinstance(other, OverallL), f"{other}"

    tup = self.basicMeetOp(other)
    if tup: return tup

    # take meet of individual entities (variables)
    meetVal: Dict[VarNameT, ComponentL] = {}
    vNames = set(self.val.keys()) | set(other.val.keys())
    selfValGet, otherValGet = self.val.get, other.val.get

    for vName in vNames:
      defaultVal = self.getDefaultVal(vName)
      dfv1: ComponentL = selfValGet(vName, defaultVal)
      dfv2: ComponentL = otherValGet(vName, defaultVal)
      dfv3, _ = dfv1.meet(dfv2)
      if dfv3 != defaultVal:
        meetVal[vName] = dfv3

    value = self.__class__(self.func, val=meetVal)
    return value, Changed


  def __lt__(self,
      other: 'OverallL'
  ) -> bool:
    lt = self.basicLessThanTest(other)
    if lt is not None: return lt

    vNames = set(self.val.keys()) | set(other.val.keys())
    selfValGet, otherValGet = self.val.get, other.val.get
    for vName in vNames:
      defaultVal = self.getDefaultVal(vName)
      dfv1, dfv2 = selfValGet(vName, defaultVal), otherValGet(vName, defaultVal)
      if not (dfv1 < dfv2): return False
    return True


  @classmethod
  def isAcceptedType(cls,
      t: types.Type,
      name: Opt[VarNameT] = None,
  ) -> bool:
    """Returns True if the type of the instruction/variable is
    of interest to the analysis.
    By default it selects only Numeric types.
    """
    check1 = t.isNumericOrVoid()
    check2 = not isStringLitName(name) if name else True
    return check1 and check2


  @classmethod
  def getAllVars(cls, func: constructs.Func) -> Set[VarNameT]:
    """Gets all the variables of the accepted type.
    Note: PPMS vars with field sensitivity are never returned.
          Vars like `1p.f` are added into the lattice as per
          the occurrence of such variables.
          Reason: PPMS vars type is not known beforehand.
    """
    names = ir.getNamesEnv(func)
    return ir.filterNames(func, names, cls.isAcceptedType)


  def __eq__(self, other) -> bool:
    """strictly equal check."""
    if not isinstance(other, self.__class__):
      return NotImplemented

    equal = self.basicEqualTest(other)
    if equal is not None: return equal

    vNames = set(self.val.keys()) | set(other.val.keys())
    selfGetVal, otherGetVal = self.val.get, other.val.get
    for vName in vNames:
      defaultVal = self.getDefaultVal(vName)
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
          assert v is not None, f"{self.func.name}: {k}, {v}"
          v.checkInvariants()


  def getDefaultVal(self,
      varName: VarNameT,
  ) -> Opt[ComponentL]:
    """Default value when a variable is not present in the map.
    Override this function if the default implementation is not suitable.
    """
    topBot = False # i.e. Bot
    tUnit: TranslationUnit = self.func.tUnit
    if varName:
      if nameHasPpmsVar(varName):
        topBot = True # i.e. Top
      elif ff.SET_LOCAL_VARS_TO_TOP and not nameHasPpmsVar(varName) and\
          varName not in tUnit.getNamesGlobal():
        topBot = True # i.e. Top
      elif ff.SET_LOCAL_ARRAYS_TO_TOP:
        topBot = tUnit.inferTypeOfVal(varName).isArray() # Top if its an Array

    return getTopBotComp(self.func, self.name, topBot)


  def isDefaultVal(self,
      val: ComponentL,
      varName: Opt[VarNameT] = None,
  ) -> bool:
    return val == self.getDefaultVal(varName)


  def getVal(self,
      varName: VarNameT
  ) -> ComponentL:
    """returns entity lattice value."""
    if self.top: return getTopBotComp(self.func, self.name, True)
    if self.bot: return getTopBotComp(self.func, self.name, False)
    selfVal = self.val
    if selfVal and varName in selfVal:
      return selfVal[varName]
    else:
      return self.getDefaultVal(varName)


  def setVal(self,
      varName: VarNameT,
      val: ComponentL
  ) -> None:
    """Mutates 'self'.
    Changes accommodate PPMS vars whose value is assumed Top by default,
    and their Bot value is explicitly kept in the dictionary.
    """
    # STEP 1: checks to avoid any explicit updates
    if self.top and val.top: return
    if self.bot and val.bot and self.getDefaultVal(varName).bot:
      # as PPMS Vars default is Top, the bot state needs modification
      # since getAllVars() never returns all the PPMS vars.
      return

    # STEP 2: if here, update of self.val is inevitable
    self.val = {} if self.val is None else self.val

    if self.top: # and not defaultVal.top:
      top = getTopBotComp(self.func, self.name, True)
      selfGetDefaultVal = self.getDefaultVal
      self.val = {vName: top for vName in self.getAllVars(self.func)
                  if not selfGetDefaultVal(vName).top}
    if self.bot: # and not defaultVal.bot:
      bot = getTopBotComp(self.func, self.name, False)
      selfGetDefaultVal = self.getDefaultVal
      self.val = {vName: bot for vName in self.getAllVars(self.func)
                  if not selfGetDefaultVal(vName).bot}

    assert self.val is not None, f"{self}"
    self.top = self.bot = False  # if it was top/bot, then its no more.
    if self.isDefaultVal(val, varName):
      if varName in self.val:
        del self.val[varName]  # since default value
    else:
      self.val[varName] = val

    # don't explicate now, let self.val remain empty if it is so.
    # self.explicateTopBot() # not needed since default val is var specific now


  def explicateTopBot(self):
    """Checks if all values are Top or Bot.
    Useful in cases where default value is not Top or Bot.

    Note: This function is now redundant as default value is
    now specific to variables.
     e.g. PPMS vars are Top and non-PPMS vars are Bot by default.
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


  def getCopy(self) -> 'OverallL':
    """Returns a shallow copy of self or a new object with newVal."""
    if self.top: return self.__class__(self.func, top=True)
    if self.bot: return self.__class__(self.func, bot=True)

    val = self.val.copy() if self.val is not None else None
    return self.__class__(self.func, val=val)


  def filterVals(self, varNames: Set[VarNameT]) -> None:
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
    selfSetVal, cTop = self.setVal, getTopBotComp(self.func, self.name, True)
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

    if localizedDfvVal:
      tUnit: tunit.TranslationUnit = self.func.tUnit
      varNames = set(localizedDfvVal.keys())
      keep = tUnit.getNamesGlobal() | (set(forFunc.paramNames) if keepParams else set())
      dropNames = varNames - keep
      for vName in dropNames:
        if nameHasPpmsVar(vName): continue #don't drop
        defaultVal = self.getDefaultVal(vName)
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
    DD1, DD3, DD5 = util.DD1, util.DD3, util.DD5
    idStr = f"(id:{id(self)})" if DD5 else ""

    if self.top: return f"Top{idStr}"
    if self.bot: return f"Bot{idStr}"

    string = io.StringIO()
    if self.val:
      selfVal = self.val
      string.write("{")
      prefix = ""
      for key in sorted(selfVal.keys()):
        if not DD3 and key == conv.NULL_OBJ_NAME: continue
        val = selfVal[key]
        if val.top and not DD1: continue  # don't write Top values
        string.write(prefix)
        prefix = ", "
        #string.write(f"{simplifyName(key)}: {self.val[key]}")
        string.write(f"{key}: {selfVal[key]}")
      string.write(f"}}{idStr}" if DD5 else "}")
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
    getAllVars: Callable[[], Set[VarNameT]],
    direction: types.DirectionT = conv.Forward,
) -> NodeDfvL:
  """It removes the variables that are not in the env of func."""
  dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
  dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())

  vNames: Set[VarNameT] = getAllVars()

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
    varNames: Set[VarNameT],
    nodeDfv: NodeDfvL  # must contain an OverallL
) -> NodeDfvL:
  """A default implementation for value analyses.
  Sets the given set of variables to top in the lattice.
  """
  dfvIn = cast(OverallL, nodeDfv.dfvIn)

  if not varNames or dfvIn.top:  # i.e. nothing to filter or no DFV to filter == Nop
    return NodeDfvL(dfvIn, dfvIn)  # = NopI

  newDfvOut = dfvIn.getCopy()
  newDfvOut.filterVals(varNames)
  return NodeDfvL(dfvIn, newDfvOut)


def updateDfv(
    dfvDict: Dict[VarNameT, ComponentL],
    dfvIn: OverallL,
) -> OverallL:
  """Creates a new dfv from `dfvIn` using `dfvDict` if needed."""
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

################################################
# BOUND START: Cache_Component_Top_Bot_Values
################################################

# cache the component Top/Bot values globally
_componentTopBot: \
  Dict[Tuple[FuncNameT, str, bool], ComponentL] = {}
_overallTopBot: \
  Dict[Tuple[FuncNameT, str, bool], OverallL] = {}

def getTopBotComp(
    func: constructs.Func,
    anName: str,
    topBot: bool = False, # False == Bot, True == Top
) -> Opt[ComponentL]:
  tup, compDict = (func.name, anName, topBot), _componentTopBot
  return compDict[tup] if tup in compDict else None


def initTopBotComp(
    func: constructs.Func,
    anName: str,
    componentL: Type[ComponentL],
) -> None:
  tupTop, compDict = (func.name, anName, True), _componentTopBot
  if tupTop not in compDict: # then init
    tupBot = (func.name, anName, False) # for bot
    compDict[tupTop] = componentL(func, top=True)
    compDict[tupBot] = componentL(func, bot=True)


def getTopBotOverall(
    func: constructs.Func,
    anName: str,
    topBot: bool = False, # False == Bot, True == Top
) -> Opt[OverallL]:
  tup, overallDict = (func.name, anName, topBot), _overallTopBot
  return overallDict[tup] if tup in overallDict else None


def initTopBotOverall(
    func: constructs.Func,
    anName: str,
    overallL: Type[OverallL],
) -> None:
  tupTop, overallDict = (func.name, anName, True), _overallTopBot
  if tupTop not in overallDict: # then init
    tupBot = (func.name, anName, False) # for bot
    overallDict[tupTop] = overallL(func, top=True)
    overallDict[tupBot] = overallL(func, bot=True)


################################################
# BOUND END  : Cache_Component_Top_Bot_Values
################################################

