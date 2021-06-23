#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""The analysis' common data flow value declarations."""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from typing import Tuple, Optional as Opt, Dict, Any, Set,\
                   Type, TypeVar, List, cast, Callable
import io

from span.ir.tunit import TranslationUnit
from span.util import ff

from span.ir import tunit, conv
from span.ir.conv import isStringLitName, nameHasPpmsVar, isLocalVarName, NULL_OBJ_NAME, simplifyName

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

OLD_VAL: ChangedT = False
NEW_VAL: ChangedT = True

################################################
# BOUND START: Node dfv related lattice
################################################

class ChangePairL(LatticeLT):
  """Flags a change in data flow values."""
  __slots__ : List[str] = ["newIn", "newOut"]

  def __init__(self,
      newIn: ChangedT,
      newOut: ChangedT
  ) -> None:
    top = not (newIn or newOut)
    bot = newIn and newOut
    super().__init__(top=top, bot=bot)

    self.newIn = newIn
    self.newOut = newOut


  def meet(self, other) -> Tuple['ChangePairL', ChangedT]:
    assert isinstance(other, ChangePairL), f"{other}"
    tup = basicMeetOp(self, other)
    if tup: return tup
    return NEW_IN_OUT, Changed


  def __lt__(self, other) -> bool:
    assert isinstance(other, ChangePairL), f"{other}"
    lt = basicLessThanTest(self, other)
    if lt is not None: return lt
    return self == other


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, ChangePairL):
      return NotImplemented
    return self.newIn == other.newIn and self.newOut == other.newOut


  def orWith(self, other: 'ChangePairL'):
    newIn = self.newIn or other.newIn
    newOut = self.newOut or other.newOut
    return getNewOldObj(newIn, newOut)


  def __str__(self):
    inChange = outChange = "NoChange"
    inChange = "Changed" if self.newIn else inChange
    outChange = "Changed" if self.newOut else outChange
    return f"(IN:{inChange}, OUT:{outChange})"


  def __repr__(self):
    return self.__str__()


  def __bool__(self) -> bool:
    """Returns True if any of the value is a True (NEW_VAL)"""
    return self.newIn or self.newOut


OLD_IN_OUT = ChangePairL(OLD_VAL, OLD_VAL)
NEW_IN_ONLY = ChangePairL(NEW_VAL, OLD_VAL)
NEW_OUT_ONLY = ChangePairL(OLD_VAL, NEW_VAL)
NEW_IN_OUT = ChangePairL(NEW_VAL, NEW_VAL)


def getNewOldObj(newIn: ChangedT, newOut: ChangedT) -> ChangePairL:
  if not newIn and not newOut:
    return OLD_IN_OUT
  elif not newIn and newOut:
    return NEW_OUT_ONLY
  elif newIn and not newOut:
    return NEW_IN_ONLY
  elif newIn and newOut:
    return NEW_IN_OUT
  raise ValueError()


class DfvPairL(LatticeLT):
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


  def meet(self, other) -> Tuple['DfvPairL', ChangedT]:
    assert isinstance(other, DfvPairL), f"{other}"
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

    if other.dfvOut is other.dfvOutFalse: # true for all non-conditional nodes
      dfvOutFalse = dfvOut
    else:
      dfvOutFalse, chOutTmp = self.dfvOutFalse.meet(other.dfvOutFalse)
      chOut = chOut or chOutTmp

    if other.dfvOut is other.dfvOutTrue: # true for all non-conditional nodes
      dfvOutTrue = dfvOut
    else:
      dfvOutTrue, chOutTmp = self.dfvOutTrue.meet(other.dfvOutTrue)
      chOut = chOut or chOutTmp

    if util.LL4: LDB(f"NodeDfv (MeetWithPrevNodeDfv):"
                     f" {getNewOldObj(chIn, chOut)}")
    return DfvPairL(dfvIn, dfvOut, dfvOutTrue, dfvOutFalse), chIn or chOut


  def widen(self,
      other: Opt['DfvPairL'] = None,
      ipa: bool = False,  # special case #IPA FIXME: is this needed?
  ) -> Tuple['DfvPairL', ChangedT]:
    assert isinstance(other, DfvPairL), f"{self.dfvIn.func}, {self}, {other}"
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

    if other.dfvOut is other.dfvOutFalse:
      dfvOutFalse = dfvOut
    else:
      dfvOutFalse, chOutTmp = self.dfvOutFalse.widen(other.dfvOutFalse)
      chOut = chOut or chOutTmp

    if other.dfvOut is other.dfvOutTrue:
      dfvOutTrue = dfvOut
    else:
      dfvOutTrue, chOutTmp = self.dfvOutTrue.widen(other.dfvOutTrue)
      chOut = chOut or chOutTmp

    if util.LL4: LDB(f"NodeDfv (WidenedWithPrevNodeDfv):"
                     f" {getNewOldObj(chIn, chOut)}")
    return DfvPairL(dfvIn, dfvOut, dfvOutTrue, dfvOutFalse), chIn or chOut


  def checkInvariants(self):
    self.dfvIn.checkInvariants()
    self.dfvOut.checkInvariants()


  def getCopy(self):
    dfvInCopy = self.dfvIn.getCopy()
    dfvOutCopy = self.dfvOut.getCopy()
    if self.dfvOut is self.dfvOutTrue:
      assert self.dfvOut is self.dfvOutFalse
      dfvOutTrueCopy, dfvOutFalseCopy = dfvOutCopy, dfvOutCopy
    else:
      dfvOutTrueCopy = self.dfvOutTrue.getCopy()
      dfvOutFalseCopy = self.dfvOutFalse.getCopy()

    return DfvPairL(dfvInCopy, dfvOutCopy, dfvOutTrueCopy, dfvOutFalseCopy)


  def __lt__(self, other: 'DfvPairL') -> bool:
    if self.dfvIn < other.dfvIn and self.dfvOut < other.dfvOut:
      return True
    return False


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, DfvPairL):
      raise NotImplemented
    return self.dfvIn == other.dfvIn and self.dfvOut == other.dfvOut


  def __hash__(self):
    return hash((self.dfvIn, self.dfvOut))


  def __str__(self):
    idStr = f"(id:{id(self)}):" if util.DD5 else ""
    if self.dfvOut is self.dfvOutFalse:
      # assert self.dfvOutFalse is self.dfvOutTrue,\
      #   f"\n DFV_OUT: {self.dfvOut},\n DFV_FALSE: {self.dfvOutFalse}," \
      #   f"\n DFV_TRUE: {self.dfvOutTrue}"
      if self.dfvIn is self.dfvOut:
        return f"NodeDfvL: {idStr}\n" \
               f" IN=OUT: {self.dfvIn}"
      else:
        return f"NodeDfvL: {idStr}\n" \
               f" IN    : {self.dfvIn}\n" \
               f" OUT   : {self.dfvOut}"
    else:
      return f"NodeDfvL: {idStr}\n" \
             f" IN    : {self.dfvIn}\n" \
             f" OUT   : {self.dfvOut}\n" \
             f" TRUE  : {self.dfvOutTrue}\n" \
             f" FALSE : {self.dfvOutFalse}"


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
  __slots__ : List[str] = ["anName", "compL"]

  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[VarNameT, ComponentL]] = None,
      top: bool = False,
      bot: bool = False,
      componentL: Type[ComponentL] = ComponentL,
      anName: str = "", # unique analysis name
  ) -> None:
    super().__init__(func, val, top, bot)
    initTopBotComp(func, anName, componentL)
    self.val: Opt[Dict[VarNameT, ComponentL]] = val
    assert componentL is not ComponentL,\
      f"Analysis should subclass dfv.ComponentL. Details: {func} {anName}"
    self.compL = componentL
    self.anName = anName


  def meet(self, other) -> Tuple['OverallL', ChangedT]:
    tup = self.basicMeetOp(other)
    if tup: return tup

    # take meet of individual entities (variables)
    meetVal: Dict[VarNameT, ComponentL] = {}
    vNames = set(self.val.keys()) | set(other.val.keys())
    selfValGet, otherValGet = self.val.get, other.val.get
    selfGetDefaultVal = self.getDefaultVal

    for vName in vNames:
      defaultVal = selfGetDefaultVal(vName)
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
    selfGetDefaultVal = self.getDefaultVal
    for vName in vNames:
      defaultVal = selfGetDefaultVal(vName)
      dfv1: ComponentL = selfValGet(vName, defaultVal)
      dfv2: ComponentL = otherValGet(vName, defaultVal)
      if not (dfv1 < dfv2): return False
    return True


  @classmethod
  def isAcceptedType(cls,
      t: types.Type,
      name: Opt[VarNameT] = None,
  ) -> bool:
    """Returns True if the type t (of an instr/expr) is
    of interest to the analysis.

    By default it selects only Numeric types.
    """
    check1 = t.isNumericOrVoid()
    check2 = not isStringLitName(name) if name else True
    check3 = name != NULL_OBJ_NAME
    return check1 and check2 and check3


  @classmethod
  def getAllVars(cls, func: constructs.Func) -> Set[VarNameT]:
    """Gets all the variables of the accepted type.

    Note: PPMS vars with field sensitivity are never returned.
          Vars like `1p.f` are added into the lattice as per
          the occurrence of such variables.
          Reason: PPMS var type is polymorphic.
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
    selfValGet, otherValGet = self.val.get, other.val.get
    for vName in vNames:
      defaultVal = self.getDefaultVal(vName)
      dfv1: ComponentL = selfValGet(vName, defaultVal)
      dfv2: ComponentL = otherValGet(vName, defaultVal)
      if not dfv1 == dfv2: return False
    return True


  def __hash__(self):
    hashThisVal = None if self.val is None else frozenset(self.val.items())
    return hash((hashThisVal, self.top)) # , self.bot))


  def checkInvariants(self):
    if util.CC1:
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
    func, anName = self.func, self.anName
    tUnit: TranslationUnit = func.tUnit
    topBot = False # i.e. Bot
    if varName:
      if nameHasPpmsVar(varName): # TODO: handle bot state
        topBot = True # i.e. Top
      elif ff.SET_LOCAL_VARS_TO_TOP:
        if varName not in tUnit.getNamesGlobal(): # avoid local looking names that are global
          topBot = True # i.e. Top
      elif ff.SET_LOCAL_ARRAYS_TO_TOP:
        topBot = tUnit.inferTypeOfVal(varName).isArray() # Top if its an Array

    defVal = getTopBotComp(func, anName, topBot, self.compL)
    return defVal


  def isDefaultVal(self,
      val: ComponentL,
      varName: Opt[VarNameT] = None,
  ) -> bool:
    return val == self.getDefaultVal(varName)


  def getVal(self,
      varName: VarNameT
  ) -> ComponentL:
    """returns entity lattice value."""
    if self.top: return getTopBotComp(self.func, self.anName, True, self.compL)
    if self.bot: return getTopBotComp(self.func, self.anName, False, self.compL)

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
      # since getAllVars() never returns all the PPMS vars. # TODO: fix this properly
      return

    # STEP 2: if here, update of self.val is inevitable
    self.val = {} if self.val is None else self.val

    if self.top: # and not defaultVal.top:
      top = getTopBotComp(self.func, self.anName, True, self.compL)
      selfGetDefaultVal = self.getDefaultVal
      self.val = {vName: top for vName in self.getAllVars(self.func)
                  if not selfGetDefaultVal(vName).top}
    if self.bot: # and not defaultVal.bot:
      bot = getTopBotComp(self.func, self.anName, False, self.compL)
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
    selfSetVal, = self.setVal
    compTop = getTopBotComp(self.func, self.anName, True, self.compL)
    for vName in varNames:
      selfSetVal(vName, compTop)
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
      selfGetDefaultVal = self.getDefaultVal
      for vName in dropNames:
        if nameHasPpmsVar(vName): continue #don't drop
        localizedDfvSetVal(vName, selfGetDefaultVal(vName)) # essentially removing the values

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
    localVars = tUnit.getNamesLocalStrict(self.func)
    selfSetVal, fromDfvGetVal = self.setVal, fromDfv.getVal
    for vName in localVars:
      selfSetVal(vName, fromDfvGetVal(vName))


  def __str__(self):
    DD1, DD3, DD5 = util.DD1, util.DD3, util.DD5
    idStr = f"(id:{id(self)})" if DD5 else ""

    s = getBasicString(self)
    if s: return f"{s}{idStr}"

    string = io.StringIO()
    if self.val:
      selfVal = self.val
      string.write(f"(Len:{len(self.val)}) {{")
      prefix = ""
      for key in sorted(selfVal.keys()):
        if not DD3 and key == conv.NULL_OBJ_NAME:
          continue
        string.write(prefix)
        val, prefix = selfVal[key], ", "
        name = key if DD3 else simplifyName(key)
        string.write(f"'{name}': {val}")
      string.write(f"}}{idStr}" if DD5 else "}")
    else:
      string.write("Default")
    return string.getvalue()


  def __repr__(self):
    if self.top: return f"{self.anName}.OverallL({self.func}, top=True)"
    if self.bot: return f"{self.anName}.OverallL({self.func}, bot=True)"

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
# BOUND START: AnalysisResult (TODO: make it a lattice)
################################################

class AnResult:
  """This class stores the result of an analysis corresponding
  to each node (single instruction) in the CFG."""


  def __init__(self,
      anName: types.AnNameT,
      func: constructs.Func,
      topVal: DataLT,
      result: Opt[Dict[types.NodeIdT, DfvPairL]] = None,
  ):
    self.anName = anName
    self.func = func
    self.topVal = topVal
    self.result = result if result else dict()


  def merge(self, other: 'AnResult') -> 'AnResult':
    """Takes the meet of the whole result.
    TODO: make it a proper meet operation."""
    glb = AnResult(self.anName, self.func, self.topVal, None)
    cfgNodeIds = set(self.result.keys())
    cfgNodeIds.update(other.result.keys())

    for nid in cfgNodeIds:
      if nid in self and nid in other:
        glb[nid], _ = self[nid].meet(other[nid])
      elif nid in self:
        glb[nid] = self[nid]
      elif nid in other:
        glb[nid] = other[nid]

    return glb


  def getCopy(self) -> 'AnResult':
    """Returns a shallow copy of this object."""
    return AnResult(self.anName, self.func, self.topVal, self.result.copy())


  def __len__(self):
    return len(self.result)


  def get(self, nid: types.NodeIdT, default=None) -> Opt[DfvPairL]:
    return self.result.get(nid, default)


  def keys(self):
    return self.result.keys()


  def values(self):
    return self.result.values()


  def items(self):
    return self.result.items()


  def __getitem__(self, nid: types.NodeIdT):
    return self.result[nid]


  def __setitem__(self, nid: types.NodeIdT, value: DfvPairL):
    self.result[nid] = value


  def __contains__(self, nid: types.NodeIdT):
    return nid in self.result


  def __eq__(self, other):
    equal = True
    if not isinstance(other, AnResult):
      equal = False
    elif not self.anName == other.anName:
      equal = False
    elif not self.func.name == other.func.name:
      equal = False
    elif not self.result == other.result:
      equal = False
    return equal


  def __str__(self):
    print(f"AnalysisResult: {self.anName}:, Func: '{self.func.name}'"
          f"TUnit: {self.func.tUnit.name}")
    topTop = "IN == OUT: Top (Unreachable/Nop)"
    for node in self.func.cfg.revPostOrder:
      nid = node.id
      nDfv = self.get(nid, topTop)
      print(f">> {nid}. ({node.insn}):\n {nDfv}")
    print() # a blank line

################################################
# BOUND END  : AnalysisResult
################################################

################################################
# BOUND START: Convenience_Functions
################################################

# def updateFuncObjInDfvs(
#     func: constructs.Func,
#     nodeDfv: NodeDfvL,
# ) -> NodeDfvL:
#   """It updates function in the values."""
#   dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
#   dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())
#   dfvIn.func = dfvOut.func = func
#
#   if dfvIn.val:
#     for value in dfvIn.val.values():
#       value.func = func
#   if dfvOut.val:
#     for value in dfvOut.val.values():
#       value.func = func
#
#   return NodeDfvL(dfvIn, dfvOut)
#
#
# def removeNonEnvVars(
#     nodeDfv: NodeDfvL,
#     getDefaultVal: Callable[[str], ComponentL],
#     getAllVars: Callable[[], Set[VarNameT]],
#     direction: types.DirectionT = conv.Forward,
# ) -> NodeDfvL:
#   """It removes the variables that are not in the env of func."""
#   dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
#   dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())
#
#   vNames: Set[VarNameT] = getAllVars()
#
#   assert direction != conv.ForwBack
#
#   if dfvIn.val and direction == conv.Backward:
#     for key in list(dfvIn.val.keys()):
#       if key not in vNames:
#         dfvIn.setVal(key, getDefaultVal(key)) # remove key
#   if dfvOut.val and direction == conv.Forward:
#     for key in list(dfvOut.val.keys()):
#       if key not in vNames:
#         dfvOut.setVal(key, getDefaultVal(key)) # remove key
#
#   return NodeDfvL(dfvIn, dfvOut)


# def Filter_Vars(
#     varNames: Set[VarNameT],
#     nodeDfv: NodeDfvL  # must contain an OverallL
# ) -> NodeDfvL:
#   """A default implementation for value analyses.
#   Sets the given set of variables to top in the lattice.
#   """
#   dfvIn = cast(OverallL, nodeDfv.dfvIn)
#
#   if not varNames or dfvIn.top:  # i.e. nothing to filter or no DFV to filter == Nop
#     return NodeDfvL(dfvIn, dfvIn)  # = NopI
#
#   newDfvOut = dfvIn.getCopy()
#   newDfvOut.filterVals(varNames)
#   return NodeDfvL(dfvIn, newDfvOut)


def updateDfv(
    dfvDict: Dict[VarNameT, ComponentL],
    overallDfv: OverallL,
) -> OverallL:
  """Creates a new dfv from `overallDfv` using `dfvDict` if needed."""
  newDfv = overallDfv
  newDfvGetVal = newDfv.getVal
  for name, val in dfvDict.items():
    if val != newDfvGetVal(name):
      if newDfv is overallDfv:
        newDfv = overallDfv.getCopy()  # creating a copy only when necessary
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
    topBot: bool, # False == Bot, True == Top
    compL: Type[ComponentL] = None, # any comp object will do
) -> Opt[ComponentL]:
  tup, compDict = (func.name, anName, topBot), _componentTopBot
  if tup not in compDict: # then add the top bot
    initTopBotComp(func, anName, compL)
  return compDict[tup]


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

