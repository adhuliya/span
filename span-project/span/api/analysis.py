#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""The analysis interface."""

import logging
LOG = logging.getLogger(__name__)
LDB, LWR, LER = LOG.debug, LOG.warning, LOG.error

from typing import List, Tuple, Set, Dict, Any, Type, Callable, cast, TypeVar
from typing import Optional as Opt
import io
from bisect import insort as bisectInsort

from span.ir.tunit import TranslationUnit
from span.util import ff

import span.util.util as util
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
  OLD_IN_OUT, NEW_IN_ONLY, DfvPairL, ChangePairL,
)
import span.api.dfv as dfv
from span.api.lattice import ChangedT, Changed, DataLT, mergeAll, DataLT_T

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

  __slots__ : List[str] = ["nodes", "postOrder", "useDdm", "wl", "isNop",
               "valueFilter", "wlNodesSet", "allNidSet", "visitedSeq",
               "totalNodes", "sign"]

  def __init__(self,
      nodes: Dict[cfg.CfgNodeId, cfg.CfgNode],
      postOrder: bool = False,  # True = revPostOrder
  ):
    self.nodes = nodes
    self.totalNodes = len(self.nodes) # total nodes in self.nodes
    self.postOrder = postOrder
    self.sign = 1 if self.postOrder else -1

    nodeIds = nodes.keys()
    self.allNidSet = set(nodeIds)  # the set of all nodes on which to work
    self.wl: List[cfg.CfgNodeId] = [nid * self.sign for nid in nodeIds]
    self.wl.sort()
    self.wlNodesSet = set(nodeIds)

    self.useDdm = False #DDM
    self.isNop = [False for i in range(self.totalNodes + 1)] #DDM
    self.valueFilter = [] #DDM

    # Sequence of nodes visited from start to end of the analysis.
    # A zero value indicates that the work list became empty.
    # A negative value indicates that the node was treated as NOP.
    self.visitedSeq: List[int] = []


  def clear(self):
    """Clear the work list."""
    self.wl.clear()
    self.wlNodesSet.clear()
    self.allNidSet.clear()


  def pop(self) -> Tuple[Opt[cfg.CfgNode], Opt[bool], Opt[Any]]:
    """Pops and returns next node id on top of queue, None otherwise."""
    if not self.wl:
      self.visitedSeq.append(0) # special value to denote wl consumed
      return None, None, None

    nid = self.wl.pop() * self.sign
    self.wlNodesSet.remove(nid)

    if self.useDdm:
      nodeIsNop = self.isNop[nid]
      self.visitedSeq.append(nid * -1 if nodeIsNop else nid)
      return self.nodes[nid], nodeIsNop, self.valueFilter[nid]
    else:
      self.visitedSeq.append(nid)
      return self.nodes[nid], False, None


  def add(self,
      node: cfg.CfgNode,
  ) -> bool:
    """Add a node to the queue."""
    nid = node.id
    attemptAdd = nid in self.allNidSet

    if attemptAdd and nid not in self.wlNodesSet:
      bisectInsort(self.wl, nid * self.sign)
      self.wlNodesSet.add(nid)
      if util.LL5: LDB("AddedNodeToWl: Node_%s: Yes. %s", node.id, node.insn)
      return True

    if util.LL5: LDB("AddedNodeToWl: Node_%s: No."
                     " (Attempted: %s, AlreadyPresent: %s). %s",
                     node.id, attemptAdd, nid in self.wlNodesSet, node.insn)
    return False


  def initForDdm(self):  #DDM
    """Initialization for DD method."""
    self.useDdm = True
    self.clear()
    # Index 0 is unused.
    self.isNop = [True for i in range(self.totalNodes + 1)]
    self.valueFilter = [None for i in range(self.totalNodes + 1)]


  def updateNodeMap(self,  #DDM
      nodeMap: Opt[Dict[cfg.CfgNode, Any]]  # node -> span.sys.ddm.NodeInfo
  ) -> bool:
    """Used by #DDM"""
    if not nodeMap: return False  # i.e. no change

    if util.LL5: LDB("UpdatedNodeMap(AddingMap): %s", nodeMap)

    changed, nopChanged, valueFilterChanged = False, False, False
    for node, nInfo in nodeMap.items():
      treatAsNop = nInfo.nop
      nid = node.id
      if nid not in self.allNidSet:  # a fresh node
        if nid not in self.wlNodesSet:
          bisectInsort(self.wl, nid * self.sign)
          self.wlNodesSet.add(nid)
        self.allNidSet.add(nid)
        self.isNop[nid] = treatAsNop and self.isNop[nid]
        self.valueFilter[nid] = nInfo.varNameSet
        changed = True
      else:  # a known node
        isNop = self.isNop[nid]
        if not treatAsNop and isNop:
          self.isNop[nid] = False
          nopChanged = True
        if self.valueFilter[nid] != nInfo.varNameSet:
          self.valueFilter[nid] = nInfo.varNameSet
          valueFilterChanged = True
        if nopChanged or valueFilterChanged:
          if nid not in self.wlNodesSet:
            bisectInsort(self.wl, nid * self.sign)
            self.wlNodesSet.add(nid)
            changed = True

    return changed or nopChanged or valueFilterChanged


  def getWorkingNodesString(self, allNodes=False) -> str:
    """Returns a string representation of the work list."""
    if allNodes:
      nodeIds = [nid * self.sign for nid in self.allNidSet]
      nodeIds.sort()
    else:
      nodeIds = self.wl

    listType = "(All)" if allNodes else ""

    prefix = ""
    with io.StringIO() as sio:
      sio.write("#DDM " if self.useDdm else "")
      sio.write(f"NodeWorkList{listType} [")
      for nid in nodeIds:
        nid = nid * self.sign
        nop = f"nop({nid})" if self.isNop[nid] else f"{nid}"
        sio.write(f"{prefix}{nop}")
        if not prefix: prefix = ", "
      sio.write("]")
      prefix = sio.getvalue()  # reusing prefix
    return prefix


  def getAllNodesStr(self) -> str:
    """Returns a string representation of the work list."""
    return self.getWorkingNodesString(allNodes=True)


  def __str__(self):
    return self.getWorkingNodesString()


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
      anName: AnNameT,
      func: constructs.Func,
      top: DataLT,
  ) -> None:
    if type(self).__name__ == "DirectionT":
      super().__init__()
    self.cfg = func.cfg
    self.anResult: dfv.AnResult = dfv.AnResult(anName, func, top)
    self.topNdfv: DfvPairL = DfvPairL(top, top)
    for nid in self.cfg.nodeMap.keys():
      self.anResult[nid] = self.topNdfv
    # set this to true once boundary values are initialized
    self.boundaryInfoInitialized = False
    self.fwl: Opt[FastNodeWorkList] = None # initialize in sub-class


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
      nodeDfv: DfvPairL,
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
      nodeDfv = DfvPairL(newIn, newOut)  # nodeDfv OVER-WRITTEN
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
    """Add node to the work list."""
    assert self.fwl is not None
    added = self.fwl.add(node)
    return added


  def calcInOut(self,
      node: cfg.CfgNode,
      fesEdges: cfg.FeasibleEdges
  ) -> Tuple[DfvPairL, ChangePairL]:
    """Merges dfv from feasible edges."""
    raise NotImplementedError()


  def getDfv(self,
      nodeId: cfg.CfgNodeId
  ) -> DfvPairL:
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
    self.fwl = self.generateInitialWorklist()  # important


  def generateInitialWorklist(self) -> FastNodeWorkList:
    """Defaults to reverse post order."""
    fwl = FastNodeWorkList(self.cfg.nodeMap, postOrder=False)
    if util.LL4: LDB("  Forward_Worklist_Init: %s", fwl)
    return fwl


  def update(self,
      node: cfg.CfgNode,
      nodeDfv: DfvPairL,
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
        self.fwl.add(dest)

    return inOutChange


  def calcInOut(self,
      node: cfg.CfgNode,
      fesEdges: cfg.FeasibleEdges
  ) -> Tuple[DfvPairL, ChangePairL]:
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
      f = fesEdges.isFeasibleEdge(predEdge)
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
    newNodeDfv = DfvPairL(newIn, ndfv.dfvOut)
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
    self.fwl = self.generateInitialWorklist()  # important


  def generateInitialWorklist(self) -> FastNodeWorkList:
    """Defaults to reverse post order."""
    fwl = FastNodeWorkList(self.cfg.nodeMap, postOrder=True)
    if util.LL0: LDB("Backward_Worklist_Init: %s", fwl)
    return fwl


  def update(self,
      node: cfg.CfgNode,
      nodeDfv: DfvPairL,
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
        if util.LL0: LDB("AddingNodeToWl(pred): Node_%s: %s (%s)",
                         pred.id, pred.insn, pred.insn.info)
        self.fwl.add(pred)

    return inOutChange


  def calcInOut(self,
      node: cfg.CfgNode,
      fesEdges: cfg.FeasibleEdges
  ) -> Tuple[DfvPairL, ChangePairL]:
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
      f = fesEdges.isFeasibleEdge(succEdge)
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
    newNodeDfv = DfvPairL(ndfv.dfvIn, newOut)
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
  """
  A super-class of all the analyses in the system.
  One instance of this class is created for each fresh analysis of a function.

  For bi-directional analyses, subclass this class directly.
  """

  __slots__ : List[str] = ["func", "overallTop", "overallBot"]

  # concrete lattice class of the analysis
  L: Type[DataLT_T] = DataLT
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
    self.overallTop = self.L(func, top=True)
    self.overallBot = self.L(func, bot=True)  # L is callable. pylint: disable=E


  def getBoundaryInfo(self,
      nodeDfv: Opt[DfvPairL] = None,
      ipa: bool = False,
      entryFunc: bool = False,
      forFunc: Opt[constructs.Func] = None,
  ) -> DfvPairL:
    """Must generate a valid boundary info."""
    if ipa: raise NotImplementedError()  # for IPA override this function

    inBi, outBi = self.overallBot, self.overallBot
    if nodeDfv: inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
    return DfvPairL(inBi, outBi)  # good to create a copy


  def getLocalizedCalleeBi(self, #IPA
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    """Computes the value context of the callee, given
    the data flow value of the caller."""
    raise NotImplementedError


  # BOUND START: special_instructions_seven

  def Any_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    """For any SPAN IR instruction.
    Default behaviour is to delegate the control to specialized functions.
    """
    if isinstance(insn, instr.AssignI):
      return self.Assign_Instr(nodeId, insn, nodeDfv, calleeBi)
    elif isinstance(insn, instr.NopI):
      return self.Nop_Instr(nodeId, insn, nodeDfv)
    elif isinstance(insn, instr.ReturnI):
      return self.Return_Instr(nodeId, insn, nodeDfv)
    elif isinstance(insn, instr.CondI):
      return self.Conditional_Instr(nodeId, insn, nodeDfv)
    elif isinstance(insn, instr.CallI):
      return self.Call_Instr(nodeId, insn, nodeDfv, calleeBi)
    elif isinstance(insn, instr.BarrierI):
      return self.Barrier_Instr(nodeId, insn, nodeDfv)
    elif isinstance(insn, instr.LiveLocationsI):
      return self.LiveLocations_Instr(nodeId, insn, nodeDfv)
    elif isinstance(insn, instr.CondReadI):
      return self.CondRead_Instr(nodeId, insn, nodeDfv)
    elif isinstance(insn, instr.UnDefValI):
      return self.UnDefVal_Instr(nodeId, insn, nodeDfv)
    elif isinstance(insn, instr.UseI):
      return self.Use_Instr(nodeId, insn, nodeDfv)
    elif isinstance(insn, instr.ExReadI):
      return self.ExRead_Instr(nodeId, insn, nodeDfv)
    else:
      raise ValueError(f"Node_{nodeId}: {self.func}, {insn}")


  def Default_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    """The default behaviour for unimplemented instructions.
    Analysis should override this method if unimplemented
    instructions have to be handled in a way other than
    like a NOP instruction.
    """
    return self.Nop_Instr(nodeId, insn, nodeDfv)


  def Nop_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    """Instr_Form: void: NopI()."""
    D = self.D

    if D == Forward:
      dfvIn = nodeDfv.dfvIn
      if dfvIn is nodeDfv.dfvOut:
        return nodeDfv
      else:
        return DfvPairL(dfvIn, dfvIn)

    elif D == Backward:
      dfvOut = nodeDfv.dfvOut
      if dfvOut is nodeDfv.dfvIn:
        return nodeDfv
      else:
        return DfvPairL(dfvOut, dfvOut)

    else: # ForwBack?
      raise ValueError("ForwBack NOP not defined!")


  def Barrier_Instr(self,
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: DfvPairL,
  ) -> DfvPairL:
    """Data Flow information is blocked from travelling
    from IN-to-OUT and OUT-to-IN.

    This implementation works for *any* direction analysis.
    """
    return nodeDfv  # no information travels from IN to OUT or OUT to IN


  def Use_Instr(self,
      nodeId: NodeIdT,
      insn: instr.UseI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    """Instr_Form: void: UseI(x).
    Value of x is read from memory."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def ExRead_Instr(self,
      nodeId: NodeIdT,
      insn: instr.ExReadI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    """Instr_Form: void: ExReadI(x).
    x and only x is read, others are forcibly
    marked as not read (in backward direction)."""
    return self.Barrier_Instr(nodeId, insn, nodeDfv)


  def CondRead_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CondReadI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    """Instr_Form: void: CondReadI(x, {y, z}).
    y and z are read if x is read."""
    return self.Barrier_Instr(nodeId, insn, nodeDfv)


  def UnDefVal_Instr(self,
      nodeId: NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    """Instr_Form: void: input(x). (user supplies value of x)
    Thus value of x is undefined."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def LiveLocations_Instr(self,
      nodeId: NodeIdT,
      insn: instr.LiveLocationsI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    """Instr_Form: void: FilterI({x,y,z}).
    x,y,z are known to be dead after this program point.
    TODO: change the semantics of this instruction to state only live variables.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  # BOUND END  : special_instructions_seven

  # BOUND START: regular_instructions
  # BOUND START: regular_insn__when_lhs_is_var

  def Assign_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    """Instr_From: expr1 = expr2."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Call_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CallI,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    """Instr_Form: void: func(args...) (just a call statement).
    Convention:
      args are either a variable, a literal or addrof expression.
    """
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Return_Instr(self,
      nodeId: NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    """Instr_Form: A return instruction with or without a value."""
    return self.Default_Instr(nodeId, insn, nodeDfv)


  def Conditional_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CondI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
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

  The second argument, nodeDfv, if its None,
  means that the return value should be either
  empty set (i.e. Pending) if the expression provided
  can be possibly simplified by the analysis,
  or Failed if the expression cannot be simplified
  given any data flow value.
  """

  def Node__to__Nil(self,
      nodeId: NodeIdT,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[bool] = None,
  ) -> Opt[Set[bool]]:
    """Node is simplified to Nil if its basically unreachable."""
    raise NotImplementedError()


  def LhsVar__to__Nil(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[List[bool]] = None,
  ) -> Opt[Set[bool]]:
    """Returns a set of live variables at out of the node."""
    raise NotImplementedError()


  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[List[NumericT]] = None,
  ) -> Opt[Set[NumericT]]:
    """Simplify to a single literal if the variable can take that value."""
    raise NotImplementedError()


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[List[NumericT]] = None,
  ) -> Opt[Set[NumericT]]:
    """Simplify to a single literal if the expr can take that value."""
    raise NotImplementedError()


  def Deref__to__Vars(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[List[VarNameT]] = None
  ) -> Opt[Set[VarNameT]]:
    """Simplify a deref expr de-referencing varName
    to a set of var pointees."""
    raise NotImplementedError()


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[DfvPairL] = None,
      values: Opt[bool] = None,
  ) -> Opt[Set[bool]]:
    """Simplify conditional jump to unconditional jump."""
    raise NotImplementedError()


  ################################################
  # BOUND END  : sim_related 2/3
  ################################################

AnalysisAT_T = TypeVar('AnalysisAT_T', bound=AnalysisAT)

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
  L: Type[dfv.OverallL_T] = dfv.OverallL  # the OverallL lattice used
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
      nodeDfv: Opt[DfvPairL] = None, # needs to be localized to the target func
      ipa: bool = False,  #IPA
      entryFunc: bool = False,
      forFunc: Opt[constructs.Func] = None,
  ) -> DfvPairL:
    """
      * IPA/Intra: initialize all local (non-parameter) vars to Top.
      * IPA: initialize all non-initialized globals to their default values
        only at the entry of the main function.
      * Intra: initialize all globals to Bot. (as is done currently)
    """
    if ipa and not nodeDfv:
      raise ValueError(f"{ipa}, {nodeDfv}")

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
      tUnitGetNameInfo = tUnit.getNameInfo
      inBiGetVal, inBiSetVal = inBi.getVal, inBi.setVal

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

      if entryFunc: # i.e. main() function
        for vName in func.paramNames: # then set its parameters to Bot
          if self.L.isAcceptedType(tUnitGetNameInfo(vName).type):
            inBiSetVal(vName, compBot)
        for vName in self.L.getAllVars(self.func):
          if conv.isGlobalName(vName):
            val = inBiGetVal(vName)
            # Set top global vars to their default initialization value.
            # As only uninitialized globals may have top values.
            if val.top:
              inBiSetVal(vName, inBi.getDefaultValForGlobal())

    nDfv1 = DfvPairL(inBi, outBi)
    return nDfv1


  def getLocalizedCalleeBi(self, #IPA
      nodeId: NodeIdT,
      insn: instr.InstrIT,
      nodeDfv: DfvPairL,  # caller's node IN/OUT
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
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

    localized = DfvPairL(newDfvIn, outDfv)
    localized = self.getBoundaryInfo(localized, ipa=True, forFunc=calleeFuncObj)
    if util.LL0: LDB("CalleeCallSiteDfv(Localized): %s", localized)
    return localized


  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def LiveLocations_Instr(self,
      nodeId: NodeIdT,
      insn: instr.LiveLocationsI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    varNames = insn.varNames

    if not varNames or dfvIn.top:  # i.e. nothing to filter or no DFV to filter == Nop
      return DfvPairL(dfvIn, dfvIn)  # = NopI

    newDfvOut = dfvIn.getCopy()
    newDfvOut.filterVals(varNames)
    return DfvPairL(dfvIn, newDfvOut)


  def UnDefVal_Instr(self,
      nodeId: NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    if not self.L.isAcceptedType(insn.type):
      return self.Default_Instr(nodeId, insn, nodeDfv)
    newOut = dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    if not dfvIn.getVal(insn.lhsName).bot:
      newOut = dfvIn.getCopy()
      newOut.setVal(insn.lhsName, self.componentBot)
    return DfvPairL(dfvIn, newOut)


  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################

  def Assign_Instr(self,
      nodeId: NodeIdT,
      insn: instr.AssignI,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    return self.processLhsRhs(nodeId, insn.lhs, insn.rhs, nodeDfv, calleeBi)


  def Conditional_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CondI,
      nodeDfv: DfvPairL
  ) -> DfvPairL:
    dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    if not self.L.isAcceptedType(insn.arg.type):  # special case
      return DfvPairL(dfvIn, dfvIn)
    outDfvFalse, outDfvTrue = self.calcFalseTrueDfv(insn.arg, dfvIn)
    return DfvPairL(dfvIn, None, outDfvTrue, outDfvFalse)


  def Call_Instr(self,
      nodeId: NodeIdT,
      insn: instr.CallI,
      nodeDfv: DfvPairL,
      calleeBi: Opt[DfvPairL] = None,  #IPA
  ) -> DfvPairL:
    dfvIn = cast(dfv.OverallL, nodeDfv.dfvIn)
    if not calleeBi: #INTRA handle intra-procedurally
      return self.genNodeDfvL(
        self.processCallE(insn.arg, dfvIn, nodeId), nodeDfv)
    else: # handle for #IPA
      newOut = calleeBi.dfvOut.localize(self.func)
      newOut.addLocals(dfvIn)
      return DfvPairL(dfvIn, newOut)


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
      outDfvValues = self.processLhsRhsRecordType(nodeId, lhs, rhs, dfvIn)

    elif self.L.isAcceptedType(lhsType):
      func = self.func
      lhsVarNames = self.getExprLValueNames(func, lhs, dfvIn)
      # assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
      mustUpdate = len(lhsVarNames) == 1

      rhsDfv = self.getExprDfv(rhs, dfvIn, calleeBi)

      if util.LL5: LDB("Analysis %s: RhsDfvOfExpr: '%s' (type: %s) is %s,"
                       " lhsVarNames are %s",
                       self.overallTop.anName, rhs, rhs.type, rhsDfv, lhsVarNames)
      if not len(lhsVarNames):
        if util.VV1: print(f"NO_LVALUE_NAMES: {self.__class__.__name__},"
                           f" {func.name}, {lhs} = {rhs}, {lhs.info}")
        if util.LL5: LWR(f"NO_LVALUE_NAMES: {self.__class__.__name__},"
                         f" {func.name}, {lhs} = {rhs}, {lhs.info}"
                         f"\n  Hence treating it as NopI.")
        return DfvPairL(dfvIn, dfvIn)  # i.e. NopI

      for name in lhsVarNames: # loop enters only once if mustUpdate == True
        newVal = self.computeLhsDfvFromRhs(
          name, rhsDfv, dfvIn, nodeId, mustUpdate
        )
        if newVal:
          outDfvValues[name] = newVal

    callNode = False  #IPA
    if isinstance(rhs, expr.CallE):
      if calleeBi: #IPA
        calleeOut = calleeBi.dfvOut
        newOut = calleeOut.localize(self.func)
        if util.LL5: LDB("CallerCallSiteDfv(Out:noLocals): %s", newOut)
        newOut.addLocals(dfvIn)
        if util.LL5: LDB("CallerCallSiteDfv(Out:withLocals): %s", newOut)
        nodeDfv = DfvPairL(dfvIn, newOut)
        callNode = True  #IPA
      else: #INTRA
        outDfvValues.update(self.processCallE(rhs, dfvIn, nodeId))

    nDfv = self.genNodeDfvL(outDfvValues, nodeDfv, callNode)
    return nDfv


  def processLhsRhsRecordType(self,
      nodeId: NodeIdT,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      dfvIn: dfv.OverallL,
  ) -> Dict[VarNameT, dfv.ComponentL]:
    """Processes assignment instruction with RecordT"""
    instrType = lhs.type
    assert isinstance(instrType, RecordT), f"{lhs}, {rhs}: {instrType}"

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
        if util.LL0: LWR(f"NO_RVALUE_NAMES: {self.__class__.__name__},"
                   f" {self.func.name}, {rhs}, {rhs.info}"
                   f"\n  Hence treating it as NopI.")
        return {}  # i.e. NopI

    allMemberInfo = instrType.getNamesOfType(None)
    outDfvValues: Dict[VarNameT, dfv.ComponentL] = {}
    isAcceptedType, func = self.L.isAcceptedType, self.func
    for memberInfo in filter(lambda x: isAcceptedType(x.type), allMemberInfo):
      memName = memberInfo.name
      for lhsName in lhsVarNames:
        fullLhsVarName = f"{lhsName}.{memName}"
        rhsDfv = self.computeLhsDfvFromRhsNames(
          rhsVarNames, memName, fullLhsVarName, dfvIn, nodeId, mustUpdate=False)
        if rhsDfv:
          outDfvValues[fullLhsVarName] = rhsDfv
    return outDfvValues


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
    if not mustUpdate or nameHasArray(dfvIn.func, lhsName) or nameHasPpmsVar(lhsName):
      newVal, _ = oldVal.meet(newVal) # do a may update

    return newVal if newVal != oldVal else None


  def computeLhsDfvFromRhsNames(self,
      rhsVarNames: Opt[Set[VarNameT]],
      memName: types.MemberNameT,
      fullLhsVarName: VarNameT,
      dfvIn: dfv.OverallL,
      nodeId: NodeIdT,
      mustUpdate: bool,
  ) -> Opt[dfv.ComponentL]:
    """Computes the combined DFV of RHS names with a record type.

    Given a set of RHS names and a member, it computes
    the combined DFV of all the `name.member` possible.
    """
    dfvInGetVal: Callable[[VarNameT], dfv.ComponentL] = dfvIn.getVal

    if rhsVarNames is not None:  # None only if rhs is CallE
      rhsDfv = mergeAll(  # merge all rhs dfvs of the same member
        dfvInGetVal(f"{n}.{memName}") for n in rhsVarNames)
    else:
      rhsDfv = self.componentBot #INTRA #FIXME: for #IPA

    oldLhsDfv = dfvInGetVal(fullLhsVarName)
    if not mustUpdate or nameHasArray(dfvIn.func, fullLhsVarName) or \
        nameHasPpmsVar(fullLhsVarName):
      rhsDfv, _ = oldLhsDfv.meet(rhsDfv)

    rhsDfv = rhsDfv if oldLhsDfv != rhsDfv else None

    return rhsDfv


  def getExprLValueNames(self,
      func: constructs.Func,
      lhs: expr.ExprET,
      dfvIn: dfv.OverallL
  ) -> Set[VarNameT]:
    """Points-to analysis overrides this function."""
    return getNamesLValuesOfExpr(func, lhs)


  def genNodeDfvL(self,
      outDfvValues: Dict[VarNameT, dfv.ComponentL],
      nodeDfv: DfvPairL,
      callNode: bool = False, #IPA True if the node has a call expression
  ) -> DfvPairL:
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
    return DfvPairL(dfvIn, newOut)


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
      calleeBi: Opt[DfvPairL] = None,  #IPA
      nodeId: NodeIdT = 0,  # This parameter is used by the subclasses
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
      calleeBi: Opt[DfvPairL] = None,  #IPA
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

