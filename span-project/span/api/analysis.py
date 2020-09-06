#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The analysis interface."""

import logging

LOG = logging.getLogger("span")
from typing import List, Tuple, Set, Dict, Any, Type, Callable, cast
from typing import Optional as Opt
import io

from span.util.util import LS, AS
import span.ir.types as types
import span.ir.conv as conv
import span.ir.graph as graph
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
from span.ir.ir import \
  (getExprRValueNames, getExprLValueNames, getNamesEnv,
   filterNames, nameHasArray, getNamesPossiblyModifiedInCallExpr)

import span.api.sim as sim
from span.api.dfv import OLD_INOUT, NEW_IN, NodeDfvL, NewOldL
import span.api.dfv as dfv
from span.api.lattice import NoChange, DataLT, mergeAll

AnalysisNameT = str


################################################
# BOUND START: worklist_related
################################################

class FastNodeWorkList:

  __slots__ : List[str] = ["nodes", "postOrder", "frozen", "wl", "isNop",
               "valueFilter", "wlNodeSet", "frozenSet", "fullSequence"]

  def __init__(self,
      nodes: Dict[graph.CfgNodeId, graph.CfgNode],
      postOrder: bool = False,  # True = revPostOrder
      frozen: bool = False,  # True restricts addition of new nodes
  ):
    self.nodes = nodes
    self.postOrder = postOrder
    self.frozen = frozen

    self.wl: List[graph.CfgNodeId] = list(nodes.keys())
    self.wl.sort(key=lambda x: x if self.postOrder else -x)
    self.isNop = [frozen for i in range(len(nodes.keys()))]
    self.valueFilter = [None for i in range(len(nodes.keys()))]
    self.wlNodeSet = set(nodes.keys())
    self.frozenSet = set(nodes.keys())  # the set of nodes on which to work

    # seq of nodes visited from start to end of the analysis
    self.fullSequence: List[str] = []


  def clear(self):
    """Clear the worklist."""
    self.wl.clear()
    self.wlNodeSet.clear()
    self.frozenSet.clear()


  def pop(self) -> Tuple[Opt[graph.CfgNode], Opt[bool], Opt[Any]]:
    """Pops and returns next node id on top of queue, None otherwise."""
    if not self.wl: return None, None, None

    nid = self.wl.pop()
    self.fullSequence.append(f"{nid}{'.' if self.isNop[nid-1] else ''}")

    self.wlNodeSet.remove(nid)
    return self.nodes[nid], self.isNop[nid-1], self.valueFilter[nid-1]


  def add(self,
      node: graph.CfgNode,
  ) -> bool:
    """Add a node to the queue."""
    frozen, nid = self.frozen, node.id

    attemptAdd = (frozen and nid in self.frozenSet) or not frozen

    if attemptAdd and nid not in self.wlNodeSet:
      self.wl.append(nid)
      self.wl.sort(key=lambda x: x if self.postOrder else -x)
      self.wlNodeSet.add(nid)
      return True
    return False


  def initForDdm(self):
    """Used by #DDM"""
    """Used by #DDM"""
    self.frozen = True
    self.clear()
    for i in range(1, len(self.isNop)):
      self.isNop[i] = True


  def updateNodeMap(self,
      nodeMap: Opt[Dict[graph.CfgNode, Any]]  # node -> span.sys.ddm.NodeInfo
  ) -> bool:
    """Used by #DDM"""
    if not nodeMap: return False  # i.e. no change

    if LS: LOG.debug("UpdatedNodeMap(AddingMap): %s", nodeMap)

    changed, nopChanged, valueFilterChanged = False, False, False
    for node, nInfo in nodeMap.items():
      treatAsNop = nInfo.nop
      nid, index = node.id, node.id - 1
      if nid not in self.frozenSet:  # a fresh node
        if nid not in self.wlNodeSet:
          self.wl.append(nid)
          self.wlNodeSet.add(nid)
        self.frozenSet.add(nid)
        self.isNop[index] = treatAsNop and self.isNop[index]
        self.valueFilter[index] = nInfo.varNameSet
        changed = True
      else:  # a known node
        isNop = self.isNop[index]
        if not treatAsNop and isNop:
          self.isNop[index] = False
          nopChanged = True
        if self.valueFilter[index] != nInfo.varNameSet:
          self.valueFilter[index] = nInfo.varNameSet
          valueFilterChanged = True
        if nopChanged or valueFilterChanged:
          if nid not in self.wlNodeSet:
            self.wl.append(nid)
            self.wlNodeSet.add(nid)

    if changed: self.wl.sort(key=lambda x: x if self.postOrder else -x)
    return changed or nopChanged or valueFilterChanged


  def getWorkingNodesString(self, allNodes=False):
    nodeIds = list(self.frozenSet if allNodes else self.wl)
    nodeIds.sort(key=lambda x: x if self.postOrder else -x)
    listType = "All" if allNodes else "CurrentWL"

    prefix = ""
    with io.StringIO() as sio:
      sio.write("#DDM " if self.frozen else "")
      sio.write(f"FastNodeWorkList({listType})[")
      for nid in nodeIds:
        sio.write(f"{prefix}{nid}")
        sio.write("." if self.isNop[nid - 1] else "")
        if not prefix: prefix = ", "
      sio.write("] ('.' is Nop)")
      prefix = sio.getvalue()  # reusing prefix
    return prefix


  def getAllNodesStr(self):
    return self.getWorkingNodesString(allNodes=True)


  def __str__(self):
    return self.getWorkingNodesString()


  def __repr__(self):
    return self.__str__()


class NodeWorkList(object):
  """Cfg node worklist.

  It remembers the initial order in which node ids are given,
  and maintains the same order when selective nodes are added later.
  """


  def __init__(self,
      nodes: Opt[List[graph.CfgNode]] = None,
      frozen: bool = False,  # True restricts addition of new nodes
  ) -> None:
    # list to remember the order of each node initially given for the first time
    self.sequence: List[graph.CfgNode] = []
    self.workque: List[bool] = []
    self.treatAsNop: List[bool] = []  # DDM used by demand driven technique
    # remembers the nodes already given
    self.nodeMem: Set[graph.CfgNodeId] = set()
    _ = [self.add(node, force=True) for node in nodes] if nodes else None
    # seq of nodes visited from start to end of the analysis
    self.fullSequence: List[graph.CfgNode] = []
    # seq of nodes visited till the analysis reaches intermediate FP
    # after each intermediate FP this is supposed to be cleared explicitly
    self.tmpSequence: List[graph.CfgNode] = []
    self.frozen = frozen


  def __contains__(self, node: graph.CfgNode):
    nid = node.id
    for index, n in enumerate(self.sequence):
      if nid == n.id: return self.workque[index]
    return False


  def clear(self):
    """Clear the worklist."""
    for index in range(len(self.workque)):
      self.workque[index] = False


  def isNodePresent(self, nid: graph.CfgNodeId):
    return nid in self.nodeMem


  def add(self,
      node: graph.CfgNode,
      treatAsNop: bool = False,
      force: bool = False,  # overrides the frozen property
  ) -> bool:
    """Add a node to the queue."""
    assert len(self.nodeMem) == len(self.sequence) or self.frozen
    assert len(self.sequence) == len(self.workque)
    nid = node.id
    if nid not in self.nodeMem:  # a new node -- add it
      if force or not self.frozen:  # checks if WL is frozen?
        self.nodeMem.add(nid)
        self.sequence.append(node)
        self.workque.append(True)
        self.treatAsNop.append(treatAsNop)
        return True
      else:
        return False  # not added since work list is frozen

    # an old node -- re-add it
    index, added = 0, False
    for index, node in enumerate(self.sequence):
      if node.id == nid: break
    if not self.workque[index]:
      self.workque[index] = True
      added = True

    return added  # possibly added


  def pop(self) -> Tuple[Opt[graph.CfgNode], Opt[bool]]:
    """Pops and returns next node id on top of queue, None otherwise."""
    for index, active in enumerate(self.workque):
      if active: break
    else:
      return None, None

    self.workque[index] = False
    node = self.sequence[index]
    self.fullSequence.append(node)
    self.tmpSequence.append(node)
    return node, self.treatAsNop[index]


  def peek(self) -> Opt[graph.CfgNode]:
    """Returns next node id on top of queue, None otherwise."""
    for index, active in enumerate(self.workque):
      if active:
        return self.sequence[index]
    return None


  def initForDdm(self):
    """Used by #DDM"""
    self.frozen = True
    self.clear()
    self.nodeMem.clear()
    for i in range(1, len(self.treatAsNop)):
      self.treatAsNop[i] = True


  def updateNodeMap(self, nodeMap: Opt[Dict[graph.CfgNode, bool]]) -> bool:
    """Used by #DDM"""
    if not nodeMap: return False  # i.e. no change

    if LS: LOG.debug("UpdatedNodeMap(AddingMap): %s", nodeMap)

    changed = False
    for node, treatAsNop in nodeMap.items():
      nid = node.id
      if nid not in self.nodeMem:  # a fresh node
        self.nodeMem.add(nid)
        for index, node in enumerate(self.sequence):
          if node.id == nid: break
        if not self.workque[index]:  # 'index' use is okay
          self.workque[index], self.treatAsNop[index] = True, treatAsNop
          changed = True
      else:  # a known node
        for index, node in enumerate(self.sequence):
          if node.id == nid: break
        treatedAsNop = self.treatAsNop[index]
        if not treatAsNop and treatedAsNop:
          self.workque[index], self.treatAsNop[index] = True, False
          changed = True

    return changed


  def shouldTreatAsNop(self, node: graph.CfgNode):
    """Should the current node be treated as containing NopI()? Used by #DDM"""
    nid = node.id
    for index, n in enumerate(self.sequence):
      if nid == n.id: return self.treatAsNop[index]
    return False


  def clearTmpSequence(self):
    self.tmpSequence.clear()


  def tmpSequenceStr(self):
    prefix = ""
    with io.StringIO() as sio:
      for node in self.tmpSequence:
        sio.write(f"{prefix}{node.id}")
        if not prefix: prefix = ","
      return sio.getvalue()


  def getAllNodesStr(self):
    prefix = ""
    with io.StringIO() as sio:
      sio.write("#DDM " if self.frozen else "")
      sio.write("NodeWorkList[")
      for index, node in enumerate(self.sequence):
        if node.id in self.nodeMem:
          sio.write(f"{prefix}{node.id}")
          sio.write("." if self.treatAsNop[index] else "")
          if not prefix: prefix = ", "
      sio.write("]")
      prefix = sio.getvalue()  # reusing prefix
    return prefix


  def __str__(self):
    prefix = ""
    with io.StringIO() as sio:
      sio.write("#DDM " if self.frozen else "")
      sio.write("NodeWorkList[")
      for index, active in enumerate(self.workque):
        if active:
          sio.write(f"{prefix}{self.sequence[index].id}")
          sio.write("." if self.treatAsNop[index] else "")
          if not prefix: prefix = ", "
      sio.write("]")
      prefix = sio.getvalue()  # reusing prefix
    return prefix


  def __repr__(self):
    return self.__str__()


################################################
# BOUND END  : worklist_related
################################################

################################################
# BOUND START: direction_related
################################################

class DirectionDT:
  """For the direction of data flow of the analysis."""


  def __init__(self,
      cfg: graph.Cfg,
      top: DataLT
  ) -> None:
    if type(self).__name__ == "DirectionT":
      super().__init__()
    self.cfg = cfg
    self.nidNdfvMap: Dict[graph.CfgNodeId, NodeDfvL] = dict()
    self.topNdfv: NodeDfvL = NodeDfvL(top, top)
    for nid in self.cfg.nodeMap.keys():
      self.nidNdfvMap[nid] = self.topNdfv
    # set this to true once boundary values are initialized
    self.wl: FastNodeWorkList = self.generateInitialWorklist()
    self.boundaryInfoInitialized = False


  def generateInitialWorklist(self) -> FastNodeWorkList:
    """Defaults to reverse post order."""
    wl = FastNodeWorkList(self.cfg.nodeMap, postOrder=False)
    return wl


  def update(self,
      node: graph.CfgNode,
      nodeDfv: NodeDfvL,
  ) -> NewOldL:
    """Update, the node dfv in wl if changed.

    Subclasses should add pred/succ to the worklist,
    if dfv is changed.
    """
    nid = node.id
    oldNdfv = self.nidNdfvMap.get(nid, self.topNdfv)
    oldIn, oldOut = oldNdfv.dfvIn, oldNdfv.dfvOut
    oldOutTrue, oldOutFalse = oldNdfv.dfvOutTrue, oldNdfv.dfvOutFalse

    if AS:
      if nodeDfv < oldNdfv:
        pass  # i.e. its okay
      else:
        LOG.error("NonMonotonicDFV: Analysis: %s", oldIn.__class__)
        if not nodeDfv.dfvIn < oldNdfv.dfvIn:
          LOG.error("NonMonotonicDFV (IN):\n NodeId: %s, Instr: %s, Info: %s, Old: %s,\n New: %s.",
                    nid, node.insn, node.insn.info, oldNdfv.dfvIn, nodeDfv.dfvIn)
        if not nodeDfv.dfvOut < oldNdfv.dfvOut:
          LOG.error("NonMonotonicDFV (OUT):\n NodeId: %s, Info: %s, Instr: %s, Old: %s,\n New: %s.",
                    nid, node.insn, node.insn.info, oldNdfv.dfvOut, nodeDfv.dfvOut)

    newIn, newOut = nodeDfv.dfvIn, nodeDfv.dfvOut
    newOutTrue, newOutFalse = nodeDfv.dfvOutTrue, nodeDfv.dfvOutFalse

    isNewIn = newIn != oldIn
    isNewOut = newOut != oldOut \
               or newOutFalse != oldOutFalse \
               or newOutTrue != oldOutTrue
    self.nidNdfvMap[nid] = nodeDfv
    return NewOldL.getNewOldObj(isNewIn, isNewOut)


  def add(self, node: graph.CfgNode):
    """Add node_id to the worklist."""
    assert self.wl is not None
    return self.wl.add(node)


  def calcInOut(self,
      node: graph.CfgNode,
      fcfg: graph.FeasibleEdges
  ) -> Tuple[NodeDfvL, NewOldL]:
    """Merges dfv from feasible edges."""
    raise NotImplementedError()


  def getDfv(self,
      nodeId: graph.CfgNodeId
  ) -> NodeDfvL:
    return self.nidNdfvMap.get(nodeId, self.topNdfv)


  def __str__(self):
    return self.__repr__()


  def __repr__(self):
    return f"analysis.{self.__class__.__name__}"


class ForwardDT(DirectionDT):
  """For all forward flow problems."""


  def __init__(self,
      cfg: graph.Cfg,
      top: DataLT,
      callCfg: Opt[graph.Cfg] = None,  # call parameter assignments
  ) -> None:
    if type(self).__name__ == "ForwardDT":
      raise NotImplementedError()  # can't create direct object
    super().__init__(cfg, top)
    self.wl = self.generateInitialWorklist()  # important


  def generateInitialWorklist(self) -> FastNodeWorkList:
    """Defaults to reverse post order."""
    wl = FastNodeWorkList(self.cfg.nodeMap, postOrder=False)
    if LS: LOG.debug("Forward_Worklist_Init: %s", wl)
    return wl


  def update(self,
      node: graph.CfgNode,
      nodeDfv: NodeDfvL,
  ) -> NewOldL:
    """Update, for forward direction.

    If OUT is changed add the pred/succ to the worklist.
    """
    inOutChange = super().update(node, nodeDfv)

    #assert not inOutChange.isNewIn, msg.INVARIANT_VIOLATED  #FIXME: why did i put this assertion?

    if inOutChange.isNewOut:
      """Add the successors only."""
      for succEdge in node.succEdges:
        if LS: LOG.debug("AddingNodeToWl (succ): Node %s", succEdge.dest.id)
        self.wl.add(succEdge.dest)

    return inOutChange


  def calcInOut(self,
      node: graph.CfgNode,
      fcfg: graph.FeasibleEdges
  ) -> Tuple[NodeDfvL, NewOldL]:
    """Forward: Merges OUT of feasible predecessors.

    It also updates the self.nidNdfvMap to make the change visible (if any).
    """
    nid = node.id
    ndfv = self.nidNdfvMap.get(nid, self.topNdfv)
    predEdges = node.predEdges
    # for start node, nothing changes
    if not predEdges: return ndfv, OLD_INOUT

    oldIn = ndfv.dfvIn

    # newIn = oldIn  # enforce_monotonicity
    newIn = None  # don't enforce_monotonicity
    changed = NoChange
    for predEdge in predEdges:
      f = fcfg.isFeasibleEdge(predEdge)
      if LS: LOG.debug("Edge: %s, Feasible: %s", predEdge, f)
      if f:
        predNodeDfv = self.nidNdfvMap.get(predEdge.src.id, self.topNdfv)
        if predEdge.label == conv.TrueEdge and predNodeDfv.dfvOutTrue is not None:
          predOut = predNodeDfv.dfvOutTrue
        elif predEdge.label == conv.FalseEdge and predNodeDfv.dfvOutFalse is not None:
          predOut = predNodeDfv.dfvOutFalse
        else:
          if predNodeDfv.dfvOut is None:
            if LS: LOG.error("dfvOut is None: %s", predNodeDfv)
          predOut = predNodeDfv.dfvOut  # must not be None, if here

        if newIn is None:
          newIn = predOut
        else:
          newIn, ch = newIn.meet(predOut)
          changed, _ = changed.meet(ch)  # old code TODO remove it

    if newIn == ndfv.dfvIn: return ndfv, OLD_INOUT

    # Update in map for use in evaluation functions.
    assert newIn is not None
    newNodeDfv = NodeDfvL(newIn, ndfv.dfvOut)
    self.nidNdfvMap[nid] = newNodeDfv  # updates the node dfv map
    return newNodeDfv, NEW_IN


class ForwardD(ForwardDT):
  """Create instance of this class for forward flow problems."""


  def __init__(self,
      cfg: graph.Cfg,
      top: DataLT
  ) -> None:
    super().__init__(cfg, top)


class BackwardDT(DirectionDT):
  """For all backward flow problems."""


  def __init__(self,
      cfg: graph.Cfg,
      top: DataLT
  ) -> None:
    if type(self).__name__ == "BackwardDT":
      raise NotImplementedError()  # can't create direct object
    super().__init__(cfg, top)
    self.wl = self.generateInitialWorklist()  # important


  def generateInitialWorklist(self) -> FastNodeWorkList:
    """Defaults to reverse post order."""
    wl = FastNodeWorkList(self.cfg.nodeMap, postOrder=True)
    if LS: LOG.debug("Backward_Worklist_Init: %s", wl)
    return wl


  def update(self,
      node: graph.CfgNode,
      nodeDfv: NodeDfvL,
  ) -> NewOldL:
    """Update, for backward direction.

    If IN is changed add the pred/succ to the worklist.
    """
    # print("OldOut:", nodeDfv.dfvOut)
    inOutChange = super().update(node, nodeDfv)

    # if not inOutChange.isNewOut:
    #   print("NewOut:", self.nidNdfvMap[node.id].dfvOut)
    # assert not inOutChange.isNewOut, msg.INVARIANT_IS_VIOLATED

    if inOutChange.isNewIn:
      """Add the predecessors."""
      for predEdge in node.predEdges:
        if LS: LOG.debug("AddingNodeToWl (pred): Node %s", predEdge.src.id)
        self.wl.add(predEdge.src)

    return inOutChange


  def calcInOut(self,
      node: graph.CfgNode,
      fcfg: graph.FeasibleEdges
  ) -> Tuple[NodeDfvL, NewOldL]:
    """Backward: Merges IN of feasible successors.

    It also updates the self.nidNdfvMap to make the change visible (if any).
    """
    nid = node.id
    ndfv = self.nidNdfvMap.get(nid, self.topNdfv)
    succEdges = node.succEdges
    # for start node, nothing changes
    if not succEdges: return ndfv, OLD_INOUT

    oldOut = ndfv.dfvOut

    newOut = oldOut  # enforce_monotonicity
    changed = NoChange
    for succEdge in succEdges:
      f = fcfg.isFeasibleEdge(succEdge)  # TODO: succEdge in fcfg.fEdges (for speed)
      if LS: LOG.debug("Edge: %s, Feasible: %s", succEdge, f)
      if f:
        succIn = self.nidNdfvMap.get(succEdge.dest.id, self.topNdfv).dfvIn
        if not succIn.top:
          newOut, ch = newOut.meet(succIn)  # enforce_monotonicity
          changed, _ = changed.meet(ch)

    if not changed: return ndfv, OLD_INOUT

    # Update in map for use in evaluation functions.
    newNodeDfv = NodeDfvL(ndfv.dfvIn, newOut)
    inOutChange = self.update(node, newNodeDfv)
    # self.nidNdfvMap[nid] = newNodeDfv  # updates the node dfv map
    return newNodeDfv, inOutChange


class BackwardD(BackwardDT):
  """Create instance of this class for backward flow problems."""


  def __init__(self,
      cfg: graph.Cfg,
      top: DataLT
  ) -> None:
    super().__init__(cfg, top)


class ForwBackDT(DirectionDT):
  """TODO: For bi-directional problems."""


  def __init__(self):
    pass


################################################
# BOUND END  : direction_related
################################################

################################################
# BOUND START: AnalysisAT_The_Base_Class.
################################################

class AnalysisAT(sim.SimAT):
  # For bi-directional analyses, subclass AnalysisAT directly.

  __slots__ : List[str] = ["func", "overallTop", "overallBot"]

  # concrete lattice class of the analysis
  L: Opt[Type[dfv.DataLT]] = None
  # concrete direction class of the analysis
  D: Opt[Type[DirectionDT]] = None
  # Simplification needed: methods simplifying (blocking) exprs of this analysis
  # list required sim function objects here (functions with '__to__' in their name)
  simNeeded: List[Callable] = []


  def __init__(self,
      func: constructs.Func  # function being analyzed
  ) -> None:
    if type(self).__name__ == "AnalysisT":
      super().__init__()  # no instance of this class
    assert self.L is not None and self.D is not None
    self.func = func
    self.overallTop = self.L(func, top=True)  # L is callable. pylint: disable=E
    self.overallBot = self.L(func, bot=True)  # L is callable. pylint: disable=E


  def Default_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """The default behaviour for unimplemented instructions.
    Analysis should override this method if unimplemented
    instructions have to handled in a way other than
    like a NOP instruction.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def getBoundaryInfo(self,
      nodeDfv: Opt[NodeDfvL] = None,
      ipa: bool = False,
  ) -> NodeDfvL:
    """Must generate a valid boundary info."""
    if ipa and not nodeDfv:
      raise ValueError(f"{ipa}, {nodeDfv}")

    inBi, outBi = self.overallBot, self.overallBot
    if ipa: raise NotImplementedError()  # for IPA override this function
    if nodeDfv: inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
    return NodeDfvL(inBi, outBi)  # good to create a copy

  # BOUND START: special_instructions_seven

  def Nop_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: NopI()."""
    # Default implementation for forward analyses.
    assert self.D and self.D.__name__.startswith("Forw"), f"{self.D}"
    dfvIn = nodeDfv.dfvIn
    if dfvIn is nodeDfv.dfvOut:
      return nodeDfv
    else:
      return NodeDfvL(dfvIn, dfvIn)


  def Barrier_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Data Flow information is blocked from travelling
    from IN-to-OUT and OUT-to-IN.

    This implementation works for *any* direction analysis.
    """
    return nodeDfv  # no information travel from IN to OUT or OUT to IN


  def Use_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UseI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: UseI(x).
    Value of x is read from memory."""
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def ExRead_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ExReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: ExReadI(x).
    x and only x is read, others are forcibly
    marked as not read (in backward direction)."""
    return self.Barrier_Instr(nodeId, insn, nodeDfv)


  def CondRead_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: CondReadI(x, {y, z}).
    y and z are read if x is read."""
    return self.Barrier_Instr(nodeId, insn, nodeDfv)


  def UnDefVal_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: input(x). (user supplies value of x)
    Thus value of x is undefined."""
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Filter_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: FilterI({x,y,z}).
    x,y,z are known to be dead after this program point."""
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : special_instructions_seven

  # BOUND START: regular_instructions
  # BOUND START: regular_insn__when_lhs_is_var

  def Num_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: lhs = rhs.
    Convention:
      Type of lhs and rhs is numeric.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: lhs = rhs.
    Convention:
      Type of lhs and rhs is a record.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: record: lhs = rhs.
    Convention:
      Type of lhs and rhs is a record.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b.
    Convention:
      a and b are variables.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = v.
    Convention:
      u and v are variables.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_FuncName_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = f.
    Convention:
      u is a variable.
      f is a function name.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): a = b.
    Convention:
      a and b are variables.
    """
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b.
    Convention:
      a is variable.
      b is a literal.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: a = b.
    Convention:
      a is a variable.
      b is a literal.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_SizeOf_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = sizeof(b).
    Convention:
      a and b are both variables.
      b is of type: types.VarArray only.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_UnaryArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = <unary arith/bit/logical op> b.
    Convention:
      a and b are both variables.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_BinArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b <binary arith/rel/bit/shift> c.
    Convention:
      a is a variable.
      b, c: at least one of them is a variable.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_BinArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b <binary +/-> c.
    Convention:
      a is a variable.
      b, c: at least one of them is a variable.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Deref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = *u.
    Convention:
      a and u are variables.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Deref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = *v.
    Convention:
      u and v are variables.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Deref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record: u = *v.
    Convention:
      v and u are variables.
    """
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Array_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b[i].
    Convention:
      a and b are variables.
      i is a variable or a literal.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Array_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = a[i].
    Convention:
      u and a are variables.
      i is a variable or a literal.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Array_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): r = a[i].
    Convention:
      u and a are variables.
      i is a variable or a literal.
    """
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Member_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b.x or a = b->x.
    Convention:
      a and b are variables.
      x is a member/field of a record.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Member_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: a = b.x or a = b->x.
    Convention:
      a and b are variables.
      x is a member/field of a record.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Member_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): a = b.x or a = b->x.
    Convention:
      a and b are variables.
      x is a member/field of a record.
    """
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Select_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: b = c ? d : e.
    Convention:
      b, c, are always variables.
      d, e are variables or literals.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Select_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: p = c ? d : e.
    Convention:
      b, c, are always variables.
      d, e are variables or literals.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Select_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record: b = c ? d : e.
    Convention:
      b, c, d, e are always variables.
    """
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: b = func(args...).
    Convention:
      b is a variable.
      func is a function pointer or a function name.
      args are either a variable, a literal or addrof expression.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: p = func()."""
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record: r = func()."""
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_CastVar_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = (int) b.
    Convention:
      a and b are variables.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_CastVar_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: a = (int*) b.
    Convention:
      a and b are variables.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_CastArr_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: b = (int*)a[i].
    Convention:
      b and a are variables.
      i is either a variable or a literal.
    Note:
      This instruction was necessary for expressions like,
        x = &a[0][1][2]; // where (say) x is int* and a is a[4][4][4].
      It is broken down as:
        t1 = (ptr to array of [4]) a[0];
        t2 = (ptr to int) t1[1];
        t3 = &t2[2];
        x = t3;
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  # Ptr_Assign_Var_CastMember_Instr() is not part of IR.
  # its broken into: t1 = x.y; b = (int*) t1;

  def Ptr_Assign_Var_AddrOfVar_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &x.
    Convention:
      u and x are variables.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_AddrOfArray_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &a[i]
    Convention:
      u and a are variables.
      i is a variable of a literal.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_AddrOfMember_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &r.x or u = &r->x.
    Convention:
      u and r are variables.
      x is a member/field of a record.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_AddrOfDeref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &*x
    Convention:
      u is a pointer variable
      x is a pointer variable
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_AddrOfFunc_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &f.
    Convention:
      u is a variable.
      f is function name.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : regular_insn__when_lhs_is_var
  # BOUND START: regular_insn__when_lhs_is_deref

  def Num_Assign_Deref_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: *u = b.
    Convention:
      u and b are variables.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Deref_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: *u = b.
    Convention:
      u is a variable.
      b is a literal.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Deref_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: *u = v.
    Convention:
      u and v are variables.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Deref_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: *u = b.
    Convention:
      u is a variable.
      b is a literal.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Deref_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record: *u = v.
    Convention:
      u and v are variables.
    """
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : regular_insn__when_lhs_is_deref
  # BOUND START: regular_insn__when_lhs_is_array

  def Num_Assign_Array_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a[i] = b.
    Convention:
      a and b are variables.
      i is either a variable or a literal.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Array_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a[i] = b.
    Convention:
      a is a variable.
      i is either a variable or a literal.
      b is a literal.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Array_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: a[i] = b.
    Convention:
      a and b are variables.
      i is a variable or a literal.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Array_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: a[i] = b.
    Convention:
      a is a variable.
      i is a variable or a literal.
      b is a literal.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Array_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): a[i] = b.
    Convention:
      a and b are variables.
      i is a variable or a literal.
    """
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : regular_insn__when_lhs_is_array
  # BOUND START: regular_insn__when_lhs_is_member_expr

  def Num_Assign_Member_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: r.x = b  or r->x = b.
    Convention:
      r is a variable.
      b is a variable.
      x is a member/field of a record.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Member_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: r.x = b or r->x = b.
    Convention:
      r is a variable.
      b is a literal.
      x is a member/field of a record.
    """
    return self.Num_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Member_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: r.x = b  or r->x = b.
    Convention:
      r is a variable.
      b is a variable.
      x is a member/field of a record.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Member_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: r.x = b or r->x = b.
    Convention:
      r is a variable.
      b is a literal.
      x is a member/field of a record.
    """
    return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Member_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): r.x = b or r->x = b.
    Convention:
      r and b are variables.
      x is a member/field of a record.
    """
    return self.Record_Assign_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : regular_insn__when_lhs_is_member_expr
  # BOUND START: regular_insn__other

  def Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: void: func(args...) (just a call statement).
    Convention:
      args are either a variable, a literal or addrof expression.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Return_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: return b.
    Convention:
      b is a variable.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Return_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: return b.
    Convention:
      b is a literal.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Return_Void_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: return;
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Conditional_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: if b.
    Convention:
      b is a variable.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)

  # BOUND END  : regular_insn__other
  # BOUND END  : regular_instructions

################################################
# BOUND END  : AnalysisAT_The_Base_Class.
################################################


################################################
# BOUND START: Value_analysis
################################################

class ValueAnalysisAT(AnalysisAT):
  """A specialized value analysis with code common
  to most value analyses."""
  __slots__ : List[str] = ["componentTop", "componentBot"]
  # redefine these variables as needed (see ConstA, IntervalA for examples)
  L: Type[dfv.OverallL] = dfv.OverallL  # the OverallL lattice used
  D: Type[DirectionDT]  = ForwardD  # its a forward flow analysis
  simNeeded: List[Callable] = [sim.SimAT.Num_Var__to__Num_Lit,
                               sim.SimAT.Deref__to__Vars,
                               sim.SimAT.Num_Bin__to__Num_Lit,
                               sim.SimAT.LhsVar__to__Nil,
                               sim.SimAT.Cond__to__UnCond,
                               #sim.SimAT.Node__to__Nil,
                               ]


  def __init__(self,
      func: constructs.Func,
      componentL: Type[dfv.ComponentL],
      overallL: Type[dfv.OverallL],
  ) -> None:
    super().__init__(func)
    self.componentTop: dfv.ComponentL = componentL(self.func, top=True)
    self.componentBot: dfv.ComponentL = componentL(self.func, bot=True)
    self.overallTop: dfv.OverallL = overallL(self.func, top=True)
    self.overallBot: dfv.OverallL = overallL(self.func, bot=True)


  def getBoundaryInfo(self,
      nodeDfv: Opt[NodeDfvL] = None,
      ipa: bool = False,
  ) -> NodeDfvL:
    if ipa and not nodeDfv:
      raise ValueError(f"{ipa}, {nodeDfv}")

    inBi, outBi = self.overallBot, self.overallBot
    if ipa:
      return dfv.getBoundaryInfoIpa(self.func, nodeDfv,
                                    self.componentBot, self.getAllVars)
    if nodeDfv:
      inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
    return NodeDfvL(inBi, outBi)  # good to create a copy


  def isAcceptedType(self, t: types.Type) -> bool:
    """Returns True if the type of the instruction is
    of interest to the analysis.
    By default it selects only Numeric types.
    """
    return t.isNumeric()


  def getAllVars(self) -> Set[types.VarNameT]:
    """Gets all the variables of the accepted type."""
    names = getNamesEnv(self.func)
    return filterNames(self.func, names, self.isAcceptedType)

  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def Filter_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return dfv.Filter_Vars(self.func, insn.varNames, nodeDfv)


  def UnDefVal_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if not self.isAcceptedType(insn.type):
      return self.Nop_Instr(nodeId, insn, nodeDfv)
    newOut = dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    if not dfvIn.getVal(insn.lhsName).bot:
      newOut = dfvIn.getCopy()
      newOut.setVal(insn.lhsName, self.componentBot)
    return NodeDfvL(dfvIn, newOut)


  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################

  def Num_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Ptr_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Record_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv)


  def Conditional_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    if not self.isAcceptedType(insn.arg.type):  # special case
      return NodeDfvL(dfvIn, dfvIn)
    outDfvFalse, outDfvTrue = self.calcFalseTrueDfv(insn.arg, dfvIn)
    return NodeDfvL(dfvIn, None, outDfvTrue, outDfvFalse)


  def Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    return self.genNodeDfvL(self.processCallE(insn.arg, dfvIn), nodeDfv)


  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """A common function to handle various assignment instructions.
    This is a common function to all the value analyses.
    """
    dfvIn = nodeDfv.dfvIn
    assert isinstance(dfvIn, dfv.OverallL), f"{type(dfvIn)}"
    if LS: LOG.debug("ProcessingAssignInstr: %s = %s, iType: %s",
                     lhs, rhs, lhs.type)

    lhsType = lhs.type
    dfvInGetVal = cast(Callable[[types.VarNameT], dfv.ComponentL], dfvIn.getVal)
    outDfvValues: Dict[types.VarNameT, dfv.ComponentL] = {}

    if isinstance(lhsType, types.RecordT):
      outDfvValues = self.processLhsRhsRecordType(lhs, rhs, dfvInGetVal)

    elif self.isAcceptedType(lhsType):
      lhsVarNames = getExprLValueNames(self.func, lhs)
      assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
      mustUpdate = len(lhsVarNames) == 1

      rhsDfv = self.getExprDfv(rhs, dfvIn)
      if LS: LOG.debug("RhsDfvOfExpr: '%s' is %s, lhsVarNames are %s",
                       rhs, rhsDfv, lhsVarNames)

      for name in lhsVarNames:
        # this loop enters only once if mustUpdate == True
        newVal = rhsDfv
        if not mustUpdate or nameHasArray(self.func, name):
          # do may updates
          oldVal = dfvInGetVal(name)
          newVal, _ = oldVal.meet(newVal)
        if dfvInGetVal(name) != newVal:
          outDfvValues[name] = newVal

    if isinstance(rhs, expr.CallE):
      outDfvValues.update(self.processCallE(rhs, dfvIn))
    nDfv = self.genNodeDfvL(outDfvValues, nodeDfv)
    return nDfv


  def genNodeDfvL(self,
      outDfvValues: Dict[types.VarNameT, dfv.ComponentL],
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """A convenience function to create and return the NodeDfvL."""
    dfvIn = newOut = nodeDfv.dfvIn
    if outDfvValues:
      newOut = cast(dfv.OverallL, dfvIn.getCopy())
      newOutSetVal = newOut.setVal
      for name, value in outDfvValues.items():
        newOutSetVal(name, value)
    return NodeDfvL(dfvIn, newOut)


  def processLhsRhsRecordType(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> Dict[types.VarNameT, dfv.ComponentL]:
    """Processes assignment instruction with RecordT"""
    instrType = lhs.type
    assert isinstance(instrType, types.RecordT), f"{lhs}, {rhs}: {instrType}"

    allMemberInfo = instrType.getNamesOfType(None)

    lhsVarNames = getExprLValueNames(self.func, lhs)
    assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
    strongUpdate: bool = len(lhsVarNames) == 1

    rhsVarNames = None
    if not isinstance(rhs, expr.CallE):  # IMPORTANT
      # call expression don't yield rhs names
      rhsVarNames = getExprRValueNames(self.func, rhs)
      assert len(rhsVarNames) >= 1, f"{lhs}: {rhsVarNames}"

    outDfvValues: Dict[types.VarNameT, dfv.ComponentL] = {}
    isAcceptedType = self.isAcceptedType
    for memberInfo in allMemberInfo:
      if isAcceptedType(memberInfo.type):
        memName = memberInfo.name
        for lhsName in lhsVarNames:
          if rhsVarNames is not None:  # None only if rhs is CallE
            rhsDfv = mergeAll(  # merge all rhs dfvs of the same member
              dfvInGetVal(f"{rhsName}.{memName}")
              for rhsName in rhsVarNames)
          else:
            rhsDfv = self.componentBot
          fullLhsVarName = f"{lhsName}.{memName}"
          oldLhsDfv = dfvInGetVal(fullLhsVarName)
          if not strongUpdate:
            rhsDfv, _ = oldLhsDfv.meet(rhsDfv)
          if oldLhsDfv != rhsDfv:
            outDfvValues[fullLhsVarName] = rhsDfv
    return outDfvValues


  def processCallE(self,
      e: expr.ExprET,
      dfvIn: DataLT,
  ) -> Dict[types.VarNameT, dfv.ComponentL]:
    assert isinstance(e, expr.CallE), f"{e}"
    assert isinstance(dfvIn, dfv.OverallL), f"{type(dfvIn)}"

    names = getNamesPossiblyModifiedInCallExpr(self.func, e)
    names = filterNames(self.func, names, self.isAcceptedType)

    bot = self.componentBot
    dfvInGetVal = dfvIn.getVal
    outDfvValues: Dict[types.VarNameT, dfv.ComponentL]\
      = {name: bot for name in names if dfvInGetVal(name) != bot}
    return outDfvValues


  def calcFalseTrueDfv(self,
      arg: expr.SimpleET,
      dfvIn: dfv.OverallL,
  ) -> Tuple[dfv.OverallL, dfv.OverallL]:  # dfvFalse, dfvTrue
    """Conditionally propagate data flow values.
    Default implementation returns the same dfvIn.
    """
    return dfvIn, dfvIn


  def getExprDfv(self,
      e: expr.ExprET,
      dfvIn: dfv.OverallL
  ) -> dfv.ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects that the rhs is a non-record type.
    (Record type expressions are handled separately.)
    """
    assert not isinstance(e.type, types.RecordT), f"{e}, {e.type}"
    dfvInGetVal = cast(Callable[[types.VarNameT], dfv.ComponentL], dfvIn.getVal)

    if isinstance(e, expr.LitE):
      return self.getExprDfvLitE(e, dfvInGetVal)

    elif isinstance(e, expr.VarE):  # handles PseudoVarE too
      return self.getExprDfvVarE(e, dfvInGetVal)

    elif isinstance(e, expr.DerefE):
      return self.getExprDfvDerefE(e, dfvInGetVal)

    elif isinstance(e, expr.CastE):
      return self.getExprDfvCastE(e, dfvInGetVal)

    elif isinstance(e, expr.SizeOfE):
      return self.getExprDfvSizeOfE(e, dfvInGetVal)

    elif isinstance(e, expr.UnaryE):
      return self.getExprDfvUnaryE(e, dfvInGetVal)

    elif isinstance(e, expr.BinaryE):
      return self.getExprDfvBinaryE(e, dfvIn)

    elif isinstance(e, expr.SelectE):
      return self.getExprDfvSelectE(e, dfvIn)

    elif isinstance(e, expr.ArrayE):
      return self.getExprDfvArrayE(e, dfvInGetVal)

    elif isinstance(e, expr.MemberE):
      return self.getExprDfvMemberE(e, dfvInGetVal)

    elif isinstance(e, expr.CallE):
      return self.getExprDfvCallE(e, dfvInGetVal)

    raise ValueError(f"{e}, {self.__class__}")


  def getExprDfvLitE(self,
      e: expr.LitE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    raise NotImplementedError()


  def getExprDfvVarE(self,
      e: expr.VarE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    return dfvInGetVal(e.name)


  def getExprDfvDerefE(self,
      e: expr.DerefE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    varNames = getExprRValueNames(self.func, e)
    assert varNames, f"{e}, {varNames}"
    return mergeAll(map(dfvInGetVal, varNames))


  def getExprDfvCastE(self,
      e: expr.CastE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation"""
    assert isinstance(e.arg, expr.VarE), f"{e}"
    if self.isAcceptedType(e.arg.type):
      return dfvInGetVal(e.arg.name)
    else:
      return self.componentBot


  def getExprDfvSizeOfE(self,
      e: expr.SizeOfE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    return self.componentBot


  def getExprDfvUnaryE(self,
      e: expr.UnaryE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    raise NotImplementedError()


  def getExprDfvBinaryE(self,
      e: expr.BinaryE,
      dfvIn: dfv.OverallL,
  ) -> dfv.ComponentL:
    raise NotImplementedError()


  def getExprDfvSelectE(self,
      e: expr.SelectE,
      dfvIn: dfv.OverallL,
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    val1 = self.getExprDfv(e.arg1, dfvIn)
    val2 = self.getExprDfv(e.arg2, dfvIn)
    value, _ = val1.meet(val2)
    return value


  def getExprDfvArrayE(self,
      e: expr.ArrayE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    varNames = getExprRValueNames(self.func, e)
    assert varNames, f"{e}, {varNames}"
    return mergeAll(map(dfvInGetVal, varNames))


  def getExprDfvMemberE(self,
      e: expr.MemberE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation"""
    varNames = getExprRValueNames(self.func, e)
    assert varNames, f"{e}, {varNames}"
    return mergeAll(map(dfvInGetVal, varNames))


  def getExprDfvCallE(self,
      e: expr.CallE,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation"""
    return self.componentBot


  def filterValues(self,
      e: expr.ExprET,
      values: Set[types.T],
      dfvIn: dfv.OverallL,
      valueType: sim.ValueTypeT = sim.NumValue,
  ) -> Set[types.T]:
    """Depends on `self.filterTest`."""
    if not values:
      return values  # returns an empty list
    exprVal = self.getExprDfv(e, dfvIn)
    if exprVal.bot:
      return values
    elif exprVal.top:
      return sim.SimPending
    else:
      assert exprVal.val is not None, f"{e}, {exprVal}, {dfvIn}"
      return set(filter(self.filterTest(exprVal, valueType), values))


  def filterTest(self,
      exprVal: dfv.ComponentL,
      valueType: sim.ValueTypeT = sim.NumValue,
  ) -> Callable[[types.T], bool]:
    return lambda x: True


  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : Value_analysis
################################################

