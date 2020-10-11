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

from typing import Dict, Tuple, Set, List
from typing import Optional as Opt
# import objgraph
import gc  # REF: https://rushter.com/blog/python-garbage-collector/
# gc.set_debug(gc.DEBUG_SAVEALL)
# print("_GC COUNT:", gc.get_count())
# import tracemalloc # REF: https://docs.python.org/3/library/tracemalloc.html
# tracemalloc.start()

import span.sys.clients as clients
from span.ir import expr, instr, constructs, tunit
from span.ir import graph
from span.ir.conv import Site, GLOBAL_INITS_FUNC_NAME, Forward, Backward
from span.ir.types import FuncNameT
from span.ir.tunit import TranslationUnit
from span.api.analysis import AnalysisNameT
from span.api.dfv import NodeDfvL

from span.sys.host import Host
# from span.util.util import LS  # ipa module uses its own LS
LS = True
import span.util.common_util as cutil

recursionLimit = 100
LIMIT = 100
count = 0

def tracemalloc_take_snapshot():
  pass
  # snapshot = tracemalloc.take_snapshot()
  # top_stats = snapshot.statistics('lineno')
  # for stat in top_stats: print(stat)

class ValueContext:
  __slots__ : List[str] = ["funcName", "dfvs"]


  def __init__(self,
      funcName: FuncNameT,
      dfvs: Opt[Dict[AnalysisNameT, NodeDfvL]] = None
  ):
    self.funcName = funcName
    self.dfvs = dfvs if dfvs is not None else {}


  def getCopy(self):
    return ValueContext(self.funcName,
                        {k: v.getCopy() for k, v in self.dfvs.items()})


  def addValue(self,
      anName: AnalysisNameT,
      nodeDfv: NodeDfvL
  ) -> None:
    self.dfvs[anName] = nodeDfv


  def __eq__(self, other):
    equal = True
    if self is other: return True
    if not isinstance(other, ValueContext):
      equal = False
    elif not self.funcName == other.funcName:
      equal = False
    elif not self.dfvs.keys() == other.dfvs.keys():
      equal = False
    else:
      for anName in self.dfvs.keys():
        direction = clients.getDirection(anName)
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
      direction = clients.getDirection(anName)
      nDfvSelf = self.dfvs[anName]
      if direction == Forward:
        theHash = hash((theHash, nDfvSelf.dfvIn))
      elif direction == Backward:
        theHash = hash((theHash, nDfvSelf.dfvOut))
      else:  # bi-directional
        theHash = hash((theHash, nDfvSelf))

    return theHash


  def __str__(self):
    return f"ValueContext: {self.funcName}, {self.dfvs}"


  def __repr__(self):
    return f"ValueContext({self.funcName}, {self.dfvs})"


class IpaHost:


  def __init__(self,
      tUnit: TranslationUnit,
      entryFunc: FuncNameT = "f:main",
      mainAnName: Opt[AnalysisNameT] = None,
      otherAnalyses: Opt[List[AnalysisNameT]] = None,
      supportAnalyses: Opt[List[AnalysisNameT]] = None,
      avoidAnalyses: Opt[List[AnalysisNameT]] = None,
      maxNumOfAnalyses: int = 1024,
      analysisSeq: Opt[List[List[AnalysisNameT]]] = None,  # for cascading/lerner
      disableAllSim: bool = False,
  ) -> None:
    if tUnit is None or not tUnit.getFunctionObj(entryFunc):
      raise ValueError(f"No {entryFunc} in translation unit {tUnit.name}.")

    self.tUnit = tUnit
    self.entryFunc = entryFunc
    self.mainAnName = mainAnName
    self.otherAnalyses = otherAnalyses
    self.supportAnalyses = supportAnalyses  # TODO: pass it to span.sys.host.Host
    self.avoidAnalyses = avoidAnalyses
    self.analyses = maxNumOfAnalyses
    self.maxNumOfAnalyses = self.analyses
    self.analysisSeq = analysisSeq
    self.disableAllSim = disableAllSim

    self.vContextMap: Dict[ValueContext, Tuple[Set[Site], Host]] = {}
    self.callSiteVContextMap: Dict[Site, Dict[int, ValueContext]] = {}
    self.finalResult: Dict[FuncNameT,
                           Dict[AnalysisNameT,
                                Dict[graph.CfgNodeId, NodeDfvL]]] = {}
    self.uniqueId = 0


  def analyze(self) -> None:
    """
    Call this function to start the IPA analysis.
    """
    print("\n\nStart IPA Analysis #####################")  # delit
    # STEP 1: Analyze the global inits and extract its BI
    hostGlobal = self.createHostInstance(GLOBAL_INITS_FUNC_NAME, ipa=False)
    hostGlobal.analyze()
    # hostGlobal.printResult() #delit

    globalBi = hostGlobal.getBoundaryResult()
    globalBi = self.swapGlobalBi(globalBi)
    print("GlobalBi:", globalBi)  # delit

    # STEP 2: start analyzing from the entry function
    ipaBi = self.computeIpaBi(self.entryFunc, globalBi)
    entryCallSite = Site(GLOBAL_INITS_FUNC_NAME, 0)
    self.analyzeFunc(entryCallSite,
                     self.entryFunc,
                     ipaBi,
                     0)

    # STEP 3: finalize IPA results
    self.finalizeIpaResults()
    self.vContextMap = {}  # free up the memory


  def getUniqueId(self):
    """Returns a unique number each time.
    This helps distinguish one invocation of analyzeFunc() from another."""
    self.uniqueId += 1
    return self.uniqueId


  def analyzeFunc(self,
      callSite: Site,
      funcName: FuncNameT,
      funcBi: Dict[AnalysisNameT, NodeDfvL],
      recursionDepth: int,
      uniqueId: int = 0,
  ) -> Dict[AnalysisNameT, NodeDfvL]:
    newUniqueId = self.getUniqueId()
    print("AnalyzingFunc:", funcName, f"{callSite} Depth: {recursionDepth},"
                                      f" VContextSize: {len(self.vContextMap)}"
                                      f" UniqueId: {uniqueId}")
                                      # f" FuncBi: {funcBi}")
    funcBi = self.computeIpaBi(funcName, funcBi)

    if recursionDepth >= recursionLimit:
      return self.analyzeFuncFinal(callSite, funcName, funcBi)

    vContext = ValueContext(funcName, funcBi)
    host, preComputed = self.getComputedValue(callSite, uniqueId, vContext)

    if preComputed:
      print("UsingPreComputedResult: ThanksToValueContext", callSite) #delit
      # if using a memoized result, no need for further computation
      return host.getBoundaryResult()

    reAnalyze = True
    while reAnalyze:
      # sizeStr = f"vContextMap: ({len(self.vContextMap)},{cutil.getSize(self.vContextMap)})," \
      #           f" tunit: {cutil.getSize(self.tUnit)})"
      # print("(Re)AnalyzingFunction:", funcName, f" {sizeStr}")
      reAnalyze = False
      host.analyze()

      callSiteDfvs = host.getCallSiteDfvs()
      if callSiteDfvs:  # check if call sites present
        print("CallSiteNodes:", [node.id for node in callSiteDfvs.keys()]) #delit
        for node, dfvs in callSiteDfvs.items():
          calleeSite = Site(funcName, node.id)
          calleeName = instr.getCalleeFuncName(node.insn)
          assert calleeName, f"{node}"
          calleeBi = self.analyzeFunc(calleeSite, calleeName,
                                      dfvs, recursionDepth + 1,
                                      newUniqueId)  # recursion
          reAnalyze = host.setCallSiteDfv(node.id, calleeBi)
          if reAnalyze:
            break  # first re-analyze then goto other call sites

      if LS: LOG.debug("ReAnalyzingFunction: %s", funcName) if reAnalyze else None
    return host.getBoundaryResult()


  def analyzeFuncFinal(self,
      callSite: Site,
      funcName: FuncNameT,
      funcBi: Dict[AnalysisNameT, NodeDfvL],
  ) -> Dict[AnalysisNameT, NodeDfvL]:
    """
    TODO:
    For problems where Value Context may not terminate,
    do something here to approximate the solution.
    """
    print(f"analyzeFuncFinal: {callSite}, {funcName}, {funcBi}")
    raise NotImplementedError()


  def getComputedValue(self,
      callSite: Site,
      uniqueId: int,
      vContext: ValueContext,
  ) -> Tuple[Host, bool]:
    """Returns the host object, and true if its present in the saved
    value contexts"""
    prevValueContext = None
    if vContext in self.vContextMap:  # memoized results
      tup = self.vContextMap[vContext]
      tup[0].add(callSite)
      return tup[1], True
    else:  # look for previous value context
      prevValueContext = self.getPrevValueContext(callSite, uniqueId, vContext)
      if prevValueContext is not None:
        tup = self.vContextMap[prevValueContext]
        allCallSites = tup[0]
        if len(allCallSites) > 1:
          # since more than one callSite needs the vContext we cannot modify it
          prevValueContext = None

    if prevValueContext is not None:
      print(f"IPA:UsingPrevValueContext: at {callSite} (uniqueId: {uniqueId})")
      if LS: LOG.debug("IPA:UsingPrevValueContext: at callsite %s", callSite)
      tup = self.vContextMap[prevValueContext]
      print("IPA:RemovingPrevValueContext:", id(vContext)) #delit
      del self.vContextMap[prevValueContext] # remove the old one
      self.callSiteVContextMap[callSite][uniqueId] = vContext # remove the old one
      self.vContextMap[vContext] = tup
      hostInstance = tup[1]
      hostInstance.setBoundaryResult(vContext.getCopy().dfvs)
    else:
      # vContext not present, hence create one and attach a Host instance
      if LS: LOG.debug("IPA:NewValueContext: %s", vContext)
      hostInstance = self.createHostInstance(vContext.funcName,
                                             biDfv=vContext.getCopy().dfvs)
      print("IPA:AddingNewValueContext:", id(vContext)) #delit
      self.vContextMap[vContext] = ({callSite}, hostInstance)  # save the instance

    return hostInstance, False


  def getPrevValueContext(self,
      callSite: Site,
      uniqueId: int,
      vContext: ValueContext,
  ) -> Opt[ValueContext]:
    print("IPA:getPrevValueContext", callSite, uniqueId) #delit
    if callSite in self.callSiteVContextMap:
      val = self.callSiteVContextMap[callSite]
      if uniqueId in val:
        return val[uniqueId]
      else:

        if LS: LOG.debug("IPA:SavingPrevValueContext1")
        val[uniqueId] = vContext # save context 1
    else:
      if LS: LOG.debug("IPA:SavingPrevValueContext2")
      self.callSiteVContextMap[callSite] = {uniqueId: vContext} # save context 2
    return None


  def computeIpaBi(self,
      funcName: FuncNameT,
      bi: Dict[AnalysisNameT, NodeDfvL],
  ) -> Dict[AnalysisNameT, NodeDfvL]:
    func = self.tUnit.getFunctionObj(funcName)
    newBi = {}

    for anName, nDfv in bi.items():
      AnalysisClass = clients.analyses[anName]
      analysisObj = AnalysisClass(func)
      newBi[anName] = analysisObj.getBoundaryInfo(nDfv, ipa=True)

    if LS: LOG.debug("IpaBI: (%s): %s", funcName, newBi)
    return newBi


  def swapGlobalBi(self, globalBi: Dict[AnalysisNameT, NodeDfvL]):
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
      biDfv: Opt[Dict[AnalysisNameT, NodeDfvL]] = None,
  ) -> Host:
    """Create an instance of Host for the given function"""

    func = self.tUnit.getFunctionObj(funcName)

    return Host(
      func=func,
      mainAnName=self.mainAnName,
      otherAnalyses=self.otherAnalyses,
      avoidAnalyses=self.avoidAnalyses,
      maxNumOfAnalyses=self.maxNumOfAnalyses,
      analysisSeq=self.analysisSeq,
      disableAllSim=self.disableAllSim,
      ipaEnabled=ipa,
      biDfv=biDfv,
    )


  def finalizeIpaResults(self):
    print("ValueContextMapSize:", len(self.vContextMap))

    self.mergeFinalResults()
    # print(f"UnMergedSize: {len(self.vContextMap)}, MemorySize: {cutil.getSize(self.vContextMap)}")
    self.vContextMap.clear() # clear the memory

    gc.collect()
    # print("Wait and observe the memory!"); time.sleep(10);
    # objgraph.show_refs(gc.garbage, filename="objgraph.dot") # too huge an output

    print(f"MergedSize: {len(self.finalResult)}") #, MemorySize: {cutil.getSize(self.finalResult)}")
    # print results if needed
    if cutil.Verbosity >= 1:
      print("\n\nFINAL RESULTS of IPA:")
      print("=" * 48)
      self.printFinalResults()


  def printFinalResults(self):
    for funcName, res in self.finalResult.items():
      func = self.tUnit.getFunctionObj(funcName)
      print("\nFunction:", funcName, "TUnit:", self.tUnit.name, "*****")
      for anName, anRes in res.items():
        print(anName, ":")

        topTop = "IN: Top, OUT: Top, TRUE: Top, FALSE: Top (Unreachable/Nop)"
        for node in func.cfg.revPostOrder:
          nid = node.id
          nDfv = anRes.get(nid, topTop)
          print(f">> {nid}. ({node.insn}): {nDfv}")


  def mergeFinalResults(self):
    """Computes the final result of an IPA computation.
    It merges all the results of all the contexts of a function
    to get the static data flow information of that function."""
    self.finalResult = {}
    allFuncNames = [vc.funcName for vc in self.vContextMap.keys()]

    for funcName in allFuncNames:
      funcResult = {}
      for valContext, tup in self.vContextMap.items():
        host = tup[1]
        if valContext.funcName == funcName:
          allAnalysisNames = host.getParticipatingAnalyses()
          for anName in allAnalysisNames:
            res = host.getAnalysisResults(anName)
            if anName not in funcResult:
              funcResult[anName] = res
            else:
              funcResult[anName] = self.mergeAnalysisResult(funcResult[anName], res)
      self.finalResult[funcName] = funcResult


  @staticmethod
  def mergeAnalysisResult(result1: Dict[graph.CfgNodeId, NodeDfvL],
      result2: Dict[graph.CfgNodeId, NodeDfvL]
  ) -> Dict[graph.CfgNodeId, NodeDfvL]:
    cfgNodeIds = set(result1.keys())
    cfgNodeIds.update(result2.keys())

    for nid in cfgNodeIds:
      if nid in result1 and nid in result2:
        result1[nid], _ = result1[nid].meet(result2[nid])
      elif nid in result2:
        result1[nid] = result2[nid]

    return result1


def diagnoseInterval(tUnit: TranslationUnit):
  """A diagnosis called by the main driver.
  Run interval analysis using SPAN
  then using Lerner's
  """
  #mainAnalysis = "ConstA"
  mainAnalysis = "IntervalA"
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

  #ipaHostLern = IpaHost(tUnit, analysisSeq=[[mainAnalysis] + otherAnalyses])
  ipaHostLern = IpaHost(tUnit, analysisSeq=[[mainAnalysis]])
  ipaHostLern.analyze()

  totalPPoints = 0  # total program points
  weakPPoints = 0  # weak program points

  print("Weak points and the values.")
  print("=" * 48)
  for funcName in ipaHostSpan.finalResult.keys():
    interSpan = ipaHostSpan.finalResult[funcName][mainAnalysis]
    interLern = ipaHostLern.finalResult[funcName][mainAnalysis]

    for nid in interSpan.keys():
      nDfvSpan = interSpan[nid]
      nDfvLern = interLern[nid]

      totalPPoints += 2

      if nDfvSpan.dfvIn != nDfvLern.dfvIn \
          and nDfvLern.dfvIn < nDfvSpan.dfvIn:
        weakPPoints += 1
        # print(f"\n{funcName}:IN  of Node {nid}:{weakPPoints}:\n",
        #       nDfvSpan.dfvIn, "\n", nDfvLern.dfvIn)  # delit

      if nDfvSpan.dfvOut != nDfvLern.dfvOut \
          and nDfvLern.dfvOut < nDfvSpan.dfvOut:
        weakPPoints += 1
        # print(f"\n{funcName}:OUT of Node {nid}:{weakPPoints}:\n",
        #       nDfvSpan.dfvOut, "\n", nDfvLern.dfvOut)  # delit

  print("\nTotalPPoints:", totalPPoints, "WeakPPoints:", weakPPoints)

  tracemalloc_take_snapshot()


