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

import span.util.util as util
import span.util.common_util as cutil
from span.util.util import LS, AS, GD
import span.util.messages as msg

from span.ir.types import NodeIdT, VarNameT
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
from span.api.sim import SimNameT, simDirnMap, SimAT, SimFailed, SimPending
from span.api.lattice import mergeAll, DataLT
from span.api.analysis import AnalysisAT, AnalysisNameT as AnNameT,\
  ForwardD, BackwardD, DirectionDT
import span.sys.clients as clients
import span.sys.ddm as ddm
import span.sys.stats as stats
from span.sys.sim import SimRecord
import span.ir.graph as graph
import span.ir.tunit as irTUnit
import span.ir.constructs as constructs
import span.ir.ir as ir

Reachability = bool
Reachable: Reachability = True
NotReachable: Reachability = False

# BOUND START: Module_Storage__for__Optimization

Node__to__Nil__Name: str = SimAT.Node__to__Nil.__name__
LhsVar__to__Nil__Name: str = SimAT.LhsVar__to__Nil.__name__
Num_Var__to__Num_Lit__Name: str = SimAT.Num_Var__to__Num_Lit.__name__
Cond__to__UnCond__Name: str = SimAT.Cond__to__UnCond.__name__
Num_Bin__to__Num_Lit__Name: str = SimAT.Num_Bin__to__Num_Lit.__name__
Deref__to__Vars__Name: str = SimAT.Deref__to__Vars.__name__

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


class PriorityAnWorklist:
  """Priority Worklist of all participating analyses (not nodes)"""

  __slots__ : List[str] = ["wl", "wlSet", "anDepGraph", "popSequence"]

  def __init__(self):
    # wl is sorted in ascending order of weights, and popped from right
    self.wl: List[Participant] = []
    self.wlSet: Set[Participant] = set()
    # remember all analyses added in the analysis dependence graph
    self.anDepGraph: \
      Dict[AnNameT, Participant] = {}
    # remember the sequence in which the analyses were run
    self.popSequence: \
      List[Participant] = []


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

    if neededBy and anName != neededBy:
      # i.e. don't record self dependence
      assert neededBy in self.anDepGraph  # neededBy should be already present
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
        self.wl.sort()  # needed since weights were updated

    return added


  def add(self,
      anName: AnNameT,
      neededBy: Opt[AnNameT] = None,
  ) -> None:
    """Add an analysis to worklist.
    neededBy should already be in self.anDepGraph.
    """
    self.addToAnDepGraph(anName, neededBy)
    participant = self.anDepGraph[anName]

    if participant not in self.wlSet:
      self.wl.append(participant)
      self.wlSet.add(participant)
      self.wl.sort()
      if LS: LOG.debug("AddedAnalysisToWl: %s, (neededBy: %s)", anName, neededBy)


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

    if updated:
      self.wl.sort()


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

    assert participant in visited
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
      mainAnName: Opt[AnNameT] = None,
      otherAnalyses: Opt[List[AnNameT]] = None,
      supportAnalyses: Opt[List[AnNameT]] = None,
      avoidAnalyses: Opt[List[AnNameT]] = None,
      maxNumOfAnalyses: int = 1024,
      analysisSeq: Opt[List[List[AnNameT]]] = None,  # for cascading/lerner
      disableAllSim: bool = False,
      ipa: bool = False,
      biDfv: Opt[Dict[AnNameT, NodeDfvL]] = None,  # call site BI
      useDdm: bool = False,  # use demand driven approach
  ) -> None:
    timer = cutil.Timer("HostSetup")

    assert func.cfg and func.tUnit, f"{func}: {func.cfg}, {func.tUnit}"
    # function's cfg
    self.funcCfg: graph.Cfg = func.cfg
    # cfg's edge feasibility information
    self.ef: graph.FeasibleEdges = graph.FeasibleEdges(self.funcCfg)

    #DDM demand driven method?
    self.useDdm: bool = useDdm
    if self.useDdm:
      if LS: LOG.debug("UsingDDM: #DDM")
      self.ddmObj: ddm.DdMethod = ddm.DdMethod(func, self)
      # analyses dependent on a demand
      self.anDemandDep: Dict[ddm.AtomicDemand, Set[AnNameT]] = dict()
      # map of (nid, simName, expr) --to-> set of demands affected
      self.nodeInstrDemandSimDep: \
        Dict[Tuple[graph.CfgNodeId, SimNameT,
                   expr.ExprET], Set[ddm.AtomicDemand]] = dict()

    #IPA inter-procedural analysis?
    self.ipa: bool = ipa
    self.biDfv: Opt[Dict[AnNameT, NodeDfvL]] = biDfv  #IPA
    if self.ipa: assert biDfv, f"{biDfv}"  #IPA

    self.disableAllSim: bool = disableAllSim
    self.tUnit: irTUnit.TranslationUnit = func.tUnit

    # BLOCK START: SomeChecks
    if not func.hasBody():
      message = f"Function '{func.name}' is empty."
      if LS: LOG.error(message)
      raise ValueError(message)

    tmpList: List[AnNameT] = []
    if mainAnName:        tmpList.append(mainAnName)
    if otherAnalyses:     tmpList.extend(otherAnalyses)
    if supportAnalyses:  tmpList.extend(supportAnalyses)
    if avoidAnalyses:     tmpList.extend(avoidAnalyses)
    if analysisSeq:
      assert mainAnName is None, msg.INVARIANT_VIOLATED
      assert otherAnalyses is None, msg.INVARIANT_VIOLATED
      assert avoidAnalyses is None, msg.INVARIANT_VIOLATED
      assert maxNumOfAnalyses == 1024, msg.INVARIANT_VIOLATED
      for anSeq in analysisSeq:
        for anName in anSeq:
          tmpList.append(anName)

    assert tmpList, msg.INVARIANT_VIOLATED
    for anName in tmpList:
      if anName not in clients.analyses:
        message = f"Analysis '{anName}' is not present/registered."
        if LS: LOG.error(message)
        raise ValueError(message)
    # BLOCK END  : SomeChecks

    # BLOCK START: Cascading_And_Lerners
    self.lerner: bool = False
    if analysisSeq:  # enable cascading and lerners
      self.analysisSeq: Opt[List[List[AnNameT]]] = analysisSeq
      self.lerner = True
      self.lernerStepCurr: int = 0
      self.lernerStepMax: int = len(analysisSeq)
    # BLOCK END  : Cascading_And_Lerners

    # block information from IN to OUT and vice-versa,
    # for non simplification analyses.
    # It should be set to false eventually,
    # for non sim analyses to to conclude safely.
    self.blockNonSimAn: bool = True  # for testing purposes: should be True

    # function to be analyzed
    self.func: constructs.Func = func

    # main analysis (that may result in addition of others)
    self.mainAnName: AnNameT = mainAnName

    # currently active analysis and its needed info/objects
    self.activeAnName: AnNameT = ""
    self.activeAnObj: Opt[AnalysisAT] = None
    self.activeAnTop: Opt[DataLT] = None
    self.activeAnSimNeeds: Set[str] = set()
    self.activeAnIsSimAn: Opt[bool] = None  # active An simplifies?
    # True if transfer function for FilterI instr is present in the analysis
    self.activeAnIsLivenessAware: bool = False
    # Set of transfer functions provided by analysis
    self.activeAnTFuncs: Set[str] = set()
    # analysis priority worklist queue
    self.anWorkList: PriorityAnWorklist = PriorityAnWorklist()

    self.anWorkListDot: List[str] = []
    self.simplificationDot: List[str] = []
    # stores the insn seen by the analysis for the node
    self.nodeInsnDot: Dict[graph.CfgNodeId, List[str]] = {}

    # participant names, with their analysis instance (for curr function)
    self.anParticipating: Dict[AnNameT, AnalysisAT] = dict()
    # participated analyses names, with their instance (for curr function)
    # Used by: Cascading_And_Lerners
    self.anParticipated: Dict[AnNameT, AnalysisAT] = dict()
    # participants and their work result
    self.anWorkDict: Dict[AnNameT, DirectionDT] = dict()
    # map of (nid, simName, expr) --to-> set of analyses affected
    self.nodeInstrSimDep:\
      Dict[Tuple[graph.CfgNodeId, SimNameT,
                 expr.ExprET], Set[AnNameT]] = dict()
    self.anRevNodeDep: \
      Dict[Tuple[AnNameT, graph.CfgNodeId],
           Dict[Tuple[Opt[expr.ExprET], SimNameT], Opt[SimRecord]]] = dict()
    # sim instruction cache: cache the instruction computed for a sim
    self.instrSimCache: \
      Dict[Tuple[NodeIdT, SimNameT],
           Dict[Tuple[instr.InstrIT, Opt[expr.ExprET]], instr.InstrIT]] = dict()

    self.stats: stats.HostStat = stats.HostStat(self, len(self.funcCfg.nodeMap))

    # sim sources: sim to analysis mapping
    self.simSrcs: Dict[SimNameT, Set[AnNameT]] = dict()
    # cache filtered sim sources
    self.filteredSimSrcs: \
      Dict[Tuple[SimNameT, expr.ExprET, NodeIdT],
           Set[AnNameT]] = dict()

    # counts the net useful simplifications by a (supporting) analysis
    self.anSimSuccessCount: Dict[AnNameT, int] = dict()

    # records sequence in which analyses have run.
    self.anRunSequence: List[AnNameT] = []

    # max analyses allowed to run in synergy
    self.maxNumOfAnalyses: int = maxNumOfAnalyses
    self.currNumOfAnalyses: int = 0
    # set of analyses to avoid adding
    self.avoidAnalyses: Set[AnNameT] \
      = avoidAnalyses if avoidAnalyses else set()

    # record stats
    # number of times full analyses have run on the CFG
    self.analysisCounter: int = 0

    # the set of analyses that the user has asked to run to completion
    self.mainAnalyses: Set[AnNameT] = set()

    # add other analyses if present (as well)
    self.supportAnalyses: Opt[Set[AnNameT]] \
      = set(supportAnalyses) if supportAnalyses else None
    if otherAnalyses:
      for anName in reversed(otherAnalyses):
        self.mainAnalyses.add(anName)
        self.addParticipantAn(anName)
    # add the main analysis last (hence it is picked up first)
    if self.mainAnName:  # could be None in case of Cascading_And_Lerners
      self.mainAnalyses.add(self.mainAnName)
      self.addParticipantAn(self.mainAnName)

    nodes = self.ef.initFeasibility()
    # add nodes that have one or more feasible pred edge
    self.addNodes(nodes)

    # for support analyses that fail to simplify ALL needs
    self.activeAnIsUseful: bool = True

    timer.stopAndPrint()


  def addNodes(self, nodes: List[graph.CfgNode]) -> None:
    """Add nodes to worklist of all analyses that have freshly become feasible."""
    if not nodes:
      return

    for anName in self.anParticipating:
      nodeWorkList = self.anWorkDict[anName]
      for node in nodes:
        nodeWorkList.add(node)
      self.addAnToWorklist(anName)


  def addDepAnToWorklist(self, node: graph.CfgNode, inOutChange: NewOldL) -> None:
    """Add analyses dependent on active analysis (wrt given node) to worklist."""
    if not self.activeAnIsSimAn: return
    if not self.doesChangeMatchAnDirection(inOutChange): return

    nid, tup1 = node.id, (self.activeAnName, node.id)

    if tup1 not in self.anRevNodeDep:
      return  # no analysis depends on the active analysis

    simRecordDict = self.anRevNodeDep[tup1]

    for tup2 in simRecordDict.keys():
      simRecord = simRecordDict[tup2]
      if simRecord is SimFailed:
        continue  # i.e. update is useless
      e, simName = tup2[0], tup2[1]  # tup2 type is (expr, simName)
      value = self.calculateSimValue(self.activeAnName, simName, node, e)
      changed = simRecord.setSimValue(value)  # update value
      if changed:
        assert e, f"{tup2}"
        self.reAddAnalyses(node, simName, e)
        self.removeCachedInstrSim(nid, simName)
        if simRecord.hasFailedValue():
          self.decSimSuccessCount(self.activeAnName)   #COUNT_HERE:DEC
          simRecordDict[tup2] = None  # None represents failed value
        self.recomputeDemands(node, simName, e)
        self.stats.simChangeCacheHits.miss()
      else:
        self.stats.simChangeCacheHits.hit()


  def recomputeDemands(self, #DDM dedicated method
      node: graph.CfgNode,
      simName: SimNameT,
      e: expr.ExprET,
  ) -> None:
    """Recompute demands that depend on this simplification."""
    if not self.useDdm: return

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


  def doesSimNeedsUpdate(self,
      simName: SimNameT,
      inOutChange: NewOldL,
  ) -> bool:
    """using self.doesChangeMatchAnDirection() instead"""
    dirn = simDirnMap[simName]
    inChange  = inOutChange.isNewIn
    outChange = inOutChange.isNewOut
    if dirn == Forward and inChange:
      return True
    if dirn == Backward and outChange:
      return True
    if dirn == ForwBack and (inChange or outChange):
      return True
    return False


  def reAddAnalyses(self,
      node: graph.CfgNode,
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
      if self.lerner and anName not in self.anParticipating:
        continue
      if LS: LOG.debug("Adding_analyses_dependent_on %s to worklist. Adding: %s, Node %s",
                       self.activeAnName, anName, nid)
      self.addAnToWorklist(anName)
      self.anWorkDict[anName].add(node)

    if LS:
      newAnCount = len(self.anWorkList.wlSet)
      if newAnCount == oldAnCount:
        LOG.debug("Analyses_Worklist (Unchanged) (%s): %s",
                  self.activeAnName, self.anWorkList)
      else:
        LOG.debug("Analyses_Worklist (Changed) (%s): %s",
                  self.activeAnName, self.anWorkList)


  def conditionallyAddParticipantAn(self,
      anName: AnNameT,
      neededBy: Opt[AnNameT] = None
  ) -> bool:
    """Conditionally add an analysis as participant."""
    if self.canAdd(anName):
      return self.addParticipantAn(anName, neededBy)
    return False


  def addParticipantAn(self,
      anName: AnNameT,
      neededBy: Opt[AnNameT] = None
  ) -> bool:
    """Adds a new analysis into the mix (if not already present)."""
    if self.currNumOfAnalyses >= self.maxNumOfAnalyses:
      return False  # i.e. don't add any new analysis
    if anName in self.avoidAnalyses:
      return False  # i.e. dont add the analysis

    added: bool = False
    self.anWorkList.addToAnDepGraph(anName, neededBy)
    if anName not in self.anParticipating:
      # Then add the analysis.
      self.currNumOfAnalyses += 1
      if LS: LOG.debug("Adding %s. Needed by %s.", anName, neededBy)
      if not self.lerner:
        message = "If not in participants dict then should not be present at all."
        if AS and anName in self.anWorkDict:    raise Exception(message)

      analysisClass = clients.analyses[anName]  # get analysis Class
      analysisObj = analysisClass(self.func)  # create analysis instance
      top = analysisObj.overallTop

      self.anParticipating[anName] = analysisObj
      if self.lerner:
        self.anParticipated[anName] = analysisObj
      self.anWorkDict[anName] = analysisObj.D(self.func.cfg, top)
      self.addAnToWorklist(anName, neededBy, force=True)
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
      return  # don't add active analysis again
    if anName in self.mainAnalyses:
      self.anWorkList.add(anName, neededBy)
    else:
      if force or self.anSimSuccessCount[anName]:
        self.anWorkList.add(anName, neededBy)


  def calcInOut(self,
      node: graph.CfgNode,
      dirn: DirectionDT
  ) -> Tuple[NodeDfvL, NewOldL, Reachability]:
    """Merge info at IN and OUT of a node."""
    nid = node.id
    if self.ef.isFeasibleNode(node):
      if LS: LOG.debug("Before InOutMerge (Node %s): NodeDfv: %s.",
                       nid, dirn.nidNdfvMap.get(nid, dirn.topNdfv))
      ndfv, inout = dirn.calcInOut(node, self.ef)
      if LS: LOG.debug("After  InOutMerge (Node %s): Change: %s, NodeDfv: %s.",
                       nid, inout, ndfv)
      return ndfv, inout, Reachable
    return dirn.topNdfv, OLD_INOUT, NotReachable


  def setupAnalysis(self,
      anName: AnNameT
  ) -> DirectionDT:
    """Sets up the given analysis as current analysis to run."""
    self.stats.anSwitchTimer.start()
    self.anRunSequence.append(anName)
    self.activeAnObj = self.anParticipating[anName]
    self.activeAnTop = self.activeAnObj.overallTop
    self.activeAnSimNeeds = clients.simNeedMap[anName]
    self.activeAnIsSimAn = anName in clients.simAnalyses
    self.activeAnTFuncs = clients.anTFuncMap[anName]
    self.activeAnIsLivenessAware = anName in clients.anNeedsFullLiveness
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
      if self.ipa:  #IPA
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


  # mainentry
  def analyze(self) -> float:
    """Starts the process of running the analysis synergy."""
    timer = cutil.Timer("HostAnalyze")
    if self.func.sig.variadic:  # SkipVariadicFunctions
      if LS: LOG.info("SkippingVariadicFunction: %s", self.func.name)
    elif self.lerner:
      self.analyzeLerner()
    else:
      if LS: LOG.info("\nRUNNING_ANALYSIS MAIN_ANALYSIS: %s. on_function: %s\n",
                      self.mainAnName, self.func.name)
      while not self.anWorkList.isEmpty():
        self.analysisCounter += 1
        self._analyze()

    timer.stopAndPrint()
    return timer.getDurationInMillisec()


  def analyzeLerner(self) -> None:
    """Simulate Lerner's approach.
    Cascading is a special case of Lerner's where
    only one analysis runs at a time. This can
    be controlled by providing an appropriate value to self.analysisSeq.
    """
    assert self.analysisSeq, f"{self.analysisSeq}"
    while self.lernerStepCurr < self.lernerStepMax:
      stepAnalyses = self.analysisSeq[self.lernerStepCurr]
      self.initLerner(stepAnalyses)
      self.analyzeLernerStep()  # the Cascading_And_Lerner step analysis
      self.lernerStepCurr += 1


  def initLerner(self, stepAnalyses: List[AnNameT]) -> None:
    """Initialize a step in lerner's/cascading approach.
    Cascading_And_Lerners
    """
    # print("Cascading/Lerner's Step:", self.lernerStepCurr, ":", stepAnalyses)

    # Note that self.anWorkDict should not be emptied
    # since it holds dfv that can be used by analyses
    # in the steps ahead.
    self.anParticipating = dict()  # start from empty participant
    self.simSrcs = dict()  # force finding simSrcs
    self.currNumOfAnalyses = 0
    self.maxNumOfAnalyses = len(stepAnalyses)
    # self.anWorkList = PriorityAnWorklist() #FIXME:testing

    self.mainAnName = stepAnalyses[0]
    for anName in reversed(stepAnalyses):
      self.addParticipantAn(anName)

    # cfg's edge feasibility information
    self.ef = graph.FeasibleEdges(self.funcCfg)
    nodes = self.ef.initFeasibility()
    # add nodes that have feasible pred edges
    self.addNodes(nodes)


  def analyzeLernerStep(self) -> None:
    if LS: LOG.debug("\nRUNNING_ANALYSIS (Cascading_And_Lerners): %s.\n", self.mainAnName)
    while not self.anWorkList.isEmpty():
      self.analysisCounter += 1
      self._analyze()


  def _analyze(self) -> None:
    """Runs the analysis with highest priority, over self.func."""
    anName = self.anWorkList.pop()
    assert anName, f"{self.anWorkList}"
    self.activeAnName = anName
    dirn = self.setupAnalysis(anName)
    if GD: self.nodeInsnDot.clear()  # reinitialize for each new analysis iteration

    while True: #self.activeAnIsUseful:  #needs testing node visits are increasing
      if LS: LOG.debug("GetNextNodeFrom_Worklist (%s): %s (NODE_NODE_NODE)",
                       self.activeAnName, dirn.wl)
      node, treatAsNop, ddmVarSet = dirn.wl.pop()
      if node is None:
        break  # worklist is empty, so exit the loop
      # print(f"{self.activeAnName} {node.id} {node.insn}: {ddmVarSet}") #delit

      nid = node.id
      nodeDfv, inOutChange, feasibleNode = self.calcInOut(node, dirn)
      if feasibleNode:  # skip infeasible nodes
        if self.useDdm and self.activeAnName not in self.mainAnalyses:  #DDM
          if not nid == 1:  # skip the first node which is always NopI()
            nodeDfv = ddm.ddmFilterInDfv(nodeDfv, ddmVarSet)
            dirn.nidNdfvMap[nid] = nodeDfv

        if not treatAsNop: self.stats.incrementNodeVisitCount()

        if GD: self.nodeInsnDot[nid] = []

        self.addDepAnToWorklist(node, inOutChange)

        if LS: LOG.debug("Curr_Node_Dfv (Before) (Node %s): %s.", nid, nodeDfv)

        nodeDfv = self.analyzeInstr(node, node.insn, nodeDfv, treatAsNop)

        if LS: LOG.debug("Curr_Node_Dfv (AnalysisResult) (Node %s): %s", nid, nodeDfv)

        inOutChange = dirn.update(node, nodeDfv)

        if LS: LOG.debug("Curr_Node_Dfv (AfterUpdate) (Node %s): %s, change: %s.",
                         nid, nodeDfv, inOutChange)
        self.addDepAnToWorklist(node, inOutChange)
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
      node: graph.CfgNode,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
      treatAsNop: Opt[bool] = False,
  ) -> NodeDfvL:
    """
    This function handles node with parallel instruction as well.
    But self._analyzeInstr() does the main work.
    """
    if treatAsNop:
      return self.activeAnObj.Nop_Instr(node.id, insn, nodeDfv)

    if not isinstance(insn, instr.ParallelI):
      return self._analyzeInstr(node, insn, nodeDfv)

    if LS: LOG.debug("Analyzing_Instr (Node %s): %s", node.id, insn)

    def ai(ins):
      dfv = self._analyzeInstr(node, ins, nodeDfv)
      if LS: LOG.debug("FinalInstrDfv: %s", dfv)
      return dfv

    return mergeAll(ai(ins) for ins in insn.insns)


  def _analyzeInstr(self,
      node: graph.CfgNode,
      insn: instr.InstrIT,  # could be a simplified form of node.insn
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    LLS = LS
    if LLS: LOG.debug("Analyzing_Instr (Node %s): %s", node.id, insn)

    if self.ipa:  #IPA
      callE = instr.getCallExpr(insn)
      if callE and not callE.isPointerCall():
        func = self.tUnit.getFunctionObj(callE.callee.name)
        if func.hasBody() and not func.sig.variadic:
          # Inter-procedural analysis does not process the instructions with call
          # currently: function pointer based calls are handled intra-procedurally
          #            func with no body are handled intra-procedurally
          #            func with variadic arguments are handled intra-procedurally
          if LLS: LOG.debug("IPA: SkippingFunctionCallForIpa"
                            " (Nid %s) Insn: %s", node.id, insn)
          return nodeDfv

    activeAnObj = self.activeAnObj
    assert activeAnObj, f"{self.activeAnName}"
    transferFunc: Callable[[Any, Any, Any], NodeDfvL]\
      = activeAnObj.Nop_Instr  # default is NOP

    # is reachable (vs feasible) ?
    if Node__to__Nil__Name in self.activeAnSimNeeds:
      nilSim = self.getSim(node, Node__to__Nil__Name)
      if nilSim is not None:
        if LLS: LOG.debug("Unreachable_Node: %s: %s", node.id, insn)
        # return nodeDfv  # i.e. Barrier_Instr
        return self.Barrier_Instr(node, node.insn, nodeDfv)

    self.stats.funcSelectionTimer.start()
    # if here, node is reachable (or no analysis provides that information)
    iType = insn.type
    iTypeCode = iType.typeCode
    numericInstrType: bool = iType.isNumeric()
    ptrInstrType: bool = iType.isPointer()
    recordInstrType: bool = iType.isRecord()
    instrCode = insn.instrCode
    if LLS: LOG.debug("InstrValueType: %s, instrCode: %s", iType, instrCode)

    lhsVarSim = False
    rhsDerefSim = False
    lhsDerefSim = False
    rhsMemDerefSim = False
    lhsMemDerefSim = False
    rhsNumBinaryExprSim = False
    rhsNumUnaryExprSim = False
    rhsNumVarSim = False
    condInstr = False
    assignInstr = False

    # BOUND START: transfer_function_selection_process.
    if instrCode == NOP_INSTR_IC:
      if LLS: LOG.debug(AnalysisAT.Nop_Instr.__doc__)
      transferFunc = activeAnObj.Nop_Instr

    elif instrCode == USE_INSTR_IC:
      if LLS: LOG.debug(AnalysisAT.Use_Instr.__doc__)
      transferFunc = activeAnObj.Use_Instr

    elif instrCode == EX_READ_INSTR_IC:
      if LLS: LOG.debug(AnalysisAT.ExRead_Instr.__doc__)
      transferFunc = activeAnObj.ExRead_Instr

    elif instrCode == COND_READ_INSTR_IC:
      if LLS: LOG.debug(AnalysisAT.CondRead_Instr.__doc__)
      transferFunc = activeAnObj.CondRead_Instr

    elif instrCode == UNDEF_VAL_INSTR_IC:
      if LLS: LOG.debug(AnalysisAT.UnDefVal_Instr.__doc__)
      transferFunc = activeAnObj.UnDefVal_Instr

    elif instrCode == FILTER_INSTR_IC:
      if LLS: LOG.debug(AnalysisAT.Filter_Instr.__doc__)
      transferFunc = activeAnObj.Filter_Instr

    elif isinstance(insn, instr.ReturnI):
      if insn.arg is None:
        if LLS: LOG.debug(AnalysisAT.Return_Void_Instr.__doc__)
        transferFunc = activeAnObj.Return_Void_Instr
      elif insn.arg.exprCode == VAR_EXPR_EC:
        if LLS: LOG.debug(AnalysisAT.Return_Var_Instr.__doc__)
        transferFunc = activeAnObj.Return_Var_Instr
      else:
        if LLS: LOG.debug(AnalysisAT.Return_Lit_Instr.__doc__)
        transferFunc = activeAnObj.Return_Lit_Instr

    elif instrCode == COND_INSTR_IC:
      if LLS: LOG.debug(AnalysisAT.Conditional_Instr.__doc__)
      transferFunc = activeAnObj.Conditional_Instr
      condInstr = True

    elif instrCode == CALL_INSTR_IC:
      if LLS: LOG.debug(AnalysisAT.Call_Instr.__doc__)
      transferFunc = activeAnObj.Call_Instr

    elif isinstance(insn, instr.AssignI):
      lhs, rhs = insn.lhs, insn.rhs
      lhsExprCode, rhsExprCode = lhs.exprCode, rhs.exprCode
      if lhsExprCode == VAR_EXPR_EC:
        lhsVarSim = True
        if rhsExprCode == VAR_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_Var_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_Var_Instr
            rhsNumVarSim = True
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_Var_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_Var_Instr
          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Var_Var_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Var_Var_Instr

        elif rhsExprCode == LIT_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_Lit_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_Lit_Instr

          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_Lit_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_Lit_Instr

        elif rhsExprCode == SIZEOF_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          # hence lhs, rhs are numeric
          if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_SizeOf_Instr.__doc__)
          transferFunc = activeAnObj.Num_Assign_Var_SizeOf_Instr

        elif isinstance(rhs, expr.UnaryE): # lhsExprCode == VAR_EXPR_EC
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_UnaryArith_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_UnaryArith_Instr
            rhsNumUnaryExprSim = True
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == DEREF_EXPR_EC:
          rhsDerefSim = True
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_Deref_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_Deref_Instr
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_Deref_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_Deref_Instr
          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Var_Deref_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Var_Deref_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s, itype: %s",
                              insn, insn.type)

        elif rhsExprCode == BINARY_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_BinArith_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_BinArith_Instr
            rhsNumBinaryExprSim = True
          elif ptrInstrType:  # must be a pointer instruction
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_BinArith_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_BinArith_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif isinstance(rhs, expr.AddrOfE): # lhsExprCode == VAR_EXPR_EC
          # iType must be a pointer
          argExprCode = rhs.arg.exprCode
          if argExprCode == VAR_EXPR_EC:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_AddrOfVar_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_AddrOfVar_Instr
          elif argExprCode == ARR_EXPR_EC:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_AddrOfArray_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_AddrOfArray_Instr
          elif argExprCode == MEMBER_EXPR_EC:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_AddrOfMember_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_AddrOfMember_Instr
          elif isinstance(rhs.arg, expr.DerefE):
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_AddrOfDeref_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_AddrOfDeref_Instr
          elif argExprCode == FUNC_EXPR_EC:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_AddrOfFunc_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_AddrOfFunc_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == ARR_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_Array_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_Array_Instr

          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_Array_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_Array_Instr

          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Var_Array_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Var_Array_Instr

          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == MEMBER_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          rhsMemDerefSim = insn.rhs.hasDereference()
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_Member_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_Member_Instr

          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_Member_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_Member_Instr

          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Var_Member_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Var_Member_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == CALL_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_Call_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_Call_Instr

          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_Call_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_Call_Instr

          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Var_Call_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Var_Call_Instr

          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == FUNC_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          if ptrInstrType:  # has to be
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_FuncName_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_FuncName_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == SELECT_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_Select_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Var_Select_Instr
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_Select_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Var_Select_Instr
          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Var_Select_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Var_Select_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif isinstance(rhs, expr.CastE):  # lhsExprCode == VAR_EXPR_EC
          if rhs.arg.exprCode == VAR_EXPR_EC:
            if numericInstrType:
              if LLS: LOG.debug(AnalysisAT.Num_Assign_Var_CastVar_Instr.__doc__)
              transferFunc = activeAnObj.Num_Assign_Var_CastVar_Instr
            elif ptrInstrType:
              if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_CastVar_Instr.__doc__)
              transferFunc = activeAnObj.Ptr_Assign_Var_CastVar_Instr
            else:
              if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

          elif rhs.arg.exprCode == ARR_EXPR_EC:
            if ptrInstrType:
              if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Var_CastArr_Instr.__doc__)
              transferFunc = activeAnObj.Ptr_Assign_Var_CastArr_Instr
            else:
              if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

      elif lhsExprCode == DEREF_EXPR_EC:
        # lhs has to be a deref
        lhsDerefSim = True
        if rhsExprCode == VAR_EXPR_EC:  # lhs is a deref
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Deref_Var_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Deref_Var_Instr
            rhsNumVarSim = True
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Deref_Var_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Deref_Var_Instr
          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Deref_Var_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Deref_Var_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == LIT_EXPR_EC:  # lhs is a deref
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Deref_Lit_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Deref_Lit_Instr
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Deref_Lit_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Deref_Lit_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

      elif lhsExprCode == ARR_EXPR_EC:
        if rhsExprCode == VAR_EXPR_EC:  # lhs is an array expr
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Array_Var_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Array_Var_Instr
            rhsNumVarSim = True
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Array_Var_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Array_Var_Instr
          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Array_Var_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Array_Var_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == LIT_EXPR_EC:  # lhs is an array expr
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Array_Lit_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Array_Lit_Instr
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Array_Lit_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Array_Lit_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

      elif lhsExprCode == MEMBER_EXPR_EC:
        lhsMemDerefSim = insn.lhs.hasDereference()
        if rhsExprCode == VAR_EXPR_EC:  # lhs is a member expr
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Member_Var_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Member_Var_Instr
            rhsNumVarSim = True
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Member_Var_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Member_Var_Instr
          elif recordInstrType:
            if LLS: LOG.debug(AnalysisAT.Record_Assign_Member_Var_Instr.__doc__)
            transferFunc = activeAnObj.Record_Assign_Member_Var_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

        elif rhsExprCode == LIT_EXPR_EC:  # lhs is a member expr
          if numericInstrType:
            if LLS: LOG.debug(AnalysisAT.Num_Assign_Member_Lit_Instr.__doc__)
            transferFunc = activeAnObj.Num_Assign_Member_Lit_Instr
          elif ptrInstrType:
            if LLS: LOG.debug(AnalysisAT.Ptr_Assign_Member_Lit_Instr.__doc__)
            transferFunc = activeAnObj.Ptr_Assign_Member_Lit_Instr
          else:
            if LLS: LOG.error("Unknown_or_Unhandled_Instruction: %s", insn)

    else:
      if LLS: LOG.error("Unknown_or_Unhandled_Instruction.")

    self.stats.funcSelectionTimer.stop()
    # BOUND END  : transfer_function_selection_process.
    transferFunc = cast(Callable[[Any, Any, Any], NodeDfvL], transferFunc)

    tFuncName = transferFunc.__name__  # needed
    if not self.disableAllSim and transferFunc != activeAnObj.Nop_Instr:
      if tFuncName == UnDefVal_Instr__Name:
        # lhs is a var, hence could be dead code
        nDfv = self.handleLivenessSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      # is the instr a var assignment (not deref etc)
      if lhsVarSim:
        # lhs is a var, hence could be dead code
        nDfv = self.handleLivenessSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if lhsDerefSim:
        # lhs is a dereference, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{node.id}: {insn}"
        nDfv = self.handleLhsDerefSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if lhsMemDerefSim:
        # lhs is a dereference, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{node.id}: {insn}"
        nDfv = self.handleLhsMemDerefSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if rhsDerefSim:
        # rhs is a dereference, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{node.id}: {insn}"
        nDfv = self.handleRhsDerefSim(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if rhsNumBinaryExprSim:
        # rhs is a numeric bin expr, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{node.id}: {insn}"
        nDfv = self.handleRhsBinArith(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        nDfv = self.handleRhsBinArithArgs(node, insn, nodeDfv, 1)
        if nDfv is not None: return nDfv
        nDfv = self.handleRhsBinArithArgs(node, insn, nodeDfv, 2)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if rhsNumUnaryExprSim:
        # rhs is a numeric unary expr, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{node.id}: {insn}"
        nDfv = self.handleRhsUnaryArith(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

      if rhsNumVarSim:
        # rhs is a numeric var, hence could be simplified
        assert isinstance(insn, instr.AssignI), f"{node.id}: {insn}"
        nDfv = self.handleRhsNumVar(node, insn, nodeDfv)
        if nDfv is not None: return nDfv
        # if nDfv is None then work on the original instruction

    if GD:
      if transferFunc == self.Nop_Instr:
        self.nodeInsnDot[node.id].append("nop")
      else:
        self.nodeInsnDot[node.id].append(str(insn))

    if condInstr:
      assert isinstance(insn, instr.CondI), f"{node.id}, {insn}"
      return self.Conditional_Instr(node, insn, nodeDfv)  # type: ignore
    else:
      self.stats.instrAnTimer.start()
      nDfv = transferFunc(node, insn, nodeDfv)  # type: ignore
      self.stats.instrAnTimer.stop()
      return nDfv


  def getCachedInstrSimResult(self,
      node: graph.CfgNode,
      simName: SimNameT,
      insn: instr.InstrIT,
      e: expr.ExprET,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Tuple[Opt[instr.InstrIT], bool]:
    """Returns data flow computation using the cache if available."""
    self.stats.simTimer.start()
    nid = node.id
    self.addExprSimNeed(node.id, simName, e, demand,
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
    return None, False


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
      if LS: LOG.debug("AddedSimDependence: (changed) (Node %s), %s, %s, Set: %s",
                       nid, simName, client, depSet)
    else:
      if LS: LOG.debug("AddedSimDependence: (unchanged) (Node %s), %s, %s, Set: %s",
                       nid, simName, client, depSet)


  def handleNewInstr(self,
      node: graph.CfgNode,
      simName: SimNameT,
      insn: instr.InstrIT,
      e: expr.ExprET,
      newInsn: instr.InstrIT,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """A basic function to encapsulate common computation in many functions."""
    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, e, newInsn)
    return self.analyzeInstr(node, newInsn, nodeDfv)


  def isLivenessSupportNeeded(self) -> bool:
    """
    TODO: check the logic.
    """
    needed = True
    if LhsVar__to__Nil__Name not in self.activeAnSimNeeds:
      needed = False
      enableLivenessSupport = False
    else:
      enableLivenessSupport = self.activeAnIsLivenessAware

    if LS: LOG.debug("ProvidingLivenessSupport?: %s (LivenessSupportNeeded?: %s)",
                     enableLivenessSupport, needed)
    return enableLivenessSupport


  def handleLivenessSim(self,
      node: graph.CfgNode,
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
      node: graph.CfgNode,
      insn: instr.AssignI,  # lhs is expr.DerefE
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getLhsDerefSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getLhsDerefSimInstr(self,
      node: graph.CfgNode,
      insn: instr.AssignI,  # lhs is expr.DerefE
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.lhs, expr.DerefE), f"{node.id}: {insn}"
    lhsArg, rhs, simName = insn.lhs.arg, insn.rhs, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, lhsArg, demand)
    if valid: return newInsn

    ret = self.Calc_Deref__to__Vars(node, lhsArg)
    if ret is None:
      self.setCachedInstrSim(node.id, simName, insn, lhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif ret == SimPending:
      newInsn = instr.ExReadI({lhsArg.name})
    else:  # take meet of the dfv of the set of instructions now possible
      assert ret.val and len(ret.val), f"{node}: {ret}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.ParallelI([AssignI(VarE(vName), rhs) for vName in ret.val])
      newInsn.addInstr(instr.ExReadI({lhsArg.name}))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, lhsArg, newInsn)
    return newInsn


  def handleRhsDerefSim(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getRhsDerefSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getRhsDerefSimInstr(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.rhs, expr.DerefE), f"{node.id}: {insn}"
    lhs, rhsArg, simName = insn.lhs, insn.rhs.arg, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, rhsArg, demand)
    if valid: return newInsn

    ret = self.Calc_Deref__to__Vars(node, rhsArg)
    if ret is None:
      self.setCachedInstrSim(node.id, simName, insn, rhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif ret == SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhsArg))
    else:  # take meet of the dfv of the set of instructions now possible
      assert ret.val and len(ret.val), f"{node}: {ret}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.ParallelI([AssignI(lhs, VarE(vName)) for vName in ret.val])
      newInsn.addInstr(instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhsArg)))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, rhsArg, newInsn)
    return newInsn


  def handleLhsMemDerefSim(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getLhsMemDerefSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getLhsMemDerefSimInstr(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.lhs, expr.MemberE), f"{node.id}: {insn}"
    lhs, rhs, simName = insn.lhs, insn.rhs, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, lhs.of, demand)
    if valid: return newInsn

    ret = self.Calc_Deref__to__Vars(node, lhs.of)
    if ret is None:
      self.setCachedInstrSim(node.id, simName, insn, lhs.of, insn)
      return None  # i.e. process_the_original_insn
    elif ret == SimPending:
      newInsn = instr.ExReadI({lhs.of.name})
    else:  # take meet of the dfv of the set of instructions now possible
      assert ret.val and len(ret.val), f"{node}: {ret}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.ParallelI([AssignI(VarE(f"{varName}.{lhs.name}"), rhs)
                                 for varName in ret.val])
      newInsn.addInstr(instr.ExReadI({lhs.of.name}))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, lhs.of, newInsn)
    return newInsn


  def handleRhsMemDerefSim(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    newInsn = self.getRhsMemDerefSimInstr(node, insn)
    if newInsn is None:
      return None  # i.e. process_the_original_insn
    else:
      return self.analyzeInstr(node, newInsn, nodeDfv)


  def getRhsMemDerefSimInstr(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[instr.InstrIT]:
    assert isinstance(insn.rhs, expr.MemberE), f"{node.id}: {insn}"
    lhs, rhs, simName = insn.lhs, insn.rhs, Deref__to__Vars__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName,
                                                  insn, rhs.of, demand)
    if valid: return newInsn

    ret = self.Calc_Deref__to__Vars(node, rhs.of)
    if ret is None:
      self.setCachedInstrSim(node.id, simName, insn, rhs.of, insn)
      return None  # i.e. process_the_original_insn
    elif ret == SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs.of))
    else:  # take meet of the dfv of the set of instructions now possible
      assert ret.val and len(ret.val), f"{node}: {ret}"
      AssignI, VarE = instr.AssignI, expr.VarE
      newInsn = instr.ParallelI([AssignI(lhs, VarE(f"{vName}.{rhs.name}"))
                                 for vName in ret.val])
      newInsn.addInstr(instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs.of)))

    self.tUnit.inferTypeOfInstr(newInsn)
    self.setCachedInstrSim(node.id, simName, insn, rhs.of, newInsn)
    return newInsn


  def handleRhsNumVar(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    assert isinstance(insn.rhs, expr.VarE), f"{node.id}: {insn}"
    lhs, rhs, simName = insn.lhs, insn.rhs, Num_Var__to__Num_Lit__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName, insn, rhs)
    if valid: return self.analyzeInstr(node, newInsn, nodeDfv) if newInsn else None

    ret = self.getSim(node, simName, rhs)
    if ret is None:
      self.setCachedInstrSim(node.id, simName, insn, rhs, insn)
      return None  # i.e. process_the_original_insn
    elif ret == SimPending:
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
        assert False, f"{insn}"

    else:  # there is some simplification
      if not self.activeAnIsSimAn and self.blockNonSimAn:
        return self.Barrier_Instr(node, node.insn, nodeDfv)
      AssignI, LitE = instr.AssignI, expr.LitE
      assert isinstance(ret.val, (int, float)), f"{ret}"
      newInsn = instr.ParallelI([AssignI(lhs, LitE(ret.val))])

    return self.handleNewInstr(node, simName, insn, rhs, newInsn, nodeDfv)


  def handleRhsUnaryArith(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    assert isinstance(insn.rhs, expr.UnaryE), f"{node.id}: {insn}"
    lhs, rhsArg, simName = insn.lhs, insn.rhs.arg, Num_Var__to__Num_Lit__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName, insn, rhsArg)
    if valid: return self.analyzeInstr(node, newInsn, nodeDfv) if newInsn else None

    ret = self.getSim(node, simName, rhsArg)
    if ret is None:
      self.setCachedInstrSim(node.id, simName, insn, rhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif ret == SimPending:
      assert isinstance(rhsArg, expr.VarE), f"{node.id}: {insn}"
      newInsn = instr.CondReadI(lhs.name, {rhsArg.name})
    else:
      assert isinstance(ret.val, (int, float)), f"{ret}"
      rhs = insn.rhs
      AssignI, UnaryE, LitE = instr.AssignI, expr.UnaryE, expr.LitE
      newInsn = instr.ParallelI(
        [AssignI(lhs, UnaryE(rhs.opr, LitE(ret.val)).computeExpr())])

    return self.handleNewInstr(node, simName, insn, rhsArg, newInsn, nodeDfv)


  def handleRhsBinArith(self,
      node: graph.CfgNode,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> Opt[NodeDfvL]:
    lhs, rhs, simName = insn.lhs, insn.rhs, Num_Bin__to__Num_Lit__Name

    newInsn, valid = self.getCachedInstrSimResult(node, simName, insn, rhs)
    if valid: return self.analyzeInstr(node, newInsn, nodeDfv) if newInsn else None

    ret = self.getSim(node, simName, rhs)
    if ret is None:
      self.setCachedInstrSim(node.id, simName, insn, rhs, insn)
      return None  # i.e. process_the_original_insn
    elif ret == SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs))
    else:
      assert isinstance(ret.val, (int, float)), f"{ret}"
      AssignI, LitE = instr.AssignI, expr.LitE
      newInsn = instr.ParallelI([AssignI(lhs, LitE(ret.val))])
      newInsn.addInstr(instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs)))

    return self.handleNewInstr(node, simName, insn, rhs, newInsn, nodeDfv)


  def handleRhsBinArithArgs(self,
      node: graph.CfgNode,
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

    ret = self.getSim(node, simName, rhsArg)
    if ret is None:
      self.setCachedInstrSim(node.id, simName, insn, rhsArg, insn)
      return None  # i.e. process_the_original_insn
    elif ret == SimPending:
      newInsn = instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs))
    else:
      AssignI, LitE, BinaryE = instr.AssignI, expr.LitE, expr.BinaryE
      assert isinstance(ret.val, (int, float)), f"{ret}"
      if argPos == 1:
        newInsn = instr.ParallelI([AssignI(lhs, BinaryE(LitE(ret.val), rhs.opr, rhs.arg2))])
      else:
        newInsn = instr.ParallelI([AssignI(lhs, BinaryE(rhs.arg1, rhs.opr, LitE(ret.val)))])
      newInsn.addInstr(instr.CondReadI(lhs.name, ir.getNamesUsedInExprSyntactically(rhs)))

    return self.handleNewInstr(node, simName, insn, rhsArg, newInsn, nodeDfv)


  # BOUND START: RegularInstructions

  def Conditional_Instr(self,
      node: graph.CfgNode,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    # always handle conditional instruction
    self.stats.instrAnTimer.stop() # okay - excluding edge feasibility computation
    nodes = self.setEdgeFeasibility(node, insn.arg)
    self.stats.instrAnTimer.start() # okay
    if nodes:
      self.addNodes(nodes)

    return self.activeAnObj.Conditional_Instr(node.id, insn, nodeDfv)


  def setEdgeFeasibility(self, node, arg) -> Opt[List[graph.CfgNode]]:
    nodes = None
    if self.disableAllSim:
      nodes = self.ef.setAllSuccEdgesFeasible(node)
    elif Cond__to__UnCond__Name in self.activeAnSimNeeds:
      boolSim = self.getSim(node, Cond__to__UnCond__Name, arg)
      if boolSim is None:
        nodes = self.ef.setAllSuccEdgesFeasible(node)
      elif boolSim == SimPending:
        nodes = None
      elif boolSim.val == False:  # only false edge taken
        nodes = self.ef.setFalseEdgeFeasible(node)
      elif boolSim.val == True:   # only true edge taken
        nodes = self.ef.setTrueEdgeFeasible(node)
      else:
        assert False, f"{boolSim}"

    if self.useDdm: self.ddmObj.timer.start()
    if nodes and self.useDdm: #DDM
      self.ddmObj.updateInfNodeDepDemands(nodes)
      self.processChangedDemands()
    if self.useDdm: self.ddmObj.timer.stop()

    return nodes

  # BOUND END  : RegularInstructions

  # BOUND START: SpecialInstructions

  def Filter_Instr(self,
      node: graph.CfgNode,  # redundant but needed
      insn: instr.FilterI,  # redundant but needed
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Let only the live variables pass through."""
    if LS: LOG.debug("FinallyProcessingInstruction (Node %s): %s", node.id, insn)
    assert self.activeAnObj
    return self.activeAnObj.Filter_Instr(node.id, insn, nodeDfv)


  def Barrier_Instr(self,
      node: graph.CfgNode,  # redundant but needed
      insn: instr.InstrIT,  # redundant but needed
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """block all info from crossing (forw&back) from within the node."""
    if LS: LOG.debug("FinallyProcessingInstruction (Node %s): BarrierI()", node.id)
    # return self.activeAnObj.Barrier_Instr(nodeDfv)
    if GD: self.nodeInsnDot[node.id].append("block")
    return nodeDfv  # i.e. block the info


  def Use_Instr(self,
      node: graph.CfgNode,
      insn: instr.UseI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if LS: LOG.debug("FinallyProcessingInstruction (Node %s): %s", node.id, insn)
    assert self.activeAnObj
    return self.activeAnObj.Use_Instr(node.id, insn, nodeDfv)


  def ExRead_Instr(self,
      node: graph.CfgNode,
      insn: instr.ExReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Assumes that the analysis has implemented ExReadI()."""
    if LS: LOG.debug("FinallyProcessingInstruction (Node %s): %s", node.id, insn)
    assert self.activeAnObj
    return self.activeAnObj.ExRead_Instr(node.id, insn, nodeDfv)


  def CondRead_Instr(self,
      node: graph.CfgNode,
      insn: instr.CondReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if LS: LOG.debug("FinallyProcessingInstruction (Node %s): %s", node.id, insn)
    assert self.activeAnObj
    return self.activeAnObj.CondRead_Instr(node.id, insn, nodeDfv)


  def UnDefVal_Instr(self,
      node: graph.CfgNode,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if LS: LOG.debug("FinallyProcessingInstruction (Node %s): %s", node.id, insn)
    assert self.activeAnObj
    return self.activeAnObj.UnDefVal_Instr(node.id, insn, nodeDfv)


  def Nop_Instr(self,
      node: graph.CfgNode,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if LS: LOG.debug("FinallyProcessingInstruction (Node %s): %s", node.id, insn)
    return self.identity(node, insn, nodeDfv)


  # BOUND END  : SpecialInstructions

  def canAdd(self,
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
    elif self.lerner and anName not in self.anWorkDict:
      # in lerner's case add no new analysis
      # lerner adds all the analyses needed at initialization
      okToAdd = False
    if LS: LOG.debug("CAN_ADD_ANALYSIS(%s): %s", anName, okToAdd)
    return okToAdd


  #@functools.lru_cache(10)
  def fetchSimSources(self,
      simName: SimNameT,
  ) -> Set[AnNameT]:
    """Fetches allowed analysis names that
    provide the simplification.
    It caches the results."""
    if simName in self.simSrcs:
      return self.simSrcs[simName]

    simAnNames: Set[AnNameT] = set()  # adds type info
    for anName in clients.simSrcMap.get(simName, set()):
      if self.canAdd(anName):
        simAnNames.add(anName)  # add simplification analyses

    self.simSrcs[simName] = simAnNames  # cache the result
    return simAnNames


  def setupSimSourcesDep(self,
      node: graph.CfgNode,
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
        self.incSimSuccessCount(simAnName, self.activeAnName) #COUNT_HERE:INC
        if not sr: self.decSimSuccessCount(simAnName)   #COUNT_HERE:DEC
        simRecordMap[tup2] = sr if sr else SimFailed


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
      self.activeAnIsUseful = False


  def calculateSimValue(self,
      simAnName: str,
      simName: SimNameT,
      node: graph.CfgNode,
      e: Opt[expr.ExprET] = None,
      values: Opt[Set] = None,
  ) -> Opt[Set]:
    """Calculates the simplification value for the given parameters."""
    if self.lerner:
      anObj = self.anParticipated[simAnName]
    else:
      anObj = self.anParticipating[simAnName]

    assert hasattr(anObj, simName), f"{simAnName}, {simName}"
    nid, simFunction = node.id, getattr(anObj, simName)
    nDfv = self.anWorkDict[simAnName].getDfv(nid)

    if LS: LOG.debug("SimOfExpr: %s isAttemptedBy %s withDfv %s.", e, simAnName, nDfv)
    # Note: if e is None, it assumes sim works on node id
    value = simFunction(e if e else nid, nDfv, values)
    if LS: LOG.debug("SimOfExpr: %s is %s, by %s.", e, value, simAnName)
    return value


  #@functools.lru_cache(500)
  def fetchAndSetupSimSrcs(self,
      node: graph.CfgNode,
      simName: SimNameT,
      e: Opt[expr.ExprET] = None,
      demand: Opt[ddm.AtomicDemand] = None,  #DDM
  ) -> Set[AnNameT]:
    """Adds analyses that can evaluate simName."""
    simAnNames = self.fetchAndFilterSimAnalyses(simName, node.id, e)

    for anName in simAnNames:
      neededBy = None if demand else self.activeAnName
      added = self.addParticipantAn(anName, neededBy=neededBy)
      if added and self.useDdm:
        self.initializeAnalysisForDdm(node, simName, anName, e)

    self.setupSimSourcesDep(node, simAnNames, simName, e)
    return simAnNames


  def initializeAnalysisForDdm(self, #DDM dedicated method
      node: graph.CfgNode,
      simName: SimNameT,
      anName: AnNameT,
      e: Opt[expr.ExprET] = None,
  ):
    """Called after anName is added using self.addParticipantAn()
    and it returns True"""
    if not self.useDdm or anName in self.mainAnalyses:
      return  # main analyses are not #DDM driven

    if self.useDdm: self.ddmObj.timer.start()
    wl = self.anWorkDict[anName].wl
    assert not wl.fullSequence, f"Analysis {anName} already started."
    wl.initForDdm()
    if self.useDdm: self.ddmObj.timer.stop()


  def attachDemandToSimAnalysis(self, #DDM dedicated method
      node: graph.CfgNode,
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
  def fetchAndFilterSimAnalyses(self,
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

    filteredSimAnNames = []

    for anName in simAnNames:
      anClass = clients.analyses[anName]
      anObj = anClass(self.func)
      simFunc = getattr(anObj, simName)
      if simFunc(e) is SimFailed:  # filtering away analyses here
        filteredSimAnNames.append(anName)

    self.filteredSimSrcs[tup] = set(filteredSimAnNames)  # caching the results
    return set(filteredSimAnNames)


  # BOUND START: Simplification_Methods

  def getSim(self,
      node: graph.CfgNode,
      simName: SimNameT,
      e: Opt[expr.ExprET] = None,  # could be None (in case of Node__to__Nil)
      demand: Opt[ddm.AtomicDemand] = None,  #DDM exclusive argument
  ) -> Opt[Set]:  # returns None if sim failed
    """Returns the simplification of the given expression.
    This function does the basic setup if needed and
    returns the combined sim of the given expression.
    """
    self.stats.simTimer.start()
    if demand is not None and simName not in self.activeAnSimNeeds:
      self.stats.simTimer.stop()
      return SimFailed  # i.e. process_the_original_insn

    if LS: LOG.debug("SimplifyingExpr:(Node %s) %s, SimName: %s. (For: %s)",
                     node.id, e, simName, demand if demand else self.activeAnName)

    # record the dependence
    self.addExprSimNeed(node.id, simName, e, demand,
                        None if demand else self.activeAnName)
    anNames = self.fetchAndSetupSimSrcs(node, simName, e, demand)

    res = self.collectAndMergeResults(anNames, simName, node, e)

    if LS: LOG.debug("SimOfExpr (merged): %s is %s.", e, res)
    self.stats.simTimer.stop()
    return res


  def collectAndMergeResults(self,
      anNames: Set[AnNameT],
      simName: SimNameT,
      node: graph.CfgNode,
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
    for anName in anNames:    # loop to select the first working sim
      simRecord = self.anRevNodeDep[(anName, nid)][tup2]
      if simRecord is not None:
        values = simRecord.getSim()
        break  # break at the first useful value
    if values in (SimPending, SimFailed):
      return values  # failed/pending values can never be refined

    # Step 2: Refine the simplification
    assert values not in (SimPending, SimFailed), f"{values}"
    for anName in anNames:
      values = self.calculateSimValue(anName, simName, node, e, values)
      assert values != SimFailed, f"{anName}, {simName}, {node}, {e}, {values}"
      if values == SimPending:
        break  # no use to continue
    return values  # a refined result


  def Calc_Deref__to__Vars(self,
      node: graph.CfgNode,
      e: expr.VarE,
      demand: Opt[ddm.AtomicDemand] = None, #DDM
  ) -> Opt[Set[VarNameT]]:
    """
    This function is basically a call to self.getSimplification()
    with some checks.
    """
    res = cast(Opt[Set], self.getSim(node, Deref__to__Vars__Name, e, demand))

    if res is SimFailed:
      return SimFailed  # i.e. process_the_original_insn

    if self.lerner and len(res) > 1:
      res = SimFailed
    elif len(res) > 1 and NULL_OBJ_NAME in res:
        res.val.remove(NULL_OBJ_NAME)
    elif len(res) == 1 and NULL_OBJ_NAME in res:
      if LS: LOG.error("NullDerefEncountered (bad user program): %s, %s",
                       e.name, node)
      res = SimFailed  # i.e. process_the_original_insn

    if LS: LOG.debug("SimOfExpr (joined): %s is %s.", e.name, res)
    return res


  # BOUND END  : Simplification_Methods

  def printResult(self):
    """prints the result of all analyses."""
    print("Function:", self.func.name, "TUnit:", self.func.tUnit.name)
    for anName, res in self.anWorkDict.items():
      print(anName, ":", self.anSimSuccessCount[anName])

      topTop = "IN: Top, OUT: Top, TRUE: Top, FALSE: Top (Unreachable/Nop)"
      for node in self.funcCfg.revPostOrder:
        nid = node.id
        nDfv = res.nidNdfvMap.get(nid, topTop)
        print(f">> {nid}. ({node.insn}): {nDfv}")
      print("Worklist:", self.anWorkDict[anName].wl.getAllNodesStr())

    print(self.stats)
    if self.useDdm: print(self.ddmObj.timer)
    print(self.tUnit.stats)
    print()  # an extra line

    if LS: LOG.debug("AnWorklistDots:\n%s", self.getAnIterationDotString())
    # print("DiagnosticInfo:", file=sys.stderr)


  def setBoundaryResult(self,
      boundaryInfo: Dict[AnNameT, NodeDfvL]
  ) -> bool:
    """
    Update the results at the boundary.
    After this, one can restart the Host.
    Return true if there is a need to restart Host.
    """
    restart = False

    for anName in boundaryInfo.keys():
      anDirn = clients.getDirection(anName)
      dirnObj = self.anWorkDict[anName]
      nDfv = boundaryInfo[anName]

      # FIXME: Assuming all analyses are forward or backward (not both)
      nodeId = 1 if anDirn == Forward else len(self.funcCfg.nodeMap)
      node = self.funcCfg.nodeMap[nodeId]
      updateDfv = NodeDfvL(nDfv.dfvIn, nDfv.dfvIn) \
                      if anDirn == Forward \
                      else NodeDfvL(nDfv.dfvOut, nDfv.dfvOut)
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
    It returns the IN  of start node, and OUT of end node for each analysis.
    Extract the relevant value as per the directionality of the analysis.
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


  def setCallSiteDfv(self,
      nodeId: NodeIdT,
      results: Dict[AnNameT, NodeDfvL]
  ) -> bool:
    """
    Update the results at the call site.
    After this, one can restart the Host.
    Return true if there is a need to restart Host.
    """
    restart = False

    node = self.funcCfg.nodeMap[nodeId]
    for anName in results.keys():
      dirn = self.anWorkDict[anName]
      nDfv = results[anName]
      inOutChange = dirn.update(node, nDfv)
      if inOutChange:
        if LS: LOG.debug("IPA_UpdatedWorklist: %s, %s", self.func.name, dirn.wl)
        self.addAnToWorklist(anName, ipa=True)
        restart = True  # Should re-run the Host

      # IMPORTANT: Not needed. No analysis dependence at call sites!
      #   self.addDepAnToWorklist(node, inOutChange)

    return restart


  def getCallSiteDfvs(self
  ) -> Opt[Dict[graph.CfgNode, Dict[AnNameT, NodeDfvL]]]:
    """
    Returns the NodeDfvL objects at the call site nodes.
    """
    callSiteNodes = self.funcCfg.getNodesWithNonPtrCallExpr()
    callSiteNodes = self.tUnit.filterAwayCalleesWithNoBody(callSiteNodes)
    if not callSiteNodes:
      return None

    callSiteDfvs = {}
    for node in callSiteNodes:
      nid = node.id
      analysisDfvs = {}
      for anName, res in self.anWorkDict.items():
        if nid not in res.nidNdfvMap:
          continue  # NODE IS UNREACHABLE
        nDfv = res.nidNdfvMap.get(nid)
        assert nDfv
        analysisDfvs[anName] = nDfv
      callSiteDfvs[node] = analysisDfvs

    return callSiteDfvs


  def getParticipatingAnalyses(self) -> Set[AnNameT]:
    return set(self.anParticipating.keys())


  def getAnIterationDotString(self) -> str:
    subGraphs = "\n".join(self.anWorkListDot)
    dotGraph = f"\ndigraph {{\n  randdir=TB;\n\n{subGraphs}\n}} // close digraph\n"
    # util.writeToFile("anWorklist.dot", dotGraph)
    return dotGraph


  def getAnalysisResults(self,
      anName: AnNameT,
  ) -> Opt[Dict[graph.CfgNodeId, NodeDfvL]]:
    """Returns the analysis results of the given analysis.

    Returns None if no information present.
    """
    if anName in self.anWorkDict:
      return self.anWorkDict[anName].nidNdfvMap
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

    # print(f"SetInstrSimCache ({self.activeAnName}",
    #       f"[{nid},{simName}][{insn},{e}])",
    #       f"::::: {newInsn}")  #delit


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


  def doesChangeMatchAnDirection(self, inOutChange: NewOldL) -> bool:
    assert self.activeAnObj
    dirnClass = self.activeAnObj.D
    iChanged = inOutChange.isNewIn
    oChanged = inOutChange.isNewOut

    if dirnClass is ForwardD and iChanged:
      return True
    if dirnClass is BackwardD and oChanged:
      return True
    if dirnClass is ForwardD and (iChanged or oChanged):
      return True
    return False


