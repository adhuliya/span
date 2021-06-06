#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The analysis interface."""

import logging
LOG = logging.getLogger("span")
LDB, LWR, LER = LOG.debug, LOG.warning, LOG.error

from span.ir.tunit import TranslationUnit
from span.util import ff

from typing import List, Tuple, Set, Dict, Any, Type, Callable, cast
from typing import Optional as Opt
import io

import span.util.util as util
from span.util.util import LS, AS
import span.ir.types as types
from span.ir.types import (
  VarNameT, RecordT, NodeIdT, DirectionT,
  NumericT, T,
)
from span.ir.conv import (
  TrueEdge, FalseEdge, Forward,
  Backward, isStringLitName,
)

import span.ir.cfg as cfg
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.conv as conv
from span.ir.conv import (
  nameHasPpmsVar,
)

from span.ir.ir import \
  (getExprRValueNames, getNamesLValuesOfExpr, getNamesEnv,
   filterNames, nameHasArray, getNamesPossiblyModifiedInCallExpr,
   isDummyGlobalFunc)

from span.api.dfv import (
  OLD_IN_OUT, NEW_IN_ONLY, NodeDfvL, ChangePairL,
)
import span.api.dfv as dfv
from span.api.lattice import ChangedT, Changed, DataLT, mergeAll

AnNameT = AnalysisNameT = str

SIM_NAME_COMMON_SUBSTR = "__to__"
"""Common substring in all the simplification function names.
This string should not be present in any other function name,
specially in the `AnalysisAT` class and its subclasses.
"""

################################################
# BOUND START: sim_related 1/3
################################################

# simplification function names (that contain SIM_NAME_COMMON_SUBSTR in their name)
SimNameT = str
SimT = Opt[Set]
SimFailed: SimT = None  # None represents a simplification failure
SimPending: SimT = set()  # an empty set represents sim is pending

ValueTypeT = str
NumValue: ValueTypeT = "Num"
BoolValue: ValueTypeT = "Bool"
NameValue: ValueTypeT = "VarName"

################################################
# BOUND END  : sim_related 1/3
################################################



################################################
# BOUND START: worklist_related
################################################

class FastNodeWorkList:

  __slots__ : List[str] = ["nodes", "postOrder", "frozen", "wl", "isNop",
               "valueFilter", "wlNodeSet", "frozenSet", "fullSequence"]

  def __init__(self,
      nodes: Dict[cfg.CfgNodeId, cfg.CfgNode],
      postOrder: bool = False,  # True = revPostOrder
      frozen: bool = False,  # True restricts addition of new nodes
  ):
    self.nodes = nodes
    self.postOrder = postOrder
    self.frozen = frozen

    self.wl: List[cfg.CfgNodeId] = list(nodes.keys())
    self.wl.sort(key=lambda x: x if self.postOrder else -x)
    self.isNop = [frozen for i in range(len(nodes.keys()))]
    self.valueFilter = [None for i in range(len(nodes.keys()))]
    self.wlNodeSet = set(nodes.keys())
    self.frozenSet = set(nodes.keys())  # the set of nodes on which to work

    # seq of nodes visited from start to end of the analysis
    self.fullSequence: List[int] = []


  def clear(self):
    """Clear the worklist."""
    self.wl.clear()
    self.wlNodeSet.clear()
    self.frozenSet.clear()


  def pop(self) -> Tuple[Opt[cfg.CfgNode], Opt[bool], Opt[Any]]:
    """Pops and returns next node id on top of queue, None otherwise."""
    if not self.wl:
      self.fullSequence.append(0) # special value to denote wl consumed
      return None, None, None

    nid = self.wl.pop()
    self.wlNodeSet.remove(nid)

    nodeIsNop = self.isNop[nid-1]
    self.fullSequence.append(nid * -1 if nodeIsNop else nid)
    return self.nodes[nid], nodeIsNop, self.valueFilter[nid-1]


  def add(self,
      node: cfg.CfgNode,
  ) -> bool:
    """Add a node to the queue."""
    frozen, nid = self.frozen, node.id

    attemptAdd = (frozen and nid in self.frozenSet) or not frozen

    if attemptAdd and nid not in self.wlNodeSet:
      self.wl.append(nid)
      self.wl.sort(key=lambda x: x if self.postOrder else -x)
      self.wlNodeSet.add(nid)
      if util.LL5: LDB("AddedNodeToWl: Node_%s: Yes. %s", node.id, node.insn)
      return True

    if util.LL5: LDB("AddedNodeToWl: Node_%s: No."
                     " (Attempted: %s, AlreadyPresent: %s). %s",
                     node.id, attemptAdd, nid in self.wlNodeSet, node.insn)
    return False


  def initForDdm(self):
    """Used by #DDM"""
    self.frozen = True
    self.clear()
    for i in range(1, len(self.isNop)):
      self.isNop[i] = True


  def updateNodeMap(self,  #DDM
      nodeMap: Opt[Dict[cfg.CfgNode, Any]]  # node -> span.sys.ddm.NodeInfo
  ) -> bool:
    """Used by #DDM"""
    if not nodeMap: return False  # i.e. no change

    if util.LL5: LDB("UpdatedNodeMap(AddingMap): %s", nodeMap)

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
    listType = "(All)" if allNodes else ""

    prefix = ""
    with io.StringIO() as sio:
      sio.write("#DDM " if self.frozen else "")
      sio.write(f"NodeWorkList{listType} [")
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


# class NodeWorkList(object):
#   """Cfg node worklist.
#
#   It remembers the initial order in which node ids are given,
#   and maintains the same order when selective nodes are added later.
#   """
#
#
#   def __init__(self,
#       nodes: Opt[List[cfg.CfgNode]] = None,
#       frozen: bool = False,  # True restricts addition of new nodes
#   ) -> None:
#     # list to remember the order of each node initially given for the first time
#     self.sequence: List[cfg.CfgNode] = []
#     self.workque: List[bool] = []
#     self.treatAsNop: List[bool] = []  # DDM used by demand driven technique
#     # remembers the nodes already given
#     self.nodeMem: Set[cfg.CfgNodeId] = set()
#     _ = [self.add(node, force=True) for node in nodes] if nodes else None
#     # seq of nodes visited from start to end of the analysis
#     self.fullSequence: List[cfg.CfgNode] = []
#     # seq of nodes visited till the analysis reaches intermediate FP
#     # after each intermediate FP this is supposed to be cleared explicitly
#     self.tmpSequence: List[cfg.CfgNode] = []
#     self.frozen = frozen
#
#
#   def __contains__(self, node: cfg.CfgNode):
#     nid = node.id
#     for index, n in enumerate(self.sequence):
#       if nid == n.id: return self.workque[index]
#     return False
#
#
#   def clear(self):
#     """Clear the worklist."""
#     for index in range(len(self.workque)):
#       self.workque[index] = False
#
#
#   def isNodePresent(self, nid: cfg.CfgNodeId):
#     return nid in self.nodeMem
#
#
#   def add(self,
#       node: cfg.CfgNode,
#       treatAsNop: bool = False,
#       force: bool = False,  # overrides the frozen property
#   ) -> bool:
#     """Add a node to the queue."""
#     assert len(self.nodeMem) == len(self.sequence) or self.frozen
#     assert len(self.sequence) == len(self.workque)
#     nid = node.id
#     if nid not in self.nodeMem:  # a new node -- add it
#       if force or not self.frozen:  # checks if WL is frozen?
#         self.nodeMem.add(nid)
#         self.sequence.append(node)
#         self.workque.append(True)
#         self.treatAsNop.append(treatAsNop)
#         return True
#       else:
#         return False  # not added since work list is frozen
#
#     # an old node -- re-add it
#     index, added = 0, False
#     for index, node in enumerate(self.sequence):
#       if node.id == nid: break
#     if not self.workque[index]:
#       self.workque[index] = True
#       added = True
#
#     return added  # possibly added
#
#
#   def pop(self) -> Tuple[Opt[cfg.CfgNode], Opt[bool]]:
#     """Pops and returns next node id on top of queue, None otherwise."""
#     for index, active in enumerate(self.workque):
#       if active: break
#     else:
#       return None, None
#
#     self.workque[index] = False
#     node = self.sequence[index]
#     self.fullSequence.append(node)
#     self.tmpSequence.append(node)
#     return node, self.treatAsNop[index]
#
#
#   def peek(self) -> Opt[cfg.CfgNode]:
#     """Returns next node id on top of queue, None otherwise."""
#     for index, active in enumerate(self.workque):
#       if active:
#         return self.sequence[index]
#     return None
#
#
#   def initForDdm(self):
#     """Used by #DDM"""
#     self.frozen = True
#     self.clear()
#     self.nodeMem.clear()
#     for i in range(1, len(self.treatAsNop)):
#       self.treatAsNop[i] = True
#
#
#   def updateNodeMap(self, nodeMap: Opt[Dict[cfg.CfgNode, bool]]) -> bool:
#     """Used by #DDM"""
#     if not nodeMap: return False  # i.e. no change
#
#     if util.LL5: LDB("UpdatedNodeMap(AddingMap): %s", nodeMap)
#
#     changed = False
#     for node, treatAsNop in nodeMap.items():
#       nid = node.id
#       if nid not in self.nodeMem:  # a fresh node
#         self.nodeMem.add(nid)
#         for index, node in enumerate(self.sequence):
#           if node.id == nid: break
#         if not self.workque[index]:  # 'index' use is okay
#           self.workque[index], self.treatAsNop[index] = True, treatAsNop
#           changed = True
#       else:  # a known node
#         for index, node in enumerate(self.sequence):
#           if node.id == nid: break
#         treatedAsNop = self.treatAsNop[index]
#         if not treatAsNop and treatedAsNop:
#           self.workque[index], self.treatAsNop[index] = True, False
#           changed = True
#
#     return changed
#
#
#   def shouldTreatAsNop(self, node: cfg.CfgNode):
#     """Should the current node be treated as containing NopI()? Used by #DDM"""
#     nid = node.id
#     for index, n in enumerate(self.sequence):
#       if nid == n.id: return self.treatAsNop[index]
#     return False
#
#
#   def clearTmpSequence(self):
#     self.tmpSequence.clear()
#
#
#   def tmpSequenceStr(self):
#     prefix = ""
#     with io.StringIO() as sio:
#       for node in self.tmpSequence:
#         sio.write(f"{prefix}{node.id}")
#         if not prefix: prefix = ","
#       return sio.getvalue()
#
#
#   def getAllNodesStr(self):
#     prefix = ""
#     with io.StringIO() as sio:
#       sio.write("#DDM " if self.frozen else "")
#       sio.write("NodeWorkList[")
#       for index, node in enumerate(self.sequence):
#         if node.id in self.nodeMem:
#           sio.write(f"{prefix}{node.id}")
#           sio.write("." if self.treatAsNop[index] else "")
#           if not prefix: prefix = ", "
#       sio.write("]")
#       prefix = sio.getvalue()  # reusing prefix
#     return prefix
#
#
#   def __str__(self):
#     prefix = ""
#     with io.StringIO() as sio:
#       sio.write("#DDM " if self.frozen else "")
#       sio.write("NodeWorkList[")
#       for index, active in enumerate(self.workque):
#         if active:
#           sio.write(f"{prefix}{self.sequence[index].id}")
#           sio.write("." if self.treatAsNop[index] else "")
#           if not prefix: prefix = ", "
#       sio.write("]")
#       prefix = sio.getvalue()  # reusing prefix
#     return prefix
#
#
#   def __repr__(self):
#     return self.__str__()


################################################
# BOUND END  : worklist_related
################################################

################################################
# BOUND START: direction_related
################################################

class DirectionDT:
  """For the direction of data flow of the analysis."""


  def __init__(self,
      anName: AnNameT,
      func: constructs.Func,
      top: DataLT,
  ) -> None:
    if type(self).__name__ == "DirectionT":
      super().__init__()
    self.cfg = func.cfg
    self.anResult: dfv.AnResult = dfv.AnResult(anName, func, top)
    self.topNdfv: NodeDfvL = NodeDfvL(top, top)
    for nid in self.cfg.nodeMap.keys():
      self.anResult[nid] = self.topNdfv
    # set this to true once boundary values are initialized
    self.boundaryInfoInitialized = False
    self.wl: Opt[FastNodeWorkList] = None # initialize in sub-class


  def generateInitialWorklist(self) -> FastNodeWorkList:
    """Defaults to reverse post order."""
    wl = FastNodeWorkList(self.cfg.nodeMap, postOrder=False)
    return wl


  def setTopValue(self,
      node: Opt[cfg.CfgNode] = None,
      nid: Opt[NodeIdT] = None,
  ) -> None:
    if not nid: nid = node.id
    self.anResult[nid] = self.topNdfv


  def update(self,
      node: cfg.CfgNode,
      nodeDfv: NodeDfvL,
      widen: bool = False, # apply widening
  ) -> ChangePairL:
    """Update, the node dfv in wl if changed.

    Subclasses should add pred/succ to the worklist,
    if dfv is changed.
    """
    nid = node.id
    oldNdfv = self.anResult.get(nid, self.topNdfv)
    oldIn, oldOut = oldNdfv.dfvIn, oldNdfv.dfvOut
    oldOutTrue, oldOutFalse = oldNdfv.dfvOutTrue, oldNdfv.dfvOutFalse

    newIn, newOut = nodeDfv.dfvIn, nodeDfv.dfvOut
    newOutTrue, newOutFalse = nodeDfv.dfvOutTrue, nodeDfv.dfvOutFalse

    if widen:  # used for widening at call sites
      assert oldOut is oldOutTrue and oldOut is oldOutFalse
      assert newOut is newOutTrue and newOut is newOutFalse
      newIn, c1 = oldIn.widen(newIn)
      newOut, c2 = oldOut.widen(newOut)
      nodeDfv = NodeDfvL(newIn, newOut)  # nodeDfv OVER-WRITTEN
      newOutFalse = newOutTrue = newOut

    if util.CC3:
      if nodeDfv < oldNdfv:
        pass  # i.e. its okay
      else:
        if util.LL1:
          LER("NonMonotonicDFV: Analysis: %s", oldIn.__class__)
          if not newIn < oldIn:
            LER("NonMonotonicDFV (IN):\n NodeId: %s, Instr: %s, Info: %s, Old: %s,\n New: %s.",
                      nid, node.insn, node.insn.info, oldIn, newIn)
          if not newOut < oldOut:
            LER("NonMonotonicDFV (OUT):\n NodeId: %s, Info: %s, Instr: %s, Old: %s,\n New: %s.",
                      nid, node.insn, node.insn.info, oldOut, newOut)

    isNewIn = newIn != oldIn
    isNewOut = newOut != oldOut \
               or newOutFalse != oldOutFalse \
               or newOutTrue != oldOutTrue
    self.anResult[nid] = nodeDfv
    return dfv.getNewOldObj(isNewIn, isNewOut)


  def add(self, node: cfg.CfgNode) -> bool:
    """Add node_id to the worklist."""
    assert self.wl is not None
    added = self.wl.add(node)
    return added


  def calcInOut(self,
      node: cfg.CfgNode,
      fcfg: cfg.FeasibleEdges
  ) -> Tuple[NodeDfvL, ChangePairL]:
    """Merges dfv from feasible edges."""
    raise NotImplementedError()


  def getDfv(self,
      nodeId: cfg.CfgNodeId
  ) -> NodeDfvL:
    return self.anResult.get(nodeId, self.topNdfv)


  def __str__(self):
    return self.__repr__()


  def __repr__(self):
    return f"analysis.{self.__class__.__name__}"


class ForwardDT(DirectionDT):
  """For all forward flow problems."""


  def __init__(self,
      anName: AnNameT,
      func: constructs.Func,
      top: DataLT,
  ) -> None:
    if type(self).__name__ == "ForwardDT":
      raise NotImplementedError()  # can't create direct object
    super().__init__(anName, func, top)
    self.wl = self.generateInitialWorklist()  # important


  def generateInitialWorklist(self) -> FastNodeWorkList:
    """Defaults to reverse post order."""
    wl = FastNodeWorkList(self.cfg.nodeMap, postOrder=False)
    if util.LL4: LDB("  Forward_Worklist_Init: %s", wl)
    return wl


  def update(self,
      node: cfg.CfgNode,
      nodeDfv: NodeDfvL,
      widen: bool = False, # apply widening
  ) -> ChangePairL:
    """Update, for forward direction.

    If OUT is changed add the pred/succ to the worklist.
    """
    inOutChange = super().update(node, nodeDfv, widen)

    #assert not inOutChange.isNewIn, msg.INVARIANT_VIOLATED  #FIXME: why did i put this assertion?

    if inOutChange.newOut:
      """Add the successors only."""
      for succEdge in node.succEdges:
        dest = succEdge.dest
        if util.LL4: LDB("AddingNodeToWl(succ): Node_%s: %s (%s)",
                         dest.id, dest.insn, dest.insn.info)
        self.wl.add(dest)

    return inOutChange


  def calcInOut(self,
      node: cfg.CfgNode,
      fcfg: cfg.FeasibleEdges
  ) -> Tuple[NodeDfvL, ChangePairL]:
    """Forward: Merges OUT of feasible predecessors.

    It also updates the self.anResult to make the change visible (if any).
    """
    nid, selfNidNdfvMapGet, topNdfv = node.id, self.anResult.get, self.topNdfv
    ndfv = selfNidNdfvMapGet(nid, topNdfv)
    predEdges = node.predEdges
    # for start node, nothing changes
    if not predEdges: return ndfv, OLD_IN_OUT

    newIn = topNdfv.dfvIn  # don't enforce_monotonicity
    for predEdge in predEdges:
      f = fcfg.isFeasibleEdge(predEdge)
      if util.LL4: LDB(" Edge(%s): %s",
                       "Feasible" if f else "Infeasible", predEdge)
      if f:
        predNodeDfv = selfNidNdfvMapGet(predEdge.src.id, topNdfv)
        if predEdge.label == TrueEdge:
          predOut = predNodeDfv.dfvOutTrue
        elif predEdge.label == FalseEdge:
          predOut = predNodeDfv.dfvOutFalse
        else:
          predOut = predNodeDfv.dfvOut  # must not be None, if here

        if util.LL4: LDB(" PredDfvOut: %s", predOut)

        newIn, _ = newIn.meet(predOut)

    if newIn == ndfv.dfvIn: return ndfv, OLD_IN_OUT

    # Update in map for use in evaluation functions.
    assert newIn is not None
    newNodeDfv = NodeDfvL(newIn, ndfv.dfvOut)
    self.anResult[nid] = newNodeDfv  # updates the node dfv map
    return newNodeDfv, NEW_IN_ONLY


class ForwardD(ForwardDT):
  """Create instance of this class for forward flow problems."""


  def __init__(self,
      anName: AnNameT,
      func: constructs.Func,
      top: DataLT,
  ) -> None:
    super().__init__(anName, func, top)


class BackwardDT(DirectionDT):
  """For all backward flow problems."""


  def __init__(self,
      anName: AnNameT,
      func: constructs.Func,
      top: DataLT,
  ) -> None:
    if type(self).__name__ == "BackwardDT":
      raise NotImplementedError()  # can't create direct object
    super().__init__(anName, func, top)
    self.wl = self.generateInitialWorklist()  # important


  def generateInitialWorklist(self) -> FastNodeWorkList:
    """Defaults to reverse post order."""
    wl = FastNodeWorkList(self.cfg.nodeMap, postOrder=True)
    if LS: LDB("Backward_Worklist_Init: %s", wl)
    return wl


  def update(self,
      node: cfg.CfgNode,
      nodeDfv: NodeDfvL,
      widen: bool = False, # apply widening
  ) -> ChangePairL:
    """Update, for backward direction.

    If IN is changed add the pred/succ to the worklist.
    """
    # print("OldOut:", nodeDfv.dfvOut)
    inOutChange = super().update(node, nodeDfv, widen)

    # if not inOutChange.isNewOut:
    #   print("NewOut:", self.anResult[node.id].dfvOut)
    # assert not inOutChange.isNewOut, msg.INVARIANT_IS_VIOLATED

    if inOutChange.newIn:
      """Add the predecessors."""
      for predEdge in node.predEdges:
        pred = predEdge.src
        if LS: LDB("AddingNodeToWl(pred): Node_%s: %s (%s)",
                         pred.id, pred.insn, pred.insn.info)
        self.wl.add(pred)

    return inOutChange


  def calcInOut(self,
      node: cfg.CfgNode,
      fcfg: cfg.FeasibleEdges
  ) -> Tuple[NodeDfvL, ChangePairL]:
    """Backward: Merges IN of feasible successors.

    It also updates the self.anResult to make the change visible (if any).
    """
    nid, selfNidNdfvMapGet, topNdfv = node.id, self.anResult.get, self.topNdfv
    ndfv = selfNidNdfvMapGet(nid, topNdfv)
    succEdges = node.succEdges
    # for end node, nothing changes
    if not succEdges: return ndfv, OLD_IN_OUT

    newOut = topNdfv.dfvOut  # don't enforce_monotonicity
    for succEdge in succEdges:
      f = fcfg.isFeasibleEdge(succEdge)
      if util.LL4: LDB(" Edge(%s): %s",
                       "Feasible" if f else "Infeasible", succEdge)
      if f:
        succNodeDfv = selfNidNdfvMapGet(succEdge.dest.id, topNdfv)
        succIn = succNodeDfv.dfvIn  # must not be None, if here

        if util.LL4: LDB(" SuccDfvIn: %s", succIn)

        newOut, _ = newOut.meet(succIn)

    if newOut == ndfv.dfvOut: return ndfv, OLD_IN_OUT

    # Update in map for use in evaluation functions.
    assert newOut is not None
    newNodeDfv = NodeDfvL(ndfv.dfvIn, newOut)
    self.anResult[nid] = newNodeDfv  # updates the node dfv map
    return newNodeDfv, NEW_IN_ONLY


class BackwardD(BackwardDT):
  """Create instance of this class for backward flow problems."""


  def __init__(self,
      anName: AnNameT,
      func: constructs.Func,
      top: DataLT,
  ) -> None:
    super().__init__(anName, func, top)


class ForwBackDT(DirectionDT):
  """TODO: For bi-directional problems."""


  def __init__(self,
      anName: AnNameT,
      func: constructs.Func,
      top: DataLT,
  ):
    pass


################################################
# BOUND END  : direction_related
################################################

################################################
# BOUND START: AnalysisAT_The_Base_Class.
################################################

class AnalysisAT:
  # For bi-directional analyses, subclass AnalysisAT directly.

  __slots__ : List[str] = ["func", "overallTop", "overallBot"]

  # concrete lattice class of the analysis
  L: Type[dfv.DataLT] = DataLT
  # direction of the analysis
  D: DirectionT = Forward  # default setting

  # Simplification needed: methods simplifying (blocking) exprs of this analysis
  # list required sim function objects here (functions with '__to__' in their name)
  needsRhsDerefToVarsSim: bool = False # also used for function pointer sim
  needsLhsDerefToVarsSim: bool = False
  needsNumVarToNumLitSim: bool = False
  needsNumBinToNumLitSim: bool = False
  needsCondToUnCondSim: bool = False #FIXME: see Host.setEdgeFeasibility, assumed True
  needsLhsVarToNilSim: bool = False
  needsNodeToNilSim: bool = False
  needsFpCallSim: bool = True


  def __init__(self,
      func: constructs.Func  # function being analyzed
  ) -> None:
    if type(self).__name__ == "AnalysisAT":
      super().__init__()  # no instance of this class
    assert self.L is not None and self.D is not None
    self.func = func
    self.overallTop = self.L(func, top=True)  # L is callable. pylint: disable=E
    self.overallBot = self.L(func, bot=True)  # L is callable. pylint: disable=E


  def getBoundaryInfo(self,
      nodeDfv: Opt[NodeDfvL] = None,
      ipa: bool = False,
      entryFunc: bool = False,
      func: Opt[constructs.Func] = None,
  ) -> NodeDfvL:
    """Must generate a valid boundary info."""
    if ipa and not nodeDfv:
      raise ValueError(f"{ipa}, {nodeDfv}")

    inBi, outBi = self.overallBot, self.overallBot
    if ipa: raise NotImplementedError()  # for IPA override this function
    if nodeDfv: inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
    return NodeDfvL(inBi, outBi)  # good to create a copy


  def getLocalizedCalleeBi(self, #IPA
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Computes the value context of the callee, given
    the data flow value of the caller."""
    raise NotImplementedError


  # BOUND START: special_instructions_seven

  def Any_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """For any SPAN IR instruction.
    Default behaviour is to delegate the control to specialized functions.
    """
    if isinstance(insn, instr.AssignI):
      return self.Assign_Instr(nodeId, insn, nodeDfv, calleeBi)
    else:
      memberFuncName = instr.getFormalInstrStr(insn)
      f = getattr(self, memberFuncName)
      if instr.getCallExpr(insn):
        return f(nodeId, insn, nodeDfv, calleeBi)
      else:
        return f(nodeId, insn, nodeDfv)


  def Default_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """The default behaviour for unimplemented instructions.
    Analysis should override this method if unimplemented
    instructions have to be handled in a way other than
    like a NOP instruction.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Nop_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: NopI()."""
    D = self.D

    if D == Forward:
      dfvIn = nodeDfv.dfvIn
      if dfvIn is nodeDfv.dfvOut:
        return nodeDfv
      else:
        return NodeDfvL(dfvIn, dfvIn)

    elif D == Backward:
      dfvOut = nodeDfv.dfvOut
      if dfvOut is nodeDfv.dfvIn:
        return nodeDfv
      else:
        return NodeDfvL(dfvOut, dfvOut)

    else: # ForwBack?
      raise ValueError("ForwBack NOP not defined!")


  def Barrier_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Data Flow information is blocked from travelling
    from IN-to-OUT and OUT-to-IN.

    This implementation works for *any* direction analysis.
    """
    return nodeDfv  # no information travels from IN to OUT or OUT to IN


  def Use_Instr(self,
      nodeId: NodeIdT,
      insn: instr.UseI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: UseI(x).
    Value of x is read from memory."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def ExRead_Instr(self,
      nodeId: NodeIdT,
      insn: instr.ExReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: ExReadI(x).
    x and only x is read, others are forcibly
    marked as not read (in backward direction)."""
    return self.Barrier_Instr(nodeId, insn, nodeDfv)


  def CondRead_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CondReadI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: CondReadI(x, {y, z}).
    y and z are read if x is read."""
    return self.Barrier_Instr(nodeId, insn, nodeDfv)


  def UnDefVal_Instr(self,
      nodeId: NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: input(x). (user supplies value of x)
    Thus value of x is undefined."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Filter_Instr(self,
      nodeId: NodeIdT,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: FilterI({x,y,z}).
    x,y,z are known to be dead after this program point."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : special_instructions_seven

  # BOUND START: regular_instructions
  # BOUND START: regular_insn__when_lhs_is_var

  def Assign_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    iType = insn.type
    if iType.isNumericOrVoid():
      return self.Num_Assign_Instr(nodeId, insn, nodeDfv, calleeBi)
    elif iType.isPointerOrVoid():
      return self.Ptr_Assign_Instr(nodeId, insn, nodeDfv, calleeBi)
    elif iType.isRecordOrVoid():
      return self.Record_Assign_Instr(nodeId, insn, nodeDfv, calleeBi)
    else:
      raise ValueError()


  def Num_Assign_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Instr_Form: numeric: lhs = rhs.
    Convention:
      Type of lhs and rhs is numeric.
    """
    memberFuncName = instr.getFormalInstrStr(insn)
    f = getattr(self, memberFuncName)
    if instr.getCallExpr(insn):
      return f(nodeId, insn, nodeDfv, calleeBi)
    else:
      return f(nodeId, insn, nodeDfv)


  def Ptr_Assign_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Instr_Form: pointer: lhs = rhs.
    Convention:
      Type of lhs and rhs is a record.
    """
    memberFuncName = instr.getFormalInstrStr(insn)
    f = getattr(self, memberFuncName)
    if instr.getCallExpr(insn):
      return f(nodeId, insn, nodeDfv, calleeBi)
    else:
      return f(nodeId, insn, nodeDfv)


  def Record_Assign_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Instr_Form: record: lhs = rhs.
    Convention:
      Type of lhs and rhs is a record.
    """
    memberFuncName = instr.getFormalInstrStr(insn)
    f = getattr(self, memberFuncName)
    if instr.getCallExpr(insn):
      return f(nodeId, insn, nodeDfv, calleeBi)
    else:
      return f(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b.
    Convention:
      a and b are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = v.
    Convention:
      u and v are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_FuncName_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = f.
    Convention:
      u is a variable.
      f is a function name.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): a = b.
    Convention:
      a and b are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b.
    Convention:
      a is a variable.
      b is a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: a = b.
    Convention:
      a is a variable.
      b is a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_SizeOf_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = sizeof(b).
    Convention:
      a and b are both variables.
      b is of type: types.VarArray only.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_UnaryArith_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = <unary arith/bit/logical op> b.
    Convention:
      a and b are both variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_BinArith_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b <binary arith/rel/bit/shift> c.
    Convention:
      a is a variable.
      b, c: at least one of them is a variable.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_BinArith_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b <binary +/-> c.
    Convention:
      a is a variable.
      b, c: at least one of them is a variable.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Deref_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = *u.
    Convention:
      a and u are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Deref_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = *v.
    Convention:
      u and v are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Deref_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record: u = *v.
    Convention:
      v and u are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Array_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b[i].
    Convention:
      a and b are variables.
      i is a variable or a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Array_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = a[i].
    Convention:
      u and a are variables.
      i is a variable or a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Array_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): r = a[i].
    Convention:
      u and a are variables.
      i is a variable or a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Member_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = b.x or a = b->x.
    Convention:
      a and b are variables.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Member_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: a = b.x or a = b->x.
    Convention:
      a and b are variables.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Member_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): a = b.x or a = b->x.
    Convention:
      a and b are variables.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Select_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: b = c ? d : e.
    Convention:
      b, c, are always variables.
      d, e are variables or literals.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Select_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: p = c ? d : e.
    Convention:
      b, c, are always variables.
      d, e are variables or literals.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Select_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record: b = c ? d : e.
    Convention:
      b, c, d, e are always variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_Call_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Instr_Form: numeric: b = func(args...).
    Convention:
      b is a variable.
      func is a function pointer or a function name.
      args are either a variable, a literal or addrof expression.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_Call_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Instr_Form: pointer: p = func()."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Call_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Instr_Form: record: r = func()."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Var_CastVar_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a = (int) b.
    Convention:
      a and b are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_CastVar_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: a = (int*) b.
    Convention:
      a and b are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_CastArr_Instr(self,
      nodeId: NodeIdT,
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
    return self.Default_Instr(nodeId, insn, nodeDfv)


  # Ptr_Assign_Var_CastMember_Instr() is not part of IR.
  # its broken into: t1 = x.y; b = (int*) t1;

  def Ptr_Assign_Var_AddrOfVar_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &x.
    Convention:
      u and x are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_AddrOfArray_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &a[i]
    Convention:
      u and a are variables.
      i is a variable of a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_AddrOfMember_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &r.x or u = &r->x.
    Convention:
      u and r are variables.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_AddrOfDeref_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &*x
    Convention:
      u is a pointer variable
      x is a pointer variable
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Var_AddrOfFunc_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: u = &f.
    Convention:
      u is a variable.
      f is function name.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : regular_insn__when_lhs_is_var
  # BOUND START: regular_insn__when_lhs_is_deref

  def Num_Assign_Deref_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: *u = b.
    Convention:
      u and b are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Deref_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: *u = b.
    Convention:
      u is a variable.
      b is a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Deref_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: *u = v.
    Convention:
      u and v are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Deref_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: *u = b.
    Convention:
      u is a variable.
      b is a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Deref_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record: *u = v.
    Convention:
      u and v are variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : regular_insn__when_lhs_is_deref
  # BOUND START: regular_insn__when_lhs_is_array

  def Num_Assign_Array_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a[i] = b.
    Convention:
      a and b are variables.
      i is either a variable or a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Array_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: a[i] = b.
    Convention:
      a is a variable.
      i is either a variable or a literal.
      b is a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Array_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: a[i] = b.
    Convention:
      a and b are variables.
      i is a variable or a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Array_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: a[i] = b.
    Convention:
      a is a variable.
      i is a variable or a literal.
      b is a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Array_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): a[i] = b.
    Convention:
      a and b are variables.
      i is a variable or a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : regular_insn__when_lhs_is_array
  # BOUND START: regular_insn__when_lhs_is_member_expr

  def Num_Assign_Member_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: r.x = b  or r->x = b.
    Convention:
      r is a variable.
      b is a variable.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Num_Assign_Member_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: numeric: r.x = b or r->x = b.
    Convention:
      r is a variable.
      b is a literal.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Member_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: r.x = b  or r->x = b.
    Convention:
      r is a variable.
      b is a variable.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Ptr_Assign_Member_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: pointer: r.x = b or r->x = b.
    Convention:
      r is a variable.
      b is a literal.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Member_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """Instr_Form: record(struct/union): r.x = b or r->x = b.
    Convention:
      r and b are variables.
      x is a member/field of a record.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : regular_insn__when_lhs_is_member_expr
  # BOUND START: regular_insn__other

  def Call_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Instr_Form: void: func(args...) (just a call statement).
    Convention:
      args are either a variable, a literal or addrof expression.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Return_Var_Instr(self,
      nodeId: NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: return b.
    Convention:
      b is a variable.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Return_Lit_Instr(self,
      nodeId: NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: return b.
    Convention:
      b is a literal.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Return_Void_Instr(self,
      nodeId: NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: return;
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Conditional_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: void: if b.
    Convention:
      b is a variable.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)

  # BOUND END  : regular_insn__other
  # BOUND END  : regular_instructions

  ################################################
  # BOUND START: sim_related 2/3
  ################################################

  """Simplification functions to be (optionally) overridden.

  For convenience, analysis.AnalysisAT inherits this class.
  So the user may only inherit AnalysisAT class, and
  override functions in this class only if the
  analysis works as a simplifier too.

  The second argument, nodeDfv, if its None,
  means that the return value should be either
  Pending if the expression provided
  can be possibly simplified by the analysis,
  or Failed if the expression cannot be simplified
  given any data flow value.
  """

  def Node__to__Nil(self,
      nodeId: NodeIdT,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[bool] = None,
  ) -> Opt[Set[bool]]:
    """Node is simplified to Nil if its basically unreachable."""
    raise NotImplementedError()


  def LhsVar__to__Nil(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[bool]] = None,
  ) -> Opt[Set[bool]]:
    """Returns a set of live variables at out of the node."""
    raise NotImplementedError()


  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[NumericT]] = None,
  ) -> Opt[Set[NumericT]]:
    """Simplify to a single literal if the variable can take that value."""
    raise NotImplementedError()


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[NumericT]] = None,
  ) -> Opt[Set[NumericT]]:
    """Simplify to a single literal if the expr can take that value."""
    raise NotImplementedError()


  def Deref__to__Vars(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[VarNameT]] = None
  ) -> Opt[Set[VarNameT]]:
    """Simplify a deref expr de-referencing varName
    to a set of var pointees."""
    raise NotImplementedError()


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[bool] = None,
  ) -> Opt[Set[bool]]:
    """Simplify conditional jump to unconditional jump."""
    raise NotImplementedError()


  ################################################
  # BOUND END  : sim_related 2/3
  ################################################

################################################
# BOUND END  : AnalysisAT_The_Base_Class.
################################################

################################################
# BOUND START: sim_related 3/3
################################################

def extractSimNames() -> Set[str]:
  """Returns set of expr simplification func names
   (these names have `SIM_NAME_COMMON_SUBSTR` in them)."""
  tmp = set()
  for memberName in AnalysisAT.__dict__:
    if memberName.find(SIM_NAME_COMMON_SUBSTR) >= 0:
      tmp.add(memberName)
  return tmp


SimNames: Set[str] = extractSimNames()

Node__to__Nil__Name: str = AnalysisAT.Node__to__Nil.__name__
LhsVar__to__Nil__Name: str = AnalysisAT.LhsVar__to__Nil.__name__
Num_Var__to__Num_Lit__Name: str = AnalysisAT.Num_Var__to__Num_Lit.__name__
Num_Bin__to__Num_Lit__Name: str = AnalysisAT.Num_Bin__to__Num_Lit.__name__
Deref__to__Vars__Name: str = AnalysisAT.Deref__to__Vars.__name__
Cond__to__UnCond__Name: str = AnalysisAT.Cond__to__UnCond.__name__

SimDirnMap = {  # the IN/OUT information needed for the sim
  Node__to__Nil__Name:        Forward,  # means dfv at IN is needed
  Num_Var__to__Num_Lit__Name: Forward,
  Cond__to__UnCond__Name:     Forward,
  Num_Bin__to__Num_Lit__Name: Forward,
  Deref__to__Vars__Name:      Forward,
  LhsVar__to__Nil__Name:      Backward,  # means dfv at OUT is needed
}

################################################
# BOUND END  : sim_related 3/3
################################################


################################################
# BOUND START: Value_analysis
################################################

class ValueAnalysisAT(AnalysisAT):
  """A specialized (value) analysis implementation.
  Common functionality to most value analyses and other similar ones."""
  __slots__ : List[str] = ["anName", "componentTop", "componentBot"]
  # redefine these variables as needed (see ConstA, IntervalA for examples)
  L: Type[dfv.OverallL] = dfv.OverallL  # the OverallL lattice used
  D: DirectionT = Forward  # its a forward flow analysis


  needsRhsDerefToVarsSim: bool = True
  needsLhsDerefToVarsSim: bool = True
  needsNumVarToNumLitSim: bool = False
  needsNumBinToNumLitSim: bool = True
  needsCondToUnCondSim: bool = True
  needsLhsVarToNilSim: bool = False # FIXME: True when using liveness analysis
  needsNodeToNilSim: bool = False
  needsFpCallSim: bool = True


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
    self.anName = self.__class__.__name__


  def getBoundaryInfo(self,
      nodeDfv: Opt[NodeDfvL] = None, # needs to be localized to the target func
      ipa: bool = False,  #IPA
      entryFunc: bool = False,
      forFunc: Opt[constructs.Func] = None,
  ) -> NodeDfvL:
    """
      * IPA/Intra: initialize all local (non-parameter) vars to Top.
      * IPA: initialize all non-initialized globals to Top
        only at the entry of the main function. (DONE)
      * Intra: initialize all globals to Bot. (as is done currently)
    """
    if ipa and not nodeDfv: raise ValueError(f"{ipa}, {nodeDfv}")

    func = forFunc if forFunc else self.func

    overTop, overBot = self.overallTop.getCopy(), self.overallBot.getCopy()
    overTop.func = overBot.func = func #IMPORTANT

    if isDummyGlobalFunc(func):  # initialize all to Top
      inBi, outBi = overTop, overTop
    else:
      if nodeDfv: #IPA or #INTRA
        inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
      else: #INTRA
        inBi, outBi = overBot, overBot

      tUnit: TranslationUnit = func.tUnit
      inBiSetVal, tUnitGetNameInfo = inBi.setVal, tUnit.getNameInfo

      compTop, compBot = self.componentTop.getCopy(), self.componentBot.getCopy()
      compTop.func = compBot.func = func #IMPORTANT

      # set arrays/locals to a top initial value
      if ff.SET_LOCAL_ARRAYS_TO_TOP or ff.SET_LOCAL_VARS_TO_TOP:
        localNames = tUnit.getNamesLocal(func)
        allVars = self.L.getAllVars(func)
        varNames = (localNames - set(func.paramNames)) & allVars
        for vName in varNames:
          if ff.SET_LOCAL_VARS_TO_TOP or\
              (ff.SET_LOCAL_ARRAYS_TO_TOP and tUnitGetNameInfo(vName).hasArray):
            inBiSetVal(vName, compTop) #Mutates inBi

      if entryFunc: # then set its parameters to Bot (main() function)
        for vName in func.paramNames:
          if self.L.isAcceptedType(tUnitGetNameInfo(vName).type):
            inBiSetVal(vName, compBot)

    nDfv1 = NodeDfvL(inBi, outBi)
    return nDfv1


  def getLocalizedCalleeBi(self, #IPA
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,  # caller's node IN/OUT
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """Computes the value context of the callee, given
    the data flow value of the caller."""
    assert insn.hasRhsCallExpr(), f"{self.func.name}, {nodeId}, {insn}, {insn.info}"

    calleeName = instr.getCalleeFuncName(insn)
    tUnit: TranslationUnit = self.func.tUnit
    calleeFuncObj = tUnit.getFuncObj(calleeName)

    # Out is unchanged in Forward analyses
    if calleeBi:
      outDfv = calleeBi.dfvOut # unchanged Out
    else:
      outDfv = self.overallTop.getCopy()
      outDfv.func = calleeFuncObj

    newDfvIn = nodeDfv.dfvIn.localize(calleeFuncObj, keepParams=True)

    localized = NodeDfvL(newDfvIn, outDfv)
    localized = self.getBoundaryInfo(localized, ipa=True, forFunc=calleeFuncObj)
    if LS: LDB("CalleeCallSiteDfv(Localized): %s", localized)
    return localized


  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def Filter_Instr(self,
      nodeId: NodeIdT,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    varNames = insn.varNames

    if not varNames or dfvIn.top:  # i.e. nothing to filter or no DFV to filter == Nop
      return NodeDfvL(dfvIn, dfvIn)  # = NopI

    newDfvOut = dfvIn.getCopy()
    newDfvOut.filterVals(varNames)
    return NodeDfvL(dfvIn, newDfvOut)


  def UnDefVal_Instr(self,
      nodeId: NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if not self.L.isAcceptedType(insn.type):
      return self.Default_Instr(nodeId, insn, nodeDfv)
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

  def Any_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """For any SPAN IR instruction.
    Default behaviour is to delegate the control to specialized functions.
    """
    if isinstance(insn, instr.AssignI):
      return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv, calleeBi)
    else:
      return super().Any_Instr(nodeId, insn, nodeDfv, calleeBi)


  def Conditional_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    if not self.L.isAcceptedType(insn.arg.type):  # special case
      return NodeDfvL(dfvIn, dfvIn)
    outDfvFalse, outDfvTrue = self.calcFalseTrueDfv(insn.arg, dfvIn)
    return NodeDfvL(dfvIn, None, outDfvTrue, outDfvFalse)


  def Call_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    if not calleeBi: #INTRA handle intra-procedurally
      return self.genNodeDfvL(self.processCallE(insn.arg, dfvIn), nodeDfv)
    else: # handle for #IPA
      newOut = calleeBi.dfvOut.localize(self.func)
      newOut.addLocals(dfvIn)
      return NodeDfvL(dfvIn, newOut)


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
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> NodeDfvL:
    """A common function to handle various assignment instructions.
    This is a common function to all the value analyses.
    """
    dfvIn, lhsType = nodeDfv.dfvIn, lhs.type
    assert isinstance(dfvIn, dfv.OverallL), f"{type(dfvIn)}"
    if util.LL5: LDB("ProcessingAssignInstr: %s = %s, iType: %s, %s",
                     lhs, rhs, lhsType, lhs.info)

    dfvInGetVal = cast(Callable[[VarNameT], dfv.ComponentL], dfvIn.getVal)
    outDfvValues: Dict[VarNameT, dfv.ComponentL] = {}

    if isinstance(lhsType, RecordT):
      outDfvValues = self.processLhsRhsRecordType(lhs, rhs, dfvIn)

    elif self.L.isAcceptedType(lhsType):
      func = self.func
      lhsVarNames = self.getExprLValueNames(func, lhs, dfvIn)
      # assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
      mustUpdate = len(lhsVarNames) == 1

      rhsDfv = self.getExprDfv(rhs, dfvIn, calleeBi)

      if rhsDfv.bot and util.VV2 and type(self).__name__ == "PointsToA":
        print(f"BOT_RHS_PTR (PointsToA): ({self.func.name}) {lhs} = {rhs} ({lhs.info})")

      if util.LL5: LDB("Analysis %s: RhsDfvOfExpr: '%s' (type: %s) is %s,"
                       " lhsVarNames are %s",
                       self.overallTop.anName, rhs, rhs.type, rhsDfv, lhsVarNames)
      if not len(lhsVarNames):
        if util.VV1: print(f"NO_LVALUE_NAMES: {self.__class__.__name__},"
                           f" {func.name}, {lhs} = {rhs}, {lhs.info}")
        if util.LL5: LWR(f"NO_LVALUE_NAMES: {self.__class__.__name__},"
                         f" {func.name}, {lhs} = {rhs}, {lhs.info}"
                         f"\n  Hence treating it as NopI.")
        return NodeDfvL(dfvIn, dfvIn)  # i.e. NopI

      for name in lhsVarNames: # loop enters only once if mustUpdate == True
        newVal, oldVal = rhsDfv, dfvInGetVal(name)
        if not mustUpdate or nameHasArray(func, name) or nameHasPpmsVar(name):
          newVal, _ = oldVal.meet(newVal) # do a may update
        if newVal != oldVal:
          outDfvValues[name] = newVal

    callNode = False  #IPA
    if isinstance(rhs, expr.CallE):
      if calleeBi: #IPA
        calleeOut = calleeBi.dfvOut
        newOut = calleeOut.localize(self.func)
        if util.LL5: LDB("CallerCallSiteDfv(Out:noLocals): %s", newOut)
        newOut.addLocals(dfvIn)
        if util.LL5: LDB("CallerCallSiteDfv(Out:withLocals): %s", newOut)
        nodeDfv = NodeDfvL(dfvIn, newOut)
        callNode = True  #IPA
      else: #INTRA
        outDfvValues.update(self.processCallE(rhs, dfvIn))

    nDfv = self.genNodeDfvL(outDfvValues, nodeDfv, callNode)
    return nDfv


  def getExprLValueNames(self,
      func: constructs.Func,
      lhs: expr.ExprET,
      dfvIn: dfv.OverallL
  ) -> Set[VarNameT]:
    """Points-to analysis overrides this function."""
    return getNamesLValuesOfExpr(func, lhs)


  def genNodeDfvL(self,
      outDfvValues: Dict[VarNameT, dfv.ComponentL],
      nodeDfv: NodeDfvL,
      callNode: bool = False, #IPA True if the node has a call expression
  ) -> NodeDfvL:
    """A convenience function to create and return the NodeDfvL.
    When callNode == True, don't copy dfvIn
    but directly work on the dfvOut.
    """
    dfvIn = newOut = nodeDfv.dfvIn
    if callNode: #IPA
      newOut = nodeDfv.dfvOut
      if outDfvValues:
        newOutSetVal = newOut.setVal
        for name, value in outDfvValues.items():
          newOutSetVal(name, value) # modify the out in-place
    else: #INTRA
      if outDfvValues:
        newOut = cast(dfv.OverallL, dfvIn.getCopy())
        newOutSetVal = newOut.setVal
        for name, value in outDfvValues.items():
          newOutSetVal(name, value)
    return NodeDfvL(dfvIn, newOut)


  def processLhsRhsRecordType(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      dfvIn: dfv.OverallL,
  ) -> Dict[VarNameT, dfv.ComponentL]:
    """Processes assignment instruction with RecordT"""
    instrType = lhs.type
    assert isinstance(instrType, RecordT), f"{lhs}, {rhs}: {instrType}"

    dfvInGetVal: Callable[[VarNameT], dfv.ComponentL] = dfvIn.getVal

    lhsVarNames = self.getExprLValueNames(self.func, lhs, dfvIn)
    if not len(lhsVarNames):
      if util.VV1: print(f"NO_LVALUE_NAMES: {self.__class__.__name__},"
                         f" {self.func.name}, {lhs}, {lhs.info}")
      if util.LL2: LWR(f"NO_LVALUE_NAMES: {self.__class__.__name__},"
                       f" {self.func.name}, {lhs}, {lhs.info}"
                       f"\n  Hence treating it as NopI.")
      return {}  # i.e. NopI
    # assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
    mustUpdate: bool = len(lhsVarNames) == 1

    rhsVarNames = None
    if not isinstance(rhs, expr.CallE):  # IMPORTANT
      # call expression don't yield rhs names
      rhsVarNames = getExprRValueNames(self.func, rhs)
      if not len(rhsVarNames):
        if util.VV1: print(f"NO_RVALUE_NAMES: {self.__class__.__name__},"
                           f" {self.func.name}, {rhs}, {rhs.info}")
        if LS: LWR(f"NO_RVALUE_NAMES: {self.__class__.__name__},"
                   f" {self.func.name}, {rhs}, {rhs.info}"
                   f"\n  Hence treating it as NopI.")
        return {}  # i.e. NopI

    allMemberInfo = instrType.getNamesOfType(None)
    outDfvValues: Dict[VarNameT, dfv.ComponentL] = {}
    isAcceptedType, func = self.L.isAcceptedType, self.func
    for memberInfo in filter(lambda x: isAcceptedType(x.type), allMemberInfo):
      memName = memberInfo.name
      for lhsName in lhsVarNames:
        if rhsVarNames is not None:  # None only if rhs is CallE
          rhsDfv = mergeAll(  # merge all rhs dfvs of the same member
            dfvInGetVal(f"{n}.{memName}") for n in rhsVarNames)
        else:
          rhsDfv = self.componentBot #INTRA #FIXME: for #IPA
        fullLhsVarName = f"{lhsName}.{memName}"
        oldLhsDfv = dfvInGetVal(fullLhsVarName)
        if not mustUpdate or nameHasArray(func, fullLhsVarName) or\
            nameHasPpmsVar(fullLhsVarName):
          rhsDfv, _ = oldLhsDfv.meet(rhsDfv)
        if oldLhsDfv != rhsDfv:
          outDfvValues[fullLhsVarName] = rhsDfv
    return outDfvValues


  def processCallE(self, #INTRA only for intra-procedural
      e: expr.ExprET,
      dfvIn: DataLT,
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

    names = getNamesPossiblyModifiedInCallExpr(self.func, e)
    names = filterNames(self.func, names, self.L.isAcceptedType)

    if util.LL5: LDB(" OverApproximating: %s", list(sorted(names)))

    bot, dfvInGetVal = self.componentBot, dfvIn.getVal
    outDfvValues: Dict[VarNameT, dfv.ComponentL]\
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
      dfvIn: dfv.OverallL,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> dfv.ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects that the rhs is a non-record type.
    (Record type expressions are handled separately.)
    """
    assert not isinstance(e.type, RecordT), f"{e}, {e.type}, {e.info}"
    dfvInGetVal = cast(Callable[[VarNameT], dfv.ComponentL], dfvIn.getVal)

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
      return self.getExprDfvCallE(e, calleeBi)

    raise ValueError(f"{e}, {self.__class__}")


  def getExprDfvLitE(self,
      e: expr.LitE,
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    raise NotImplementedError()


  def getExprDfvVarE(self,
      e: expr.VarE,
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    return dfvInGetVal(e.name)


  def getExprDfvDerefE(self,
      e: expr.DerefE,
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    return self.componentBot
    # varNames = getExprRValueNames(self.func, e)
    # assert varNames, f"{e}, {varNames}"
    # return mergeAll(map(dfvInGetVal, varNames))


  def getExprDfvCastE(self,
      e: expr.CastE,
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation"""
    assert isinstance(e.arg, expr.VarE), f"{e}"
    if self.L.isAcceptedType(e.arg.type):
      return dfvInGetVal(e.arg.name) #FIXME: very loose
    else:
      return self.componentBot


  def getExprDfvSizeOfE(self,
      e: expr.SizeOfE,
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    return self.componentBot


  def getExprDfvUnaryE(self,
      e: expr.UnaryE,
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
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
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation (assuming Constant Propagation)."""
    if e.hasDereference():
      return self.componentBot
    varNames = getExprRValueNames(self.func, e)
    assert varNames, f"{e}, {varNames}"
    return mergeAll(map(dfvInGetVal, varNames))


  def getExprDfvMemberE(self,
      e: expr.MemberE,
      dfvInGetVal: Callable[[VarNameT], dfv.ComponentL],
  ) -> dfv.ComponentL:
    """A default implementation"""
    return self.componentBot  # since e.hasDereference() == True
    # varNames = getExprRValueNames(self.func, e)
    # assert varNames, f"{e}, {varNames}"
    # return mergeAll(map(dfvInGetVal, varNames))


  def getExprDfvCallE(self,
      e: expr.CallE,
      calleeBi: Opt[NodeDfvL] = None,  #IPA
  ) -> dfv.ComponentL:
    """A default implementation."""
    tUnit: TranslationUnit = self.func.tUnit
    calleeName = e.getFuncName()

    if not calleeBi or not calleeName: return self.componentBot

    outCalleeBi = calleeBi.dfvOut
    calleeFuncObj = tUnit.getFuncObj(calleeName)
    returnExprList: Opt[List[expr.SimpleET]] = \
      calleeFuncObj.getReturnExprList()

    if not returnExprList: return self.componentBot

    val, selfGetExprDfv = self.componentTop, self.getExprDfv
    valIter = [selfGetExprDfv(e, outCalleeBi) for e in returnExprList]
    mVal = mergeAll(valIter)
    return mVal


  def filterValues(self,
      e: expr.ExprET,
      values: Set[T],
      dfvIn: dfv.OverallL,
      valueType: ValueTypeT = NumValue,
  ) -> Set[T]:
    """Depends on `self.filterTest`."""
    assert values is not None, f"{dfvIn.func.name}, {e}, {e.info}"
    if not values:
      return values  # returns an empty set
    exprVal = self.getExprDfv(e, dfvIn)
    if exprVal.bot:   return values
    elif exprVal.top: return SimPending
    else:
      assert exprVal.val is not None, f"{e}, {exprVal}, {dfvIn}"
      return set(filter(self.filterTest(exprVal, valueType), values))


  def filterTest(self,
      exprVal: dfv.ComponentL,
      valueType: ValueTypeT = NumValue,
  ) -> Callable[[T], bool]:
    """Filter out values that are not agreeable."""
    return lambda x: True


  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : Value_analysis
################################################

