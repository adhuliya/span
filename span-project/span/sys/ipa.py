#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""
Inter-Procedural Analysis (IPA)
Using the Value-Context Method.
"""
import logging
_LOG = logging.getLogger(__name__)
LDB, LIN = _LOG.debug, _LOG.info

import io
from typing import Dict, Tuple, Set, List, cast, Optional as Opt, Type
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
from span.api.analysis import AnalysisNameT as AnNameT, DirectionDT, AnalysisAT, SimFailed, AnalysisAT_T
from span.api.dfv import DfvPairL, OverallL

from span.sys.host import Host
from span.sys.common import CalleeAndCallSite, AnDfvPairDict
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
      dfvPair: DfvPairL
  ) -> None:
    self.dfvDict[anName] = dfvPair


  def __eq__(self, other):
    if self is other: return True
    equal = True
    if not isinstance(other, ValueContext):
      equal = False
    elif not self.funcName == other.funcName:
      if util.LL2: LDB(f"unequal valuecontext: {self.funcName} other: {other.funcName}") #delit
      equal = False
    elif not self.dfvDict == other.dfvDict:
      if util.LL2: LDB(f"unequal valuecontext:\n self value:  {self.dfvDict}\n other value: {other.dfvDict}") #delit
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
    return f"ValueContext{idStr}({self.funcName}, {self.dfvDict})"


  def __repr__(self):
    return str(self)


class ComputedBoundaryResult:
  """Stores the Boundary Information and the callSites where its computation
  is (re)used due to common ValueContexts."""

  __slots__ : List[str] = ["result", "funcName", "callSites"]


  def __init__(self,
      funcName: FuncNameT,
      result: AnDfvPairDict,
      callSites: Opt[Set[GlobalNodeIdT]] = None,
  ):
    self.funcName = funcName
    self.result =  result
    # A set of call sites where this information is useful.
    # Currently unused but a useful metric to keep.
    self.callSites: Set[GlobalNodeIdT] = callSites if callSites else set()


  def hasCallSites(self) -> bool:
    return bool(self.callSites)


  def hasSingleSite(self):
    return len(self.callSites) == 1


  def addSite(self, callSite: GlobalNodeIdT):
    """Adds a site where the saved result is used."""
    self.callSites.add(callSite)


  def removeSite(self, callSite: GlobalNodeIdT):
    if callSite in self.callSites:
      self.callSites.remove(callSite)
    else:
      if util.LL1: LIN(f"WARN: {getGlobalNodeIdStr(callSite)} not present.")


  def __str__(self):
    return f"{self.__class__.__name__}({self.funcName}, {self.callSites})"


  def __repr__(self):
    return self.__str__()


class ValueContextInfo:
  """Value context method stores all its information in
  an object of ValueContextInfo."""

  def __init__(self,
      reUsePrevHostObject: bool = ff.IPA_VC_RE_USE_SAVED_HOST_OBJECTS,
  ):
    self.reUsePrevHostObject: bool = reUsePrevHostObject

    # This map stores the ValueContexts and the corresponding result
    self.valueContextMap: Dict[ValueContext, ComputedBoundaryResult] = {}

    # The site where the value context was saved / used.
    self.valueContextSite: \
      Dict[CalleeAndCallSite, ValueContext] = {}

    # Record the max size of value context map. (Useful for testing)
    # Useful when deleting some contexts to save memory. (Not currently used.)
    self.maxVcMapSize: int = 0

    # Map to store prev host object used at a call site,
    # to help reuse the previous host computation.
    self.callSiteToHostObjMap: \
      Dict[Tuple[CalleeAndCallSite, InvocationIdT], Host] = {}

    # The stack used to store value contexts in a stack of invocations.
    # This is used in termination of value contexts.
    # Note: The recursive function invocations track the order of CalleeAndCallSite.
    self.callSiteContextMapStack: Dict[CalleeAndCallSite, AnDfvPairDict] = {}

    self.finalResult: Dict[FuncNameT, Dict[AnNameT, AnResult]] = {}

    # Stores the number of contexts for each function (info for debugging etc.)
    self._funcContextCountMap: Dict[FuncNameT, int] = {}

    # CalleeAndCallSite stack to hold the stack of functions being
    # visited during the recursive call in the analyzeFunc() method
    self.analyzeFuncStack: List[CalleeAndCallSite] = []


  def __getitem__(self, vContext: ValueContext):
    """Get the stored value context information."""
    if vContext in self.valueContextMap:
      return self.valueContextMap[vContext]
    raise ValueError(f"ValueContext Missing"
                     f" (Total: {len(self.valueContextMap)}): {vContext}")


  def __setitem__(self,
      vContext: ValueContext,
      boundaryResult: ComputedBoundaryResult,
  ):
    """Add a new value context information."""
    self.valueContextMap[vContext] = boundaryResult
    self.countFuncCtx(vContext.funcName)
    self.maxVcMapSize = max(self.maxVcMapSize, len(self.valueContextMap))


  def __delitem__(self, vContext: ValueContext):
    self.countFuncCtx(vContext.funcName, add=False)
    del self.valueContextMap[vContext]


  def hasKey(self, vContext: ValueContext) -> bool:
    """Is the context present?"""
    return vContext in self.valueContextMap


  def getValue(self, vContext: ValueContext) -> Opt[ComputedBoundaryResult]:
    """Get the stored value context information."""
    if vContext in self.valueContextMap:
      return self.valueContextMap[vContext]
    return None


  def delKey(self, vContext: ValueContext):
    """Delete the value context."""
    self.countFuncCtx(vContext.funcName, add=False)
    del self.valueContextMap[vContext]
    if util.VV1: print(f"Deleted value context for function {vContext.funcName}")


  def addItem(self,
      vContext: ValueContext,
      boundaryResult: ComputedBoundaryResult,
  ):
    """Add a new value context information."""
    assert vContext.funcName == boundaryResult.funcName, f"{vContext.funcName}"
    self.valueContextMap[vContext] = boundaryResult
    self.countFuncCtx(vContext.funcName)
    self.maxVcMapSize = max(self.maxVcMapSize, len(self.valueContextMap))


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


  def getAllVisitedFuncNames(self):
    """Returns a set of function names visited for the analysis."""
    allFuncNames = set(vc.funcName for vc in self.valueContextMap.keys())
    allFuncNames |= set(self.finalResult.keys())
    return allFuncNames


  def removeCtxSite(self,
      vContext: ValueContext,
      callSite: GlobalNodeIdT,
  ) -> None:
    """Removes a call site from the ComputedBoundaryResult instance
    for the given context."""
    boundaryResult: ComputedBoundaryResult = self.valueContextMap.get(vContext, None)
    if boundaryResult:
      boundaryResult.removeSite(callSite)
      if ff.IPA_VC_REMOVE_UNUSED_VC:
        if not boundaryResult.hasCallSites():
          self.delKey(vContext)  # delete when no site needs the value context


  def getPrevHostObject(self,
      callSite: CalleeAndCallSite,
      parentInvocationId: InvocationIdT,
  ) -> Opt[Host]:
    """Returns previous host objects to optimize computations."""
    if not self.reUsePrevHostObject:
      return None

    tup = (callSite, parentInvocationId)
    return self.callSiteToHostObjMap.get(tup, None)


  def setPrevHostObject(self,
      callSite: CalleeAndCallSite,
      parentInvocationId: InvocationIdT,
      host: Host,
  ) -> None:
    """Saves temporary host objects to optimize computations."""
    if not self.reUsePrevHostObject:
      return

    tup = (callSite, parentInvocationId)
    self.callSiteToHostObjMap[tup] = host


  def clearPrevHostObjects(self,
      callSitePairs: Set[CalleeAndCallSite],
      invocationId: int, # the invocation id used in `self.setPrevHostObject()`
  ) -> None:
    """Removes temporary host objects completely."""
    if not self.reUsePrevHostObject:
      return

    for callSite in callSitePairs:
      tup = (callSite, invocationId)
      if tup in self.callSiteToHostObjMap:
        del self.callSiteToHostObjMap[tup]
    gc.collect() # to free up memory quickly


  def clear(self, hard=False):
    """Clears the redundant data after computation."""
    if util.LL2: LDB(f"ValueContextInfo(Before:Clear):"
                     f" Size: {util.getSize2(self)}")

    self.valueContextMap.clear()
    self.callSiteToHostObjMap.clear()
    self.analyzeFuncStack.clear()
    self.callSiteContextMapStack.clear()
    self._funcContextCountMap.clear()
    if hard:
      self.finalResult.clear()

    n = gc.collect()
    if util.LL2: LDB(f"ValueContextInfo(After:Clear):"
                     f" Size: {util.getSize2(self)} (gc.collect(): {n})")


  def removeSiteStack(self, callSite):
    if callSite in self.callSiteContextMapStack:
      ctx = self.callSiteContextMapStack[callSite]
      if not ctx.decDepth(): # remove when depth == 0.
        del self.callSiteContextMapStack[callSite]


  def getCallStackCtx(self, callSite) -> Opt[AnDfvPairDict]:
    if callSite in self.callSiteContextMapStack:
      return self.callSiteContextMapStack[callSite]
    return None


  def setCallStackCtx(self, callSite, dfvDict: AnDfvPairDict):
    self.callSiteContextMapStack[callSite] = dfvDict


  def countFuncCtx(self, funcName: FuncNameT, add: bool = True) -> int:
    increment = 1 if add else -1
    if funcName in self._funcContextCountMap:
      self._funcContextCountMap[funcName] += increment
    else:
      assert add, f"Function should be present before deletion"
      self._funcContextCountMap[funcName] = 1

    if util.VV1: print(f"{funcName}'s total contexts = {self._funcContextCountMap[funcName]}")
    return self._funcContextCountMap[funcName]


  def getFuncCtxCount(self, funcName: FuncNameT) -> int:
    """Returns the number of contexts for the given function."""
    if funcName in self._funcContextCountMap:
      return self._funcContextCountMap[funcName]
    else:
      return 0


  def mergeFuncResult(self, host: Host) -> None:
    """
    Merges the result of given host object of a function with its previously saved result.
    """
    funcName = host.func.name

    if util.LL1: LDB(f"MergingResultsOfFunc: {funcName}")
    if util.VV1: print(f"    MergingResultsOfFunc: {funcName}")

    funcResult = {} if funcName not in self.finalResult \
      else self.finalResult[funcName]

    allAnalysisNames = host.getAllAnalysesUsed()
    for anName in allAnalysisNames:
      currRes = host.getAnalysisResults(anName)
      if anName not in funcResult:
        funcResult[anName] = currRes
      else:
        prevRes = funcResult[anName]
        newRes  = prevRes.merge(currRes)
        funcResult[anName] = newRes

    self.finalResult[funcName] = funcResult # save the merged value


  def removePreviousContext(self, vContext: ValueContext, calleeAndCallSite: CalleeAndCallSite):
    if calleeAndCallSite in self.valueContextSite:
      vContextOld = self.valueContextSite[calleeAndCallSite]
      if vContextOld != vContext:
        self.valueContextSite[calleeAndCallSite] = vContext
        # remove the older value context from the value context map
        self.delKey(vContextOld)
    else:
      self.valueContextSite[calleeAndCallSite] = vContext


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
      reUsePrevHostObjects: bool = ff.IPA_VC_RE_USE_SAVED_HOST_OBJECTS,
      widenValueContext: bool = ff.IPA_VC_WIDEN_VALUE_CONTEXT,
  ) -> None:
    if tUnit is None:
      raise ValueError(f"Translation unit is None.")

    if not tUnit.getFuncObj(entryFuncName):
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
    self.reUsePrevHostObjects = reUsePrevHostObjects
    self.widen = widenValueContext

    # invocation id uniquely identifies the invocation instance of analyzeFunc()
    self.invocationId = 0
    self.gStat = GlobalStats()

    self.vci: ValueContextInfo = ValueContextInfo(reUsePrevHostObjects)

    self.logUsefulInfo()


  def analyze(self) -> Dict[FuncNameT, Dict[AnNameT, AnResult]]:
    """Call this function to start the IPA VC analysis.

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
    swappedGlobalBi = globalBi.swapBiInOut()
    if util.LL2: LDB("GlobalBi(SwappedInOut)(%s): %s",
                     GLOBAL_INITS_FUNC_NAME, swappedGlobalBi)

    # STEP 2: start analyzing from the entry function
    calleeAndCallSite = CalleeAndCallSite(self.entryFuncName,
                                          genGlobalNodeId(GLOBAL_INITS_FUNC_ID, 0))
    mainBi = self.prepareEntryFuncBi(self.entryFuncName, swappedGlobalBi)
    # This call executes the Value Context Method on every function reachable from
    # the given entry function.
    self.analyzeFunc(calleeAndCallSite, mainBi, GLOBAL_INITS_FUNC_NAME)

    # STEP 3: finalize IPA results
    self.finalizeIpaResults()
    self.clear() # clear the memory

    if util.LL1: LIN("\n\nIpaHost_Analyze: End #####################")

    return self.vci.finalResult


  def analyzeFunc(self,
      calleeAndCallSite: CalleeAndCallSite, # location of the call (has callee name too)
      ipaFuncBi: AnDfvPairDict, # the boundary info (value context)
      parentName: FuncNameT, # i.e. caller's name
      rDepth: int = 0, # recursion depth, starts from 0
      parentInvocationId: InvocationIdT = 0, # starts from 0
  ) -> AnDfvPairDict:
    thisInvocationId, vci = self.getNewInvocationId(), self.vci
    currFuncName, callSite = calleeAndCallSite.tuple()
    vci.analyzeFuncStack.append(calleeAndCallSite) # to keep a record for debugging etc.

    if util.LL1: LIN("AnalyzingFunction(IpaHost:START):"
                    " %s, Caller: %s, InvocationId:(Parent:%s, This:%s): %s",
                     calleeAndCallSite, parentName, parentInvocationId, thisInvocationId,
                     "*" * 16)
    if util.LL2: LDB(f"RecursionDepth: {rDepth}, VContextSize: {len(vci)}")
    if util.LL2: LDB(f" ValueContext(CurrBi:BeforeWidening({self.widen})):"
                     f" {ipaFuncBi}")

    if rDepth > ff.IPA_VC_RECURSION_LIMIT:
      return self.analyzeFuncFinal(calleeAndCallSite, ipaFuncBi, rDepth)

    wideningAttempted = False
    if self.widen: #TODO: ADD A TEST CASE
      ipaFuncBi, wideningAttempted = self.widenTheValueContext(calleeAndCallSite, ipaFuncBi)

    vContext = ValueContext(calleeAndCallSite.funcName, ipaFuncBi.getCopy(deep=False))
    if util.LL2: LDB(f" ValueContext(CurrBi:AfterWidening({self.widen}))(attempted:{wideningAttempted}):"
                     f" Id:{id(vContext)}, {vContext}")

    prevResult = vci.getValue(vContext)
    if prevResult: # VALUE Context HIT !
      if util.LL2: LDB(f"ValueContextCache: HIT !! :)")

      prevResult.addSite(callSite)

      if self.widen:
        vci.removeSiteStack(calleeAndCallSite)

      if util.VV1: print(f"{util.dsf(rDepth)} AnalyzingFunction(IpaHost):"
                         f" {currFuncName} ({calleeAndCallSite})"
                         f" (TotalCtx:{len(vci)}) (TotalSavedHosts:{len(vci.callSiteToHostObjMap)}) [HIT]")
      if util.LL1: LIN("AnalyzingFunction(IpaHost:DONE:HIT):"
                       " %s, Caller: %s, InvocationId:(Parent:%s, This:%s): %s",
                       calleeAndCallSite, parentName, parentInvocationId, thisInvocationId,
                       "*" * 16)
      vci.analyzeFuncStack.pop()
      return prevResult.result # HIT! Use prev result.

    # IF HERE: Value context MISSED !!
    if util.VV1: print(f"{util.dsf(rDepth)} AnalyzingFunction(IpaHost):"
                       f" {currFuncName} ({calleeAndCallSite})"
                       f" (TotalCtx:{len(vci)}) [MISS]")

    host = self.getPrevHostObject(calleeAndCallSite, parentInvocationId, vContext)
    ##### Current Callee is now a Caller #######################################
    allCallSites, callerName, reAnalyze = set(), currFuncName, True

    vci.removePreviousContext(vContext, calleeAndCallSite)

    while reAnalyze:
      reAnalyze = False
      host.analyze()  # RUN THE ANALYSIS.
      # set the context here
      vci.addItem(vContext,
                  ComputedBoundaryResult(currFuncName, host.getBoundaryResult(),
                                                   {calleeAndCallSite.callSite}))

      callSiteDfvs = host.getCallSiteDfvsIpaHost()
      if callSiteDfvs:  # check if call sites present
        for csPair in sorted(callSiteDfvs.keys(), key=lambda x: x.callSite):
          calleeName, calleeSite = csPair.tuple()
          allCallSites.add(csPair)

          calleeBi = callSiteDfvs[csPair]
          if util.LL2: LDB(f"CalleeBi ({callerName} --> {calleeName})"
                           f"(Before:Analyzing_{calleeName}__Caller__{callerName}):\n {calleeBi}")
          newCalleeBi = self.analyzeFunc(csPair, calleeBi, currFuncName, rDepth + 1,
                                         thisInvocationId) #recurse
          if util.LL2: LDB(f"CalleeBi ({callerName} --> {calleeName})"
                           f"(After:Analyzing_{calleeName}__Caller__{callerName}):\n {newCalleeBi}")
          reAnalyze = host.setCallSiteDfvsIpaHost(csPair, newCalleeBi)

          if util.VV2: self.printToDebug(calleeName, calleeBi, newCalleeBi, reAnalyze)
          if util.CC2: self.checkInvariants1(calleeName, calleeBi)

          if reAnalyze: break  # first re-analyze then goto other call sites

      if reAnalyze and util.LL1:
        LDB("AnalyzingFunction(IpaHost:ReStart:Miss):"
            " %s, Caller: %s, InvocationId:(Parent:%s, This:%s): %s",
            calleeAndCallSite, parentName, parentInvocationId,
            thisInvocationId, "*" * 16)
      if util.LL2: LDB(f" ValueContext: Id:{id(vContext)}, {vContext}")

    host.printOrLogResult()
    vci.mergeFuncResult(host) # save function's result

    if self.reUsePrevHostObjects:
      vci.clearPrevHostObjects(allCallSites, thisInvocationId)
    if self.widen:
      vci.removeSiteStack(calleeAndCallSite)

    if util.LL1: LIN("AnalyzingFunction(IpaHost:DONE:Miss):"
                     " %s, Caller: %s, InvocationId:(Parent:%s, This:%s): %s",
                     calleeAndCallSite, parentName, parentInvocationId,
                     thisInvocationId, "*" * 16)

    vci.analyzeFuncStack.pop()
    return host.getBoundaryResult()


  def widenTheValueContext(self, #widen
      calleeAndCallSite: CalleeAndCallSite,
      currDfvDict: AnDfvPairDict,
  ) -> Tuple[AnDfvPairDict, bool]:
    """Widens the value context for frameworks with infinite height lattices."""
    assert self.widen
    wideDfvDict, vci = None, self.vci
    prevStackCtx = vci.getCallStackCtx(calleeAndCallSite)

    if prevStackCtx:
      if prevStackCtx.depth >= ff.IPA_VC_MAX_WIDENING_DEPTH:
        if util.LL2: LDB(" Widening w.r.t. ValueContext(PrevBi): %s", prevStackCtx)
        if util.VV1: print(f" WIDENING: {calleeAndCallSite}")
        widenedBi = dict()
        for anName, prevNdfv in prevStackCtx.items():
          currNdfv = currDfvDict[anName]
          widenedBi[anName], _ = prevNdfv.widen(currNdfv) #widen here
        wideDfvDict = AnDfvPairDict(widenedBi, 1) # initial depth=1
      else:
        currDfvDict.setIncDepth(prevStackCtx) #IMPORTANT

    newDfvDict = wideDfvDict if wideDfvDict else currDfvDict
    wideningAttempted = False if wideDfvDict is None else True
    vci.setCallStackCtx(calleeAndCallSite, newDfvDict)  # memoize
    return newDfvDict, wideningAttempted


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
      callSite: CalleeAndCallSite,
      funcBi: AnDfvPairDict,
      recursionDepth: int,
  ) -> AnDfvPairDict:
    """
    For problems where Value Context may not terminate,
    finally fail/terminate at this function.
    """
    raise AssertionError(f"AnalyzeFuncFinal: (Depth: {recursionDepth}):"
                         f" {callSite}, {funcBi}\n"
                         f" AnalyzeFuncStack: {self.vci.analyzeFuncStack}")


  def getPrevHostObject(self,
      callSite: CalleeAndCallSite,
      parentInstanceId: int,
      vContext: ValueContext,
  ) -> Host:
    """Returns the host object, and a boolean flag.
    The boolean flag is,
      * true, if the value context is already present.
      * false, if value context is not present and analysis
        using the host object needs to be done with the new context.
    """
    vci = self.vci

    if self.reUsePrevHostObjects:
      prevHost = vci.getPrevHostObject(callSite, parentInstanceId)
      if prevHost:
        prevHost.setBoundaryResult(vContext.dfvDict)
        return prevHost

    # vContext not present, hence create one and attach a Host instance
    if util.LL2: LDB("ValueContextCache(New): id:%s, %s", id(vContext), vContext)

    vContextCopy = vContext.getCopy() # FIXME: can this be removed?
    hostInstance = self.createHostInstance(
      vContext.funcName, biDfv=vContextCopy.dfvDict)

    if self.reUsePrevHostObjects:
      vci.setPrevHostObject(callSite, parentInstanceId, hostInstance)

    return hostInstance


  def prepareEntryFuncBi(self,
      funcName: FuncNameT,
      bi: AnDfvPairDict, # Mutates: bi.
  ) -> AnDfvPairDict:
    func, newBi = self.tUnit.getFuncObj(funcName), AnDfvPairDict()

    for anName, nDfv in bi:
      AnalysisClass: Type[AnalysisAT_T] = clients.analyses[anName]
      anObj = AnalysisClass(func)

      # localize the boundary info
      newDfvIn = nDfv.dfvIn.localize(func, keepParams=True)
      newDfvOut = nDfv.dfvOut.localize(func, keepParams=True)
      localized = DfvPairL(newDfvIn, newDfvOut)

      newBi[anName] = anObj.getBoundaryInfo(localized, ipa=True, entryFunc=True)

    if util.LL2: LDB("IpaBi: (%s): %s", funcName, newBi)
    return newBi


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

    if util.VV2:
      print("\n\nFINAL RESULTS of IpaHost:")
      print("=" * 48)
      self.printFinalResults()


  def collectStats(self):
    """Collects various statistics."""
    if util.VV1: self.gStat.print()


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
    sio.write(f"  ReUsePrevValCxt: {self.reUsePrevHostObjects}\n")
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
           runs two cascaded steps and the first step runs the two
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



