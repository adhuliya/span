#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Reaching Def Analysis

This (and every) analysis subclasses,

* `span.sys.lattice.DataLT` (to define its lattice)
* `span.sys.analysis.AnalysisAT` (to define the analysis)
"""

import logging
LOG = logging.getLogger(__name__)
LDB, LIN = LOG.debug, LOG.info

from span.util.consts import TopAsBool, BotAsBool

from typing import Tuple, Dict, List, Optional as Opt, Set, Callable, cast
import io

import span.util.util as util
from span.util.util import LS, AS

from span.ir.tunit import TranslationUnit
import span.ir.ir as ir
from span.ir.types import (
  VarNameT, NodeIdT, GlobalNodeIdT, RecordT, DirectionT,
  Type as SpanType, MemberNameT,
)
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs

from span.api.lattice import (ChangedT, Changed, DataLT,
                              basicLessThanTest, basicEqualsTest, mergeAll, )
import span.api.dfv as dfv
from span.api.dfv import (
  DfvPairL, ComponentL
)

from span.api.analysis import AnalysisAT, ValueAnalysisAT
from span.ir.conv import (
  simplifyName, isCorrectNameFormat, genGlobalNodeId, getNodeId,
  GLOBAL_INITS_FUNC_ID, isGlobalName, getGlobalNodeIdStr,
  getFuncId, Forward, nameHasPpmsVar,
)

GLOBAL_INITS_FNID = genGlobalNodeId(GLOBAL_INITS_FUNC_ID, 1)  # initialized global

################################################
# BOUND START: ReachingDef lattice.
################################################

class ComponentL(DataLT):

  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[Set[GlobalNodeIdT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)


  def meet(self,
      other: 'ComponentL'
  ) -> Tuple['ComponentL', ChangedT]:
    tup = self.basicMeetOp(other)
    if tup: return tup

    # if (len(self.val) + len(other.val)) > 100:  #MEMOPTRD
    #   new = ComponentL(self.func, bot=True)  #MEMOPTRD
    # else:
    new = self.getCopy()
    new.val.update(other.val)
    return new, Changed


  def __lt__(self,
      other: 'ComponentL'
  ) -> bool:
    lt = basicLessThanTest(self, other)
    return self.val >= other.val if lt is None else lt


  def getCopy(self) -> 'ComponentL':
    if self.top: return ComponentL(self.func, top=True)
    if self.bot: return ComponentL(self.func, bot=True)

    return ComponentL(self.func, self.val.copy())


  def __len__(self):
    if self.top: return 0
    if self.bot: return 0x7FFFFFFF  # a large number

    assert len(self.val), "Defs should be one or more"
    return len(self.val)


  def __contains__(self, fNid: GlobalNodeIdT):
    if self.top: return False
    if self.bot: return True
    return fNid in self.val


  def addVal(self, gNid: GlobalNodeIdT) -> None:
    if self.top:
      self.val = set()
      self.top = False
    if gNid == 0: raise ValueError() # delit
    self.val.add(gNid)


  def delVal(self, gNid: GlobalNodeIdT) -> None:
    if self.top:
      return None

    self.val.remove(gNid)
    if not len(self.val):
      self.top = True
      self.val = None


  def isInitialized(self,
      must: bool = False, # False=May initialized, True=Must initialized
  ) -> bool:
    gNid = genGlobalNodeId(0, 0)  # i.e. uninitialized def
    if self.top: # only possible if code is unreachable
      return True # assume must initialized (since unreachable)
    elif self.bot:
      return not must
    elif gNid in self.val:
      return False if len(self.val) == 1 else not must
    else:
      return True  # a must initialized value


  def isUnInitialized(self,
      must: bool = False, # False=May uninitialized, True=Must uninitialized
  ) -> bool:
    gNid = genGlobalNodeId(0, 0)  # i.e. uninitialized def
    if self.top: # only possible if code is unreachable
      return False # assume must initialized (since unreachable)
    elif self.bot:
      return not must
    elif gNid in self.val:
      return True if len(self.val) == 1 else not must
    else:
      return False  # a must uninitialized value


  def __eq__(self,
      other: 'ComponentL'
  ) -> bool:
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = basicEqualsTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    val = frozenset(self.val) if self.val else None
    return hash((val, self.top, self.bot))


  def __str__(self):
    if self.top: return "Top"
    if self.bot: return "Bot"
    string = io.StringIO()
    string.write("{")
    prefix, funcId = "", self.func.id
    for val in self.val:
      # string.write(f"{getFuncNodeIdStr(val)}")
      if getFuncId(val) == funcId:
        string.write(f"{prefix}{getNodeId(val)}")
      else:
        string.write(f"{prefix}{getGlobalNodeIdStr(val)}")
      if not prefix: prefix = ", "
    string.write("}")
    return string.getvalue()


  def __repr__(self):
    return self.__str__()


class OverallL(dfv.OverallL):
  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[VarNameT, dfv.ComponentL]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot, ComponentL, "ReachingDefA")


  def getDefaultVal(self,
      varName: Opt[VarNameT] = None
  ) -> Opt[ComponentL]:
    if varName is None:
      return None # None tells that default is not Top/Bot

    assert isCorrectNameFormat(varName), f"{varName}"
    func = self.func
    if func.isParamName(varName):
      # this default value is only used in intra-procedural analysis
      # in inter-procedural analysis, params are defined in the caller,
      # and only in case of main() function this is useful.
      gNid = genGlobalNodeId(func.id, 1)  # as node 1 is always NopI()
    elif func.isLocalName(varName):
      gNid = genGlobalNodeId(0, 0)  # i.e. uninitialized
    elif isGlobalName(varName):
      gNid = GLOBAL_INITS_FNID
    else: # assume an address taken global
      gNid = GLOBAL_INITS_FNID
    return ComponentL(func, val={gNid})


  def getDefaultValForGlobal(self) -> ComponentL:
    return ComponentL(self.func, val={GLOBAL_INITS_FNID})


  @classmethod
  def isAcceptedType(cls,
      t: SpanType,
      name: Opt[VarNameT] = None,
  ) -> bool:
    return True # accepts all types


  def isInitialized(self,
      varName: VarNameT,
      must: bool = False, # False=May uninitialized, True=Must uninitialized
  ) -> bool:
    varDfv = self.getVal(varName)
    try:
      return varDfv.isInitialized(must=must)
    except ValueError as e:
      raise ValueError(f"{varName}: {e}")


  def isUnInitialized(self,
      varName: VarNameT,
      must: bool = False, # False=May uninitialized, True=Must uninitialized
  ) -> bool:
    varDfv = self.getVal(varName)
    try:
      return varDfv.isUnInitialized(must=must)
    except ValueError as e:
      raise ValueError(f"{varName}: {e}")


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
      top = dfv.getTopBotComp(self.func, self.anName, TopAsBool, self.compL)
      selfGetDefaultVal = self.getDefaultVal
      self.val = {vName: top for vName in self.getAllVars(self.func)
                  if not selfGetDefaultVal(vName).top}
    if self.bot: # and not defaultVal.bot:
      bot = dfv.getTopBotComp(self.func, self.anName, BotAsBool, self.compL)
      selfGetDefaultVal = self.getDefaultVal
      self.val = {vName: bot for vName in self.getAllVars(self.func)
                  if not selfGetDefaultVal(vName).bot}

    assert self.val is not None, f"{self}"
    self.top = self.bot = False  # if it was top/bot, then its no more.
    if self.isDefaultVal(val, varName):
      if varName in self.val:
        del self.val[varName]  # since default value
    else:
      val =  val if len(val) < 100 else \
        dfv.getTopBotComp(self.func, self.anName, BotAsBool, self.compL) #ToSaveMemory
      self.val[varName] = val


################################################
# BOUND END  : ReachingDef lattice.
################################################

################################################
# BOUND START: ReachingDef_Analysis
################################################

class ReachingDefA(ValueAnalysisAT):
  """Reaching Definitions Analysis."""
  __slots__ : List[str] = ["defaultDfv"]
  L: type = OverallL              # lattice of analysis
  D: DirectionT = Forward   # direction of analysis


  needsRhsDerefToVarsSim: bool = False
  needsLhsDerefToVarsSim: bool = True
  needsNumVarToNumLitSim: bool = False
  needsNumBinToNumLitSim: bool = True
  needsCondToUnCondSim: bool = True
  needsLhsVarToNilSim: bool = False # FIXME: True when using liveness analysis
  needsNodeToNilSim: bool = False
  needsFpCallSim: bool = True


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func, ComponentL, OverallL)
    dfv.initTopBotOverall(func, ReachingDefA.__name__, ReachingDefA.L)
    self.defaultDfv = OverallL(self.func, val={})


  def getBoundaryInfo(self,
      nodeDfv: Opt[DfvPairL] = None, # needs to be localized to the target func
      ipa: bool = False,  #IPA
      entryFunc: bool = False,
      forFunc: Opt[constructs.Func] = None,
  ) -> DfvPairL:
    if ipa and not nodeDfv:
      raise ValueError(f"{ipa}, {nodeDfv}")

    func = forFunc if forFunc else self.func

    overTop = self.overallTop.getCopy()
    overTop.func = func #IMPORTANT

    if nodeDfv: #IPA or #INTRA
      inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
    else: #INTRA
      inBi, outBi = self.defaultDfv.getCopy(), overTop

    inBi.func = outBi.func = func  #IMPORTANT

    nDfv1 = DfvPairL(inBi, outBi)
    return nDfv1


  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def UnDefVal_Instr(self,
      nodeId: NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    func = self.func
    newOut = dfvIn = cast(OverallL, nodeDfv.dfvIn)

    fNid = genGlobalNodeId(func.id, nodeId)
    val, varName = ComponentL(func, val={fNid}), insn.lhsName

    if val != dfvIn.getVal(varName):
      newOut = dfvIn.getCopy()
      newOut.setVal(varName, val)

    return DfvPairL(dfvIn, newOut)

  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################
  # uses the default implementation
  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def processLhsRhs(self,
      nodeId: NodeIdT,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    dfvIn = nodeDfv.dfvIn
    assert isinstance(dfvIn, OverallL), f"{type(dfvIn)}"
    if LS: LOG.debug("ProcessingAssignInstr: (Node_%s) %s, iType: %s, %s = %s",
                     nodeId, lhs.type, rhs, lhs)

    lhsType = lhs.type
    dfvInGetVal = cast(Callable[[VarNameT], dfv.ComponentL], dfvIn.getVal)
    outDfvValues: Dict[VarNameT, dfv.ComponentL] = {}

    if isinstance(lhsType, RecordT):
      outDfvValues = self.processLhsRhsRecordType(nodeId, lhs, rhs, dfvIn)
    else:
      func = self.func
      lhsVarNames = ir.getNamesLValuesOfExpr(func, lhs)
      assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
      mustUpdate = len(lhsVarNames) == 1

      rhsDfv = ComponentL(func, val={genGlobalNodeId(func.id, nodeId)})
      if LS: LOG.debug("RhsDfvOfExpr: '%s' is %s, lhsVarNames are %s",
                       rhs, rhsDfv, lhsVarNames)

      for name in lhsVarNames: # loop enters only once if mustUpdate == True
        newVal, oldVal = rhsDfv, dfvInGetVal(name)
        if not mustUpdate or ir.nameHasArray(func, name):
          newVal, _ = oldVal.meet(newVal) # do a may update
        if newVal != oldVal:
          outDfvValues[name] = newVal

    if isinstance(rhs, expr.CallE):
      outDfvValues.update(self.processCallE(rhs, dfvIn, nodeId))

    nDfv = self.genNodeDfvL(outDfvValues, nodeDfv)
    return nDfv


  def processLhsRecordType(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
  ) -> Dict[VarNameT, dfv.ComponentL]:
    """Processes assignment instruction with RecordT"""
    lhs, rhs, iType, func = insn.lhs, insn.rhs, insn.type, self.func
    assert isinstance(iType, RecordT), f"{lhs}, {rhs}: {iType}"

    allMemberInfo = iType.getNamesOfType(None)

    lhsVarNames = ir.getNamesLValuesOfExpr(func, lhs)
    assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
    mustUpdate: bool = len(lhsVarNames) == 1

    val = ComponentL(func, val={genGlobalNodeId(func.id, nodeId)})

    outDfvValues: Dict[VarNameT, dfv.ComponentL] = {}
    for memberInfo in allMemberInfo:
      memName = memberInfo.name
      for lhsName in lhsVarNames:
        fullMemName = f"{lhsName}.{memName}"
        for name in (lhsName, fullMemName): # handle both names
          newVal, oldVal = val, dfvInGetVal(name)
          if not mustUpdate or ir.nameHasArray(func, name):
            newVal, _ = oldVal.meet(newVal) # do a may update
          if newVal != oldVal:
            outDfvValues[name] = newVal

    return outDfvValues


  def getExprDfv(self,
      e: expr.ExprET,
      dfvIn: dfv.OverallL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
      nodeId: NodeIdT = 0,
  ) -> dfv.ComponentL:
    return ComponentL(self.func, val={genGlobalNodeId(self.func.id, nodeId)})


  def computeLhsDfvFromRhs(self,
      lhsName: VarNameT,
      rhsDfv: dfv.ComponentL,
      dfvIn: dfv.OverallL,
      nodeId: NodeIdT,
      mustUpdate: bool,
  ) -> Opt[dfv.ComponentL]:
    """Computes the DFV of the LHS variable from a given RHS DFV."""

    dfvInGetVal = cast(Callable[[VarNameT], dfv.ComponentL], dfvIn.getVal)

    newVal, oldVal = rhsDfv, dfvInGetVal(lhsName)
    if (not mustUpdate
        or ir.nameHasArray(dfvIn.func, lhsName)
        # or nameHasPpmsVar(lhsName)
    ):
      newVal, _ = oldVal.meet(newVal) # do a may update

    return newVal if newVal != oldVal else None


  def computeLhsDfvFromRhsNames(self,
      rhsVarNames: Opt[Set[VarNameT]],
      memName: MemberNameT,
      fullLhsVarName: VarNameT,
      dfvIn: dfv.OverallL,
      nodeId: NodeIdT,
      mustUpdate: bool,
  ) -> Opt[dfv.ComponentL]:
    dfvInGetVal: Callable[[VarNameT], dfv.ComponentL] = dfvIn.getVal

    rhsDfv = ComponentL(self.func, val={genGlobalNodeId(self.func.id, nodeId)})

    oldLhsDfv = dfvInGetVal(fullLhsVarName)
    if (not mustUpdate
        or ir.nameHasArray(dfvIn.func, fullLhsVarName)
        # or nameHasPpmsVar(fullLhsVarName)
    ):
      rhsDfv, _ = oldLhsDfv.meet(rhsDfv)

    return rhsDfv if oldLhsDfv != rhsDfv else None


  def processCallE(self, #INTRA only for intra-procedural
      e: expr.ExprET,
      dfvIn: DataLT,
      nodeId: NodeIdT,
  ) -> Dict[VarNameT, dfv.ComponentL]:
    """Under-approximates specific functions.
    See TranslationUnit.underApproxFunc() definition.
    """
    assert isinstance(e, expr.CallE), f"{e}"
    assert isinstance(dfvIn, dfv.OverallL), f"{type(dfvIn)}"

    tUnit: TranslationUnit = self.func.tUnit
    calleeName = e.getFuncName()
    if calleeName:
      calleeFuncObj = tUnit.getFuncObj(calleeName)
      if tUnit.underApproxFunc(calleeFuncObj):  # should under-approx test ?
        return {}  # FIXME: too narrow an under-approximation

    names = ir.getNamesPossiblyModifiedInCallExpr(self.func, e)
    names = ir.filterNames(self.func, names, self.L.isAcceptedType)

    if util.LL5: LDB(" OverApproximating: %s", list(sorted(names)))

    newVal = ComponentL(self.func, val={genGlobalNodeId(self.func.id, nodeId)})
    dfvInGetVal = dfvIn.getVal
    outDfvValues: Dict[VarNameT, dfv.ComponentL] = {
      name: dfvInGetVal(name).meet(newVal)[0]
      for name in names
    }
    return outDfvValues

  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : ReachingDef_Analysis
################################################
