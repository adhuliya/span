#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Inter-Procedural Analysis (IPA)
Using the Value-Context Method.

Note: All IR related processing for IPA is done in span.ir.ipa module.
"""
import logging
LOG = logging.getLogger("span")
LDB, LIN = LOG.debug, LOG.info

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
from span.ir import cfg
import span.ir.conv as conv
from span.ir.conv import (GLOBAL_INITS_FUNC_NAME,
                          Forward, Backward, GLOBAL_INITS_FUNC_ID,
                          genFuncNodeId)
from span.ir.types import FuncNameT, FuncNodeIdT, NodeIdT
from span.ir.tunit import TranslationUnit
from span.api.analysis import AnalysisNameT as AnNameT, DirectionDT
from span.api.dfv import NodeDfvL

from span.sys.host import Host
from span.sys.common import CallSitePair, DfvDict
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
      dfvDict: Opt[DfvDict] = None
  ):
    self.funcName = funcName
    self.dfvDict = dfvDict if dfvDict is not None else DfvDict()


  def getCopy(self):
    return ValueContext(self.funcName, self.dfvDict.getCopy())


  def addValue(self,
      anName: AnNameT,
      nodeDfv: NodeDfvL
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
    else:
      for anName, nDfvSelf in self.dfvDict:
        direction = clients.getAnDirection(anName)
        nDfvOther = other.dfvDict[anName]
        if direction == Forward:
          if not nDfvSelf.dfvIn == nDfvOther.dfvIn:
            equal = False
        elif direction == Backward:
          if not nDfvSelf.dfvOut == nDfvOther.dfvOut:
            equal = False
        else:  # bi-directional
          if not nDfvSelf == nDfvOther:
            equal = False

    return equal


  def __hash__(self) -> int:
    theHash = hash(self.funcName)
    for anName, nDfvSelf in self.dfvDict:
      direction = clients.getAnDirection(anName)
      if direction == Forward:
        theHash = hash((theHash, nDfvSelf.dfvIn))
      elif direction == Backward:
        theHash = hash((theHash, nDfvSelf.dfvOut))
      else:  # bi-directional
        theHash = hash((theHash, nDfvSelf))

    return theHash


  def __str__(self):
    idStr = "" if not util.VV5 else f"(id:{id(self)})"
    return f"ValueContext({self.funcName}, {self.dfvDict}){idStr}"


  def __repr__(self):
    return f"ValueContext({self.funcName}, {self.dfvDict})"


class HostSitesPair:
  """Stores the Host class and the callSites where its computation
  is (re)used due to common ValueContexts."""


  def __init__(self,
      host: Host,
      callSites: Opt[Set[FuncNodeIdT]] = None,
  ):
    self.host =  host
    self.callSites: Set[FuncNodeIdT] = callSites if callSites else set()


  def hasSingleSite(self):
    return len(self.callSites) == 1


  def addSite(self, callSite):
    self.callSites.add(callSite)


  def removeSite(self, callSite):
    #FIXME: Not used currently. Use this function for better efficiency.
    self.callSites.remove(callSite)


  def __str__(self):
    return f"HostCallSitesPair({self.host.func.name}, {self.callSites})"


  def __repr__(self): return self.__str__()


class ValueContextInfo:
  """The information related to value contexts
   needed while using the method."""

  def __init__(self,
      reUsePrevValueContextHost: bool = ff.IPA_VC_RE_USE_PREV_VALUE_CONTEXT_HOST,
  ):
    self.reUsePrevValueContextHost = reUsePrevValueContextHost

    # This map stores the ValueContexts and the corresponding Host objects
    self.valueContextMap: Dict[ValueContext, HostSitesPair] = {}

    # Map to store prev value context at a call site,
    # to help reuse the previous host computation.
    self.callSitePairContextMap: \
      Dict[CallSitePair, Dict[InvocationIdT, ValueContext]] = {}

    # The stack used to store value contexts in a stack of invocations.
    # This is used in termination of value contexts.
    self.callSiteContextMapStack: Dict[CallSitePair, DfvDict] = {}

    # stores the final result of the value context run
    self.finalResult:\
      Dict[FuncNameT, Dict[AnNameT, Dict[NodeIdT, NodeDfvL]]] = {}


  def addValueContext(self,
      vContext: ValueContext,
      hostSitesPair: HostSitesPair,
  ) -> None:
    """Add a new value context information."""
    self.valueContextMap[vContext] = hostSitesPair


  def removeValueContext(self, vContext):
    del self.valueContextMap[vContext]


  def getHostSitesPair(self,
      vContext: ValueContext
  ) -> HostSitesPair:
    """Get old value context information."""
    if vContext in self.valueContextMap:
      return self.valueContextMap[vContext]
    raise ValueError(f"{vContext}")


  def isContextPresent(self,
      vContext: ValueContext
  ) -> bool:
    """Is the context present?"""
    return vContext in self.valueContextMap


  def getPrevValueContext(self,
      callSitePair: CallSitePair,
      parentInvocationId: InvocationIdT,
  ) -> Opt[ValueContext]:
    """Get previous value context at the given call site pair.
    This is used to re-use the host object for a new value context.
    """
    if not self.reUsePrevValueContextHost: return None
    cspcm = self.callSitePairContextMap
    if callSitePair in cspcm:
      idContextDict = cspcm[callSitePair]
      if parentInvocationId in idContextDict:
        return idContextDict[parentInvocationId]
    return None


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

    cspcm = self.callSitePairContextMap
    if callSitePair in cspcm:
      idContextDict = cspcm[callSitePair]
    else:
      idContextDict = cspcm[callSitePair] = {}

    idContextDict[parentInvocationId] = vContext


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
      invocationId: int,
  ) -> None:
    for callSitePair in callSitePairs:
      if callSitePair in self.callSitePairContextMap:
        val = self.callSitePairContextMap[callSitePair]
        if invocationId in val:
          del val[invocationId]


  def vContextSize(self):
    return len(self.valueContextMap)


  def removeSiteStack(self, callSitePair):
    del self.callSiteContextMapStack[callSitePair]


  def getCallStackCtx(self, callSitePair) -> Opt[DfvDict]:
    if callSitePair in self.callSiteContextMapStack:
      return self.callSiteContextMapStack[callSitePair]
    return None


  def setCallStackCtx(self, callSitePair, dfvDict: DfvDict):
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
      disableAllSim: bool = False,
      useDdm: bool = False,
      reUsePrevValueContextHost: bool = True,
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
    self.disableAllSim = disableAllSim
    self.useDdm = useDdm
    self.widen = widenValueContext

    self.invocationId = 0
    self.gst = GlobalStats()

    self.reUsePrevValueContextHost = reUsePrevValueContextHost
    self.vci = ValueContextInfo(reUsePrevValueContextHost)

    self.logUsefulInfo()


  def analyze(self) -> None:
    """Call this function to start the IPA analysis."""
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
                                genFuncNodeId(GLOBAL_INITS_FUNC_ID, 0))
    mainBi = self.prepareEntryFuncBi(self.entryFuncName, globalBi)
    self.analyzeFunc(callSitePair, mainBi, 0, 0)

    # STEP 3: finalize IPA results
    self.finalizeIpaResults()
    self.clear() # clear the memory

    if util.LL1: LIN("\n\nIpaHost_Analyze: End #####################")


  def analyzeFunc(self,
      callSitePair: CallSitePair,
      ipaFuncBi: DfvDict,
      recursionDepth: int, # start with 0
      parentInvocationId: InvocationIdT, # start with 0
  ) -> DfvDict:
    thisInvocationId, vci = self.getNewInvocationId(), self.vci
    funcName, callSite = callSitePair.tuple()
    if util.LL1: LIN("AnalyzingFunction(IpaHost:START):"
                    " InvocationId:(This:%s, Parent:%s): %s %s",
                     thisInvocationId, parentInvocationId, funcName, "*" * 16)
    if util.LL2: LDB(f" {callSitePair}: "
                     f"ParentInvocationId: {parentInvocationId}, "
                     f"Depth: {recursionDepth}, "
                     f"VContextSize: {vci.vContextSize()}")
    if util.LL2: LDB(f" ValueContext(CurrBi): {ipaFuncBi}")

    if recursionDepth >= ff.IPA_VC_RECURSION_LIMIT:
      return self.analyzeFuncFinal(callSitePair, ipaFuncBi, recursionDepth)

    if self.widen: ipaFuncBi = self.widenTheValueContext(callSitePair, ipaFuncBi)

    vContext = ValueContext(callSitePair.funcName, ipaFuncBi.getCopyShallow())
    if util.LL2: LDB(f" ValueContext: Id:{id(vContext)}, {vContext}")
    host, preComputed = self.getComputedValue(
      callSitePair, parentInvocationId, vContext)

    if preComputed:
      if self.widen: vci.removeSiteStack(callSitePair)
      if util.VV1: print(f"{'>' * recursionDepth}AnalyzingFunction(IpaHost):"
                         f" {funcName} ({callSitePair}) [HIT]")
      if util.LL1: LIN("AnalyzingFunction(IpaHost:DONE:HIT):"
                       " InvocationId:(This:%s, Parent:%s): %s %s",
                       thisInvocationId, parentInvocationId, funcName, "*" * 16)
      return host.getBoundaryResult() # HIT! Use prev result.

    if util.VV1: print(f"{'>' * recursionDepth}AnalyzingFunction(IpaHost):"
                       f" {funcName} ({callSitePair}) [MISS]")
    ##### Current Callee is now a Caller #######################################
    allCallSites, callerName, reAnalyze = set(), funcName, True

    while reAnalyze:
      reAnalyze = False
      host.analyze()  # run the real analysis

      callSiteDfvs = host.getCallSiteDfvsIpaHost()
      if callSiteDfvs:  # check if call sites present
        for csPair in sorted(callSiteDfvs.keys(), key=lambda x: x.callSite):
          calleeName, calleeSite = csPair.tuple()
          allCallSites.add(csPair)

          calleeBi = callSiteDfvs[csPair]
          if util.LL2: LDB(f"CalleeBi ({callerName} --> {calleeName})(Old):\n {calleeBi}")
          newCalleeBi = self.analyzeFunc(csPair, calleeBi, recursionDepth + 1,
                                         thisInvocationId) #recurse
          if util.LL2: LDB(f"CalleeBi ({callerName} --> {calleeName})(New):\n {newCalleeBi}")
          reAnalyze = host.setCallSiteDfvsIpaHost(csPair, newCalleeBi)

          if util.VV2: self.printToDebug(calleeName, calleeBi, newCalleeBi, reAnalyze)
          if util.CC2: self.checkInvariants1(calleeName, calleeBi)

          if reAnalyze: break  # first re-analyze then goto other call sites

      if reAnalyze and util.LL1:
        LDB("AnalyzingFunction(IpaHost:ReStart:Miss):"
            " InvocationId:(This:%s, Parent:%s): %s %s",
            thisInvocationId, parentInvocationId, funcName, "*" * 16)
      if util.LL2: LDB(f" ValueContext: Id:{id(vContext)}, {vContext}")

    host.printOrLogResult()
    vci.clearPrevValueContexts(allCallSites, thisInvocationId)
    if self.widen: vci.removeSiteStack(callSitePair)
    if util.LL1: LIN("AnalyzingFunction(IpaHost:DONE:Miss):"
                     " InvocationId:(This:%s, Parent:%s): %s %s",
                     thisInvocationId, parentInvocationId, funcName, "*" * 16)
    return host.getBoundaryResult()


  def widenTheValueContext(self, #widen
      callSitePair: CallSitePair,
      currDfvDict: DfvDict,
  ) -> DfvDict:
    assert self.widen
    vci = self.vci
    wideDfvDict, prevStackCtx = None, vci.getCallStackCtx(callSitePair)

    if prevStackCtx:
      if prevStackCtx.depth >= ff.IPA_VC_MAX_WIDENING_DEPTH:
        if util.LL2: LDB(" Widening with ValueContext(PrevBi): %s", prevStackCtx)
        widenedBi = dict()
        for anName, prevNdfv in prevStackCtx.dfvs.items():
          currNdfv = currDfvDict[anName]
          widenedBi[anName], _ = prevNdfv.widen(currNdfv) #widen here
        wideDfvDict = DfvDict(widenedBi, 1) # initial depth=1
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
      nodeDfvs: DfvDict,
  ) -> None:
    pass


  def analyzeFuncFinal(self,
      callSitePair: CallSitePair,
      funcBi: DfvDict,
      recursionDepth: int,
  ) -> DfvDict:
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

    if vci.isContextPresent(vContext): # memoized results
      hostSitePair = vci.getHostSitesPair(vContext)
      if util.LL2: LDB(f"PrevValueContext: HIT !! :)")
      hostSitePair.addSite(callSitePair.callSite)
      return hostSitePair.host, True

    if self.reUsePrevValueContextHost:
      prevHost = self.getPrevValueContextHost(
        callSitePair, parentInstanceId, vContext)
      if prevHost: return prevHost, False

    # vContext not present, hence create one and attach a Host instance
    if util.LL2: LDB("PrevValueContext(Fresh): id:%s, %s",
                     id(vContext), vContext)
    vContextCopy = vContext.getCopy()
    hostInstance = self.createHostInstance(
      vContext.funcName, biDfv=vContextCopy.dfvDict)
    vci.addValueContext(vContext, HostSitesPair(
      hostInstance, {callSitePair.callSite}))

    return hostInstance, False


  def getPrevValueContextHost(self,
      callSitePair: CallSitePair,
      parentInstanceId: int,
      vContext: ValueContext,
  ) -> Opt[Host]:
    """Returns the host object, and true if its present in the saved
    value contexts"""
    if util.LL2: LDB(f"PrevValueContext: MISS !! :(")
    vci = self.vci
    prevValueContext = self.getPrevValueContext(
      callSitePair, parentInstanceId, vContext)
    if prevValueContext is None: return None

    if util.LL2: LDB(f"PrevValueContext(Checking):"
                     f" Id:{id(prevValueContext)}, {prevValueContext}")
    hostSitesPair = vci.getHostSitesPair(prevValueContext)
    if not hostSitesPair.hasSingleSite():
      # since more than one callSite may need the vContext, hence cannot modify
      return None

    if util.LL2: LDB(f"PrevValueContext(ReUsing):"
                     f" Id:{id(prevValueContext)}, {prevValueContext}")
    vci.removeValueContext(prevValueContext)
    vci.addValueContext(vContext, hostSitesPair)
    vci.setPrevValueContext(callSitePair, parentInstanceId, vContext) # replace
    host = hostSitesPair.host
    host.setBoundaryResult(vContext.getCopy().dfvDict)
    return host


  def getPrevValueContext(self,
      callSitePair: CallSitePair,
      parentInvocationId: int,
      vContext: ValueContext,
  ) -> Opt[ValueContext]:
    vci = self.vci
    prevCtx = vci.getPrevValueContext(callSitePair, parentInvocationId)

    if prevCtx:
      if util.LL2: LDB(f"PrevValueContext(fetch) prev context at"
                       f" Site:{callSitePair}:"
                       f" with ParentInvocationId:{parentInvocationId}"
                       f"\n vContext(prev): id:{id(prevCtx)}, {prevCtx}")
      return prevCtx
    else:
      if util.LL2: LDB(f"PrevValueContext(saving) context at"
                       f" Site:{callSitePair},"
                       f" with ParentInvocationId:{parentInvocationId}"
                       f"\n vContext: id:{id(vContext)}, {vContext}")
      vci.setPrevValueContext(callSitePair, parentInvocationId, vContext)
    return None


  def prepareEntryFuncBi(self,
      funcName: FuncNameT,
      bi: DfvDict,
  ) -> DfvDict:
    func, newBi = self.tUnit.getFuncObj(funcName), DfvDict()

    for anName, nDfv in bi:
      AnalysisClass = clients.analyses[anName]
      analysisObj = AnalysisClass(func)
      newBi[anName] = analysisObj.getBoundaryInfo(nDfv, ipa=True, entryFunc=True)

    if util.LL2: LDB("IpaBi: (%s): %s", funcName, newBi)
    return newBi


  def swapGlobalBiInOut(self, globalBi: DfvDict) -> DfvDict:
    """Swaps IN and OUT, because the OUT of the end node in
    the global function is the IN of the main() function."""
    for anName, nDfv in globalBi:
      nDfv.dfvIn, nDfv.dfvOut = nDfv.dfvOut, nDfv.dfvIn
      nDfv.dfvOutFalse = nDfv.dfvOutTrue = nDfv.dfvOut
    return globalBi


  def createHostInstance(self,
      funcName: FuncNameT,
      ipa: bool = True,
      biDfv: Opt[DfvDict] = None,
      useDdm: bool = False,  #DDM
  ) -> Host:
    """Create an instance of Host for the given function"""

    func = self.tUnit.getFuncObj(funcName)

    return Host(
      func=func,
      mainAnName=self.mainAnName,
      otherAnalyses=self.otherAnalyses,
      avoidAnalyses=self.avoidAnalyses,
      maxNumOfAnalyses=self.maxNumOfAnalyses,
      disableSim=self.disableAllSim,
      biDfv=biDfv,
      ipaEnabled=ipa,
      useDdm=useDdm,
    )


  def finalizeIpaResults(self):
    vci = self.vci
    if util.VV1: print(f"TotalValueContexts: {vci.vContextSize()}, "
                       f"SizeInBytes: {util.getSize2(vci.valueContextMap)},"
                       f"VCI(Total): {util.getSize2(vci)}")

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

    print(f"  CondToUncondSims Count: {condSimCount}")




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
                     f" NotVisited: {sorted(notVisitedFuns)}")
    if util.VV1: print(f"MergingResultsOfFunctions:"
                       f" Total {len(allFuncNames):<5}"
                       f" NotVisited: {sorted(notVisitedFuns)}")

    for i, funcName in enumerate(sorted(allFuncNames)):
      funcResult = {}
      if util.LL1:
        LDB(f"MergingResultsOfFunc: {funcName} ({i+1:>5}/{len(allFuncNames):<5})")
      for valContext, hostSitesPair in vci.valueContextMap.items():
        host = hostSitesPair.host
        if valContext.funcName == funcName:
          assert host.func.name == funcName, f"{funcName}"
          allAnalysisNames = host.getParticipatingAnalyses()
          for anName in allAnalysisNames:
            currRes = host.getAnalysisResults(anName).nidNdfvMap
            if anName not in funcResult:
              funcResult[anName] = currRes
            else:
              prevRes = funcResult[anName]
              newRes  = self.mergeAnalysisResult(prevRes, currRes)
              funcResult[anName] = newRes
      vci.finalResult[funcName] = funcResult


  def delitTestResult(self,  #delit
      anName: str,
      res: Dict[cfg.CfgNodeId, NodeDfvL],
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
  def mergeAnalysisResult(result1: Dict[cfg.CfgNodeId, NodeDfvL],
      result2: Dict[cfg.CfgNodeId, NodeDfvL]
  ) -> Dict[cfg.CfgNodeId, NodeDfvL]:
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
    sio.write(f"  DisableAllSim  : {self.disableAllSim}\n")
    sio.write(f"  UseDDM         : {self.useDdm}\n")
    sio.write(f"  EntryFuncName  : {self.entryFuncName}\n")
    sio.write(f"  MaxAnalyses    : {self.maxNumOfAnalyses}\n")
    sio.write(f"  MainAnalysis   : {self.mainAnName}\n")
    sio.write(f"  OtherAnalyses  : {self.otherAnalyses}\n")
    sio.write(f"  AvoidAnalyses  : {self.avoidAnalyses}\n")
    sio.write(f"  SupportAnalyses: {self.supportAnalyses}\n")

    LIN(sio.getvalue())


  def printFinalResults(self):
    vci = self.vci
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

  #ipaHostLern = IpaHost(tUnit, analysisSeq=[[mainAnalysis] + otherAnalyses])
  #ipaHostLern = IpaHost(tUnit, analysisSeq=[[mainAnalysis]])
  ipaHostLern = IpaHost(tUnit, mainAnName=mainAnalysis,
                        maxNumOfAnalyses=1) # span with single analysis
  ipaHostLern.analyze()
  if util.VV1: ipaHostLern.printSimCounts("CASCADED")

  totalPPoints = 0  # total program points
  weakPPoints = 0  # weak program points
  totalPreciseComparisons1 = 0
  totalPreciseComparisons2 = 0
  total1 = 0

  if util.VV1: print("Weak points and the values.")
  if util.VV1: print("=" * 48)
  for funcName in ipaHostSpan.vci.finalResult.keys():
    if not (funcName in ipaHostSpan.vci.finalResult and
      funcName in ipaHostLern.vci.finalResult): continue

    interSpan = ipaHostSpan.vci.finalResult[funcName][mainAnalysis]
    interLern = ipaHostLern.vci.finalResult[funcName][mainAnalysis]

    for nid in sorted(interSpan.keys()):
      nDfvSpan = interSpan[nid]
      nDfvLern = interLern[nid]

      totalPPoints += 2

      if nDfvSpan.dfvIn != nDfvLern.dfvIn \
          and nDfvLern.dfvIn < nDfvSpan.dfvIn:
        weakPPoints += 1

      if nDfvSpan.dfvOut != nDfvLern.dfvOut:
        valS = nDfvSpan.dfvOut.val
        valL = nDfvLern.dfvOut.val
        if valS and valL:
          setS, setL = set(valS.items()), set(valL.items())
          if util.VV1: print(f"NOT_SAME ({nid})({funcName}):"
                f"\n  S-L:{sorted(setS-setL)}\n  L-S:{sorted(setL-setS)}")
        else:
          if util.VV1: print(f"NOT_SAME ({nid})({funcName}): {valS} {valL}")
      if nDfvSpan.dfvOut != nDfvLern.dfvOut \
          and nDfvLern.dfvOut < nDfvSpan.dfvOut:
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
      #       val2 = nDfvLern.dfvOut.getVal(name)
      #       if val2.isConstant():
      #         print(f"{node.id}: {name}: {val1}, {val2} ({insn.info})")
      #         totalPreciseComparisons2 += 1

  print("\nTotalPPoints:", totalPPoints, "WeakPPoints:", weakPPoints)
  print(f"TotalPreciseComparisons: {totalPreciseComparisons1}"
        f" ({totalPreciseComparisons2}) / {total1}")

  takeTracemallocSnapshot()




