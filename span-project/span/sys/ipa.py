#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Inter-Procedural Analysis (IPA)
Using the Value-Context Method.

Note: All IR related processing for IPA is done in span.ir.ipa module.
"""
import io
import logging

from span.sys.stats import GST, GlobalStats

LOG = logging.getLogger("span")

from typing import Dict, Tuple, Set, List, cast
from typing import Optional as Opt
# import objgraph
import gc  # REF: https://rushter.com/blog/python-garbage-collector/
# gc.set_debug(gc.DEBUG_SAVEALL)
# print("_GC COUNT:", gc.get_count())

TRACE_MALLOC: bool = False

if TRACE_MALLOC:
  import tracemalloc # REF: https://docs.python.org/3/library/tracemalloc.html
  tracemalloc.start()

import span.sys.clients as clients
from span.ir import expr, instr, constructs, tunit
from span.ir import cfg
import span.ir.conv as conv
from span.ir.conv import GLOBAL_INITS_FUNC_NAME, Forward, Backward
from span.ir.types import FuncNameT, FuncNodeIdT
from span.ir.tunit import TranslationUnit
from span.api.analysis import AnalysisNameT as AnNameT
from span.api.dfv import NodeDfvL

from span.sys.host import Host, MAX_ANALYSES
# from span.util.util import LS  # ipa module uses its own LS
import span.util.util as util
LS = True
import span.util.common_util as cutil

RECURSION_LIMIT = 200
count: int = 0

def takeTracemallocSnapshot():
  if TRACE_MALLOC:
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    for stat in top_stats: print(stat)


class ValueContext:
  __slots__ : List[str] = ["funcName", "dfvs"]


  def __init__(self,
      funcName: FuncNameT,
      dfvs: Opt[Dict[AnNameT, NodeDfvL]] = None
  ):
    self.funcName = funcName
    self.dfvs = dfvs if dfvs is not None else {}


  def getCopy(self):
    return ValueContext(self.funcName,
                        {k: v.getCopy() for k, v in self.dfvs.items()})


  def addValue(self,
      anName: AnNameT,
      nodeDfv: NodeDfvL
  ) -> None:
    self.dfvs[anName] = nodeDfv


  def __eq__(self, other):
    if self is other: return True
    equal = True
    if not isinstance(other, ValueContext):
      equal = False
    elif not self.funcName == other.funcName:
      equal = False
    elif not self.dfvs.keys() == other.dfvs.keys():
      equal = False
    else:
      for anName in self.dfvs.keys():
        direction = clients.getAnDirection(anName)
        nDfvSelf = self.dfvs[anName]
        nDfvOther = other.dfvs[anName]
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
    for anName in self.dfvs.keys():
      direction = clients.getAnDirection(anName)
      nDfvSelf = self.dfvs[anName]
      if direction == Forward:
        theHash = hash((theHash, nDfvSelf.dfvIn))
      elif direction == Backward:
        theHash = hash((theHash, nDfvSelf.dfvOut))
      else:  # bi-directional
        theHash = hash((theHash, nDfvSelf))

    return theHash


  def __str__(self):
    idStr = "" if not util.VV5 else f"(id:{id(self)})"
    return f"ValueContext({self.funcName}, {self.dfvs}){idStr}"


  def __repr__(self):
    return f"ValueContext({self.funcName}, {self.dfvs})"


class IpaHost:


  def __init__(self,
      tUnit: TranslationUnit,
      entryFuncName: FuncNameT = conv.ENTRY_FUNC,
      mainAnName: Opt[AnNameT] = None,
      otherAnalyses: Opt[List[AnNameT]] = None,
      supportAnalyses: Opt[List[AnNameT]] = None,
      avoidAnalyses: Opt[List[AnNameT]] = None,
      maxNumOfAnalyses: int = MAX_ANALYSES,
      disableAllSim: bool = False,
      useDdm: bool = False,
      reUsePrevValueContextHost: bool = True,
      widenValueContext: bool = False,
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
    self.widenValueContext = widenValueContext

    self.valueContextMap: Dict[ValueContext, Tuple[Set[FuncNodeIdT], Host]] = {}

    self.reUsePrevValueContextHost = reUsePrevValueContextHost
    self.callSiteVContextMap:\
      Dict[Tuple[FuncNodeIdT, FuncNameT], Dict[int, ValueContext]] = {}

    self.finalResult: Dict[FuncNameT,
                           Dict[AnNameT, Dict[cfg.CfgNodeId, NodeDfvL]]] = {}
    self.uniqueId = 0
    self.gst = GlobalStats()

    self.logUsefulInfo()


  def analyze(self) -> None:
    """
    Call this function to start the IPA analysis.
    """
    if LS: LOG.info("\n\nIpaHost_Start #####################")  # delit
    # STEP 1: Analyze the global inits and extract its BI
    if LS: LOG.info("AnalyzingFunction(IpaHost): %s %s",
                    GLOBAL_INITS_FUNC_NAME, "*" * 16)
    hostGlobal = self.createHostInstance(GLOBAL_INITS_FUNC_NAME, ipa=False)
    hostGlobal.analyze()
    if util.VV2: hostGlobal.printOrLogResult()

    globalBi = hostGlobal.getBoundaryResult()
    globalBi = self.swapGlobalBiInOut(globalBi)
    if LS: LOG.debug("GlobalBi(%s): %s", GLOBAL_INITS_FUNC_NAME, globalBi)

    # STEP 2: start analyzing from the entry function
    entryCallSite = conv.genFuncNodeId(conv.GLOBAL_INITS_FUNC_ID, 0)
    mainBi = self.prepareCalleeBi(self.entryFuncName, globalBi)
    self.analyzeFunc(entryCallSite,
                     self.entryFuncName,
                     mainBi,
                     0, 0, {entryCallSite: mainBi})

    # STEP 3: finalize IPA results
    self.finalizeIpaResults()
    self.freeMemory()


  def freeMemory(self, hard=False):
    self.valueContextMap = {}
    self.callSiteVContextMap = {}
    if hard: self.finalResult = {}


  def getUniqueId(self):
    """Returns a unique number each time.
    This helps distinguish one invocation of analyzeFunc() from another."""
    self.uniqueId += 1
    return self.uniqueId


  def analyzeFunc(self,
      callSite: FuncNodeIdT,
      funcName: FuncNameT,  # the function being analyzed (callee)
      ipaFuncBi: Dict[AnNameT, NodeDfvL],
      recursionDepth: int,
      parentUid: int, # start with 0
      callSiteContextMap: Dict[FuncNodeIdT, Dict[AnNameT, NodeDfvL]],
  ) -> Dict[AnNameT, NodeDfvL]:
    thisUid = self.getUniqueId()
    if LS: LOG.info("AnalyzingFunction(IpaHost)(Fresh,"
                    " Uid:(This:%s, Parent:%s)): %s %s",
                    thisUid, parentUid, funcName, "*" * 16)
    if LS: LOG.debug(f" {funcName} (Id:{self.tUnit.getFuncObj(funcName).id}): "
                     f"Site:{conv.getFuncNodeIdStr(callSite)}, "
                     f"Depth: {recursionDepth}, "
                     f"VContextSize: {len(self.valueContextMap)}, "
                     f"ParentUid: {parentUid}")
    if LS: LOG.debug(f" ValueContext(CurrBi): {ipaFuncBi}")

    if recursionDepth >= RECURSION_LIMIT:
      return self.analyzeFuncFinal(callSite, funcName, ipaFuncBi)

    ipaFuncBi = self.widenTheValueContext(callSite, ipaFuncBi, callSiteContextMap)
    callSiteContextMap[callSite] = ipaFuncBi #for #widen

    vContext = ValueContext(funcName, ipaFuncBi.copy())
    if LS: LOG.debug(f" ValueContext: Id:{id(vContext)}, {vContext}")
    host, preComputed = self.getComputedValue(callSite, parentUid, vContext)

    if preComputed:
      if callSite in callSiteContextMap: del callSiteContextMap[callSite]
      return host.getBoundaryResult() # HIT! Use prev result.

    ##### Current Callee is now a Caller #######################################
    allCallSites = set()
    callerName, callerId = funcName, host.func.id
    reAnalyze = True
    while reAnalyze:
      reAnalyze = False
      host.analyze()

      callSiteDfvs = host.getCallSiteDfvsIpaHost()
      if callSiteDfvs:  # check if call sites present
        for nid, calleeName in sorted(callSiteDfvs.keys()):
          tup = nid, calleeName
          calleeSite = conv.genFuncNodeId(callerId, nid)
          allCallSites.add((calleeSite, calleeName))

          calleeBi = callSiteDfvs[tup]
          if LS: LOG.debug(f"CalleeBi(Old) ({callerName} --> {calleeName}):\n {calleeBi}")
          newCalleeBi = self.analyzeFunc(calleeSite, calleeName, calleeBi,
                                         recursionDepth + 1, thisUid,
                                         callSiteContextMap) #recurse
          if LS: LOG.debug(f"CalleeBi(Old) ({callerName} --> {calleeName}):\n {calleeBi}")
          if LS: LOG.debug(f"CalleeBi(New) ({callerName} --> {calleeName}):\n {newCalleeBi}")
          reAnalyze = host.setCallSiteDfvsIpaHost(nid, calleeName, newCalleeBi)

          if util.VV2: self.printToDebug(calleeName, calleeBi, newCalleeBi, reAnalyze)
          if util.CC2: self.checkInvariants1(calleeName, calleeBi)

          if reAnalyze: break  # first re-analyze then goto other call sites

      if LS: LOG.debug("AnalyzingFunction(IpaHost)(Again:%s,"
                       " Uid:(This:%s, Parent:%s)): %s %s",
                       reAnalyze, thisUid, parentUid, funcName, "*" * 16)
      if LS: LOG.debug(f" ValueContext: Id:{id(vContext)}, {vContext}")
    if util.VV3:
      host.printOrLogResult()
    self.freePrevValueContexts(allCallSites, thisUid)
    if callSite in callSiteContextMap: del callSiteContextMap[callSite]
    return host.getBoundaryResult()


  def widenTheValueContext(self, #widen
      callSite: FuncNodeIdT,
      ipaFuncBi: Dict[AnNameT, NodeDfvL],
      callSiteContextMap: Dict[FuncNodeIdT, Dict[AnNameT, NodeDfvL]],
  ) -> Dict[AnNameT, NodeDfvL]:
    if self.widenValueContext:
      if callSite in callSiteContextMap:
        prevBi = callSiteContextMap[callSite]
        if LS: LOG.debug(" Widening with ValueContext(PrevBi): %s", prevBi)
        widenedBi = dict()
        for anName, nDfv in prevBi.items():
          currNdfv = ipaFuncBi[anName]
          widenedBi[anName], _ = nDfv.widen(currNdfv)
        return widenedBi
    return ipaFuncBi # no change


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


  def allTopValues(self,
      dfvs: Dict[AnNameT, NodeDfvL]
  ) -> bool:
    """Returns true if all the data flow values are Top."""
    tops = [nDfv.top for nDfv in dfvs.values()]
    isTop = all(tops)
    if any(tops): assert all(tops), f"NotAllTop: {dfvs}"
    return isTop


  def checkInvariants1(self,
      funcName: FuncNameT,
      nodeDfvs: Dict[AnNameT, NodeDfvL],
  ) -> None:
    pass


  def separateLocalNonLocalDfvs(self,
      dfvs: Dict[AnNameT, NodeDfvL],
  ) -> Tuple[Dict[AnNameT, NodeDfvL], Dict[AnNameT, NodeDfvL]]:
    localDfvs, nonLocalDfvs = dict(), dict()
    for aName, nDfv in dfvs.items():
      l, nl = nDfv.separateLocalNonLocalDfvs()
      localDfvs[aName], nonLocalDfvs[aName] = l, nl
    return localDfvs, nonLocalDfvs


  def prepareCallNodeDfv(self,
      funcName: FuncNameT,
      newCalleeBi: Dict[AnNameT, NodeDfvL],
      localDfvs: Dict[AnNameT, NodeDfvL],
  ) -> Dict[AnNameT, NodeDfvL]:
    localizedDfvs = dict()
    for anName, localDfv in localDfvs.items():
      newCalleeDfv = newCalleeBi[anName]
      localizedDfv = newCalleeDfv.addLocalDfv(localDfv, clients.getAnDirection(anName))
      localizedDfvs[anName] = localizedDfv
    return localizedDfvs


  def analyzeFuncFinal(self,
      callSite: FuncNodeIdT,
      funcName: FuncNameT,
      funcBi: Dict[AnNameT, NodeDfvL],
  ) -> Dict[AnNameT, NodeDfvL]:
    """
    TODO:
    For problems where Value Context may not terminate,
    do something here to approximate the solution.
    """
    print(f"analyzeFuncFinal: {conv.getFuncNodeIdStr(callSite)}, {funcName}, {funcBi}")
    raise NotImplementedError()


  def getComputedValue(self,
      callSite: FuncNodeIdT,
      parentUid: int,
      vContext: ValueContext,
  ) -> Tuple[Host, bool]:
    """Returns the host object, and true if its present in the saved
    value contexts"""
    prevValueContext = None
    if vContext in self.valueContextMap:  # memoized results
      if LS: LOG.debug(f"PrevValueContext: HIT !! :)")
      tup = self.valueContextMap[vContext]
      tup[0].add(callSite)
      return tup[1], True

    if self.reUsePrevValueContextHost:
      prevHost = self.getPrevValueContextHost(callSite, parentUid, vContext)
      if prevHost and prevHost.func.name == vContext.funcName: return prevHost, False

    # vContext not present, hence create one and attach a Host instance
    if LS: LOG.debug("PrevValueContext(Fresh): id:%s, %s",
                     id(vContext), vContext)
    vContextCopy = vContext.getCopy()
    hostInstance = self.createHostInstance(vContext.funcName,
                                           biDfv=vContextCopy.dfvs)
    self.valueContextMap[vContext] = ({callSite}, hostInstance)  # save the instance

    return hostInstance, False


  def getPrevValueContextHost(self,
      callSite: FuncNodeIdT,
      parentUid: int,
      vContext: ValueContext,
  ) -> Opt[Host]:
    """Returns the host object, and true if its present in the saved
    value contexts"""
    if LS: LOG.debug(f"PrevValueContext: MISS !! :(")
    siteTup = callSite, vContext.funcName
    prevValueContext = self.getPrevValueContext(callSite, parentUid, vContext)
    if prevValueContext is not None:
      if LS: LOG.debug(f"PrevValueContext(Checking):"
                       f" Id:{id(prevValueContext)}, {prevValueContext}")
      if LS: LOG.debug(f"ValueContext(s): %s", self.valueContextMap)  #delit
      tup = self.valueContextMap[prevValueContext]
      allCallSites = tup[0]
      if len(allCallSites) > 1:
        # since more than one callSite needs the vContext we cannot modify it
        prevValueContext = None

    if prevValueContext is not None:
      if LS: LOG.debug(f"PrevValueContext(ReUsing):"
                       f" Id:{id(prevValueContext)}, {prevValueContext}")
      tup = self.valueContextMap[prevValueContext]
      del self.valueContextMap[prevValueContext] # remove the old one
      self.callSiteVContextMap[siteTup][parentUid] = vContext # replace the old one
      self.valueContextMap[vContext] = tup
      hostInstance = tup[1]
      hostInstance.setBoundaryResult(vContext.getCopy().dfvs)
      return hostInstance

    return None


  def getPrevValueContext(self,
      callSite: FuncNodeIdT,
      parentUid: int,
      vContext: ValueContext,
  ) -> Opt[ValueContext]:
    siteTup = callSite, vContext.funcName
    if siteTup in self.callSiteVContextMap:
      val = self.callSiteVContextMap[siteTup]
    else:
      val = self.callSiteVContextMap[siteTup] = {}

    if parentUid in val:
      if LS: LOG.debug(f"PrevValueContext(fetch) prev context at"
                       f" Site:{conv.getFuncNodeIdStr(callSite)}:"
                       f" with ParentUid:{parentUid}"
                       f"\n vContext(prev): id:{id(val[parentUid])}, {val[parentUid]}")
      return val[parentUid]
    else:
      if LS: LOG.debug(f"PrevValueContext(saving) context at"
                       f" Site:{conv.getFuncNodeIdStr(callSite)},"
                       f" with ParentUid:{parentUid}"
                       f"\n vContext: id:{id(vContext)}, {vContext}")
      val[parentUid] = vContext # save context
    return None


  def freePrevValueContexts(self,
      siteTups: Set[Tuple[FuncNodeIdT, FuncNameT]],
      parentUid: int,
  ) -> None:
    for siteTup in siteTups:
      if siteTup in self.callSiteVContextMap:
        val = self.callSiteVContextMap[siteTup]
        if parentUid in val:
          del val[parentUid]


  def prepareCalleeBi(self,
      funcName: FuncNameT,
      bi: Dict[AnNameT, NodeDfvL],
  ) -> Dict[AnNameT, NodeDfvL]:
    func = self.tUnit.getFuncObj(funcName)
    newBi = {}

    for anName, nDfv in bi.items():
      AnalysisClass = clients.analyses[anName]
      analysisObj = AnalysisClass(func)
      newBi[anName] = analysisObj.getBoundaryInfo(nDfv, ipa=True)

    if LS: LOG.debug("IpaBI: (%s): %s", funcName, newBi)
    return newBi


  def swapGlobalBiInOut(self, globalBi: Dict[AnNameT, NodeDfvL]):
    """Swaps IN and OUT, because the OUT of the end node in
    the global function is the IN of the main() function."""
    for anName in globalBi.keys():
      nDfv = globalBi[anName]
      nDfv.dfvIn, nDfv.dfvOut = nDfv.dfvOut, nDfv.dfvIn
      nDfv.dfvOutFalse = nDfv.dfvOutTrue = nDfv.dfvOut
    return globalBi


  def createHostInstance(self,
      funcName: FuncNameT,
      ipa: bool = True,
      biDfv: Opt[Dict[AnNameT, NodeDfvL]] = None,
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
    if util.VV1: print(f"TotalValueContexts: {len(self.valueContextMap)}, "
                       f"SizeInBytes: {util.getSize2(self.valueContextMap)}")

    self.collectStats()
    self.mergeFinalResults()
    # print(f"UnMergedSize: {len(self.vContextMap)}, MemorySize: {cutil.getSize(self.vContextMap)}")
    self.valueContextMap.clear() # clear the memory

    gc.collect()
    # print("Wait and observe the memory!"); time.sleep(10);
    # objgraph.show_refs(gc.garbage, filename="objgraph.dot") # too huge an output

    if util.VV1:
      print(f"MergedSize: {len(self.finalResult)}, "
            f"MemorySize: {util.getSize2(self.finalResult)}\n")
    # print results if needed
    if util.VV2:
      print("\n\nFINAL RESULTS of IpaHost:")
      print("=" * 48)
      self.printFinalResults()


  def printFinalResults(self):
    for funcName, res in self.finalResult.items():
      func = self.tUnit.getFuncObj(funcName)
      print("\nFunction:", funcName, "TUnit:", self.tUnit.name, "*****")
      for anName, anRes in res.items():
        print(anName, ":")

        topTop = "IN: Top, OUT: Top, TRUE: Top, FALSE: Top (Unreachable/Nop)"
        for node in func.cfg.revPostOrder:
          nid = node.id
          nDfv = anRes.get(nid, topTop)
          print(f">> {nid}. ({node.insn}): {nDfv}")


  def collectStats(self):
    """Collects various statistics."""
    for vc, (fn, host) in self.valueContextMap.items():
      host.collectStats(self.gst)
    if util.VV1: self.gst.print()


  def mergeFinalResults(self):
    """Computes the final result of an IPA computation.
    It merges all the results of all the contexts of a function
    to get the static data flow information of that function."""
    self.finalResult = {}
    allFuncNames = list(set(vc.funcName for vc in self.valueContextMap.keys()))

    for i, funcName in enumerate(sorted(allFuncNames)):
      funcResult = {}
      if util.VV1:
        print(f"Merging Results of Func: {funcName} ({i+1:>5}/{len(allFuncNames):<5})")
      for valContext, tup in self.valueContextMap.items():
        host = tup[1]
        if valContext.funcName == funcName:
          allAnalysisNames = host.getParticipatingAnalyses()
          for anName in allAnalysisNames:
            currRes = host.getAnalysisResults(anName).nidNdfvMap
            if anName not in funcResult:
              funcResult[anName] = currRes
            else:
              prevRes = funcResult[anName]
              newRes  = self.mergeAnalysisResult(prevRes, currRes)
              funcResult[anName] = newRes
      self.finalResult[funcName] = funcResult


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
    if not LS: return

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

    LOG.info(sio.getvalue())


def diagnoseInterval(tUnit: TranslationUnit):
  """A diagnosis called by the main driver.
  Run interval analysis using SPAN
  then using Lerner's
  """
  #mainAnalysis = "ConstA"
  #mainAnalysis = "IntervalA"
  mainAnalysis = "PointsToA"
  #otherAnalyses : List[str] = ["PointsToA"]
  #otherAnalyses : List[str] = ["EvenOddA"]
  otherAnalyses : List[str] = []
  maxNumOfAnalyses = len(otherAnalyses) + 1

  ipaHostSpan = IpaHost(tUnit,
                        mainAnName=mainAnalysis,
                        otherAnalyses=otherAnalyses,
                        maxNumOfAnalyses=maxNumOfAnalyses
                        )
  ipaHostSpan.analyze()

  #ipaHostLern = IpaHost(tUnit, analysisSeq=[[mainAnalysis] + otherAnalyses])
  #ipaHostLern = IpaHost(tUnit, analysisSeq=[[mainAnalysis]])
  ipaHostLern = IpaHost(tUnit, mainAnName=mainAnalysis, maxNumOfAnalyses=1) # span with single analysis
  ipaHostLern.analyze()

  totalPPoints = 0  # total program points
  weakPPoints = 0  # weak program points
  totalPreciseComparisons1 = 0
  totalPreciseComparisons2 = 0
  total1 = 0

  print("Weak points and the values.")
  print("=" * 48)
  for funcName in ipaHostSpan.finalResult.keys():
    interSpan = ipaHostSpan.finalResult[funcName][mainAnalysis]
    interLern = ipaHostLern.finalResult[funcName][mainAnalysis]

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
          print(f"NOT_SAME ({nid})({funcName}):"
                f"\n  S-L:{sorted(setS-setL)}\n  L-S:{sorted(setL-setS)}")
        else:
          print(f"NOT_SAME ({nid})({funcName}): {valS} {valL}")
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



