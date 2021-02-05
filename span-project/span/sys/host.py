#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The Host that manages SPAN."""

import logging
LOG = logging.getLogger("span")

from typing import Dict, Tuple, Set, List, Callable,\
  Optional as Opt, cast, Any, List
from collections import deque
import time
import io
import functools

from span.api import dfv
import span.util.util as util
from span.util.util import LS, AS, GD

from span.ir.types import NodeIdT, VarNameT, FuncNameT, DirectionT
from span.ir.conv import FalseEdge, TrueEdge
from span.ir.conv import Forward, Backward, ForwBack, NULL_OBJ_NAME
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
from span.ir.instr import (NOP_INSTR_IC, BARRIER_INSTR_IC, UNDEF_VAL_INSTR_IC,
                           COND_READ_INSTR_IC, USE_INSTR_IC, EX_READ_INSTR_IC,
                           ASSIGN_INSTR_IC, COND_INSTR_IC, RETURN_INSTR_IC, CALL_INSTR_IC,
                           FILTER_INSTR_IC, FAILED_INSN_SIM)
from span.ir.expr import (VAR_EXPR_EC, FUNC_EXPR_EC, LIT_EXPR_EC, UNARY_EXPR_EC,
                          BINARY_EXPR_EC, ADDROF_EXPR_EC, MEMBER_EXPR_EC, ARR_EXPR_EC,
                          SIZEOF_EXPR_EC, CALL_EXPR_EC, SELECT_EXPR_EC,
                          CAST_EXPR_EC, DEREF_EXPR_EC, )

from span.api.dfv import NodeDfvL, NewOldL, OLD_INOUT
from span.api.analysis import SimNameT, simDirnMap, SimFailed, SimPending
from span.api.lattice import mergeAll, DataLT
from span.api.analysis import (AnalysisAT, AnalysisNameT as AnNameT,\
  DirectionDT,
  Node__to__Nil__Name,
  LhsVar__to__Nil__Name,
  Num_Var__to__Num_Lit__Name,
  Cond__to__UnCond__Name,
  Num_Bin__to__Num_Lit__Name,
  Deref__to__Vars__Name,
  )
import span.sys.clients as clients
import span.sys.ddm as ddm
from span.sys.stats import HostStat, GST, GlobalStats
from span.sys.sim import SimRecord
import span.ir.cfg as cfg
import span.ir.tunit as irTUnit
import span.ir.constructs as constructs
import span.ir.ir as ir


MAX_ANALYSES: int = 16

Reachability = bool
Reachable: Reachability = True
NotReachable: Reachability = not Reachable

# BOUND START: Module_Storage__for__Optimization
ExRead_Instr__Name: str = AnalysisAT.ExRead_Instr.__name__
CondRead_Instr__Name: str = AnalysisAT.CondRead_Instr.__name__
Conditional_Instr__Name: str = AnalysisAT.Conditional_Instr.__name__
UnDefVal_Instr__Name: str = AnalysisAT.UnDefVal_Instr.__name__
Filter_Instr__Name: str = AnalysisAT.Filter_Instr.__name__
# BOUND END  : Module_Storage__for__Optimization


class Participant:
  """Participant analysis details."""

  __slots__ : List[str] = ["analysisName", "weight", "dependsOn", "neededBy"]

  def __init__(self,
      analysisName: AnNameT,
      weight: int = 0,
      dependsOn: Opt[Set['Participant']] = None,
      neededBy: Opt[Set['Participant']] = None
  ) -> None:
    self.analysisName = analysisName
    self.weight: int = weight
    self.dependsOn = dependsOn if dependsOn else set()
    self.neededBy = neededBy if neededBy else set()


  def __lt__(self,
      other: 'Participant'
  ) -> bool:
    return self.weight < other.weight


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, Participant):
      return NotImplemented
    return self.analysisName == other.analysisName


  def __hash__(self):
    return hash(self.analysisName)


  def getDotGraphName(self) -> str:
    return f"{self.analysisName[:2]}{self.weight}"


  def __str__(self):
    return f"({self.analysisName},{self.weight})"


  def __repr__(self): return self.__str__()


class PriorityAnWorklist:
  """Priority Worklist of all participating analyses (not nodes)"""

  __slots__ : List[str] = ["wl", "wlSet", "anDepGraph", "popSequence"]

  def __init__(self):
    # wl is sorted in ascending order of weights, and popped from right
    self.wl: List[Participant] = []
    self.wlSet: Set[Participant] = set() # in sync with self.wl, to test AN presence
    # remember all analyses added in the analysis dependence graph
    self.anDepGraph: Dict[AnNameT, Participant] = {}
    # remember the sequence in which the analyses were run
    self.popSequence: List[Participant] = []


  def addToAnDepGraph(self,
      anName: AnNameT,
      neededBy: Opt[AnNameT] = None
  ) -> bool:
    """Add the dependence in the graph and adjust weights.
    neededBy should already be in the graph.
    Returns True if the addition made any changes to the graph."""
    added = False
    if anName in self.anDepGraph:
      participant = self.anDepGraph[anName]
    else:
      participant = Participant(anName)
      self.anDepGraph[anName] = participant
      added = True  # added an isolated node

    if neededBy and anName != neededBy: # don't record self dependence
      assert neededBy in self.anDepGraph, f"{self.anDepGraph.keys()}"
      neededByParticipant = self.anDepGraph[neededBy]

      # record neededBy dependence
      if neededByParticipant not in participant.neededBy:
        participant.neededBy.add(neededByParticipant)
        added = True  # added a connection

      # record dependsOn dependence
      if participant not in neededByParticipant.dependsOn:
        neededByParticipant.dependsOn.add(participant)
        added = True  # added a connection
        self.updateWeight(neededByParticipant)
        self.wl.sort()  # needed since weights may be updated

    return added


  def add(self,
      anName: AnNameT,
      neededBy: Opt[AnNameT] = None,
  ) -> None:
    """Add an analysis to worklist.
    neededBy should already be in self.anDepGraph.
    """
    if LS: LOG.debug("AddedAnalysisToWl(Y/N): %s, (neededBy: %s)", anName, neededBy)

    self.addToAnDepGraph(anName, neededBy)
    participant = self.anDepGraph[anName]

    if participant not in self.wlSet:
      self.wl.append(participant)
      self.wlSet.add(participant)
      self.wl.sort()
      if LS: LOG.debug("AddedAnalysisToWl(YES): %s, (neededBy: %s)", anName, neededBy)
    else:
      if LS: LOG.debug("AddedAnalysisToWl(NO2): %s, (neededBy: %s), (wlSet: %s)",
                       anName, neededBy, self.wlSet)


  def addDependents(self,
      anName: AnNameT
  ) -> None:
    """Add dependent analyses on the given analysis."""
    assert anName in self.anDepGraph, f"{anName}: {self.anDepGraph.keys()}"

    updated = False
    for participant in self.anDepGraph[anName].neededBy:
      if participant not in self.wlSet:
        self.wl.append(participant)
        self.wlSet.add(participant)
        updated = True

    if updated: self.wl.sort()


  def pop(self) -> Opt[AnNameT]:
    if not self.wl:
      return None
    participant: Participant = self.wl.pop()
    self.wlSet.remove(participant)
    self.popSequence.append(participant)
    return participant.analysisName


  def updateWeight(self, participant: Participant) -> None:
    maxDepth = self.updateWeightRecursively(participant, {})
    if LS: LOG.debug("MaxUpdateWeigthCallDepth: %s", maxDepth)


  def updateWeightRecursively(self, participant: Participant,
      visited: Dict[Participant, int]
  ) -> int:
    """FIXME: replace this with Tarjan's algorithm."""
    maxDepth = 0  # returns the maximum recursion depth
    if participant in visited:
      visited[participant] += 1
    else:
      visited[participant] = 1

    for dependsOn in participant.dependsOn:
      weightChanged = False
      if dependsOn in visited:  # equalize weights of SCC
        if participant.weight != dependsOn.weight:
          dependsOn.weight = participant.weight
          weightChanged = True
      else:
        newWeight = participant.weight + 1
        if newWeight > dependsOn.weight:
          dependsOn.weight = newWeight
          weightChanged = True

      if weightChanged:
        depth = self.updateWeightRecursively(dependsOn, visited)
        if maxDepth < depth:
          maxDepth = depth

    visited[participant] -= 1
    if visited[participant] <= 0:
      del visited[participant]

    return maxDepth + 1


  def genDiGraph(self, label: str = None) -> str:
    if label is None: label = ""
    with io.StringIO() as sio:
      if label:
        sio.write(f"  label = \"{label}\";\n")
      for participant in self.anDepGraph.values():
        pDotName = participant.getDotGraphName()
        sio.write(f"  \"{label}{pDotName}\" [label=\"{pDotName}\"")
        if participant in self.wlSet:
          sio.write(", penwidth=2, color=blue];\n")
        else:
          sio.write("];\n")

      for participant in self.anDepGraph.values():
        pDotName = participant.getDotGraphName()
        for neededBy in participant.neededBy:
          nDotName = neededBy.getDotGraphName()
          sio.write(f"  \"{label}{pDotName}\" -> \"{label}{nDotName}\";\n")

      sio.write(f"  \"{label}WL\" [shape=box, label=\"")
      prefix = ""
      for participant in self.wl:
        sio.write(prefix)
        sio.write(participant.analysisName[:2])
        sio.write(f"{participant.weight}")
        if not prefix: prefix = ","

      sio.write(".\"];\n")  # end WL [...
      # remember to close it in the caller
      # sio.write("} // close subgraph\n")
      return sio.getvalue()


  def isEmpty(self):
    return not self.wl


  def worklistStr(self) -> str:
    with io.StringIO() as sio:
      prefix = ""
      sio.write("[")
      for participant in self.wl:
        sio.write(f"{prefix}{participant}")
        if not prefix: prefix = ", "
      sio.write("]")
      return sio.getvalue()


  def popSequenceStr(self) -> str:
    with io.StringIO() as sio:
      sio.write("[")
      prefix = ""
      for participant in self.popSequence:
        sio.write(f"{prefix}{participant}")
        if not prefix: prefix = ", "

      sio.write("]")
      return sio.getvalue()


  def __str__(self):
    return f"{self.worklistStr()}"


  def __repr__(self):
    return self.__str__()


class Host:


  def __init__(self,
      func: constructs.Func,
      mainAnName: Opt[AnNameT] = None, # the first analysis to start from
      otherAnalyses: Opt[List[AnNameT]] = None, # these analyses must be run
      supportAnalyses: Opt[List[AnNameT]] = None, # analyses that are optional
      avoidAnalyses: Opt[List[AnNameT]] = None, # these are always avoided
      maxNumOfAnalyses: int = MAX_ANALYSES, # max (participating) analyses at a time
      anDfvs: Opt[Dict[AnNameT, DirectionDT]] = None, # pre-computed dfvs of some analyses
      transform: bool = False, # transform mode (for Cascading/Lerners)
      biDfv: Opt[Dict[AnNameT, NodeDfvL]] = None,  # custom boundary info
      ipaEnabled: bool = False,
      useDdm: bool = False,  # use demand driven approach
      disableSim: bool = False, # by default sims are enabled
      simFpCalls: bool = True, # sim func pointer calls
  ) -> None:
    timer = util.Timer("HostSetup")

    if LS: LOG.info(f"HostSetup ({func.name}): IPA: {ipaEnabled}, DDM: {useDdm}, "
                     f"SIM: {not disableSim}, TRANSFORM: {transform}")

    assert func.cfg and func.tUnit, f"{func}: {func.cfg}, {func.tUnit}"

    # function to be analyzed
    self.func: constructs.Func = func
    self.tUnit: irTUnit.TranslationUnit = func.tUnit

    # function's cfg
    self.funcCfg: cfg.Cfg = func.cfg

    # cfg's edge feasibility information
    self.ef: cfg.FeasibleEdges = cfg.FeasibleEdges(self.funcCfg)

    #DDM demand driven method?
    self.useDdm: bool = useDdm
    if self.useDdm:
      if LS: LOG.debug("UsingDDM:######## #DDM ################################")
      self.ddmObj: ddm.DdMethod = ddm.DdMethod(func, self)
      # analyses dependent on a demand
      self.anDemandDep: Dict[ddm.AtomicDemand, Set[AnNameT]] = dict()
      # map of (nid, simName, expr) --to-> set of demands affected
      self.nodeInstrDemandSimDep: \
        Dict[Tuple[NodeIdT, SimNameT, expr.ExprET],
             Set[ddm.AtomicDemand]] = dict()

    #IPA inter-procedural analysis?
    self.biDfv: Opt[Dict[AnNameT, NodeDfvL]] = biDfv  #IPA
    self.ipaEnabled: bool = ipaEnabled #IPA
    if self.ipaEnabled: assert biDfv, f"{biDfv}"  #IPA

    # Set some more flags:
    self.disableSim: bool = disableSim  #SIM
    self.transform: bool = transform    #TRANSFORM
    self.enableNodeReachabilitySim = False  # set to True if needed
    self.simFpCalls = simFpCalls  # simplify fp based calls

    # BLOCK START: SomeChecks
    if not func.canBeAnalyzed():
      message = f"Function '{func.name}' cannot be analyzed (see Func.canBeAnalyzed())."
      if LS: LOG.error(message)
      raise ValueError(message)

    tmpList: List[AnNameT] = []
    if mainAnName:       tmpList.append(mainAnName)
    if otherAnalyses:    tmpList.extend(otherAnalyses)
    if supportAnalyses:  tmpList.extend(supportAnalyses)
    if avoidAnalyses:    tmpList.extend(avoidAnalyses)
    if anDfvs:           tmpList.extend(anDfvs.keys())

    assert tmpList
    for anName in tmpList:
      stop = False
      if anName not in clients.analyses:
        message = f"Analysis '{anName}' is not present/registered."
        if LS: LOG.error(message)
        stop = True
      if stop: raise ValueError(f"Analysis not present: {anName}")
    # BLOCK END  : SomeChecks

    # block information from IN to OUT and vice-versa,
    # for non simplification analyses.
    # It should be set to false eventually,
    # for non sim analyses to conclude safely.
    # TODO: initializing to False until proper handling is added.
    self.blockNonSimAn: bool = False  # for testing purposes: should be True

    # main analysis (that may result in addition of others)
    self.mainAnName: AnNameT = mainAnName

    # currently active analysis and its needed info/objects
    self.activeAnName: AnNameT = ""
    self.activeAnDirn: DirectionT = ""
    self.activeAnObj: Opt[AnalysisAT] = None
    self.activeAnTop: Opt[DataLT] = None
    self.activeAnSimNeeds: Set[str] = set()
    self.activeAnIsSimAn: Opt[bool] = None  # active An simplifies?
    # True if transfer function for FilterI instr is present in the analysis
    self.activeAnAcceptsLivenessSim: bool = False

    #graphviz some variables for dot graph visualization
    self.anWorkListDot: List[str] = []
    self.simplificationDot: List[str] = []
    # stores the insn seen by the analysis for the node
    self.nodeInsnDot: Dict[cfg.CfgNodeId, List[str]] = {}

    # analysis priority worklist queue (not node worklist)
    self.anWorkList: PriorityAnWorklist = PriorityAnWorklist()

    # participant names, with their analysis instance (for curr function)
    self.anParticipating: Dict[AnNameT, AnalysisAT] = dict()

    # participants and their work result
    self.anWorkDict: Dict[AnNameT, DirectionDT] = dict()

    # Used by: #TRANSFORM (and possibly by anyone)
    # If anDfvs contains the analysis also given as one of the
    # analyses to participate. The results of the 'participating'
    # version is given preference.
    self.anDfvs: Opt[Dict[AnNameT, DirectionDT]] = anDfvs
    self.anDfvsAnObj: Opt[Dict[AnNameT, AnalysisAT]] = {}
    if self.anDfvs:
      for anName in self.anDfvs:
        self.anDfvsAnObj[anName] = clients.analyses[anName](self.func)

    # map of (nid, simName, expr) --to-> set of analyses affected
    self.nodeInstrSimDep:\
      Dict[Tuple[NodeIdT, SimNameT, expr.ExprET], Set[AnNameT]] = dict()

    # simplifications that depend on the given analysis (active analysis)
    self.anRevNodeDep: \
      Dict[Tuple[AnNameT, NodeIdT],
           Dict[Tuple[Opt[expr.ExprET], SimNameT], Opt[SimRecord]]] = dict()

    # sim instruction cache: cache the instruction computed for a sim
    self.instrSimCache: \
      Dict[Tuple[NodeIdT, SimNameT],
           Dict[Tuple[instr.InstrIT, Opt[expr.ExprET]], instr.InstrIT]] = dict()

    self.stats: HostStat = HostStat(self, len(self.funcCfg.nodeMap))

    # sim sources: sim to simplifying analyses map
    self.simSrcs: Dict[SimNameT, Set[AnNameT]] = dict()

    # cache filtered sim sources
    self.filteredSimSrcs: \
      Dict[Tuple[SimNameT, expr.ExprET, NodeIdT], Set[AnNameT]] = dict()

    # counts the net useful simplifications by an analysis
    # If a 'support' analysis's count goes zero, it is not run anymore.
    self.anSimSuccessCount: Dict[AnNameT, int] = dict()

    # for support analyses that fail to simplify ALL needs
    self.activeAnIsUseful: bool = True  # becomes False if 'support' AN is not useful

    # record stats
    # number of times full analyses have run on the CFG
    self.analysisCounter: int = 0

    # records sequence in which analyses have run.
    self.anRunSequence: List[AnNameT] = []

    # max analyses allowed to run in synergy
    self.maxNumOfAnalyses: int = maxNumOfAnalyses
    self.currNumOfAnalyses: int = 0
    # set of analyses to avoid adding
    self.avoidAnalyses: Set[AnNameT] \
      = avoidAnalyses if avoidAnalyses else set()

    # the set of analyses that the user has asked to run to completion
    self.mainAnalyses: Set[AnNameT] = set()

    # add other analyses if present (as well)
    # Assumption: results of support analyses is not required by the user.
    # Thus the execution of such analyses is optimized in useful ways.
    self.supportAnalyses: Opt[Set[AnNameT]] \
      = set(supportAnalyses) if supportAnalyses else None
    if LS: LOG.debug(f"AddingParticipantAnalyses(HostSetup) START.")
    if otherAnalyses:
      for anName in reversed(otherAnalyses):
        self.mainAnalyses.add(anName)
        self.addParticipantAn(anName)
    # add the main analysis last (then it is picked up first)
    self.mainAnalyses.add(self.mainAnName)
    self.addParticipantAn(self.mainAnName)
    if LS: LOG.debug(f"AddingParticipantAnalyses(HostSetup) END.")

    # Host writes to this map, IpaHost reads from this map
    self.callSiteDfvMap: \
      Dict[Tuple[NodeIdT, FuncNameT], Dict[AnNameT, NodeDfvL]] = dict()
    # IpaHost writes to this map, Host reads from this map
    self.callSiteDfvMapIpaHost:\
      Dict[Tuple[NodeIdT, FuncNameT], Dict[AnNameT, NodeDfvL]] = dict()

    # add nodes that have one or more feasible pred edge
    if LS: LOG.debug(f"AddingFeasibleNodes(HostSetup) START.")
    self.addNodes(self.ef.initFeasibility())
    if LS: LOG.debug(f"AddingFeasibleNodes(HostSetup) END.")

    timer.stopAndLog()


  def addNodes(self, nodes: Opt[List[cfg.CfgNode]]) -> None:
    """Add nodes to worklist of all analyses that have freshly become feasible."""
    if not nodes: return

    for anName in self.anParticipating:
      nodeWorkList = self.anWorkDict[anName]
      for node in nodes:
        nodeWorkList.add(node)
      self.addAnToWorklist(anName)


  def addDepAnToWorklist(self, node: cfg.CfgNode, inOutChange: NewOldL) -> None:
    """Add analyses dependent on active analysis (wrt given node) to worklist."""
    if not self.activeAnIsSimAn: return
    if not self.willChangeAffectSimDep(inOutChange): return

    nid, tup1 = node.id, (self.activeAnName, node.id)

    if tup1 not in self.anRevNodeDep:
      return  # no analysis depends on the active analysis

    simRecordDict = self.anRevNodeDep[tup1]

    for tup2 in simRecordDict:
      simRecord = simRecordDict[tup2]  # tup2 type is (expr, simName)
      if simRecord is None: # i.e. failed value
        continue  # hence update is useless
      e, simName = tup2[0], tup2[1]  # tup2 type is (expr, simName)
      value = self.calculateSimValue(self.activeAnName, simName, node, e)
      changed = simRecord.setSimValue(value)  # update value
      if LS: LOG.debug("SimOfExpr: '%s' with simRecord: %s, changed: %s",
                       e, simRecord, changed)
      if changed:
        assert e, f"{tup2}"
        self.reAddAnalyses(node, simName, e)
        self.removeCachedInstrSim(nid, simName)
        if simRecord.hasFailedValue():
          self.decSimSuccessCount(self.activeAnName)   #COUNT_HERE:DEC
          simRecordDict[tup2] = None  # None represents failed value
        if self.useDdm: self.recomputeDemands(node, simName, e)
        self.stats.simChangeCacheHits.miss()
      else:
        self.stats.simChangeCacheHits.hit()


  def recomputeDemands(self, #DDM dedicated method
      node: cfg.CfgNode,
      simName: SimNameT,
      e: expr.ExprET,
  ) -> None:
    """Recompute demands that depend on this simplification."""
    nid = node.id
    tup = (nid, simName, e)

    if tup not in self.nodeInstrDemandSimDep:
      return # i.e. no demand is dependent on it

    if self.useDdm: self.ddmObj.timer.start()
    demands = list(self.nodeInstrDemandSimDep[tup])
    for demand in demands:
      slice = self.ddmObj.propagateDemandForced(demand)

    self.processChangedDemands()
    if self.useDdm: self.ddmObj.timer.stop()


  def processChangedDemands(self): #DDM dedicated method
    if not self.useDdm: return

    if self.useDdm: self.ddmObj.timer.start()
    changedDemands = self.ddmObj.getChangedDemands()

    for demand in changedDemands:
      if LS: LOG.debug("ChangedDemand: %s", demand)
      if demand in self.anDemandDep:
        slice = self.ddmObj.propagateDemand(demand)  # gets slice from cache
        depAnalyses = self.anDemandDep[demand]
        for anName in depAnalyses:
          wl = self.anWorkDict[anName].wl
          self.stats.nodeMapUpdateTimer.start()
          changed = wl.updateNodeMap(slice.nodeMap)  # add possible new nodes
          self.stats.nodeMapUpdateTimer.stop()
          if changed and LS:
            LOG.debug("UpdatedNodeMap(%s): %s", anName, wl)
          if changed:
            self.addAnToWorklist(anName)
    if self.useDdm: self.ddmObj.timer.stop()


  def reAddAnalyses(self,
      node: cfg.CfgNode,
      simName: SimNameT,
      e: expr.ExprET,
  ) -> None:
    if LS: oldAnCount = len(self.anWorkList.wlSet)

    nid = node.id
    tup = (nid, simName, e)
    if tup not in self.nodeInstrSimDep:
      self.nodeInstrSimDep[tup] = set()
    anNames = self.nodeInstrSimDep[tup]

    activeAnName = self.activeAnName
    for anName in anNames:
      if anName == activeAnName: continue  # don't add active analysis
      if LS: LOG.debug("Adding_analyses_dependent_on %s to worklist. Adding: %s, Node %s",
                       self.activeAnName, anName, nid)
      self.addAnToWorklist(anName)
      self.anWorkDict[anName].add(node)

    if LS:
      newAnCount = len(self.anWorkList.wlSet)
      if newAnCount == oldAnCount:
        LOG.debug("Analyses_Worklist (Unchanged) (%s): %s (AnParticipating: %s)",
                  self.activeAnName, self.anWorkList, self.anParticipating)
      else:
        LOG.debug("Analyses_Worklist (Changed) (%s): %s",
                  self.activeAnName, self.anWorkList)


  def conditionallyAddParticipantAn(self,
      anName: AnNameT,
      neededBy: Opt[AnNameT] = None
  ) -> bool:
    """Conditionally add an analysis as participant."""
    if self.canAddToParticipate(anName):
      return self.addParticipantAn(anName, neededBy)
    return False


  def addParticipantAn(self,
      anName: AnNameT,
      neededBy: Opt[AnNameT] = None,
      ipa: bool = False,  #FIXME: is this redundant? use self.ipaEnabled ?
  ) -> bool:
    """Adds a new analysis into the mix (if not already present)."""
    if anName in self.anParticipating:
      if LS: LOG.debug("AddingNewAnalysis(AlreadyPresent): %s: False", anName)
      return False
    if self.currNumOfAnalyses >= self.maxNumOfAnalyses:
      if LS: LOG.debug("AddingNewAnalysis(MaxAnalysesReached(%s)):"
                       " %s: False", self.currNumOfAnalyses, anName)
      return False  # i.e. don't add any new analysis
    if anName in self.avoidAnalyses:
      if LS: LOG.debug("AddingNewAnalysis(InAvoidList): %s: False", anName)
      return False  # i.e. dont add the analysis

    added: bool = False
    self.anWorkList.addToAnDepGraph(anName, neededBy)
    if anName not in self.anParticipating:
      # Then add the analysis.
      self.currNumOfAnalyses += 1
      if LS: LOG.debug("Adding %s. Needed by %s.", anName, neededBy)
      message = "If not in participants dict then should not be present at all."
      if AS and anName in self.anWorkDict:    raise Exception(message)

      analysisClass = clients.analyses[anName]  # get analysis Class
      analysisObj = analysisClass(self.func)  # create analysis instance
      top = analysisObj.overallTop

      self.anParticipating[anName] = analysisObj
      self.anWorkDict[anName] = clients.getAnDirnClass(anName)(self.func.cfg, top)
      self.addAnToWorklist(anName, neededBy, force=True, ipa=ipa)
      self.anSimSuccessCount[anName] = 1 if anName in self.mainAnalyses else 0
      added = True

      assert len(self.anParticipating) == len(self.anWorkDict)

    if neededBy is None: return added

    return added  # if a new analysis was added


  def addAnToWorklist(self,
      anName: AnNameT,
      neededBy: Opt[AnNameT] = None,
      force: bool = False,
      ipa: bool = False
  ) -> None:
    """Don't add self.activeAnName and analyses
    that failed to provide simplification"""
    if not ipa and anName == self.activeAnName:
      if LS: LOG.debug("AddedAnalysisToWl(NO): Not adding ActiveAn:"
                       " %s, (neededBy: %s)", anName, neededBy)
      return  # don't add active analysis again
    if anName in self.mainAnalyses:
      self.anWorkList.add(anName, neededBy)
      return
    else:
      if force or self.anSimSuccessCount[anName]:
        self.anWorkList.add(anName, neededBy)
        return

    if LS: LOG.debug("AddedAnalysisToWl(NO): An: %s, neededBy: %s, simSuccess: %s, ActiveAn: %s",
                     anName, neededBy, self.anSimSuccessCount.get(anName, -1), self.activeAnName)


  def calcInOut(self,
      node: cfg.CfgNode,
      dirn: DirectionDT
  ) -> Tuple[NodeDfvL, NewOldL, Reachability]:
    """Merge info at IN and OUT of a node."""
    nid = node.id
    if self.ef.isFeasibleNode(node):
      if LS: LOG.debug("Before InOutMerge (Node_%s): NodeDfv: %s.",
                       nid, dirn.nidNdfvMap.get(nid, dirn.topNdfv))
      ndfv, inout = dirn.calcInOut(node, self.ef)
      if LS: LOG.debug("After  InOutMerge (Node_%s): Change: %s, NodeDfv: %s.",
                       nid, inout, ndfv)
      return ndfv, inout, Reachable
    return dirn.topNdfv, OLD_INOUT, NotReachable


  def setupActiveAnalysis(self,
      anName: AnNameT
  ) -> DirectionDT:
    """Sets up the given analysis as current analysis to run."""
    self.stats.anSwitchTimer.start()
    self.anRunSequence.append(anName)
    self.activeAnName = anName
    self.activeAnDirn = clients.getAnDirection(anName)
    self.activeAnObj = self.anParticipating[anName]
    self.activeAnTop = self.activeAnObj.overallTop
    self.activeAnSimNeeds = clients.simNeedMap[anName]
    self.activeAnIsSimAn = anName in clients.simAnalyses
    self.activeAnAcceptsLivenessSim = anName in clients.anReadyForLivenessSim
    self.activeAnIsUseful = True

    top = self.activeAnTop  # to shorten name
    dirn = self.anWorkDict[self.activeAnName]

    if LS: LOG.debug("\nRUNNING_ANALYSIS: %s, Direction: %s,\nFunc: %s, Iteration: %s\n",
                     anName, dirn, self.func.name, self.analysisCounter)

    # init boundary info for start and end nodes, if not already done
    if not dirn.boundaryInfoInitialized:
      assert dirn.cfg and dirn.cfg.start and dirn.cfg.end, f"{dirn}"
      startNodeId = dirn.cfg.start.id
      endNodeId = dirn.cfg.end.id
      if self.ipaEnabled:  #IPA
        assert self.biDfv, f"{self.biDfv}"
        if self.activeAnName in self.biDfv:
          nDfv = self.biDfv[self.activeAnName]
          bi = (nDfv.dfvIn, nDfv.dfvOut)
        else:
          bi = (top, top)
      else:
        nDfv = self.activeAnObj.getBoundaryInfo()
        bi = (nDfv.dfvIn, nDfv.dfvOut)

      dirn.nidNdfvMap[startNodeId] = NodeDfvL(bi[0], top)
      dirn.nidNdfvMap[endNodeId] = NodeDfvL(top, bi[1])
      dirn.boundaryInfoInitialized = True
      if LS: LOG.debug("Init_Boundary_Info (StartNode %s' In, EndNode %s' Out): %s.",
                       startNodeId, endNodeId, bi)

    self.stats.anSwitchTimer.stop()
    return dirn


  #mainentry
  def analyze(self) -> float:
    """Starts the process of running the analysis synergy.
    Conditionally simulates SPAN approach"""
    timer = util.Timer("HostAnalyze")
    if LS: LOG.info("AnalysisWorklist: %s", self.anWorkList)
    if LS: LOG.info(f"MODE: IPA: {self.ipaEnabled}, DDM: {self.useDdm},"
                    f" SIM: {not self.disableSim}, TRANSFORM: {self.transform}")

    while not self.anWorkList.isEmpty():
      self.analysisCounter += 1
      self._analyze()

    timer.stopAndLog()
    return timer.getDurationInMillisec()


  def _analyze(self) -> None:
    """Runs the analysis with highest priority, on self.func."""
    anName = self.anWorkList.pop()  # pops the highest priority analysis
    if LS: LOG.info("\nRUNNING_ANALYSIS: %s. on_function: %s\n",
                    anName, self.func.name)
    assert anName, f"{self.anWorkList}"
    dirn = self.setupActiveAnalysis(anName)
    if GD: self.nodeInsnDot.clear()  # reinitialize for each new analysis iteration

    while True: #self.activeAnIsUseful:  #needs testing node visits are increasing
      node, treatAsNop, ddmVarSet = dirn.wl.pop()
      if LS: LOG.debug("GetNextNodeFrom_Worklist (%s, %s): %s"
                       "\n Got %s. %s",
                       self.func.name, self.activeAnName, "*" * 16,
                       f"Node_{node.id}" if node else None, dirn.wl)
      if node is None: break  # worklist is empty, so exit the loop
      if LS: LOG.debug(" Node_%s: %s (info:%s) (TreatAsNop: %s, ddmVarSet: %s)",
                       node.id, node.insn, node.insn.info, treatAsNop, ddmVarSet)

      nid = node.id
      nodeDfv, inOutChange1, feasibleNode = self.calcInOut(node, dirn)
      if feasibleNode:  # skip infeasible nodes
        if self.useDdm and self.activeAnName not in self.mainAnalyses:  #DDM
          if not nid == 1:  # skip the first node which is always NopI()
            nodeDfv = ddm.ddmFilterInDfv(nodeDfv, ddmVarSet)
            dirn.nidNdfvMap[nid] = nodeDfv

        if not treatAsNop: self.stats.incrementNodeVisitCount()
        if GD: self.nodeInsnDot[nid] = []

        self.addDepAnToWorklist(node, inOutChange1)

        if LS: LOG.debug("Curr_Node_Dfv (Before) (Node_%s): %s.", nid, nodeDfv)
        nodeDfv = self.analyzeInstr(node, node.insn, nodeDfv, treatAsNop)
        if LS: LOG.debug("Curr_Node_Dfv (AnalysisResult) (Node_%s): %s", nid, nodeDfv)

        inOutChange2 = dirn.update(node, nodeDfv)

        if LS: LOG.debug("Curr_Node_Dfv (AfterUpdate) (Node_%s): %s, change: %s.",
                         nid, nodeDfv, inOutChange2)
        self.addDepAnToWorklist(node, inOutChange2)
      else:
        if LS: LOG.debug("Infeasible_Node: Func: %s, Node: %s.", self.func.name, node)
        continue

    # if LS: _log.debug("Analyses_Dependence: %s.", self.anDependence)
    # if LS: _log.debug("Analyses_Rev_Node_Dependence: %s.", self.anRevNodeDep)
    if LS: LOG.debug("Analyses_Run_Sequence: %s.", self.anWorkList.popSequenceStr())
    if LS: LOG.debug("Analyses_Worklist: %s.", self.anWorkList)
    if LS: LOG.debug("Analyses_Participating: %s.", self.anParticipating.keys())

    if GD: self.generateDot()


  def analyzeInstr(self,
      node: cfg.CfgNode,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
      treatAsNop: Opt[bool] = False,
  ) -> NodeDfvL:
    """
    This function handles node with parallel instruction as well.
    self._analyzeInstr() does the main work.
    """
    if treatAsNop:
      return self.activeAnObj.Nop_Instr(node.id, insn, nodeDfv)

    if not isinstance(insn, instr.III):
      return self._analyzeInstr(node, insn, nodeDfv)

    # if here its a III instruction
    if LS: LOG.debug("Analyzing_Instr (ParallelI) (Node_%s): %s", node.id, insn)

    def ai(ins):
      nDfv = self._analyzeInstr(node, ins, nodeDfv)
      if LS: LOG.debug(" FinalInstrDfv: %s", nDfv)
      return nDfv

    res = mergeAll(ai(ins) for ins in insn.insns)
    return res


  def _analyzeInstr(self,
      node: cfg.CfgNode,
      insn: instr.InstrIT,  # could be a simplified form of node.insn
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    LLS, nid = LS, node.id
    if LLS: LOG.debug("Analyzing_Instr (Node_%s): %s, iType: %s",
                      nid, insn, insn.type)

    # is reachable (vs feasible) ?
    if self.enableNodeReachabilitySim and\
        Node__to__Nil__Name in self.activeAnSimNeeds:
      res = self.handleNodeReachability(node, insn, nodeDfv)
      if res: return res

    # if here, node is assumed reachable (or no analysis provides that information)
    activeAnObj = self.activeAnObj
    assert activeAnObj, f"{self.activeAnName}"

    self.stats.funcSelectionTimer.start()
    tFuncName = instr.getFormalStr(insn)
    assert hasattr(AnalysisAT, tFuncName), f"{tFuncName}, {insn}"
    assert hasattr(activeAnObj, tFuncName), f"{tFuncName}, {insn}, {activeAnObj}"
    transferFunc = getattr(activeAnObj, tFuncName)
    self.stats.funcSelectionTimer.stop()

    if LLS: LOG.debug("Instr_identified_as: %s",
                      getattr(AnalysisAT, tFuncName).__doc__.strip())
    if not self.disableSim and transferFunc != activeAnObj.Nop_Instr:
      # is the instr a var assignment (not deref etc)
      if activeAnObj.needsLhsVarToNilSim and insn.needsLhsVarSim():
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleLivenessSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsLhsDerefToVarsSim and insn.needsLhsDerefSim():
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleLhsDerefSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsRhsDerefToVarsSim and insn.needsRhsDerefSim():
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleRhsDerefSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsLhsDerefToVarsSim and insn.needsLhsMemDerefSim():
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleLhsMemDerefSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsRhsDerefToVarsSim and insn.needsRhsMemDerefSim():
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleRhsMemDerefSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsRhsDerefToVarsSim and insn.needsRhsPtrCallSim():
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleRhsPtrCallSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsFpCallSim and insn.needsPtrCallSim():
        assert isinstance(insn, instr.CallI), f"{nid}: {insn}"
        nDfv = self.handlePtrCallSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsNumBinToNumLitSim and insn.needsRhsNumBinaryExprSim():
        # rhs is a numeric bin expr, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleRhsBinArith(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        nDfv = self.handleRhsBinArithArgs(node, insn, nodeDfv, 1)
        if nDfv is not None: return nDfv
        nDfv = self.handleRhsBinArithArgs(node, insn, nodeDfv, 2)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsNumVarToNumLitSim and insn.needsRhsNumUnaryExprSim():
        # rhs is a numeric unary expr, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleRhsUnaryArith(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if activeAnObj.needsNumVarToNumLitSim and insn.needsRhsNumVarSim():
        # rhs is a numeric var, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{nid}: {insn}"
        nDfv = self.handleRhsNumVar(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

    if GD:
      if transferFunc == activeAnObj.Nop_Instr:
        self.nodeInsnDot[nid].append("nop")
      else:
        self.nodeInsnDot[nid].append(str(insn))

    if insn.needsCondInstrSim():
      assert isinstance(insn, instr.CondI), f"{nid}, {insn}"
      return self.Conditional_Instr(node, insn, nodeDfv)  # type: ignore
    else:
      self.stats.instrAnTimer.start()
      if self.ipaEnabled and insn.hasCallExpr():
        nDfv = self.processInstrWithCall(node, insn, nodeDfv,
                                         transferFunc, tFuncName)
      else:
        if LS: LOG.debug("FinallyInvokingInstrFunc: %s.%s() on %s",
                         self.activeAnName, tFuncName, insn)
        nDfv = transferFunc(nid, insn, nodeDfv)  # type: ignore
      self.stats.instrAnTimer.stop()
      return nDfv


  def processInstrWithCall(self, #IPA
      node: cfg.CfgNode,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
      transferFunc: Callable,
      tFuncName: str,
  ) -> NodeDfvL:
    """
    # Inter-procedural analysis does not process the instructions with call
    # currently: function pointer based calls are handled intra-procedurally
    #            func which cannot be analyzed are handled intra-procedurally
    """
    assert self.ipaEnabled
    if LS: LOG.debug(f" ProcessingIPACall(Host): {self.func.name}, {node.id}, {insn}")

    nid = node.id
    callE = instr.getCallExpr(insn)
    calleeFuncName = callE.getFuncName()

    if not calleeFuncName:
      return transferFunc(nid, insn, nodeDfv) # go #INTRA
    else:
      func = self.tUnit.getFuncObj(calleeFuncName)
      if not func.canBeAnalyzed():
        return transferFunc(nid, insn, nodeDfv) # go #INTRA

    if LS: LOG.debug("CalleeCallSiteDfv(CallerDfv): %s", nodeDfv)

    calleeBi = self.getCallSiteDfv(nid, calleeFuncName, self.activeAnName)
    if not calleeBi: # i.e. wait for the calleeBi to be some useful value
      callDfv = self.processCallArguments(node, callE, nodeDfv)
      newCalleeBi = self.activeAnObj.getLocalizedCalleeBi(nid, insn, callDfv, calleeBi)
      self.setCallSiteDfv(nid, calleeFuncName, self.activeAnName, newCalleeBi)
      return self.Barrier_Instr(node, insn, nodeDfv)

    if self.activeAnDirn == Forward:
      callDfv = self.processCallArguments(node, callE, nodeDfv)
      newCalleeBi = self.activeAnObj.getLocalizedCalleeBi(nid, insn, callDfv, calleeBi)
      self.setCallSiteDfv(nid, calleeFuncName, self.activeAnName, newCalleeBi)
      if LS: LOG.debug("FinallyInvokingInstrFunc: %s.%s() on %s",
                       self.activeAnName, tFuncName, insn)
      nodeDfv = transferFunc(nid, insn, nodeDfv, calleeBi)  # type: ignore
    else: # both for Backward and ForwBack
      assert False
      assert self.activeAnDirn in (Backward, ForwBack), f"{self.activeAnDirn}"
      if LS: LOG.debug("FinallyInvokingInstrFunc: %s.%s() on %s",
                       self.activeAnName, tFuncName, insn)
      nodeDfv = transferFunc(nid, insn, nodeDfv, calleeBi)  # type: ignore
      newCalleeBi = self.activeAnObj.getLocalizedCalleeBi(nid, insn, nodeDfv, calleeBi)
      self.setCallSiteDfv(nid, calleeFuncName, self.activeAnName, newCalleeBi)
      # nodeDfv = self.processCallArguments(node, callE, nodeDfv)  #FIXME: think

    return nodeDfv


  def processCallArguments(self,
      node: cfg.CfgNode,
      callE: expr.CallE, # must not be a pointer-call
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Analyzes the argument assignment to function params."""
    funcName = callE.getFuncName()
    assert funcName, f"{self.func.name}, {callE}: {callE.info}"
    funcObj = self.tUnit.getFuncObj(funcName)

    # adding Top to avoid unintended widening of params (esp. IntervalA)
    if self.activeAnDirn == Forward:
      nextNodeDfv = NodeDfvL(nodeDfv.dfvIn, self.activeAnTop)
    elif self.activeAnDirn == Backward:
      nextNodeDfv = NodeDfvL(self.activeAnTop, nodeDfv.dfvOut)
    else:
      raise ValueError(f"{self.activeAnDirn}")

    for i, paramName in enumerate(funcObj.paramNames):
      arg = callE.args[i]
      lhs = expr.VarE(paramName, arg.info)
      insn = instr.AssignI(lhs, arg, arg.info)
      self.tUnit.inferTypeOfInstr(insn)
      nextNodeDfv = self.analyzeInstr(node, insn, nextNodeDfv)
      if LS: LOG.debug(" FinalInstrDfv(ParamAssign): %s", nextNodeDfv)

      # in/out of succ/pred becomes out/in of the current node
      if self.activeAnDirn == Forward:
        nextNodeDfv = NodeDfvL(nextNodeDfv.dfvOut, self.activeAnTop)
      elif self.activeAnDirn == Backward:
        nextNodeDfv = NodeDfvL(self.activeAnTop, nextNodeDfv.dfvIn)
      else:
        raise ValueError(f"{self.activeAnDirn}")

    # restore in/out dfv
    if self.activeAnDirn == Forward:
      nextNodeDfv.dfvOut = nodeDfv.dfvOut
      nextNodeDfv.dfvOutTrue = nextNodeDfv.dfvOutFalse = nextNodeDfv.dfvOut
    elif self.activeAnDirn == Backward:
      nextNodeDfv.dfvIn = nodeDfv.dfvIn
    else:
      raise ValueError(f"{self.activeAnDirn}")

    if LS: LOG.debug("CalleeCallSiteDfv(AfterParams): %s", nextNodeDfv)

    return nextNodeDfv


  def handleNodeReachability(self, node, insn, nodeDfv) -> Opt[NodeDfvL]:
    nilSim = self.getSim(node, Node__to__Nil__Name)
    if nilSim is not None:
      if LS: LOG.debug("Unreachable_Node: %s: %s", node.id, insn)
      return self.Barrier_Instr(node, node.insn, nodeDfv)
    return None


  def getCachedInstrSimResult(self,
      node: cfg.CfgNode,
      simName: SimNameT,
      insn: instr.InstrIT,
      e: expr.ExprET,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Tuple[Opt[instr.InstrIT], bool]:
    """Returns already computed instruction simplification."""
    self.stats.simTimer.start()
    nid = node.id
    self.addExprSimNeed(nid, simName, e, demand,
                        None if demand else self.activeAnName)  # record the dependence
    newInsn = self.getCachedInstrSim(nid, simName, insn, e)

    if newInsn is FAILED_INSN_SIM:  # i.e. simplification failed already
      self.stats.cachedInstrSimHits.hit()
      self.stats.simTimer.stop()
      return None, True  # i.e. process_the_original_insn (IMPORTANT)

    if newInsn is not None:   # i.e. some simplification happened
      self.stats.cachedInstrSimHits.hit()
      self.stats.simTimer.stop()
      return newInsn, True

    self.stats.cachedInstrSimHits.miss()
    self.stats.simTimer.stop()
    return None, False  # i.e. compute the newInsn


  #@functools.lru_cache(500)
  def addExprSimNeed(self,
      nid: NodeIdT,
      simName: SimNameT,
      e: Opt[expr.ExprET] = None,
      demand: Opt[ddm.AtomicDemand] = None,  #DDM exclusive argument
      anName: Opt[AnNameT] = None,
  ):
    """Adds active analysis name or demand to the sim needed set."""
    # if demand is not None: # Invariant
    #   assert self.useDdm, f"{demand}: {self.useDdm}"

    tup = (nid, simName, e)
    tmp = self.nodeInstrSimDep if demand is None else self.nodeInstrDemandSimDep
    depMap = cast(Dict, tmp)
    if tup in depMap:
      depSet = depMap[tup]
    else:
      depMap[tup] = depSet = set()

    client = anName if demand is None else demand
    if client not in depSet:
      depSet.add(client)
      if LS: LOG.debug("AddedSimDependence: (changed) (Node_%s), %s, %s, Set: %s",
                       nid, simName, client, depSet)
    else:
      if LS: LOG.debug("AddedSimDependence: (unchanged) (Node_%s), %s, %s, Set: %s",
                       nid, simName, client, depSet)


  def handleNewInstr(self,
      node: cfg.CfgNode,
      simName: SimNameT,
      insn: instr.InstrIT,
      e: expr.ExprET,
      newInsn: instr.InstrIT,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Encapsulates common sequence of computation in many functions."""
    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, e, newInsn)
    return self.analyzeInstr(node, newInsn, nodeDfv)


  def isLivenessSupportNeeded(self) -> bool:
    """
    TODO: check the logic.
    """
    needed = True
    if not self.activeAnObj.needsLhsVarToNilSim:
      needed = False
      enableLivenessSupport = False
    else:
      enableLivenessSupport = self.activeAnAcceptsLivenessSim

    if LS: LOG.debug("ProvidingLivenessSupport?: %s (LivenessSupportNeeded?: %s)",
                     enableLivenessSupport, needed)
    return enableLivenessSupport


  def handleLivenessSim(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    """Handles liveness simplification for assignment instructions, where,
    lhs is a variable.

    It returns None if either,
    * Liveness support is not needed/provided
    * the lhs is live
    * no information is available.
    """
    if not self.isLivenessSupportNeeded():
      return None

    lhs, simName = insn.lhs, LhsVar__to__Nil__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName, insn, lhs)
    if valid: return self.analyzeInstr(node, newInsn, nodeDfv) if newInsn else None

    simToLive = self.getSim(node, simName, lhs)
    if simToLive is None:
      self.setCachedInstrSim(node.id, simName, insn, lhs, insn)
      return None  # i.e. no liveness info available

    simVal: Opt[Set[VarNameT]] = simToLive.val
    if simToLive == SimPending:
      newInsn = instr.FilterI(ir.getNamesEnv(self.func))
    elif simVal and lhs.name in simVal:
      self.setCachedInstrSim(node.id, simName, insn, lhs, insn)
      return None  # i.e. lhs is live, hence no simplification
    elif simVal is not None:
      newInsn = instr.FilterI(ir.getNamesEnv(self.func) - simVal)
    else:
      assert False, f"{simVal}"

    return self.handleNewInstr(node, simName, insn, lhs, newInsn, nodeDfv)


  def handleLhsDerefSim(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,  # lhs is expr.DerefE
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getLhsDerefSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getLhsDerefSimInstr(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,  # lhs is expr.DerefE
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.lhs, expr.DerefE), f"{node.id}: {insn}"
    lhsArg, rhs, simName = insn.lhs.arg, insn.rhs, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, lhsArg, demand)
    if valid: return newInsn

    values = self.Calc_Deref__to__Vars(node, lhsArg)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, lhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif values is SimPending:
      newInsn = instr.ExReadI({lhsArg.name})
    else:  # take meet of the dfv of the set of instructions now possible
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.III([AssignI(VarE(vName), rhs) for vName in values])
      newInsn.addInstr(instr.ExReadI({lhsArg.name}))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, lhsArg, newInsn)
    return newInsn


  def handleRhsDerefSim(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getRhsDerefSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getRhsDerefSimInstr(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.rhs, expr.DerefE), f"{node.id}: {insn}"
    lhs, rhsArg, simName = insn.lhs, insn.rhs.arg, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, rhsArg, demand)
    if valid: return newInsn

    values = self.Calc_Deref__to__Vars(node, rhsArg)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, rhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif values == SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhsArg))
    else:  # take meet of the dfv of the set of instructions now possible
      assert values and len(values), f"{node}: {values}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.III([AssignI(lhs, VarE(vName)) for vName in values])
      newInsn.addInstr(instr.CondReadI(
        lhs.name, ir.getNamesUsedInExprSyntactically(rhsArg)))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, rhsArg, newInsn)
    return newInsn


  def handleLhsMemDerefSim(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getLhsMemDerefSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getLhsMemDerefSimInstr(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.lhs, expr.MemberE), f"{node.id}: {insn}"
    lhs, rhs, simName = insn.lhs, insn.rhs, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, lhs.of, demand)
    if valid: return newInsn

    values = self.Calc_Deref__to__Vars(node, lhs.of)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, lhs.of, insn)
      return None  # i.e. process_the_original_insn
    elif values is SimPending:
      newInsn = instr.ExReadI({lhs.of.name})
    else:  # take meet of the dfv of the set of instructions now possible
      assert values, f"{node}: {values}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.III([AssignI(VarE(f"{varName}.{lhs.name}"), rhs)
                           for varName in values])
      newInsn.addInstr(instr.ExReadI({lhs.of.name}))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, lhs.of, newInsn)
    return newInsn


  def handleRhsMemDerefSim(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getRhsMemDerefSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getRhsMemDerefSimInstr(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.rhs, expr.MemberE), f"{node.id}: {insn}"
    lhs, rhs, simName = insn.lhs, insn.rhs, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, rhs.of, demand)
    if valid: return newInsn

    values = self.Calc_Deref__to__Vars(node, rhs.of)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, rhs.of, insn)
      return None  # i.e. process_the_original_insn
    elif values is SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs.of))
    else:  # take meet of the dfv of the set of instructions now possible
      assert values, f"{node}: {values}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.III([AssignI(lhs, VarE(f"{vName}.{rhs.name}"))
                           for vName in values])
      newInsn.addInstr(instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs.of)))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, rhs.of, newInsn)
    return newInsn


  def handleRhsPtrCallSim(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getRhsPtrCallSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getRhsPtrCallSimInstr(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.rhs, expr.CallE), f"{node.id}: {insn}"
    lhs, rhsArg, simName = insn.lhs, insn.rhs.callee, Deref__to__Vars__Name
    rhs = insn.rhs

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, rhsArg, demand)
    if valid: return newInsn

    values = self.Calc_Deref__to__Vars(node, rhsArg)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, rhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif values == SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhsArg))
    else:  # take meet of the dfv of the set of instructions now possible
      assert values and len(values), f"{node}: {values}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.III(
        [AssignI(lhs, expr.CallE(VarE(vName), rhs.args, rhs.info), insn.info)
         for vName in values])
      newInsn.addInstr(instr.CondReadI(
        lhs.name, ir.getNamesUsedInExprSyntactically(rhsArg)))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, rhsArg, newInsn)
    return newInsn


  def handlePtrCallSim(self,
      node: cfg.CfgNode,
      insn: instr.CallI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getPtrCallSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getPtrCallSimInstr(self,
      node: cfg.CfgNode,
      insn: instr.CallI,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn, instr.CallI), f"{node.id}: {insn}"
    callE, callee, simName = insn.arg, insn.arg.callee, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, callee, demand)
    if valid: return newInsn

    values = self.Calc_Deref__to__Vars(node, callee)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, callee, insn)
      return None  # i.e. process_the_original_insn
    elif values == SimPending:
      newInsn = instr.ExReadI({callee.name})
    else:  # take meet of the dfv of the set of instructions now possible
      assert values and len(values), f"{node}: {values}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.III(
        [instr.CallI(expr.CallE(VarE(vName), callE.args, callE.info), insn.info)
         for vName in values])
      newInsn.addInstr(instr.ExReadI({callee.name}))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, callee, newInsn)
    return newInsn


  def handleRhsNumVar(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    assert isinstance(insn.rhs, expr.VarE), f"{node.id}: {insn}"
    lhs, rhs, simName = insn.lhs, insn.rhs, Num_Var__to__Num_Lit__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName, insn, rhs)
    if valid: return self.analyzeInstr(node, newInsn, nodeDfv) if newInsn else None

    values = self.getSim(node, simName, rhs)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, rhs, insn)
      return None  # i.e. process_the_original_insn
    elif values is SimPending:
      if isinstance(lhs, expr.VarE):
        newInsn = instr.CondReadI(lhs.name, {rhs.name})
      elif lhs.hasDereference():
        if isinstance(lhs, expr.ArrayE):
          names = {lhs.of.name}
        else:
          names = ir.getNamesUsedInExprSyntactically(lhs)
        newInsn = instr.ExReadI(names)
      elif isinstance(lhs, expr.ArrayE):  # array expr without a pointer
        indexName = lhs.getIndexName()
        readVarNames = {indexName} if indexName else set()
        newInsn = instr.CondReadI(lhs.of.name, {rhs.name} | readVarNames)
      else:
        raise ValueError(f"{insn}")

    else:  # there is some simplification
      if not self.activeAnIsSimAn and self.blockNonSimAn:
        return self.Barrier_Instr(node, node.insn, nodeDfv)
      AssignI, LitE = instr.AssignI, expr.LitE
      newInsn = instr.III([AssignI(lhs, LitE(val)) for val in values])

    return self.handleNewInstr(node, simName, insn, rhs, newInsn, nodeDfv)


  def handleRhsUnaryArith(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    assert isinstance(insn.rhs, expr.UnaryE), f"{node.id}: {insn}"
    lhs, rhsArg, simName = insn.lhs, insn.rhs.arg, Num_Var__to__Num_Lit__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName, insn, rhsArg)
    if valid: return self.analyzeInstr(node, newInsn, nodeDfv) if newInsn else None

    values = self.getSim(node, simName, rhsArg)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, rhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif values is SimPending:
      assert isinstance(rhsArg, expr.VarE), f"{node.id}: {insn}"
      newInsn = instr.CondReadI(lhs.name, {rhsArg.name})
    else:
      rhs = insn.rhs
      AssignI, UnaryE, LitE = instr.AssignI, expr.UnaryE, expr.LitE
      newInsn = instr.III(
        [AssignI(lhs, UnaryE(rhs.opr, LitE(val)).computeExpr()) for val in values])

    return self.handleNewInstr(node, simName, insn, rhsArg, newInsn, nodeDfv)


  def handleRhsBinArith(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    lhs, rhs, simName = insn.lhs, insn.rhs, Num_Bin__to__Num_Lit__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName, insn, rhs)
    if valid: return self.analyzeInstr(node, newInsn, nodeDfv) if newInsn else None

    values = self.getSim(node, simName, rhs)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, rhs, insn)
      return None  # i.e. process_the_original_insn
    elif values is SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs))
    else:
      AssignI, LitE = instr.AssignI, expr.LitE
      newInsn = instr.III(
        [AssignI(lhs, LitE(val)) for val in values])
      newInsn.addInstr(instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs)))

    nDfv = self.handleNewInstr(node, simName, insn, rhs, newInsn, nodeDfv)
    return nDfv


  def handleRhsBinArithArgs(self,
      node: cfg.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
      argPos: int,  # 1 or 2 only
  ) -> Opt[NodeDfvL]:
    assert argPos in (1, 2), f"{argPos}"

    lhs, rhs, simName = insn.lhs, insn.rhs, Num_Var__to__Num_Lit__Name
    assert isinstance(rhs, expr.BinaryE), f"{node.id}: {insn}"
    rhsArg = rhs.arg1 if argPos == 1 else rhs.arg2
    if not isinstance(rhsArg, expr.VarE):
      return None  # i.e. process_the_original_insn

    newInsn, valid = self.getCachedInstrSimResult(node, simName, insn, rhsArg)
    if valid: return self.analyzeInstr(node, newInsn, nodeDfv) if newInsn else None

    values = self.getSim(node, simName, rhsArg)
    if values is SimFailed:
      self.setCachedInstrSim(node.id, simName, insn, rhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif values is SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs))
    else:
      AssignI, LitE, BinaryE = instr.AssignI, expr.LitE, expr.BinaryE
      if argPos == 1:
        newInsn = instr.III(
          [AssignI(lhs, expr.reduceConstExpr(BinaryE(LitE(val), rhs.opr, rhs.arg2)))
           for val in values])
      else:
        newInsn = instr.III(
          [AssignI(lhs, expr.reduceConstExpr(BinaryE(rhs.arg1, rhs.opr, LitE(val))))
           for val in values])
      newInsn.addInstr(
        instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs)))

    return self.handleNewInstr(node, simName, insn, rhsArg, newInsn, nodeDfv)


  # BOUND START: RegularInstructions

  def Conditional_Instr(self,
      node: cfg.CfgNode,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    # always handle conditional instruction
    if LS: LOG.debug("FinallyInvokingInstrFunc: Conditional_Instr() on %s", insn)
    self.stats.instrAnTimer.stop() # okay - excluding edge feasibility computation
    nodes = self.setEdgeFeasibility(node, insn.arg)
    self.addNodes(nodes)
    self.stats.instrAnTimer.start() # okay

    return self.activeAnObj.Conditional_Instr(node.id, insn, nodeDfv)


  def setEdgeFeasibility(self, node, arg) -> Opt[List[cfg.CfgNode]]:
    nodes = None
    if self.disableSim:
      nodes = self.ef.setAllSuccEdgesFeasible(node)
    elif self.activeAnObj.needsCondToUnCondSim:
      boolSim = self.getSim(node, Cond__to__UnCond__Name, arg)
      if boolSim is SimFailed:
        nodes = self.ef.setAllSuccEdgesFeasible(node)
      elif boolSim is SimPending:
        nodes = None  # no edge to be taken yet
      elif False in boolSim:  # only false edge taken
        nodes = self.ef.setFalseEdgeFeasible(node)
      elif True in boolSim:   # only true edge taken
        nodes = self.ef.setTrueEdgeFeasible(node)
      else:
        raise ValueError(f"{node}, {arg}, {boolSim}")

    if self.useDdm: self.ddmObj.timer.start()
    if nodes and self.useDdm: #DDM
      self.ddmObj.updateInfNodeDepDemands(nodes)
      self.processChangedDemands()
    if self.useDdm: self.ddmObj.timer.stop()

    return nodes

  # BOUND END  : RegularInstructions


  # BOUND START: SpecialInstructions

  def Barrier_Instr(self,
      node: cfg.CfgNode,  # redundant but needed
      insn: instr.InstrIT,  # redundant but needed
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """block all info from crossing (forw&back) from within the node."""
    if LS: LOG.debug("FinallyInvokingInstrFunc (Node_%s): BarrierI()", node.id)
    # return self.activeAnObj.Barrier_Instr(nodeDfv)
    if GD: self.nodeInsnDot[node.id].append("block")
    return nodeDfv  # i.e. block the info

  # BOUND END  : SpecialInstructions


  def canAddToParticipate(self,
      anName: AnNameT
  ) -> bool:
    """Can this analysis be added?"""
    okToAdd = True  # by default add
    if anName in self.anParticipating:  # most likely
      okToAdd = True  # already a participant hence no harm in re-adding
    elif self.supportAnalyses and anName not in self.supportAnalyses:
      okToAdd = False
    elif anName not in clients.analyses:
      okToAdd = False  # not present in the system
    elif anName in self.avoidAnalyses:
      okToAdd = False  # avoid this analysis
    elif self.currNumOfAnalyses >= self.maxNumOfAnalyses:
      okToAdd = False  # max analysis count reached
    if LS: LOG.debug("  CanAddAnalysis ToParticipate(%s): %s", anName, okToAdd)
    return okToAdd


  def canAddToSimplify(self,
      anName: AnNameT
  ) -> bool:
    """Can this analysis be added?"""
    okToAdd = False  # by default don't add
    if self.canAddToParticipate(anName):
      okToAdd = True
    elif self.anDfvs and anName in self.anDfvs:
      okToAdd = True
    if LS: LOG.debug("  CanAddAnalysis ToSimplify   (%s): %s", anName, okToAdd)
    return okToAdd


  #@functools.lru_cache(10)
  def fetchSimSources(self,
      simName: SimNameT,
  ) -> Set[AnNameT]:
    """Fetches allowed analysis names that
    provide the simplification.
    It caches the results."""
    if simName in self.simSrcs:  # check the cache first
      return self.simSrcs[simName]

    simAnNames: Set[AnNameT] = set()  # adds type info
    for anName in clients.simSrcMap.get(simName, set()):
      if self.canAddToSimplify(anName):
        simAnNames.add(anName)  # add simplification analyses

    self.simSrcs[simName] = simAnNames  # cache the result
    return simAnNames


  def setupSimSourcesDep(self,
      node: cfg.CfgNode,
      simAnNames: Set[SimNameT],
      simName: SimNameT,
      e: Opt[expr.ExprET] = None,  # None is a special case (Node__to__Nil)
  ) -> None:
    """Adds curr analysis' dependence on analyses providing simplification.
    Assumes that all simAnNames analyses have been setup before.
    """
    if not simAnNames: return

    nid, revNodeDep, tup2 = node.id, self.anRevNodeDep, (e, simName)

    for simAnName in simAnNames:
      tup1 = (simAnName, nid)
      if tup1 not in revNodeDep:
        revNodeDep[tup1] = {}
      simRecordMap = revNodeDep[tup1]

      if tup2 not in simRecordMap:  # do the initial setup
        self.attachDemandToSimAnalysis(node, simName, simAnName, e)
        simValue = self.calculateSimValue(simAnName, simName, node, e)
        sr = SimRecord(simName, simValue)
        if LS: LOG.debug("InitialSimValue of '%s' for '%s' is %s (%s)",
                         e, simName, simValue, sr)
        self.incSimSuccessCount(simAnName, self.activeAnName) #COUNT_HERE:INC
        if not sr: self.decSimSuccessCount(simAnName)   #COUNT_HERE:DEC
        simRecordMap[tup2] = sr if sr else None


  def incSimSuccessCount(self,
      simAnName: AnNameT,
      neededBy: AnNameT,
  ):
    """Count the possible success in simplification."""
    self.anSimSuccessCount[simAnName] += 1
    self.activeAnIsUseful = True
    self.addAnToWorklist(simAnName, neededBy)


  def decSimSuccessCount(self, simAnName: AnNameT):
    """Count the confirmed failure in simplification."""
    self.anSimSuccessCount[simAnName] -= 1
    if not self.anSimSuccessCount[simAnName]:
      """Any of the main analyses will never reach here."""
      assert simAnName not in self.mainAnalyses, f"{simAnName}, {self.mainAnalyses}"
      self.activeAnIsUseful = False


  def calculateSimValue(self,
      simAnName: str,
      simName: SimNameT,
      node: cfg.CfgNode,
      e: Opt[expr.ExprET] = None,
      values: Opt[Set] = None,
  ) -> Opt[Set]:
    """Calculates the simplification value for the given parameters."""
    nid = node.id
    if self.canAddToParticipate(simAnName):
      anObj = self.anParticipating[simAnName]
      nDfv = self.anWorkDict[simAnName].getDfv(nid)
    else:
      anObj = self.anDfvsAnObj[simAnName]
      nDfv = self.anDfvs[simAnName].getDfv(nid)

    assert hasattr(anObj, simName), f"{simAnName}, {simName}"
    simFunction = getattr(anObj, simName)

    if LS: LOG.debug("SimOfExpr: '%s' isAttemptedBy %s withDfv %s.", e, simAnName, nDfv)
    # Note: if e is None, it assumes sim works on node id
    val = value = simFunction(e if e else nid, nDfv, values)
    if val and self.transform: # and any simName #TRANSFORM
      val = SimFailed if len(val) > 1 else val
      if not val and util.VV1:
        print(f"TRANSFORM: SimFailed: ({self.func.name, nid})"
              f" ({simName}) {e} {e.info} Vals: {value}") #delit
    if LS: LOG.debug("SimOfExpr: '%s' is %s, by %s.", e, val, simAnName)
    return val


  #@functools.lru_cache(500)
  def fetchSimSourcesAndSetup(self,
      node: cfg.CfgNode,
      simName: SimNameT,
      e: Opt[expr.ExprET] = None,
      demand: Opt[ddm.AtomicDemand] = None,  #DDM
  ) -> Set[AnNameT]:
    """Adds analyses that can evaluate simName."""
    simAnNames = self.fetchSimSourcesAndFilter(simName, node.id, e)

    for anName in simAnNames:
      neededBy = None if demand else self.activeAnName
      if self.canAddToParticipate(anName):
        added = self.addParticipantAn(anName, neededBy=neededBy)
        if added and self.useDdm:
          self.initializeAnalysisForDdm(node, simName, anName, e)

    self.setupSimSourcesDep(node, simAnNames, simName, e)
    return simAnNames


  def initializeAnalysisForDdm(self, #DDM dedicated method
      node: cfg.CfgNode,
      simName: SimNameT,
      anName: AnNameT,
      e: Opt[expr.ExprET] = None,
  ):
    """Called after anName is added using self.addParticipantAn()
    and it returns True"""
    if not self.useDdm or anName in self.mainAnalyses:
      return  # main analyses are not ddm driven

    if self.useDdm: self.ddmObj.timer.start()
    wl = self.anWorkDict[anName].wl
    assert not wl.fullSequence, f"Analysis {anName} already started."
    wl.initForDdm()
    if self.useDdm: self.ddmObj.timer.stop()


  def attachDemandToSimAnalysis(self, #DDM dedicated method
      node: cfg.CfgNode,
      simName: SimNameT,
      anName: AnNameT,
      e: Opt[expr.ExprET] = None,
  ):
    if not self.useDdm: return
    if anName in self.mainAnalyses: return

    if self.useDdm: self.ddmObj.timer.start()
    wl = self.anWorkDict[anName].wl

    assert e, f"{node}: {simName}, {anName}"
    simDemands = self.ddmObj.getDemandForExprSim(self.func, node, simName, e)
    slice = ddm.NewSlice()
    for dem in simDemands:
      slice.update(self.ddmObj.propagateDemand(dem))

    self.stats.nodeMapUpdateTimer.start()
    changed = wl.updateNodeMap(slice.nodeMap)
    self.stats.nodeMapUpdateTimer.stop()
    if changed and LS:
      LOG.debug("UpdatedNodeMap(%s): %s", anName, wl)
    if changed:
      if LS: LOG.debug("%s_WorkList: (WL_Changed): %s", anName, wl)
      self.addAnToWorklist(anName)

    for dem in simDemands:
      if dem not in self.anDemandDep:
        self.anDemandDep[dem] = anDep = set()  # type: ignore
      else:
        anDep = self.anDemandDep[dem]
      anDep.add(anName)
    if self.useDdm: self.ddmObj.timer.stop()


  #@functools.lru_cache(1000)
  def fetchSimSourcesAndFilter(self,
      simName: SimNameT,
      nid: NodeIdT,
      e: Opt[expr.ExprET] = None,
  ) -> Set[AnNameT]:
    """
    Fetch the sim analyses and filters away analyses that
    *syntactically* cannot simplify the given expression.
    It caches the results.
    """
    if e is None:
      return self.fetchSimSources(simName)

    tup = (simName, e, nid)
    if tup in self.filteredSimSrcs:
      return self.filteredSimSrcs[tup]

    simAnNames = self.fetchSimSources(simName)
    if LS: LOG.debug("SimAnalyses (unfiltered) for sim '%s' are %s",
                     simName, simAnNames)

    filteredSimAnNames = set()

    for anName in simAnNames:
      anClass = clients.analyses[anName]
      anObj = anClass(self.func)  # FIXME: remove this redundancy
      simFunc = getattr(anObj, simName)
      if simFunc(e) is not SimFailed:  # filtering away analyses here
        filteredSimAnNames.add(anName)

    if LS: LOG.debug("SimAnalyses (filtered) for sim '%s' are %s",
                     simName, filteredSimAnNames)
    self.filteredSimSrcs[tup] = filteredSimAnNames  # caching the results
    return filteredSimAnNames


  # BOUND START: Simplification_Methods

  def getSim(self,
      node: cfg.CfgNode,
      simName: SimNameT,
      e: Opt[expr.ExprET] = None,  # could be None (in case of Node__to__Nil)
      demand: Opt[ddm.AtomicDemand] = None,  #DDM exclusive argument
  ) -> Opt[Set]:  # returns None if sim failed
    """Returns the simplification of the given expression.
    This function does the basic setup if needed and
    returns the combined sim of the given expression.
    """
    self.stats.simTimer.start()
    if demand is not None and simName not in self.activeAnSimNeeds: #DDM
      self.stats.simTimer.stop()
      return SimFailed  # i.e. process_the_original_insn

    if LS: LOG.debug("SimOfExpr (attempting): (Node_%s), %s, SimName: %s. (ForAn: %s)",
                     node.id, e, simName, demand if demand else self.activeAnName)

    # record the dependence
    self.addExprSimNeed(node.id, simName, e, demand,
                        None if demand else self.activeAnName)
    anNames = self.fetchSimSourcesAndSetup(node, simName, e, demand)

    res = self.collectAndMergeSimResults(anNames, simName, node, e)
    if res is not None and len(res) == 0: assert res is SimPending, f"{res}"

    if LS: LOG.debug("SimOfExpr (merged): '%s' is %s.", e, res)
    self.stats.simTimer.stop()
    return res


  def collectAndMergeSimResults(self,
      anNames: Set[AnNameT],
      simName: SimNameT,
      node: cfg.CfgNode,
      e: Opt[expr.ExprET],
  ) -> Opt[Set]:  # A None value indicates failed sim
    """Collects and merges the simplification by various analyses.
    Step 1: Select one working simplification from any one analysis.
    Step 2: Refine the simplification.
    """
    if not anNames: return SimFailed  # no sim analyses -- hence fail

    nid, tup2, res = node.id, (e, simName), []

    # Step 1: Find the first useful result
    values: Opt[Set] = SimFailed
    if LS: LOG.debug("SimAnalyses for %s: %s", simName, anNames)
    for anName in anNames:    # loop to select the first working sim
      simRecord = self.anRevNodeDep[(anName, nid)][tup2]
      if simRecord is not None:
        values = simRecord.getSim()
        if LS: LOG.debug("SelectedSim of %s for refinement: %s",
                         anName, values)
        break  # break at the first useful value
    if values in (SimPending, SimFailed):
      return values  # failed/pending values can never be refined

    # Step 2: Refine the simplification
    assert values not in (SimPending, SimFailed), f"{values}"
    if LS: LOG.debug("Refining(Start): %s", values)
    for anName in anNames:
      values = self.calculateSimValue(anName, simName, node, e, values)
      assert values != SimFailed, f"{anName}, {simName}, {node}, {e}, {values}"
      if values == SimPending:
        break  # no use to continue
    if LS: LOG.debug("Refining(End): Refined value is %s", values)
    return values  # a refined result


  def Calc_Deref__to__Vars(self,
      node: cfg.CfgNode,
      e: expr.VarE,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[Set[VarNameT]]:
    """
    This function is basically a call to self.getSim()
    with some checks.
    """
    res = cast(Opt[Set], self.getSim(node, Deref__to__Vars__Name, e, demand))

    if res is SimFailed:
      return SimFailed  # i.e. process_the_original_insn

    if self.transform and len(res) > 1:  #TRANSFORM
      if LS: print(f"SimFailed(TransformDeref): ({node.id}): {e}, {e.info}")
      res = SimFailed
    elif len(res) > 1 and NULL_OBJ_NAME in res:
        res.remove(NULL_OBJ_NAME)
    elif len(res) == 1 and NULL_OBJ_NAME in res:
      if LS: LOG.error("NullDerefEncountered (bad user program)(%s,%s): %s, %s",
                       self.func.name, node.id, e.name, node)
      if util.VV0: print(f"NullDerefEncountered (bad user program)"
                         f"({self.func.name},{node.id}), {e}, {e.info}")
      res = SimFailed  # i.e. process_the_original_insn

    if LS: LOG.debug("SimOfExpr (merged): '%s' is %s.", e.name, res)
    return res


  # BOUND END  : Simplification_Methods

  def printOrLogResult(self):
    """prints the result of all analyses."""
    if LS: LOG.debug("Stats:\n%s", self.stats)
    if self.useDdm:
      if LS: LOG.debug("DDM Stats\n%s", self.ddmObj.timer)
    if LS: LOG.debug("Stats:\n%s", self.tUnit.stats)

    if LS and GD: LOG.debug("AnWorklistDots:\n%s", self.getAnIterationDotString())

    if not util.VV2: return # i.e. then don't print what is below
    print() # some blank lines for neatness
    print(self.func, "TUnit:", self.func.tUnit.name)
    print(f"MODE: IPA: {self.ipaEnabled}, DDM: {self.useDdm},"
          f" SIM: {not self.disableSim}, TRANSFORM: {self.transform}")
    print("========================================")
    for anName, res in self.anWorkDict.items():
      print(f"{anName}:(SimCount: {self.anSimSuccessCount[anName]})")

      topTop = "IN == OUT: Top (Unreachable/Nop)"
      for node in self.funcCfg.revPostOrder:
        nid = node.id
        nDfv = res.nidNdfvMap.get(nid, topTop)
        print(f">> {nid}. ({node.insn}): {nDfv}")
      #print("Worklist:", self.anWorkDict[anName].wl.getAllNodesStr())
      print("NodesVisitOrder:", self.anWorkDict[anName].wl.fullSequence)

    # print("DiagnosticInfo:", file=sys.stderr)


  def setBoundaryResult(self,
      boundaryInfo: Dict[AnNameT, NodeDfvL]
  ) -> bool:
    """
    Update the results at the boundary.
    Returns true if there is a need to restart Host.
    """
    restart = False

    for anName in boundaryInfo.keys():
      anDirn = clients.getAnDirection(anName)
      dirnObj = self.anWorkDict[anName]
      nDfv = boundaryInfo[anName]

      nodeId = 1 if anDirn == Forward else len(self.funcCfg.nodeMap)
      node = self.funcCfg.nodeMap[nodeId]
      if anDirn == Forward: updateDfv = NodeDfvL(nDfv.dfvIn, nDfv.dfvIn)
      elif anDirn == Backward: updateDfv = NodeDfvL(nDfv.dfvOut, nDfv.dfvOut)
      else: raise TypeError("Analysis Direction ForwBack not handled.")
      inOutChange = dirnObj.update(node, updateDfv)
      if inOutChange:
        if LS: LOG.debug("IPA_UpdatedWorklist: %s, %s", self.func.name, dirnObj.wl)
        self.addAnToWorklist(anName, ipa=True)
        restart = True  # Should re-run the Host

      # IMPORTANT: Not needed. No analysis dependence at call sites!
      #   self.addDepAnToWorklist(node, inOutChange)

    return restart


  def getBoundaryResult(self) -> Dict[AnNameT, NodeDfvL]:
    """
    Returns the boundary result for all the analyses that participated.
    It returns the IN of start node, and OUT of end node for each analysis.
    User should extract the relevant value as per analysis directionality.
    """
    results = {}
    assert self.funcCfg.start and self.funcCfg.end, f"{self.funcCfg}"

    startId = self.funcCfg.start.id
    endId = self.funcCfg.end.id
    for anName, res in self.anWorkDict.items():
      startIn = res.nidNdfvMap.get(startId).dfvIn  # type: ignore
      endOut = res.nidNdfvMap.get(endId).dfvOut  # type: ignore
      results[anName] = NodeDfvL(startIn, endOut)

    return results


  def setCallSiteDfv(self, #IPA
      nodeId: NodeIdT,
      calleeName: FuncNameT,
      anName: AnNameT,
      nodeDfv: NodeDfvL,
      widen: bool = False,
  ) -> None:
    """
    Update the results for the call site.
    """
    tup = (nodeId, calleeName)
    if tup not in self.callSiteDfvMap:
      dfvDict = self.callSiteDfvMap[tup] = dict()
    else:
      dfvDict = self.callSiteDfvMap[tup]

    nDfv = nodeDfv
    if anName in dfvDict: # if already present, then try widening
      oldDfv = dfvDict[anName]
      if widen: nDfv, _ = oldDfv.widen(nodeDfv, ipa=True)
      if LS: LOG.debug(f"CalleeCallSiteDfv(Old): {tup}: {oldDfv}")
      if LS: LOG.debug(f"CalleeCallSiteDfv(New): {tup}: {nodeDfv}")
      if widen and LS:
        LOG.debug(f"CalleeCallSiteDfv(Widened): {tup}: {nDfv}")
    else:
      if LS: LOG.debug(f"CalleeCallSiteDfv(Old): {tup}: EMPTY.")
      if LS: LOG.debug(f"CalleeCallSiteDfv(New): {tup}: {nodeDfv}")
      if widen and LS:
        LOG.debug(f"CalleeCallSiteDfv(Widened): {tup}: is New, as Old=EMPTY.")

    dfvDict[anName] = nDfv


  def getCallSiteDfv(self, #IPA
      nodeId: NodeIdT,
      calleeName: Opt[FuncNameT],
      anName: AnNameT,
  ) -> Opt[NodeDfvL]:
    """
    Gets the callee BI as provided by IpaHost to the Host.
    """
    if not calleeName: return None # can happen in case of #INTRA analysis
    tup = (nodeId, calleeName)
    if tup not in self.callSiteDfvMapIpaHost:
      return None
    else:
      return self.callSiteDfvMapIpaHost[tup][anName]


  def setCallSiteDfvsIpaHost(self, #IPA
      nodeId: NodeIdT,
      calleeName: FuncNameT,
      newResults: Dict[AnNameT, NodeDfvL]
  ) -> bool:
    """
    Update the results for the call site.
    Returns true if there is a need to restart Host.
    """
    restart = False

    node = self.funcCfg.nodeMap[nodeId]
    tup = (nodeId, calleeName)
    if tup not in self.callSiteDfvMapIpaHost:
      oldResults = self.callSiteDfvMapIpaHost[tup] = dict()
      restart = True
    else:
      oldResults = self.callSiteDfvMapIpaHost[tup]

    widenedResult = newResults.copy() # a shallow copy (important)
    for anName in newResults.keys():
      restartAn = False
      wideDfv = newDfv = newResults[anName]
      if anName not in oldResults:
        restart = restartAn = True
      else:
        oldDfv = oldResults[anName]
        wideDfv, changed = oldDfv.widen(newDfv)
        if changed: restart = restartAn = True
      widenedResult[anName] = wideDfv

      if restartAn: # then modify the analysis' worklist
        dirn = self.anWorkDict[anName]
        if dirn.add(node):
          self.addAnToWorklist(anName, ipa=True)

    self.callSiteDfvMapIpaHost[tup] = widenedResult
    return restart


  def getCallSiteDfvsIpaHost(self,
  ) -> Dict[Tuple[NodeIdT, FuncNameT], Dict[AnNameT, NodeDfvL]]:
    """
    Returns the NodeDfvL objects for each analysis at the call site nodes.
    """
    if LS and util.VV3:
      LOG.debug(f"CallSitesDfvs(Host): {self.func.name}: {self.callSiteDfvMap}")
    return self.callSiteDfvMap


  def getParticipatingAnalyses(self) -> Set[AnNameT]:
    return set(self.anParticipating.keys())


  def getAnIterationDotString(self) -> str:
    subGraphs = "\n".join(self.anWorkListDot)
    dotGraph = f"\ndigraph {{\n  randdir=TB;\n\n{subGraphs}\n}} // close digraph\n"
    # util.writeToFile("anWorklist.dot", dotGraph)
    return dotGraph


  def getAnalysisResults(self,
      anName: AnNameT,
  ) -> Opt[DirectionDT]:
    """Returns the analysis results of the given analysis.

    Returns None if no information present.
    """
    if anName in self.anWorkDict:
      return self.anWorkDict[anName]
    return None


  def getResults(self):
    return self.anWorkDict


  def generateDot(self):
    currentIterName = f"{self.analysisCounter}_{self.activeAnName[:2]}"

    self.anWorkListDot.append(f"subgraph \"cluster_{currentIterName}\" {{")
    self.anWorkListDot.append(self.anWorkList.genDiGraph(currentIterName))

    dirn = self.anWorkDict[self.activeAnName]
    self.anWorkListDot.append(f"  \"{currentIterName}NodeWl\" [shape=box, label=\"{dirn.wl.tmpSequenceStr()}\"];")
    self.anWorkListDot.append(f"  \"{currentIterName}WL\" -> \"{currentIterName}NodeWl\" [style=invis];")
    self.anWorkListDot.append("} // close Wl subgraph")
    self.anWorkListDot.append("\n")
    dirn.wl.clearTmpSequence()

    # generate cfg seen by the analysis
    self.anWorkListDot.append(f"subgraph \"{currentIterName}Cfg\" {{")
    funcCfg = self.func.cfg

    for bbId, bb in funcCfg.bbMap.items():
      nodeStrs = []
      for node in bb.cfgNodeSeq:
        nid = node.id
        if nid in self.nodeInsnDot:
          content = ",".join(self.nodeInsnDot[nid])
        else:
          content = "Unprocessed"
        content = f"{nid}: {content}"
        nodeStrs.append(content)

      bbLabel: str = funcCfg.genDotBbLabel(bbId)
      nodeStrs.insert(0, "[" + bbLabel + "]")

      bbContent = "\\l".join(nodeStrs)
      bbNodeDot = f"  \"{currentIterName}{bbLabel}\" [shape=box, label=\"{bbContent}\\l\"];"
      self.anWorkListDot.append(bbNodeDot)

      for bbEdge in bb.succEdges:
        fromLabel = funcCfg.genDotBbLabel(bbEdge.src.id)
        toLabel = funcCfg.genDotBbLabel(bbEdge.dest.id)

        suffix = ""
        if bbEdge.label == TrueEdge:
          suffix = " [color=green, penwidth=2]"
        elif bbEdge.label == FalseEdge:
          suffix = " [color=red, penwidth=2]"

        content = f"  \"{currentIterName}{fromLabel}\" -> \"{currentIterName}{toLabel}\" {suffix};"
        self.anWorkListDot.append(content)

    self.anWorkListDot.append("} // close cfg subgraph")
    self.anWorkListDot.append("\n")


  def getCachedInstrSim(self,
      nid: NodeIdT,
      simName: SimNameT,
      insn: instr.InstrIT,
      e: expr.ExprET,
  ) -> Opt[instr.InstrIT]:
    """Returns the cached instruction simplification for the given
    node, simName, insn, expression."""
    tup1 = (nid, simName)
    if tup1 in self.instrSimCache:
      simCache = self.instrSimCache[tup1]
      tup2 = (insn, e)
      if tup2 in simCache:
        if LS: LOG.debug(f"Fetching CachedInsn(%s): (%s, %s): INSN: %s",
                         tup1, str(tup2[0]), str(tup2[1]), simCache[tup2])
        return simCache[tup2]

    return None


  def setCachedInstrSim(self,
      nid: NodeIdT,
      simName: SimNameT,
      insn: instr.InstrIT,
      e: expr.ExprET,
      newInsn: instr.InstrIT,
  ) -> None:
    tup1 = (nid, simName)
    if tup1 not in self.instrSimCache:
      self.instrSimCache[tup1] = {}

    tup2 = (insn, e)
    if insn == newInsn:
      self.instrSimCache[tup1][tup2] = FAILED_INSN_SIM
    else:
      self.instrSimCache[tup1][tup2] = newInsn
    if LS: LOG.debug(f"Added CachedInsn(%s): (%s, %s): INSN: %s",
                     tup1, str(tup2[0]), str(tup2[1]), newInsn)


  def removeCachedInstrSim(self,
      nid: NodeIdT,
      simName: SimNameT,
      insn: Opt[instr.InstrIT] = None,
      e: Opt[expr.ExprET] = None,
  ) -> None:
    assert insn is None and e is None or (insn is not None), f"{nid}: {insn}: {e}"

    tup1 = (nid, simName)
    if tup1 in self.instrSimCache:
      if insn is None:
        if LS: LOG.debug("Removing CachedInsn(s)(All): %s", tup1)
        self.instrSimCache[tup1] = {}
      else:
        tup2 = (insn, e)
        if tup2 in self.instrSimCache[tup1]:
          if LS: LOG.debug("Removing CachedInsn(%s): (%s, %s): INSN: %s",
                           tup1, str(insn), str(e), self.instrSimCache[tup1][tup2])
          del self.instrSimCache[tup1][tup2]


  def willChangeAffectSimDep(self, inOutChange: NewOldL) -> bool:
    """Returns True if the direction of change matters for sim dependence."""
    assert self.activeAnObj
    dirnStr = clients.getAnDirection(self.activeAnName)
    iChanged = inOutChange.isNewIn
    oChanged = inOutChange.isNewOut

    if dirnStr == Forward and iChanged:
      return True # for forward analyses change at IN can change sim
    if dirnStr == Backward and oChanged:
      return True # for backward analyses change at OUT can change sim
    if dirnStr == ForwBack and (iChanged or oChanged):
      return True # for forw/backward analyses change at IN/OUT can change sim
    return False


  def collectStats(self, gst: GlobalStats):
    """Collects useful stats in the system.
    This function must be called once the host is finished.
    """
    for tupAnNid, simMap in self.anRevNodeDep.items():
      for (e, simName), simRecord in simMap.items():
        if simRecord is not None and not simRecord.hasFailedValue():
          gst.simCountMap[simName] += 1

