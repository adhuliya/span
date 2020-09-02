#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Program abstraction as control flow graph, call graph etc."""

import logging

LOG = logging.getLogger("span")
from typing import List, Dict, Set, Tuple
from typing import Optional as Opt
import io

from span.util.logger import LS
import span.ir.instr as instr
import span.ir.expr as expr
from span.ir.types import EdgeLabelT, BasicBlockIdT, FuncNameT
from span.ir.conv import FalseEdge, TrueEdge, UnCondEdge
import span.ir.types as types
import span.util.messages as msg

from span.util.messages import START_BB_ID_NOT_MINUS_ONE, END_BB_ID_NOT_ZERO
import span.util.util as util

# Type names to make code self documenting
CfgNodeId = int
CfgEdgeId = int
MinHeightT = int


class CfgEdge:
  """A directed edge (with label) between two CfgNodes."""

  __slots__ : List[str] = ["src", "dest", "label"]

  def __init__(self,
      src: 'CfgNode',
      dest: 'CfgNode',
      label: EdgeLabelT = UnCondEdge,
  ) -> None:
    self.src = src
    self.dest = dest
    self.label = label


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, CfgEdge):
      return NotImplemented
    return self.src == other.src and self.dest == other.dest


  def __hash__(self): return self.src.id + self.dest.id


  def __str__(self): return self.__repr__()


  def __repr__(self):
    return f"CfgEdge({self.src}, {self.dest}, {self.label!r})"


class CfgNode(object):
  """A cfg statement node (which contains one and only one instruction).
  """
  __slots__ : List[str] = ["id", "insn", "predEdges", "succEdges"]


  def __init__(self,
      insn: instr.InstrIT,
      predEdges: Opt[List[CfgEdge]] = None,
      succEdges: Opt[List[CfgEdge]] = None,
  ) -> None:
    # The min height of this node from the end node.
    # i.e. min no. of edges between this and end node.
    # Its used for worklist generation.
    # it eventually stores a unique id (within a func)
    self.id: int = 0x7FFFFFFF  # init to infinite
    self.insn = insn
    self.predEdges = predEdges if predEdges else []
    self.succEdges = succEdges if succEdges else []


  def addSucc(self,
      cfgEdge: CfgEdge
  ) -> None:
    """Ensures succ[0] is true edge and succ[1] is false edge"""
    if cfgEdge.label == UnCondEdge:
      self.succEdges.append(cfgEdge)
      return

    # if here then node has True/False succ
    if len(self.succEdges) == 0:
      # create a space for two
      self.succEdges.extend([None, None])  # type: ignore

    assert len(self.succEdges) == 2, msg.INVARIANT_VIOLATED

    if cfgEdge.label == TrueEdge:
      self.succEdges[0] = cfgEdge
    else:
      self.succEdges[1] = cfgEdge


  def addPred(self, edge: CfgEdge):
    self.predEdges.append(edge)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, CfgNode):
      return NotImplemented
    return self.id == other.id


  def __hash__(self) -> int:
    return self.id


  def __str__(self):
    predIds = []
    for predEdge in self.predEdges:
      predIds.append(predEdge.src.id)
    succIds = []
    for succEdge in self.succEdges:
      succIds.append(succEdge.dest.id)
    return f"Node {self.id}: ({self.insn}, pred={predIds}, succ={succIds})"


  def __repr__(self):
    return self.__str__()


class BbEdge:
  """A directed edge (with label) between two BB (Basic Blocks)."""

  __slots__ : List[str] = ["src", "dest", "label"]

  def __init__(self,
      src: 'BB',
      dest: 'BB',
      label: EdgeLabelT = UnCondEdge,
  ) -> None:
    self.src = src
    self.dest = dest
    self.label = label


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, BbEdge):
      return NotImplemented
    return self.src == other.src and self.dest == other.dest


  def __hash__(self): return self.src.id + self.dest.id


  def __str__(self): return self.__repr__()


  def __repr__(self):
    return f"BBEdge({self.src}, {self.dest}, {self.label!r})"


class BB:
  """A Basic Block."""

  __slots__ : List[str] = ["id", "instrSeq", "predEdges", "succEdges", "cfgNodeSeq",
               "firstCfgNode", "lastCfgNode"]

  def __init__(self,
      id: BasicBlockIdT = 0,
      instrSeq: Opt[List[instr.InstrIT]] = None,
      predEdges: Opt[List[BbEdge]] = None,  # predecessor basic blocks
      succEdges: Opt[List[BbEdge]] = None,  # successor basic blocks (zero, one or two only)
  ) -> None:
    self.id = id  # id is user defined (unique within func)
    self.instrSeq = instrSeq
    self.cfgNodeSeq: Opt[List[CfgNode]] = self.genCfgNodeSeq(instrSeq)
    self.predEdges = predEdges if predEdges else []
    self.succEdges = succEdges if succEdges else []

    self.firstCfgNode = self.cfgNodeSeq[0]
    self.lastCfgNode = self.cfgNodeSeq[-1]


  def getSuccEdge(self,
      edgeLabel: EdgeLabelT = UnCondEdge
  ) -> Opt[BbEdge]:
    """Returns the succ edge of the given label (if present)"""
    assert len(self.succEdges) <= 2, msg.INVARIANT_VIOLATED

    if len(self.succEdges) == 1:
      if edgeLabel == UnCondEdge:
        return self.succEdges[0]
      else:
        return None

    succ1, succ2 = self.succEdges[0], self.succEdges[1]

    if succ1.label == edgeLabel:
      return succ1
    elif succ2.label == edgeLabel:
      return succ2

    return None


  def addSucc(self,
      bbEdge: BbEdge
  ) -> None:
    """Ensures succ[0] is true edge and succ[1] is false edge"""
    if bbEdge.label == UnCondEdge:
      self.succEdges.append(bbEdge)
      return

    # if here then bb has True/False succ
    if len(self.succEdges) == 0:
      # create a space for two
      self.succEdges.extend([None,None])  # type: ignore

    assert len(self.succEdges) == 2, msg.INVARIANT_VIOLATED

    if bbEdge.label == TrueEdge:
      self.succEdges[0] = bbEdge
    else:
      self.succEdges[1] = bbEdge


  def genCfgNodeSeq(self,
      instrSeq: Opt[List[instr.InstrIT]]
  ) -> List[CfgNode]:
    """Convert sequence of instructions to sequentially connected CfgNodes."""
    if not instrSeq: return [CfgNode(instr.NopI())]

    # If only one instruction, then its simple.
    if len(instrSeq) == 1: return [CfgNode(instrSeq[0])]

    # For two or more instructions:
    prev = CfgNode(instrSeq[0])
    cfgNodeSeq: List[CfgNode] = [prev]
    for insn in instrSeq[1:]:
      curr = CfgNode(insn)
      edge = CfgEdge(prev, curr, UnCondEdge)
      curr.addPred(edge)
      prev.addSucc(edge)
      cfgNodeSeq.append(curr)
      prev = curr

    return cfgNodeSeq


  def addPred(self, edge: BbEdge):
    self.predEdges.append(edge)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, BB):
      return NotImplemented
    equal = True
    if self.instrSeq and not other.instrSeq:
      equal = False
    elif not self.instrSeq and other.instrSeq:
      equal = False
    elif self.instrSeq and other.instrSeq and\
        not len(self.instrSeq) == len(other.instrSeq):
      equal = False
    elif not self.instrSeq == other.instrSeq:
      equal = False
    return equal


  def isEqual(self,
      other: 'BB'
  ) -> bool:
    equal = True
    if not isinstance(other, BB):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if self.instrSeq and not other.instrSeq:
      equal = False
      if LS: LOG.error("InstrSeqIsNone: other.instrSeq")
    if not self.instrSeq and other.instrSeq:
      equal = False
      if LS: LOG.error("InstrSeqIsNone: self.instrSeq")
    if self.instrSeq and other.instrSeq and \
        not len(self.instrSeq) == len(other.instrSeq):
      equal = False
      if LS: LOG.error("InstrCountsDiffer: %s, %s",
                       len(self.instrSeq), len(other.instrSeq))
    else:
      if self.instrSeq and other.instrSeq:  # None check
        for i in range(len(self.instrSeq)):
          if self.instrSeq[i].isEqual(other.instrSeq[i]):
            equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffers: %s, %s", self, other)

    return equal


  def __str__(self):
    return self.__repr__()


  def __repr__(self):
    return f"BB({self.instrSeq})"


class Cfg(object):
  """A Cfg (the body of a function)"""

  __slots__ : List[str] = ["funcName", "inputBbMap", "inputBbEdges", "startBb",
               "endBb", "start", "end", "bbMap", "nodeMap", "revPostOrder",
               "_nodesWithCall"]

  def __init__(self,
      funcName: FuncNameT,
      inputBbMap: Dict[BasicBlockIdT, List[instr.InstrIT]],
      inputBbEdges: List[Tuple[BasicBlockIdT, BasicBlockIdT, EdgeLabelT]]
  ) -> None:
    self.funcName = funcName
    self.inputBbMap = inputBbMap
    self.inputBbEdges = inputBbEdges

    self.startBb: Opt[BB] = None
    self.endBb: Opt[BB] = None

    self.start: Opt[CfgNode] = None
    self.end: Opt[CfgNode] = None

    self.bbMap: Dict[BasicBlockIdT, BB] = dict()
    self.nodeMap: Dict[CfgNodeId, CfgNode] = dict()
    self.revPostOrder: List[CfgNode] = []

    self._nodesWithCall: Opt[List[CfgNode]] = None

    # fills the variables above correctly.
    self.buildCfgStructure(inputBbMap, inputBbEdges)


  def yieldInsns(self):
    for _, cfgNode in self.nodeMap.items():
      yield cfgNode.insn


  def getNodesWithNonPtrCallExpr(self,
      filterAwayFuncPtrCalls=True
  ) -> Opt[List[CfgNode]]:
    """
    Returns nodes with function calls in them.
    It filters away function calls using pointers.
    """
    if self._nodesWithCall is not None:
      return None if not self._nodesWithCall else self._nodesWithCall

    self._nodesWithCall = []
    for node in self.nodeMap.values():
      callE = instr.getCallExpr(node.insn)
      if callE is not None:
        if filterAwayFuncPtrCalls and callE.isPointerCall():
          continue  # don't add function pointer calls
        self._nodesWithCall.append(node)

    return None if not self._nodesWithCall else self._nodesWithCall


  def buildCfgStructure(self,
      inputBbMap: Dict[BasicBlockIdT, List[instr.InstrIT]],
      inputBbEdges: List[Tuple[BasicBlockIdT, BasicBlockIdT, EdgeLabelT]]
  ) -> None:
    """Builds the complete Cfg structure."""

    assert inputBbMap and inputBbEdges, msg.INVARIANT_VIOLATED
    # -1 is start bb id, 0 is the end bb id (MUST)
    assert -1 in inputBbMap, msg.INVARIANT_VIOLATED
    assert 0 in inputBbMap, msg.INVARIANT_VIOLATED

    # STEP 1: Create BBs in their dict.
    for bbId, instrSeq in inputBbMap.items():
      self.bbMap[bbId] = BB(id=bbId, instrSeq=instrSeq)

    if -1 not in self.bbMap:
      if LS: LOG.error(START_BB_ID_NOT_MINUS_ONE)

    if 0 not in self.bbMap:
      if LS: LOG.error(END_BB_ID_NOT_ZERO)

    self.startBb = self.bbMap[-1]
    self.endBb = self.bbMap[0]
    self.start = self.startBb.firstCfgNode
    self.end = self.endBb.lastCfgNode

    # STEP 2: Based on bbMap and inputBbEdges, interconnect CfgNodes and BBs.
    self.connectNodes(self.bbMap, inputBbEdges)

    # STEP 3: Find the reverse post order sequence of CFG Nodes
    self.revPostOrder = self.calcRevPostOrder()

    # STEP 4: Number the nodes in reverse post order and add to dict
    newId = 0
    for node in self.revPostOrder:
      newId += 1
      node.id = newId
      self.nodeMap[newId] = node


  def connectNodes(self,
      bbMap: Dict[BasicBlockIdT, BB],
      inputBbEdges: List[Tuple[BasicBlockIdT, BasicBlockIdT, EdgeLabelT]]
  ) -> None:
    """Interconnects basic blocks and cfg nodes."""
    for startBbId, endBbId, edgeLabel in inputBbEdges:
      # STEP 2.1: Interconnect BBs with read ids.
      startBb = bbMap[startBbId]
      endBb = bbMap[endBbId]
      bbEdge = BbEdge(startBb, endBb, edgeLabel)
      startBb.addSucc(bbEdge)
      endBb.addPred(bbEdge)

      # STEP 2.2: Connect CfgNodes across basic blocks.
      startNode = startBb.lastCfgNode
      endNode = endBb.firstCfgNode
      cfgEdge = CfgEdge(startNode, endNode, edgeLabel)
      startNode.addSucc(cfgEdge)
      endNode.addPred(cfgEdge)


  def calcMinHeights(self, currNode: CfgNode):
    """Calculates and allocates min_height of each node."""
    newPredHeight = currNode.id + 1
    for predEdge in currNode.predEdges:
      pred = predEdge.src
      currPredHeight = pred.id
      if currPredHeight > newPredHeight:
        pred.id = newPredHeight
        self.calcMinHeights(pred)


  def calcRevPostOrder(self) -> List[CfgNode]:
    if self.end is None or self.start is None:
      raise ValueError()
    self.end.id = 0
    self.calcMinHeights(self.end)
    done = {id(self.start)}
    sequence: List[CfgNode] = []
    worklist: List[Tuple[CfgNodeId, CfgNode]] = [(self.start.id, self.start)]
    return self.genRevPostOrderSeq(sequence, done, worklist)


  def genRevPostOrderSeq(self,
      seq: List[CfgNode],
      done: Set[CfgNodeId],
      worklist: List[Tuple[MinHeightT, CfgNode]]
  ) -> List[CfgNode]:
    if not worklist: return seq
    _, node = worklist.pop()  # get node with max height
    seq.append(node)
    for succEdge in node.succEdges:
      destNode = succEdge.dest
      if id(destNode) not in done:
        destMinHeight = destNode.id
        tup = (destMinHeight, destNode)
        done.add(id(destNode))
        worklist.append(tup)
    worklist.sort(key=lambda x: x[0])
    return self.genRevPostOrderSeq(seq, done, worklist)


  def genDotBbLabel(self,
      bbId: BasicBlockIdT
  ) -> str:
    """Generate BB label to be used in printing dot graph."""
    bbLabel: str = ""
    if bbId == -1:
      bbLabel = "START"
    elif bbId == 0:
      bbLabel = "END"
    else:
      bbLabel = f"BB{bbId}"
    return bbLabel


  def genBbDotGraph(self) -> str:
    """Generates Dot graph of itself at basic block level.
    It assumes the reverse post-order sequence is already set.
    """
    if not self.inputBbMap: return "digraph{}"
    ret = None
    with io.StringIO() as sio:
      sio.write("digraph {\n  node [shape=box]\n")
      for bbId, bb in self.bbMap.items():
        assert bb.cfgNodeSeq is not None
        nodeStrs = [f"{node.id}: {node.insn}" for node in bb.cfgNodeSeq]

        bbLabel: str = self.genDotBbLabel(bbId)
        nodeStrs.insert(0, "[" + bbLabel + "]")

        bbContent = "\\l".join(nodeStrs)
        content = f"  {bbLabel} [label=\"{bbContent}\\l\"];\n"
        sio.write(content)

        for bbEdge in bb.succEdges:
          fromLabel = self.genDotBbLabel(bbEdge.src.id)
          toLabel = self.genDotBbLabel(bbEdge.dest.id)

          suffix = ""
          if bbEdge.label == TrueEdge:
            suffix = " [color=green, penwidth=2]"
          elif bbEdge.label == FalseEdge:
            suffix = " [color=red, penwidth=2]"

          content = f"  {fromLabel} -> {toLabel}{suffix};\n"
          sio.write(content)

      sio.write("} // close digraph\n")
      ret = sio.getvalue()

    return ret


  def genDotGraph(self) -> str:
    """ Generates Dot graph of itself. """
    if not self.inputBbMap: return "digraph{}"
    ret = None
    with io.StringIO() as sio:
      sio.write("digraph {\n  node [shape=box]\n")
      for nodeId, node in self.nodeMap.items():
        suffix = ""
        if len(node.succEdges) == 0 or len(node.predEdges) == 0:
          suffix = ", color=blue, penwidth=4"
        content = f"  n{nodeId} [label=\"{nodeId}: {node.insn}\"{suffix}];\n"
        sio.write(content)
      sio.write("\n")

      for nodeId, node in self.nodeMap.items():
        for succ in node.succEdges:
          suffix = ""
          if succ.label == FalseEdge:
            suffix = "[color=red, penwidth=2]"
          elif succ.label == TrueEdge:
            suffix = "[color=green, penwidth=2]"
          content = f"  n{nodeId} -> n{succ.dest.id} {suffix};\n"
          sio.write(content)
      sio.write("}\n")
      ret = sio.getvalue()
    return ret


  def genInstrSequence(self) -> List[instr.InstrIT]:
    """Generates an instruction sequence, useful to dump
    the IR for user editing.

    This function requires self.bbMap to reflect the latest
    version of the IR and processes it to generate the
    instruction sequence.
    """

    instrSeq: List[instr.InstrIT] = []
    for bbId in sorted(self.bbMap.keys()):
      if bbId == 0: continue  # handle END BB last
      instrSeq.extend(self.genInstrSeqBb(self.bbMap[bbId]))
    # self._genInstrSequenceRecursive(self.startBb, instrSeq, set())

    instrSeq.extend(self.genInstrSeqBb(self.bbMap[0]))

    return instrSeq


  def genInstrSeqBb(self,
      bb: BB,
  ) -> List[instr.InstrIT]:
    instrSeq: List[instr.InstrIT] = []
    labelName = "bb-{bbId}"

    # unconditionally add the label
    bbId = "start" if bb.id == -1 else bb.id
    bbId = "end" if bb.id == 0 else bbId
    instrSeq.append(instr.LabelI(labelName.format(bbId=bbId)))

    # not using bb.instrSeq here, since
    # the insn in the cfg could be transformed
    assert bb.cfgNodeSeq is not None
    for cfgNode in bb.cfgNodeSeq:
      instrSeq.append(cfgNode.insn)

    if bb.succEdges:  # end node has no successors
      if len(bb.succEdges) > 1:  # bb ends with a conditional instruction
        # modify jump labels of the last instruction
        condInsn = bb.lastCfgNode.insn
        assert isinstance(condInsn, instr.CondI), msg.INVARIANT_VIOLATED

        trueEdge = bb.getSuccEdge(TrueEdge)
        assert trueEdge is not None
        condInsn.trueLabel = labelName.format(bbId=trueEdge.dest.id)

        falseEdge = bb.getSuccEdge(FalseEdge)
        assert falseEdge is not None
        condInsn.falseLabel = labelName.format(bbId=falseEdge.dest.id)
      elif len(bb.succEdges) == 1:
        uncondEdge = bb.getSuccEdge(UnCondEdge)
        assert uncondEdge is not None
        if len(uncondEdge.dest.predEdges) > 1:
          instrSeq.append(instr.GotoI(labelName.format(bbId=uncondEdge.dest.id)))
    else:
      # must be the end node
      assert bb.id == 0, msg.INVARIANT_VIOLATED

    return instrSeq


  def __str__(self):
    sorted_nids = sorted(self.nodeMap.keys())
    with io.StringIO() as sio:
      sio.write("Cfg(")
      sio.write("\n  RevPostOrder:" + str(self.revPostOrder))
      for nid in sorted_nids:
        sio.write("\n  ")
        sio.write(str(self.nodeMap[nid]))
      sio.write(")")
      ret = sio.getvalue()
    return ret


  def __repr__(self):
    return self.__str__()


class FeasibleEdges:
  """Keeps record of feasible edges in a CFG.
  Provides helper routines to manage feasible edges."""

  __slots__ : List[str] = ["cfg", "fEdges", "feasibleNodes", "allFeasible"]

  def __init__(self,
      cfg: Cfg,
      allFeasible: bool = False, # when set True make everything feasible
  ) -> None:
    self.cfg: Cfg = cfg
    self.fEdges: Set[CfgEdge] = set()
    self.feasibleNodes: Set[CfgNode] = set()
    self.allFeasible = allFeasible


  def initFeasibility(self) -> List[CfgNode]:
    """Assuming start node as feasible, marks initial set of feasible edges.

    All initial UnCondEdges chains are marked feasible.
    """
    assert self.cfg.start is not None
    feasibleNodes: List[CfgNode] = [self.cfg.start]  # start node is always feasible
    for succEdge in self.cfg.start.succEdges:
      if succEdge.label == UnCondEdge:
        nodes = self.setFeasible(succEdge)
        feasibleNodes.extend(nodes)

    self.feasibleNodes.update(feasibleNodes)
    return feasibleNodes


  def setFeasible(self,
      cfgEdge: CfgEdge
  ) -> List[CfgNode]:
    """Marks the given edge, and all subsequent UnCondEdges chains as feasible.

    Returns list of nodes id of nodes, that may become reachable,
    due to the freshly marked incoming feasible edges.
    """
    if cfgEdge in self.fEdges:
      # edge already present, hence must have been already set
      return []

    feasibleNodes: List[CfgNode] = []
    feasibleNodes.append(cfgEdge.dest)
    if LS: LOG.debug("New_Feasible_Edge: %s.", cfgEdge)

    self.fEdges.add(cfgEdge)
    toNode = cfgEdge.dest
    for edge in toNode.succEdges:
      if self.allFeasible or edge.label == UnCondEdge:
        nodes = self.setFeasible(edge)
        feasibleNodes.extend(nodes)

    self.feasibleNodes.update(feasibleNodes)
    return feasibleNodes


  def isFeasibleEdge(self,
      cfgEdge: CfgEdge
  ) -> bool:
    """Returns true if edge is feasible."""
    if cfgEdge in self.fEdges: return True
    return False


  def setAllSuccEdgesFeasible(self,
      node: CfgNode
  ) -> List[CfgNode]:
    """Sets all succ edges of node_id as feasible.

    All subsequent UnCondEdges chains are marked feasible.
    """
    feasibleNodes = []
    for edge in node.succEdges:
      nodes = self.setFeasible(edge)
      feasibleNodes.extend(nodes)

    self.feasibleNodes.update(feasibleNodes)
    return feasibleNodes


  def setFalseEdgeFeasible(self,
      node: CfgNode
  ) -> List[CfgNode]:
    """Sets all succ edges of node, with label FalseEdge as feasible.

    All subsequent UnCondEdges chains are marked feasible.
    """
    feasibleNodes: List[CfgNode] = []
    for edge in node.succEdges:
      if edge.label == FalseEdge:
        nodes = self.setFeasible(edge)
        feasibleNodes.extend(nodes)

    self.feasibleNodes.update(feasibleNodes)
    return feasibleNodes


  def setTrueEdgeFeasible(self,
      node: CfgNode
  ) -> List[CfgNode]:
    """Sets all succ edges of node, with label TrueEdge as feasible.

    All subsequent UnCondEdges chains are marked feasible.
    """
    feasibleNodes: List[CfgNode] = []
    for edge in node.succEdges:
      if edge.label == TrueEdge:
        nodes = self.setFeasible(edge)
        feasibleNodes.extend(nodes)

    self.feasibleNodes.update(feasibleNodes)
    return feasibleNodes


  def isFeasibleNode(self, node: CfgNode) -> bool:
    """Return true if node is feasible."""
    return node in self.feasibleNodes


  def __str__(self):
    return f"Feasible Nodes: {self.feasibleNodes}."


  def __repr__(self):
    return self.__str__()


class CalleeInfo:

  __slots__ : List[str] = ["callExpr", "caller", "calleeNames"]

  def __init__(self,
      callExpr: expr.CallE,  # the call expr that invokes the call
      caller: FuncNameT,  # the caller function name
      calleeNames: List[FuncNameT]  # the callee(s) - if function ptr
  ):
    self.callExpr = callExpr
    self.caller = caller
    self.calleeNames = calleeNames


  def isIndeterministicCall(self):
    """The call is in-deterministic if its made using a variable name."""
    return not self.callExpr.callee.hasFunctionName()


class CallGraph:
  """Call graph of the given translation unit.
  This could work for inter-procedural level also.
  """


  def __init__(self):
    self.callGraph: Dict[FuncNameT, List[CalleeInfo]] = {}
    # entryFunctions is calculated from the callgraph dictionary
    self.entryFunctions: Opt[List[FuncNameT]] = None


