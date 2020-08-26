#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Function and data structures for C function"""

import logging

LOG = logging.getLogger("span")
from typing import List, Dict, Tuple, Optional as Opt, Set
import io

from span.util.util import LS
from span.ir.types import (StructNameT, UnionNameT, MemberNameT, FuncNameT, VarNameT,
                           EdgeLabelT, BasicBlockIdT, Void, ConstructT,
                           Type, FuncSig, Info, Loc, LabelNameT, )
import span.ir.instr as instr
from span.ir.instr import InstrIT, LabelI, GotoI, CondI, NopI, ReturnI
from span.ir.conv import FalseEdge, TrueEdge, UnCondEdge
from span.ir.types import BasicBlockIdT, InstrIndexT, FuncNodeIdT
import span.ir.expr as expr
import span.ir.graph as graph


class Func(ConstructT):
  """A function.

  A function with instructions divided into basic blocks.
  The only pre-processing of SPAN IR here is to divide sequence of instructions to BB.
  """

  __slots__ : List[str] = ["name", "paramNames", "basicBlocks", "bbEdges",
               "instrSeq", "info", "cfg", "tUnit", "sig", "id"]


  def __init__(self,
      name: FuncNameT,
      returnType: Type = Void,
      paramTypes: Opt[List[Type]] = None,
      paramNames: Opt[List[VarNameT]] = None,
      variadic: bool = False,

      basicBlocks: Opt[Dict[BasicBlockIdT, List[InstrIT]]] = None,
      bbEdges: Opt[List[Tuple[BasicBlockIdT, BasicBlockIdT, EdgeLabelT]]] =
      None,
      instrSeq: Opt[List[InstrIT]] = None,
      info: Opt[Info] = None,
  ) -> None:
    self.name = name
    self.paramNames = paramNames if paramNames is not None else []
    # in case paramTypes is empty,
    # self.sig is then properly initialized in span.ir.tunit
    self.sig = FuncSig(returnType, paramTypes, variadic)

    self.basicBlocks = basicBlocks if basicBlocks else dict()
    self.bbEdges = bbEdges if bbEdges else []
    self.instrSeq = instrSeq
    self.info = info
    self.cfg: Opt[graph.Cfg] = None  # initialized in TUnit class
    self.tUnit = None  # initialized to TranslationUnit object in span.ir.tunit
    self.id: FuncNodeIdT = -1 # it is assigned a unique id

    if self.instrSeq:
      self.basicBlocks, self.bbEdges = self.genBasicBlocks(self.instrSeq)


  def hasBody(self) -> bool:
    return bool(self.basicBlocks) or bool(self.instrSeq)


  def checkInvariants(self, level: int = 0):  # -> 'ExprET':
    """Runs some invariant checks on self.
    Args:
      level: An argument to help invoke specific checks in future.
    """
    if self.hasBody():
      assert self.cfg and self.cfg.start and self.cfg.end, f"{self}"
    # Assertion check on self.tUnit cannot be done here.
    # Hence, do it in span.ir.tunit module.
    return self


  @staticmethod
  def genBasicBlocks(instrSeq: List[InstrIT]
  ) -> Tuple[Dict[BasicBlockIdT, List[InstrIT]],
             List[Tuple[BasicBlockIdT, BasicBlockIdT, EdgeLabelT]]]:
    """
    Divides the list of instructions given, into basic blocks.
    Assumption: every target except the first instruction must have a label.

    Explicitly called from span.ir.tunit.TUnit class if self.basicBlocks is empty.
    """

    if not instrSeq:
      return dict(), list()

    if not isinstance(instrSeq[0], instr.NopI):
      instrSeq.insert(0, instr.NopI())  # IMPORTANT

    leaders: Dict[InstrIndexT, BasicBlockIdT] = {0: -1}  # first instr is leader
    bbEdges: List[Tuple[BasicBlockIdT, BasicBlockIdT, EdgeLabelT]] = []
    bbMap: Dict[BasicBlockIdT, List[InstrIT]] = {}
    labelMap: Dict[LabelNameT, BasicBlockIdT] = {}
    maxBbId = 0

    # STEP 0: Record all target labels
    validTargets: Set[LabelNameT] = set()
    for insn in instrSeq:
      if isinstance(insn, GotoI):
        validTargets.add(insn.label)
      if isinstance(insn, CondI):
        assert insn.trueLabel and insn.falseLabel
        validTargets.add(insn.trueLabel)
        validTargets.add(insn.falseLabel)

    # STEP 1: put at least one instruction after the last LabelI (IMPORTANT)
    if isinstance(instrSeq[-1], LabelI):
      instrSeq.append(NopI())

    # STEP 2: Record all leaders and allocate them bb ids
    currLabelSet: Set[LabelNameT] = set()
    for index, insn in enumerate(instrSeq):
      if isinstance(insn, LabelI):
        if insn.label in validTargets:
          currLabelSet.add(insn.label)
      elif currLabelSet:
        maxBbId += 1
        leaders[index] = maxBbId  # add the non-label instr as target
        for label in currLabelSet:  # allocate a unique bbid to the label set
          if label not in validTargets:
            continue  # ignore label
          labelMap[label] = maxBbId  # allocate bb id
        currLabelSet.clear()

    # STEP 3: Now divide instr sequence into basic blocks.
    foundReturn = False  # to skip redundant instructions after the return stmt
    instructions: List[instr.InstrIT] = []
    currBbId = -1  # start block id
    for index, insn in enumerate(instrSeq):
      if index in leaders:
        foundReturn = False
        # save the old bb
        prevBbId = currBbId
        bbMap[prevBbId] = instructions

        # start a new basic block
        currBbId = leaders[index]

        # connect the fall through basic block to its successor
        if prevBbId != currBbId:  # could be equal due to the first instruction
          if bbMap[prevBbId]:
            lastInstr = bbMap[prevBbId][-1]
            if not isinstance(lastInstr, (GotoI, ReturnI, CondI)):
              edge = (prevBbId, currBbId, UnCondEdge)
              bbEdges.append(edge)
          else:
            edge = (prevBbId, currBbId, UnCondEdge)
            bbEdges.append(edge)

        # reset the instructions list for the next basic block
        instructions = []

      # add the instruction if not a label (GotoI is deliberately added)
      if not isinstance(insn, LabelI):
        if isinstance(insn, ReturnI):
          instructions.append(insn)
          foundReturn = True
        elif not foundReturn:
          instructions.append(insn)

    bbMap[currBbId] = instructions  # add the last basic block
    bbMap[0] = [NopI()]  # end bb

    # STEP 4: inter-connect all basic blocks
    for bbId, bbInstrSeq in bbMap.items():
      if bbInstrSeq:
        lastInstr = bbInstrSeq[-1]
        fromBbId = bbId
        if isinstance(lastInstr, GotoI):
          toBbId = labelMap[lastInstr.label]
          bbEdges.append((fromBbId, toBbId, UnCondEdge))
          bbInstrSeq.pop()  # Remove GotoI
        elif isinstance(lastInstr, ReturnI):
          toBbId = 0  # end bb id
          bbEdges.append((fromBbId, toBbId, UnCondEdge))
        elif isinstance(lastInstr, CondI):
          toFalseLabel, toTrueLabel = lastInstr.falseLabel, lastInstr.trueLabel
          assert toFalseLabel and toTrueLabel
          toFalse, toTrue = labelMap[toFalseLabel], labelMap[toTrueLabel]
          bbEdges.append((fromBbId, toFalse, FalseEdge))
          bbEdges.append((fromBbId, toTrue, TrueEdge))
          lastInstr.falseLabel = f"BB{toFalse}"
          lastInstr.trueLabel = f"BB{toTrue}"

    # STEP 5: Connect all leaf BBs to the end BB.
    # 5.1: Collect ids of all bbs with outgoing edge (inner bbs)
    innerBbIds: Set[BasicBlockIdT] = set()
    for bbEdge in bbEdges:
      innerBbIds.add(bbEdge[0])

    # 5.2: Connect all leaf bbs to end bb with unconditional edge
    for bbId in range(-1, maxBbId + 1):
      if bbId not in innerBbIds and bbId != 0:  # hence its a leaf bb
        bbEdge = (bbId, 0, UnCondEdge)  # connect it to end bb
        bbEdges.append(bbEdge)

    bbEdges = list(set(bbEdges))
    return bbMap, bbEdges


  def __eq__(self, other) -> bool:
    """For C programs, just the name of the function is enough
    for equality."""
    if self is other:
      return True
    if not isinstance(other, Func):
      return NotImplemented
    equal = True
    if not self.tUnit == other.tUnit:
      equal = False
    elif not self.name == other.name:
      equal = False
    return equal


  def __hash__(self) -> int:
    return hash((self.name, self.tUnit))


  def isEqualDeep(self,
      other: 'Func'
  ) -> bool:
    if not isinstance(other, Func):
      return False
    if not self.name == other.name:
      return False
    if not self.paramNames == other.paramNames:
      return False
    if not self.sig == other.sig:
      return False

    if not self.bbEdges == other.bbEdges:
      return False
    selfBbIds = self.basicBlocks.keys()
    otherBbIds = other.basicBlocks.keys()
    if not len(selfBbIds) == len(otherBbIds):
      return False
    if not selfBbIds == otherBbIds:
      return False
    for bbId in self.basicBlocks.keys():
      selfBb = self.basicBlocks[bbId]
      otherBb = other.basicBlocks[bbId]
      if not selfBb == otherBb:
        return False

    if self.instrSeq and other.instrSeq:
      if not self.instrSeq == other.instrSeq:
        return False

    if not self.info == other.info:
      return False
    return True


  def isEqual(self,
      other: 'Func'
  ) -> bool:
    equal = True
    if not isinstance(other, Func):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.name == other.name:
      if LS: LOG.error("FuncNamesDiffer: %s, %s", self.name, other.name)
      equal = False
    if not self.paramNames == other.paramNames:
      if LS: LOG.error("ParamNamesDiffer: (Func: '%s') %s, %s",
                       self.name, self.paramNames, other.paramNames)
      equal = False
    if not self.sig == other.sig:
      if LS: LOG.error("FuncSigsDiffer: (Func: '%s')", self.name)
      equal = False

    if not self.bbEdges == other.bbEdges:
      if LS: LOG.error("CfgStructuresDiffer: (func: '%s'):\n\n%s,\n\n,%s",
                       self.name, self.bbEdges, other.bbEdges)
      equal = False
    selfBbIds = self.basicBlocks.keys()
    otherBbIds = other.basicBlocks.keys()
    if not len(selfBbIds) == len(otherBbIds):
      if LS: LOG.error("NumOfBBsDiffer: (Func: '%s') %s, %s",
                       self.name, selfBbIds, otherBbIds)
      equal = False
    if not selfBbIds == otherBbIds:
      if LS: LOG.error("BbNumberingsDiffer: (Func: '%s') %s, %s",
                       self.name, self, other)
      equal = False

    for bbId in self.basicBlocks.keys():
      selfBb = self.basicBlocks[bbId]
      otherBb = other.basicBlocks[bbId]
      if selfBb and otherBb:
        if not len(selfBb) == len(otherBb):
          if LS: LOG.error("BbInsnCountsDiffer: %s, %s",
                           len(selfBb), len(otherBb))
          equal = False
        else:
          for i in range(len(selfBb)):
            if not selfBb[i].isEqual(otherBb[i]):
              equal = False
      elif not selfBb == otherBb:
        if LS: LOG.error("BbsDiffer: %s, %s", selfBb, otherBb)
        equal = False

    if self.instrSeq and other.instrSeq:
      if not len(self.instrSeq) == len(other.instrSeq):
        if LS: LOG.error("IntrSeqCountsDiffer: %s, %s",
                         len(self.instrSeq), len(other.instrSeq))
        equal = False
      else:
        for i in range(len(self.instrSeq)):
          if not self.instrSeq[i].isEqual(other.instrSeq[i]):
            equal = False

    if self.info and not self.info.isEqual(other.info):
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def genDotBbLabel(self,
      bbId: BasicBlockIdT
  ) -> str:
    """Generate BB label to be used in printing dot graph."""
    if bbId == -1:
      bbLabel = "START"
    elif bbId == 0:
      bbLabel = "END"
    else:
      bbLabel = f"BB{bbId}"
    return bbLabel


  def genDotGraph(self) -> str:
    """Generates a basic block level CFG for dot program."""
    ret = None
    with io.StringIO() as sio:
      sio.write("digraph {\n  node [shape=box]\n")
      for bbId, insnSeq in self.basicBlocks.items():
        insnStrs = [str(insn) for insn in insnSeq]

        bbLabel: str = self.genDotBbLabel(bbId)
        insnStrs.insert(0, "[" + bbLabel + "]")

        bbContent = "\\l".join(insnStrs)
        content = f"  {bbLabel} [label=\"{bbContent}\\l\"];\n"
        sio.write(content)

      for bbIdFrom, bbIdTo, edgeLabel in self.bbEdges:
        fromLabel = self.genDotBbLabel(bbIdFrom)
        toLabel = self.genDotBbLabel(bbIdTo)

        suffix = ""
        if edgeLabel == TrueEdge:
          suffix = " [color=green, penwidth=2]"
        elif edgeLabel == FalseEdge:
          suffix = " [color=red, penwidth=2]"

        content = f"  {fromLabel} -> {toLabel}{suffix};\n"
        sio.write(content)

      sio.write("}\n")
      ret = sio.getvalue()
    return ret


  def yieldInstrSeq(self):
    """Yield all the instructions in no particular order."""
    if self.cfg:
      for bbId, bb in self.cfg.bbMap.items():
        yield from bb.instrSeq
    elif self.basicBlocks:
      for _, insnSeq in self.basicBlocks.items():
        yield from insnSeq
    elif self.instrSeq:
      yield from self.instrSeq
    else:
      yield from []


  def yieldBasicBlocks(self):
    """Yields tuples of (BBId, InstructionSequence) in no particular order."""
    if self.basicBlocks:
      yield from self.basicBlocks.items()
    else:
      yield from []


  def __str__(self):
    return f"constructs.Func({repr(self.name)})"


  def __repr__(self):
    instrSeq = self.cfg.genInstrSequence() if self.cfg else []
    sio = io.StringIO()
    sp0 = " " * 4
    sp1 = " " * 6
    sp2 = " " * 8

    sio.write("[\n")
    for insn in instrSeq:
      tmp = repr(insn).split("\n")
      for i in range(len(tmp)):
        sio.write(f"{sp2}{tmp[i]}")
        if i == len(tmp) - 1:
          sio.write(",")
        sio.write("\n")
    sio.write(f"{sp1}]")

    return f"constructs.Func(\n" \
           f"{sp1}name= {repr(self.name)},\n" \
           f"{sp1}returnType= {repr(self.sig.returnType)},\n" \
           f"{sp1}paramTypes= {repr(self.sig.paramTypes)},\n" \
           f"{sp1}variadic= {repr(self.sig.variadic)},\n" \
           f"{sp1}paramNames= {repr(self.paramNames)},\n" \
           f"{sp1}info= {repr(self.info)},\n\n" \
           f"{sp1}instrSeq= {sio.getvalue()} # end instrSeq\n" \
           f"{sp0})"


if __name__ == "__main__":
  instrs = [
    instr.AssignI(expr.VarE("v:main:x"), expr.LitE(10)),
    instr.CondI(expr.VarE("v:main:x"), "True", "False"),
    instr.LabelI("True"),
    instr.LabelI("False"),
  ]
  print(Func.genBasicBlocks(instrs))
