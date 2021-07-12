#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""
Inter-Procedural Analysis (IPA)
Using the Value-Context Method.
"""
import logging
_LOG = logging.getLogger(__name__)
LDB, LIN = _LOG.debug, _LOG.info

import io
from typing import Dict, Tuple, Set, List, cast, Optional as Opt
# import objgraph
import gc  # REF: https://rushter.com/blog/python-garbage-collector/

TRACE_MALLOC: bool = False

if TRACE_MALLOC:
  import tracemalloc # REF: https://docs.python.org/3/library/tracemalloc.html
  tracemalloc.start()

from span.sys.stats import GlobalStats
import span.sys.clients as clients
from span.ir.instr import getDerefExpr, AssignI
from span.ir import cfg, expr, types, op
import span.ir.conv as conv
from span.ir.conv import (GLOBAL_INITS_FUNC_NAME,
                          Forward, Backward, GLOBAL_INITS_FUNC_ID,
                          genGlobalNodeId, getGlobalNodeIdStr)
from span.ir.types import FuncNameT, GlobalNodeIdT, NodeIdT
from span.ir.tunit import TranslationUnit
from span.api.analysis import AnalysisNameT as AnNameT, DirectionDT, AnalysisAT, SimFailed
from span.api.dfv import DfvPairL, OverallL

from span.sys.host import Host
from span.sys.common import CallSitePair, AnDfvPairDict
from span.api.dfv import AnResult # replacing span.sys.common.AnResult
import span.util.ff as ff
import span.util.util as util

# the invocation id type used to identify the unique invocation id of
# analyzeFunc() call in IPA value context method.
InvocationIdT = int

def takeTracemallocSnapshot():
  if TRACE_MALLOC:
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    for stat in top_stats: print(stat)


class ValueContext:
  __slots__ : List[str] = ["funcName", "dfvDict"]


  def __init__(self,
      funcName: FuncNameT,
      dfvDict: Opt[AnDfvPairDict] = None
  ):
    self.funcName = funcName
    self.dfvDict = dfvDict if dfvDict is not None else AnDfvPairDict()


  def getCopy(self):
    return ValueContext(self.funcName, self.dfvDict.getCopy())


  def addValue(self,
      anName: AnNameT,
      nodeDfv: DfvPairL
  ) -> None:
    self.dfvDict[anName] = nodeDfv


  def __eq__(self, other):
    if self is other: return True
    equal = True
    if not isinstance(other, ValueContext):
      equal = False
    elif not self.funcName == other.funcName:
      equal = False
    elif not self.dfvDict == other.dfvDict:
      equal = False

    return equal


  def __hash__(self) -> int:
    theHash = hash(self.funcName)
    for anName, nDfvSelf in self.dfvDict:
      direction = clients.getAnDirn(anName)
      if direction == Forward:
        theHash = hash((theHash, nDfvSelf.dfvIn))
      elif direction == Backward:
        theHash = hash((theHash, nDfvSelf.dfvOut))
      else:  # bi-directional
        theHash = hash((theHash, nDfvSelf))

    return theHash


  def __str__(self):
    idStr = "" if not util.DD5 else f"(id:{id(self)})"
    return f"ValueContext({self.funcName}, {self.dfvDict}){idStr}"


  def __repr__(self):
    return f"ValueContext({self.funcName}, {self.dfvDict})"


class HostSitesPair:
  """Stores the Host class and the callSites where its computation
  is (re)used due to common ValueContexts."""


  def __init__(self,
      host: Host,
      callSites: Opt[Set[GlobalNodeIdT]] = None,
  ):
    self.host =  host
    self.callSites: Set[GlobalNodeIdT] = callSites if callSites else set()


  def hasCallSites(self) -> bool:
    return bool(self.callSites)


  def hasSingleSite(self):
    return len(self.callSites) == 1


  def addSite(self, callSite):
    self.callSites.add(callSite)


  def removeSite(self, callSite):
    if callSite in self.callSites:
      if util.LL1: LIN(f"WARN: {getGlobalNodeIdStr(callSite)} not present.")
      self.callSites.remove(callSite)


  def __str__(self):
    return f"HostCallSitesPair({self.host.func.name}, {self.callSites})"


  def __repr__(self): return self.__str__()


class ValueContextInfo:
  """Value context method stores all its information in
  an object of ValueContextInfo."""

  def __init__(self,
      reUsePrevValueContextHost: bool = ff.IPA_VC_RE_USE_PREV_VALUE_CONTEXT_HOST,
  ):
    self.reUsePrevValueContextHost = reUsePrevValueContextHost

    # This map stores the ValueContexts and the corresponding Host objects
    self.valueContextMap: Dict[ValueContext, HostSitesPair] = {}

    # Record the max size of value context map. (Useful for testing)
    self.maxVcMapSize: int = 0

    # Map to store prev value context at a call site,
    # to help reuse the previous host computation.
    self.callSitePairContextMap: \
      Dict[Tuple[CallSitePair, InvocationIdT], ValueContext] = {}

    # The stack used to store value contexts in a stack of invocations.
    # This is used in termination of value contexts.
    # Note: The recursive function invocations track the order of CallSitePair.
    self.callSiteContextMapStack: Dict[CallSitePair, AnDfvPairDict] = {}

    self.finalResult: Dict[FuncNameT, Dict[AnNameT, AnResult]] = {}


  def __getitem__(self, vContext: ValueContext):
    """Get the stored value context information."""
    if vContext in self.valueContextMap:
      return self.valueContextMap[vContext]
    raise ValueError(f"ValueContext Missing"
                     f" (Total: {len(self.valueContextMap)}): {vContext}")


  def __setitem__(self,
      vContext: ValueContext,
      hostSitesPair: HostSitesPair,
  ):
    """Add a new value context information."""
    self.valueContextMap[vContext] = hostSitesPair
    self.maxVcMapSize = max(self.maxVcMapSize, len(self.valueContextMap))


  def __delitem__(self, vContext: ValueContext):
    del self.valueContextMap[vContext]


  def __contains__(self, vContext: ValueContext) -> bool:
    """Is the context present?"""
    return vContext in self.valueContextMap


  def __len__(self) -> int:
    return len(self.valueContextMap)


  def __iter__(self):
    return iter(self.valueContextMap)


  def keys(self):
    return self.valueContextMap.keys()


  def values(self):
    return self.valueContextMap.values()


  def items(self):
    return self.valueContextMap.items()


  def removeCtxSite(self,
      vContext: ValueContext,
      callSite: GlobalNodeIdT,
  ) -> None:
    """Removes a call site from the HostSitePair instance
    for the given context."""
    hostSitesPair = self.valueContextMap.get(vContext, None)
    if hostSitesPair:
      hostSitesPair.removeSite(callSite)
      if ff.IPA_VC_REMOVE_UNUSED_VC:
        if not hostSitesPair.hasCallSites():
          del self[vContext]  # delete when no site needs the value context


  def getPrevValueContext(self,
      callSitePair: CallSitePair,
      parentInvocationId: InvocationIdT,
  ) -> Opt[ValueContext]:
    """Get previous value context at the given call site pair.
    This is used to re-use the host object for a new value context.
    """
    if not self.reUsePrevValueContextHost:
      return None

    tup = (callSitePair, parentInvocationId)
    return self.callSitePairContextMap.get(tup, None)


  def setPrevValueContext(self,
      callSitePair: CallSitePair,
      parentInvocationId: InvocationIdT,
      vContext: ValueContext,
  ) -> None:
    """Set value context at the given call site pair.
    This is used to re-use the host object for a new value context,
    at the same call site and invocation of the function.
    """
    if not self.reUsePrevValueContextHost:
      return

    tup = (callSitePair, parentInvocationId)
    self.callSitePairContextMap[tup] = vContext


  def clear(self, hard=False):
    """Clears the redundant data after computation."""
    if util.LL2: LDB(f"ValueContextInfo(Before:Clear):"
                     f" Size: {util.getSize2(self)}")

    self.valueContextMap.clear()
    self.callSitePairContextMap.clear()
    self.callSiteContextMapStack.clear()
    if hard: self.finalResult.clear()

    n = gc.collect()
    if util.LL2: LDB(f"ValueContextInfo(After:Clear):"
                     f" Size: {util.getSize2(self)} (gc.collect(): {n})")


  def clearPrevValueContexts(self,
      callSitePairs: Set[CallSitePair],
      invocationId: int, # the invocation id used in `self.setPrevValueContext()`
  ) -> None:
    for callSitePair in callSitePairs:
      tup = (callSitePair, invocationId)
      if tup in self.callSitePairContextMap:
        del self.callSitePairContextMap[tup]


  def removeSiteStack(self, callSitePair):
    if callSitePair in self.callSiteContextMapStack:
      ctx = self.callSiteContextMapStack[callSitePair]
      if not ctx.decDepth(): # remove when depth == 0.
        del self.callSiteContextMapStack[callSitePair]


  def getCallStackCtx(self, callSitePair) -> Opt[AnDfvPairDict]:
    if callSitePair in self.callSiteContextMapStack:
      return self.callSiteContextMapStack[callSitePair]
    return None


  def setCallStackCtx(self, callSitePair, dfvDict: AnDfvPairDict):
    self.callSiteContextMapStack[callSitePair] = dfvDict


class IpaHost:


  def __init__(self,
      tUnit: TranslationUnit,
      entryFuncName: FuncNameT = conv.ENTRY_FUNC,
      mainAnName: Opt[AnNameT] = None,
      otherAnalyses: Opt[List[AnNameT]] = None,
      supportAnalyses: Opt[List[AnNameT]] = None,
      avoidAnalyses: Opt[List[AnNameT]] = None,
      maxNumOfAnalyses: int = ff.MAX_ANALYSES,
      inputAnResults: Opt[Dict[FuncNameT, Dict[AnNameT, AnResult]]] = None,
      disableAllSim: bool = False,
      useTransformation: bool = False,
      useDdm: bool = False,
      reUsePrevValueContextHost: bool = ff.IPA_VC_RE_USE_PREV_VALUE_CONTEXT_HOST,
      widenValueContext: bool = ff.IPA_VC_WIDEN_VALUE_CONTEXT,
  ) -> None:
    if tUnit is None or not tUnit.getFuncObj(entryFuncName):
      raise ValueError(f"No {entryFuncName} in translation unit {tUnit.name}.")

    self.tUnit = tUnit
    self.entryFuncName = entryFuncName
    self.mainAnName = mainAnName
    self.otherAnalyses = otherAnalyses
    self.supportAnalyses = supportAnalyses  # TODO: pass it to span.sys.host.Host
    self.avoidAnalyses = avoidAnalyses
    self.maxNumOfAnalyses = maxNumOfAnalyses
    self.inputAnResults = inputAnResults
    self.disableAllSim = disableAllSim
    self.useTransformation = useTransformation
    self.useDdm = useDdm
    self.reUsePrevValueContextHost = reUsePrevValueContextHost
    self.widen = widenValueContext

    # invocation id uniquely identifies the invocation instance of analyzeFunc()
    self.invocationId = 0
    self.gst = GlobalStats()

    self.vci: ValueContextInfo = ValueContextInfo(reUsePrevValueContextHost)

    self.logUsefulInfo()


  def analyze(self) -> Dict[FuncNameT, Dict[AnNameT, AnResult]]:
    """Call this function to start the IPA analysis.

    It returns the final results computed.
    """
    if util.LL1: LIN("\n\nIpaHost_Analyze: Start #####################")

    # STEP 1: Analyze the global inits and extract its BI
    if util.LL1: LIN("AnalyzingFunction(IpaHost:START): %s %s",
                    GLOBAL_INITS_FUNC_NAME, "*" * 16)
    hostGlobal = self.createHostInstance(GLOBAL_INITS_FUNC_NAME, ipa=False)
    hostGlobal.analyze()
    if util.LL1: LIN("AnalyzingFunction(IpaHost:DONE:Miss): %s %s",
                     GLOBAL_INITS_FUNC_NAME, "*" * 16)
    hostGlobal.printOrLogResult()

    globalBi = hostGlobal.getBoundaryResult()
    globalBi = self.swapGlobalBiInOut(globalBi)
    if util.LL2: LDB("GlobalBi(%s): %s", GLOBAL_INITS_FUNC_NAME, globalBi)

    # STEP 2: start analyzing from the entry function
    callSitePair = CallSitePair(self.entryFuncName,
                                genGlobalNodeId(GLOBAL_INITS_FUNC_ID, 0))
    mainBi = self.prepareEntryFuncBi(self.entryFuncName, globalBi)
    self.analyzeFunc(callSitePair, mainBi, GLOBAL_INITS_FUNC_NAME)

    # STEP 3: finalize IPA results
    self.finalizeIpaResults()
    self.clear() # clear the memory

    if util.LL1: LIN("\n\nIpaHost_Analyze: End #####################")

    return self.vci.finalResult


  def analyzeFunc(self,
      callSitePair: CallSitePair, # location of the call (has callee name too)
      ipaFuncBi: AnDfvPairDict, # the boundary info (value context)
      parentName: FuncNameT, # i.e. caller name
      rDepth: int = 0, # recursion depth, start with 0
      parentInvocationId: InvocationIdT = 0, # start with 0
  ) -> AnDfvPairDict:
    thisInvocationId, vci = self.getNewInvocationId(), self.vci
    currFuncName, callSite = callSitePair.tuple()
    if util.LL1: LIN("AnalyzingFunction(IpaHost:START):"
                    " %s, Caller: %s, InvocationId:(Parent:%s, This:%s): %s",
                     callSitePair, parentName, parentInvocationId, thisInvocationId,
                     "*" * 16)
    if util.LL2: LDB(f"RecursionDepth: {rDepth}, VContextSize: {len(vci)}")
    if util.LL2: LDB(f" ValueContext(CurrBi:BeforeWidening({self.widen})):"
                     f" {ipaFuncBi}")

    if rDepth >= ff.IPA_VC_RECURSION_LIMIT:
      return self.analyzeFuncFinal(callSitePair, ipaFuncBi, rDepth)

    if self.widen:
      ipaFuncBi = self.widenTheValueContext(callSitePair, ipaFuncBi)

    vContext = ValueContext(callSitePair.funcName, ipaFuncBi.getCopyShallow())
    if util.LL2: LDB(f" ValueContext(CurrBi:AfterWidening({self.widen})):"
                     f" Id:{id(vContext)}, {vContext}")
    host, preComputed = self.getComputedValue(
      callSitePair, parentInvocationId, vContext)

    if preComputed:
      if self.widen: vci.removeSiteStack(callSitePair)
      if util.VV1: print(f"{util.dsf(rDepth)} AnalyzingFunction(IpaHost):"
                         f" {currFuncName} ({callSitePair}) [HIT]")
      if util.LL1: LIN("AnalyzingFunction(IpaHost:DONE:HIT):"
                       " %s, Caller: %s, InvocationId:(Parent:%s, This:%s): %s",
                       callSitePair, parentName, parentInvocationId, thisInvocationId,
                       "*" * 16)
      return host.getBoundaryResult() # HIT! Use prev result.

    if util.VV1: print(f"{util.dsf(rDepth)} AnalyzingFunction(IpaHost):"
                       f" {currFuncName} ({callSitePair}) [MISS]")
    ##### Current Callee is now a Caller #######################################
    allCallSites, callerName, reAnalyze = set(), currFuncName, True

    while reAnalyze:
      reAnalyze = False
      host.analyze()  # RUN THE ANALYSIS.

      callSiteDfvs = host.getCallSiteDfvsIpaHost()
      if callSiteDfvs:  # check if call sites present
        for csPair in sorted(callSiteDfvs.keys(), key=lambda x: x.callSite):
          calleeName, calleeSite = csPair.tuple()
          allCallSites.add(csPair)

          calleeBi = callSiteDfvs[csPair]
          if util.LL2: LDB(f"CalleeBi ({callerName} --> {calleeName})(Old):\n {calleeBi}")
          newCalleeBi = self.analyzeFunc(csPair, calleeBi, currFuncName, rDepth + 1,
                                         thisInvocationId) #recurse
          if util.LL2: LDB(f"CalleeBi ({callerName} --> {calleeName})(New):\n {newCalleeBi}")
          reAnalyze = host.setCallSiteDfvsIpaHost(csPair, newCalleeBi)

          if util.VV2: self.printToDebug(calleeName, calleeBi, newCalleeBi, reAnalyze)
          if util.CC2: self.checkInvariants1(calleeName, calleeBi)

          if reAnalyze: break  # first re-analyze then goto other call sites

      if reAnalyze and util.LL1:
        LDB("AnalyzingFunction(IpaHost:ReStart:Miss):"
            " %s, Caller: %s, InvocationId:(Parent:%s, This:%s): %s",
            callSitePair, parentName, parentInvocationId,
            thisInvocationId, "*" * 16)
      if util.LL2: LDB(f" ValueContext: Id:{id(vContext)}, {vContext}")

    host.printOrLogResult()
    vci.clearPrevValueContexts(allCallSites, thisInvocationId)
    if self.widen: vci.removeSiteStack(callSitePair)
    if util.LL1: LIN("AnalyzingFunction(IpaHost:DONE:Miss):"
                     " %s, Caller: %s, InvocationId:(Parent:%s, This:%s): %s",
                     callSitePair, parentName, parentInvocationId,
                     thisInvocationId, "*" * 16)
    return host.getBoundaryResult()


  def widenTheValueContext(self, #widen
      callSitePair: CallSitePair,
      currDfvDict: AnDfvPairDict,
  ) -> AnDfvPairDict:
    assert self.widen
    wideDfvDict, vci = None, self.vci
    prevStackCtx = vci.getCallStackCtx(callSitePair)

    if prevStackCtx:
      if prevStackCtx.depth >= ff.IPA_VC_MAX_WIDENING_DEPTH:
        if util.LL2: LDB(" Widening w.r.t. ValueContext(PrevBi): %s", prevStackCtx)
        widenedBi = dict()
        for anName, prevNdfv in prevStackCtx.dfvs.items():
          currNdfv = currDfvDict[anName]
          widenedBi[anName], _ = prevNdfv.widen(currNdfv) #widen here
        wideDfvDict = AnDfvPairDict(widenedBi, 1) # initial depth=1
      else:
        currDfvDict.setIncDepth(prevStackCtx) #IMPORTANT

    newDfvDict = wideDfvDict if wideDfvDict else currDfvDict
    vci.setCallStackCtx(callSitePair, newDfvDict)  # memoize
    return newDfvDict


  def printToDebug(self, calleeName, calleeBi, newCalleeBi, reAnalyze):
    if util.CC >= util.CC1 and calleeName in ("f:_read_min"):
      ptaOld = calleeBi["PointsToA"].dfvOut
      ptaNew = newCalleeBi["PointsToA"].dfvOut
      # ptaNew = nonLocalDfvs["PointsToA"].dfvIn
      if ptaOld.val and ptaNew.val:
        print(f"PTA/INTERVAL diff ({reAnalyze}):")
        ptaOldSet = set((k,v) for k,v in ptaOld.val.items())
        ptaNewSet = set((k,v) for k,v in ptaNew.val.items())
        print(f"Diff (Old-New): ({len(ptaOldSet)}, {len(ptaNewSet)})",
              sorted(ptaOldSet - ptaNewSet))
        print(f"Diff (New-Old): ({len(ptaOldSet)}, {len(ptaNewSet)})",
              sorted(ptaNewSet - ptaOldSet))
      else:
        print(f"PTA diff: on of the val is None/Empty"
              f" {ptaOld.top}, {ptaNew.top} || {ptaOld.bot}, {ptaNew.bot}")
      # print(f"ReAnalyze: {reAnalyze} ({calleeName}):"
      #       f"\n OLD: {dfvs}\n NEW: {newDfvs}") #delit


  def checkInvariants1(self,
      funcName: FuncNameT,
      nodeDfvs: AnDfvPairDict,
  ) -> None:
    pass


  def analyzeFuncFinal(self,
      callSitePair: CallSitePair,
      funcBi: AnDfvPairDict,
      recursionDepth: int,
  ) -> AnDfvPairDict:
    """
    For problems where Value Context may not terminate,
    finally fail/terminate at this function.
    """
    raise AssertionError(f"AnalyzeFuncFinal: (Depth: {recursionDepth}):"
                         f" {callSitePair}, {funcBi}")


  def getComputedValue(self,
      callSitePair: CallSitePair,
      parentInstanceId: int,
      vContext: ValueContext,
  ) -> Tuple[Host, bool]:
    """Returns the host object, and true if its present in the saved
    value contexts"""
    vci = self.vci

    if vContext in vci: # memoized results
      hostSitePair = vci[vContext]
      if util.LL2: LDB(f"ValueContextCache: HIT !! :)")
      hostSitePair.addSite(callSitePair.callSite)
      return hostSitePair.host, True

    if self.reUsePrevValueContextHost:
      prevHost = self.getPrevValueContextHost(
        callSitePair, parentInstanceId, vContext)
      if prevHost: return prevHost, False

    # vContext not present, hence create one and attach a Host instance
    if util.LL2: LDB("ValueContextCache(New): id:%s, %s", id(vContext), vContext)
    vContextCopy = vContext.getCopy() # FIXME: can this be removed?
    hostInstance = self.createHostInstance(
      vContext.funcName, biDfv=vContextCopy.dfvDict)
    vci[vContext] = HostSitesPair(hostInstance, {callSitePair.callSite})

    return hostInstance, False


  def getPrevValueContextHost(self,
      callSitePair: CallSitePair,
      parentInstanceId: int,
      vContext: ValueContext,
  ) -> Opt[Host]:
    """Returns the previous host object if present."""
    if util.LL2: LDB(f"ValueContextCache: MISS !! :(")
    vci = self.vci
    prevValueContext = self.getPrevValueContext(
      callSitePair, parentInstanceId, vContext)
    if prevValueContext is None:
      return None

    if util.LL2: LDB(f"ValueContextCache(Prev:OlderCtx):"
                     f" Id:{id(prevValueContext)}, {prevValueContext}")
    hostSitesPair = vci[prevValueContext]
    if not hostSitesPair.hasSingleSite():
      # since more than one callSite may need the vContext, hence cannot modify
      vci.removeCtxSite(prevValueContext, callSitePair.callSite)
      return None

    if util.LL2: LDB(f"ValueContextCache(Prev:ReUsing):"
                     f" Id:{id(prevValueContext)}, {prevValueContext}")
    del vci[prevValueContext]
    vci[vContext] = hostSitesPair
    vci.setPrevValueContext(callSitePair, parentInstanceId, vContext) # replace
    host = hostSitesPair.host
    host.setBoundaryResult(vContext.getCopy().dfvDict) # FIXME: is copy needed?
    return host


  def getPrevValueContext(self,
      callSitePair: CallSitePair,
      parentInvocationId: int,
      vContext: ValueContext,
  ) -> Opt[ValueContext]:
    vci = self.vci
    prevCtx = vci.getPrevValueContext(callSitePair, parentInvocationId)

    if prevCtx:
      if util.LL2: LDB(f"ValueContextCache(Prev:fetch) prev context at"
                       f" Site:{callSitePair}:"
                       f" with ParentInvocationId:{parentInvocationId}"
                       f"\n vContext(prev): id:{id(prevCtx)}, {prevCtx}")
      return prevCtx
    else:
      if util.LL2: LDB(f"ValueContextCache(Prev:saving) context at"
                       f" Site:{callSitePair},"
                       f" with ParentInvocationId:{parentInvocationId}"
                       f"\n vContext: id:{id(vContext)}, {vContext}")
      vci.setPrevValueContext(callSitePair, parentInvocationId, vContext)
    return None


  def prepareEntryFuncBi(self,
      funcName: FuncNameT,
      bi: AnDfvPairDict,
  ) -> AnDfvPairDict:
    func, newBi = self.tUnit.getFuncObj(funcName), AnDfvPairDict()

    for anName, nDfv in bi:
      AnalysisClass = clients.analyses[anName]
      anObj = AnalysisClass(func)

      # localize the boundary info
      newDfvIn = nDfv.dfvIn.localize(func, keepParams=True)
      newDfvOut = nDfv.dfvOut.localize(func, keepParams=True)
      localized = DfvPairL(newDfvIn, newDfvOut)

      newBi[anName] = anObj.getBoundaryInfo(localized, ipa=True, entryFunc=True)

    if util.LL2: LDB("IpaBi: (%s): %s", funcName, newBi)
    return newBi


  def swapGlobalBiInOut(self, globalBi: AnDfvPairDict) -> AnDfvPairDict:
    """Swaps IN and OUT, because the OUT of the end node in
    the global function is the IN of the main() function."""
    for anName, nDfv in globalBi:
      nDfv.dfvIn, nDfv.dfvOut = nDfv.dfvOut, nDfv.dfvIn
      nDfv.dfvOutFalse = nDfv.dfvOutTrue = nDfv.dfvOut
    return globalBi


  def createHostInstance(self,
      funcName: FuncNameT,
      ipa: bool = True,
      biDfv: Opt[AnDfvPairDict] = None,
      useDdm: bool = False,  #DDM
  ) -> Host:
    """Create an instance of Host for the given function"""

    func = self.tUnit.getFuncObj(funcName)
    inputAnResults = self.inputAnResults.get(func.name, None)\
      if self.inputAnResults else None

    return Host(
      func=func,
      mainAnName=self.mainAnName,
      otherAnalyses=self.otherAnalyses,
      avoidAnalyses=self.avoidAnalyses,
      maxNumOfAnalyses=self.maxNumOfAnalyses,
      inputAnResults=inputAnResults,
      disableSim=self.disableAllSim,
      biDfv=biDfv,
      ipaEnabled=ipa,
      useTransformation=self.useTransformation,
      useDdm=useDdm,
    )


  def finalizeIpaResults(self):
    vci = self.vci
    if util.VV0:
      print(f"\n"
            f"TotalValueContexts     : {len(vci)}\n"
            f"TotalSize(ValueContext): {util.getSize2(vci.valueContextMap)//1024} KB.\n"
            f"TotalSize(VCI object)  : {util.getSize2(vci)//1024} KB.\n")

    self.collectStats()
    self.mergeFinalResults()

    if util.VV2:
      print("\n\nFINAL RESULTS of IpaHost:")
      print("=" * 48)
      self.printFinalResults()


  def collectStats(self):
    """Collects various statistics."""
    for vc, hostSitesPair in self.vci.valueContextMap.items():
      hostSitesPair.host.collectStats(self.gst)
    if util.VV1: self.gst.print()


  def printSimCounts(self, msg=""):
    """Prints the number of simplifications done."""
    assert self.vci.finalResult
    finalResult = self.vci.finalResult
    print(f"\n\nSimplificationCounts {msg}")

    anName = "IntervalA"
    condSimCount = 0
    intervalA = clients.analyses[anName]

    for funcName, allResults in finalResult.items():
      func = self.tUnit.getFuncObj(funcName)
      if anName in allResults:
        intervalRes = allResults[anName]
        condSimCount += intervalA.countSimCondToUncond(func, intervalRes)

    print(f"  CondToUncondSims Count: {condSimCount}\n")


  def mergeFinalResults(self):
    """Computes the final result of an IPA computation.
    It merges all the results of all the contexts of a function
    to get the static data flow information of that function."""
    vci = self.vci
    vci.finalResult = {}
    allFuncNames = set(vc.funcName for vc in vci.valueContextMap.keys())
    notVisitedFuns = {f.name for f in self.tUnit.yieldFunctionsWithBody()}\
                     - allFuncNames

    if util.LL1: LDB(f"MergingResultsOfFunctions:"
                     f" Total {len(allFuncNames):<5}"
                     f" NotVisited({len(notVisitedFuns)}):"
                     f" {sorted(notVisitedFuns)}")
    if util.VV1: print(f"MergingResultsOfFunctions:"
                       f" Total {len(allFuncNames):<5}"
                       f" NotVisited({len(notVisitedFuns)}):"
                       f" {sorted(notVisitedFuns)}")

    for i, funcName in enumerate(sorted(allFuncNames)):
      funcResult = {}
      if util.LL1:
        LDB(f"MergingResultsOfFunc: {funcName} ({i+1:>5}/{len(allFuncNames):<5})")
      for valContext, hostSitesPair in vci.valueContextMap.items():
        host = hostSitesPair.host
        if valContext.funcName == funcName:
          assert host.func.name == funcName, f"{funcName}, {host.func.name}"
          allAnalysisNames = host.getAllAnalysesUsed()
          for anName in allAnalysisNames:
            currRes = host.getAnalysisResults(anName)
            if anName not in funcResult:
              funcResult[anName] = currRes
            else:
              prevRes = funcResult[anName]
              newRes  = prevRes.merge(currRes)
              funcResult[anName] = newRes
      vci.finalResult[funcName] = funcResult


  def delitTestResult(self,  #delit
      anName: str,
      res: Dict[cfg.CfgNodeId, DfvPairL],
      nid: int,
      vName: str,
  ):
    if anName != "IntervalA": return
    if nid in res:
      dfv = res[nid].dfvOut
      val = dfv.getVal(vName)
    else:
      val = f"Top(nid {nid} not present)"
    print(f"SIM_:({vName}): {val}")


  @staticmethod
  def mergeAnalysisResult(result1: Dict[cfg.CfgNodeId, DfvPairL],
      result2: Dict[cfg.CfgNodeId, DfvPairL]
  ) -> Dict[cfg.CfgNodeId, DfvPairL]:
    """Modifies `result1` argument (and returns it)."""
    cfgNodeIds = set(result1.keys())
    cfgNodeIds.update(result2.keys())

    for nid in cfgNodeIds:
      if nid in result1 and nid in result2:
        result1[nid], _ = result1[nid].meet(result2[nid])
      elif nid in result2:
        result1[nid] = result2[nid]

    return result1


  def logUsefulInfo(self):
    if not util.LL1: return

    sio = io.StringIO()
    sio.write(f"IpaHostConfiguration:\n")
    sio.write(f"  TranslationUnit: {self.tUnit.name}\n")
    sio.write(f"  EntryFuncName  : {self.entryFuncName}\n")
    sio.write(f"  MainAnalysis   : {self.mainAnName}\n")
    sio.write(f"  OtherAnalyses  : {self.otherAnalyses}\n")
    sio.write(f"  AvoidAnalyses  : {self.avoidAnalyses}\n")
    sio.write(f"  SupportAnalyses: {self.supportAnalyses}\n")
    sio.write(f"  MaxAnalyses    : {self.maxNumOfAnalyses}\n")
    sio.write(f"  DisableAllSim  : {self.disableAllSim}\n")
    sio.write(f"  UseTransform   : {self.useTransformation}\n")
    sio.write(f"  UseDDM         : {self.useDdm}\n")
    sio.write(f"  ReUsePrevValCxt: {self.reUsePrevValueContextHost}\n")
    sio.write(f"  UseWidening    : {self.widen}\n")

    LIN(sio.getvalue())


  def printFinalResults(self):
    vci = self.vci
    for funcName, res in sorted(vci.finalResult.items(), key=lambda x: x[0]):
      print(f"\nFunction: '{funcName}', TUnit: {self.tUnit.name} *****")
      for anName, anRes in sorted(res.items(), key=lambda x: x[0]):
        print()
        print(anRes)

    for funcName, res in sorted(vci.finalResult.items(), key=lambda x: x[0]):
      func = self.tUnit.getFuncObj(funcName)
      print(f"\nFunction: '{funcName}', TUnit: {self.tUnit.name} *****")
      for anName, anRes in sorted(res.items(), key=lambda x: x[0]):
        print(f"{anName}: '{funcName}'")

        topTop = "IN: Top, OUT: Top, TRUE: Top, FALSE: Top (Unreachable/Nop)"
        for node in func.cfg.revPostOrder:
          nid = node.id
          nDfv = anRes.get(nid, topTop)
          print(f">> {nid}. ({node.insn}): {nDfv}")


  def clear(self, hard=False):
    self.vci.clear(hard)


  def getNewInvocationId(self):
    """Returns a unique number each time.
    This helps distinguish one invocation of analyzeFunc() from another."""
    self.invocationId += 1
    return self.invocationId


def ipaAnalyzeCascade(
    tUnit: TranslationUnit,
    anSequence: List[List[AnNameT]],
) -> Dict[FuncNameT, Dict[AnNameT, AnResult]]:
  """
  Runs Inter-Procedural technique for Cascading.

  The results of each step are fed into the next step.

  Args:
    tUnit: The translation unit.
    anSequence: Sequence of a sequence of analyses names. Each sequence,
           in the sequence, forms one step of Cascading which is run
           using Lerner's approach. To run pure Cascading, specify
           only one analysis name in each subsequence. For example,
           `[["IntervaA"],["PointsToA"]]` runs pure cascading of the
           two analyses, and `[["IntervalA","EvenOddA"],["PointsToA"]]`
           runs two cascaded steps and in the first step runs the two
           analyses IntervalA and EvenOddA together with Lerner's approach.

  Returns:
    The results computed in each function, for each analysis.
  """
  assert isinstance(anSequence, list), f"({tUnit.name}): {anSequence}"

  res, ipaHost = None, None
  for seq in anSequence:
    assert isinstance(seq, (str, list)), f"'{seq}' in '{anSequence}'"

    # In case the list is like `["IntervalA", "PointsToA"]`:
    anSeq: List[AnNameT] = seq if isinstance(seq, list) else [seq]

    ipaHost = IpaHost(
      tUnit=tUnit,
      mainAnName=anSeq[0],
      otherAnalyses=anSeq[1:],
      maxNumOfAnalyses=len(anSeq),
      inputAnResults=res,
      useTransformation=True,
    )
    res = ipaHost.analyze()

  # do something with the final ipaHost object if needed, here

  return res


def diagnoseInterval(tUnit: TranslationUnit):
  """A diagnosis called by the main driver.
  Run interval analysis using SPAN
  then using Lerner's
  """
  #mainAnalysis = "ConstA"
  mainAnalysis = "IntervalA"
  #mainAnalysis = "PointsToA"
  otherAnalyses : List[str] = ["PointsToA"]
  #otherAnalyses : List[str] = ["EvenOddA"]
  #otherAnalyses : List[str] = []
  maxNumOfAnalyses = len(otherAnalyses) + 1

  ipaHostSpan = IpaHost(tUnit,
                        mainAnName=mainAnalysis,
                        otherAnalyses=otherAnalyses,
                        maxNumOfAnalyses=maxNumOfAnalyses
                        )
  ipaHostSpan.analyze()
  if util.VV1: ipaHostSpan.printSimCounts("SPAN")

  ipaHostLern = IpaHost(tUnit,
                        mainAnName=mainAnalysis,
                        otherAnalyses=otherAnalyses,
                        maxNumOfAnalyses=maxNumOfAnalyses,
                        useTransformation=True,
                        )
  # ipaHostLern = IpaHost(tUnit,
  #                       mainAnName="PointsToA",
  #                       otherAnalyses=None,
  #                       maxNumOfAnalyses=1,
  #                       )
  #ipaHostLern = IpaHost(tUnit, mainAnName=mainAnalysis, maxNumOfAnalyses=1) # span with single analysis
  ipaHostLern.analyze()
  if util.VV1: ipaHostLern.printSimCounts("TRANSFORM")

  # computeStats01("IntervalA", ipaHostSpan, ipaHostLern)
  # computeStats01("PointsToA", ipaHostSpan, ipaHostLern, tUnit)
  computeStatsAverageDeref("PointsToA", ipaHostSpan, ipaHostLern, tUnit)
  computeStatsIntervalPrecision("IntervalA", ipaHostSpan, ipaHostLern, tUnit)
  computeStatsDivByZeroPrecision("IntervalA", ipaHostSpan, ipaHostLern, tUnit)

  takeTracemallocSnapshot()


def computeStats01(
    mainAnName: AnNameT,
    ipaHostSpan: IpaHost,
    ipaHostOther: IpaHost,
    tUnit: TranslationUnit,
):
  totalPPoints = 0  # total program points
  weakPPoints = 0  # weak program points
  totalPreciseComparisons1 = 0
  totalPreciseComparisons2 = 0
  total1 = 0

  if util.VV1: print("Weak points and the values.")
  if util.VV1: print("=" * 48)
  for funcName in ipaHostSpan.vci.finalResult.keys():
    if not (funcName in ipaHostSpan.vci.finalResult and
      funcName in ipaHostOther.vci.finalResult): continue

    interSpan = ipaHostSpan.vci.finalResult[funcName][mainAnName]
    interOther = ipaHostOther.vci.finalResult[funcName][mainAnName]

    for nid in sorted(interSpan.keys()):
      nDfvSpan = interSpan[nid]
      nDfvOther = interOther[nid]

      totalPPoints += 2

      if nDfvSpan.dfvIn != nDfvOther.dfvIn \
          and nDfvOther.dfvIn < nDfvSpan.dfvIn:
        weakPPoints += 1

      if nDfvSpan.dfvOut != nDfvOther.dfvOut:
        valS = nDfvSpan.dfvOut.val
        valL = nDfvOther.dfvOut.val
        if valS and valL:
          setS, setL = set(valS.items()), set(valL.items())
          if util.VV1: print(f"NOT_SAME ({nid})({funcName}):"
                f"\n  S-L:{sorted(setS-setL)}\n  L-S:{sorted(setL-setS)}")
        else:
          if util.VV1: print(f"NOT_SAME ({nid})({funcName}): {valS} {valL}")
      if nDfvSpan.dfvOut != nDfvOther.dfvOut \
          and nDfvOther.dfvOut < nDfvSpan.dfvOut:
        weakPPoints += 1

      # # some queries
      # node = tUnit.getNode(funcName, nid)
      # assert node, f"{funcName} {nid}"
      # if node:
      #   insn = node.insn
      #   if isinstance(insn, instr.AssignI)\
      #       and isinstance(insn.rhs, expr.BinaryE):
      #     rhs: expr.BinaryE = insn.rhs
      #     if rhs.opr.isRelationalOp():
      #       total1 += 1
      #       lhs = cast(expr.VarE, insn.lhs)
      #       name = lhs.name
      #       val1 = nDfvSpan.dfvOut.getVal(name)
      #       if val1.isConstant():
      #         totalPreciseComparisons1 += 1
      #       val2 = nDfvOther.dfvOut.getVal(name)
      #       if val2.isConstant():
      #         print(f"{node.id}: {name}: {val1}, {val2} ({insn.info})")
      #         totalPreciseComparisons2 += 1

  print(f"\n{mainAnName}: TotalPPoints:", totalPPoints, "WeakPPoints:", weakPPoints)
  # print(f"TotalPreciseComparisons: {totalPreciseComparisons1}"
  #       f" ({totalPreciseComparisons2}) / {total1}")



def computeStatsAverageDeref(
    mainAnName: AnNameT, # always a pointer analysis
    ipaHostSpan: IpaHost,
    ipaHostOther: IpaHost,
    tUnit: TranslationUnit,
):
  """Compute "Average Deref" Metric."""
  rhsDerefPointCount = 1
  rhsDerefPointeesCount = [0, 0] # [0] Span, [1] Other
  lhsDerefPointCount = 1
  lhsDerefPointeesCount = [0, 0] # [0] Span, [1] Other

  AnClass = clients.analyses[mainAnName]

  for funcName in sorted(ipaHostSpan.vci.finalResult.keys()):
    #FIXME: skipping some functions here
    if util.VV1: print(f"FUNC_NAME (ForAvgDerefCompute): {funcName}")
    if not (funcName in ipaHostSpan.vci.finalResult and
            funcName in ipaHostOther.vci.finalResult):
      if util.VV1: print(f"  SKIPPING_FUNC (ForAvgDerefCompute): {funcName}")
      continue

    interSpan = ipaHostSpan.vci.finalResult[funcName][mainAnName]
    interOther = ipaHostOther.vci.finalResult[funcName][mainAnName]
    fObj = tUnit.getFuncObj(funcName)
    nodeMap = fObj.cfg.nodeMap

    anObj: AnalysisAT = AnClass(fObj)

    for nid in sorted(interSpan.keys()):
      insn = nodeMap[nid].insn
      if not getDerefExpr(insn): continue

      assert isinstance(insn, AssignI), f"{funcName}, {nid}, {insn}, {insn.info}"
      lhsDeref, rhsDeref = expr.getDerefExpr(insn.lhs), expr.getDerefExpr(insn.rhs)
      derefE = lhsDeref if lhsDeref else rhsDeref
      varE = derefE.getDereferencedVarE()
      assert varE, f"{funcName}, {nid}, {insn}, {derefE}, {varE}, {insn.info}"

      lhsDerefPointCount += 1 if lhsDeref else 0
      rhsDerefPointCount += 1 if rhsDeref else 0

      nDfvSpan = interSpan[nid]
      nDfvOther = interOther[nid]

      sims = anObj.Deref__to__Vars(varE, nDfvSpan), anObj.Deref__to__Vars(varE, nDfvOther)

      for i, sim in enumerate(sims):
        oldSim = sim
        # sim = SimFailed if i == 1 and tUnit.hasAbstractVars(sim) else sim
        # sim = SimFailed if sim and i == 1 and len(sim) > 1 else sim

        if i == 1 and util.VV1 and sim != sims[0]:
          print(f"DEREF_DIFFERENCE {funcName} (DIFF): {derefE}, {insn}, {insn.info}:"
                f"\n  Other( NO ): {oldSim},\n  Span( YES ): {sims[0]}")

        if sim: # some set of values
          lhsDerefPointeesCount[i] += len(sim) if lhsDeref else 0
          rhsDerefPointeesCount[i] += len(sim) if rhsDeref else 0
        elif sim is SimFailed:
          allNames = tUnit.getNamesEnv(fObj, derefE.type)
          lhsDerefPointeesCount[i] += len(allNames) if lhsDeref else 0
          rhsDerefPointeesCount[i] += len(allNames) if rhsDeref else 0
        # elif sim is SimPending: count 0

  totalDerefPoints = lhsDerefPointCount + rhsDerefPointCount
  totalDerefPointeesCount = [lhsDerefPointeesCount[0] + rhsDerefPointeesCount[0],
                             lhsDerefPointeesCount[1] + rhsDerefPointeesCount[1]]
  if True:
    print(f"\nAverageDeref(Span) (Total): {totalDerefPointeesCount[0]/totalDerefPoints}")
    print(  f"AverageDeref(Other)(Total): {totalDerefPointeesCount[1]/totalDerefPoints}")
    print(f"\nAverageDeref(Span)   (LHS): {lhsDerefPointeesCount[0]/lhsDerefPointCount}")
    print(  f"AverageDeref(Other)  (LHS): {lhsDerefPointeesCount[1]/lhsDerefPointCount}")
    print(f"\nAverageDeref(Span)   (RHS): {rhsDerefPointeesCount[0]/rhsDerefPointCount}")
    print(  f"AverageDeref(Other)  (RHS): {rhsDerefPointeesCount[1]/rhsDerefPointCount}")


def computeStatsIntervalPrecision(
    mainAnName: AnNameT, # always Interval Analysis
    ipaHostSpan: IpaHost,
    ipaHostOther: IpaHost,
    tUnit: TranslationUnit,
):
  """Compute Interval Precision Comparison"""
  rValueEqual = 0 # equal by both the approaches
  rValueWorse = 0 # worse than the other approach
  rValuePointsPrecise = 0 # better than the other approach
  rValuePointsTotal = 0

  AnClass = clients.analyses[mainAnName]

  for funcName in sorted(ipaHostSpan.vci.finalResult.keys()):
    #FIXME: skipping some functions here
    if util.VV1: print(f"FUNC_NAME (ForIntervalPrecision): {funcName}")
    if not (funcName in ipaHostSpan.vci.finalResult and
            funcName in ipaHostOther.vci.finalResult):
      if util.VV1: print(f"  SKIPPING_FUNC (ForIntervalPrecision): {funcName}")
      continue

    interSpan = ipaHostSpan.vci.finalResult[funcName][mainAnName]
    interOther = ipaHostOther.vci.finalResult[funcName][mainAnName]
    fObj = tUnit.getFuncObj(funcName)
    nodeMap = fObj.cfg.nodeMap

    for nid in sorted(interSpan.keys()):
      insn = nodeMap[nid].insn
      rValueVars = insn.getRValueNames()
      if rValueVars and util.VV2:
        print(f"COMPARING_FOR_INSN: {funcName}: (NodId:{nid}): {insn}, {insn.info}")

      nDfvInSpan = interSpan[nid].dfvIn
      nDfvInOther = interOther[nid].dfvIn

      for vName in rValueVars:
        rValuePointsTotal += 1
        valSpan = nDfvInSpan.getVal(vName)
        valOther = nDfvInOther.getVal(vName)
        if valOther == valSpan:
          rValueEqual += 1
        elif valSpan < valOther and valOther != valSpan:
          rValueWorse += 1
          if util.VV1:
            print(f"MORE_WORSE: ({funcName}): {insn}, Var: {vName}"
                  f"\n SPAN : {valSpan},\n OTHER: {valOther}")
        if valOther < valSpan and valOther != valSpan:
          rValuePointsPrecise += 1
          if util.VV1:
            print(f"MORE_PRECISE: ({funcName}): {insn}, Var: {vName}"
                  f"\n SPAN : {valSpan},\n OTHER: {valOther}")

  print(f"TOTAL_PRECISION (IntervalA)(Better): {rValuePointsPrecise}/{rValuePointsTotal}")
  print(f"TOTAL_PRECISION (IntervalA) (Worse): {rValueWorse}/{rValuePointsTotal}")
  print(f"TOTAL_PRECISION (IntervalA) (Equal): {rValueEqual}/{rValuePointsTotal}")


def computeStatsDivByZeroPrecision(
    mainAnName: AnNameT, # always Interval Analysis
    ipaHostSpan: IpaHost,
    ipaHostOther: IpaHost,
    tUnit: TranslationUnit,
):
  """Compute Interval Precision Comparison"""
  totalDivCount = 0
  nonZeroDivSpan = 0
  nonZeroDivOther = 0

  AnClass = clients.analyses[mainAnName]

  for funcName in sorted(ipaHostSpan.vci.finalResult.keys()):
    #FIXME: skipping some functions here
    if util.VV1: print(f"FUNC_NAME (ForIntervalPrecision): {funcName}")
    if not (funcName in ipaHostSpan.vci.finalResult and
            funcName in ipaHostOther.vci.finalResult):
      if util.VV1: print(f"  SKIPPING_FUNC (ForIntervalPrecision): {funcName}")
      continue

    interSpan = ipaHostSpan.vci.finalResult[funcName][mainAnName]
    interOther = ipaHostOther.vci.finalResult[funcName][mainAnName]
    fObj = tUnit.getFuncObj(funcName)
    nodeMap = fObj.cfg.nodeMap

    for nid in sorted(interSpan.keys()):
      insn = nodeMap[nid].insn
      if isinstance(insn, AssignI):
        rhs = insn.rhs
        if isinstance(rhs, expr.BinaryE) and \
            rhs.opr == op.BO_DIV and isinstance(rhs.arg2, expr.VarE):
          totalDivCount += 1

          nDfvInSpan: OverallL = interSpan[nid].dfvIn
          nDfvInOther: OverallL = interOther[nid].dfvIn

          if not nDfvInSpan.getVal(rhs.arg2.name).inRange(0):
            nonZeroDivSpan += 1
          if not nDfvInOther.getVal(rhs.arg2.name).inRange(0):
            nonZeroDivOther += 1

  print(f"MORE_PRECISE: Total: {totalDivCount},\n SPAN: {nonZeroDivSpan}"
    f"\n OTHER: {nonZeroDivOther}")



