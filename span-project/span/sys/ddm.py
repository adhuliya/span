#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Akshat Garg, Anshuman Dhuliya

"""Demand Driven Method (#DDM) Augmentation
This module provides the demand driven logic to SPAN.
"""

import logging

from span.ir import conv

LOG = logging.getLogger(__name__)
from typing import List, Set, Dict, Tuple, Callable, FrozenSet, Any
from typing import Optional as Opt
import functools
from copy import copy

from span.util.util import LS
import span.api.analysis as analysis
import span.sys.clients as clients
import span.ir.types as types
import span.ir.expr as expr
import span.ir.instr as instr
from span.ir.instr import (NOP_INSTR_IC, BARRIER_INSTR_IC, UNDEF_VAL_INSTR_IC,
                           COND_READ_INSTR_IC, USE_INSTR_IC, EX_READ_INSTR_IC,
                           ASSIGN_INSTR_IC, COND_INSTR_IC, RETURN_INSTR_IC, CALL_INSTR_IC,
                           FILTER_INSTR_IC, )
from span.ir.expr import (VAR_EXPR_EC, LIT_EXPR_EC, UNARY_EXPR_EC,
                          BINARY_EXPR_EC, ADDROF_EXPR_EC, MEMBER_EXPR_EC, ARR_EXPR_EC,
                          SIZEOF_EXPR_EC, FUNC_EXPR_EC, CALL_EXPR_EC, SELECT_EXPR_EC,
                          CAST_EXPR_EC, DEREF_EXPR_EC, )

from span.api.dfv import DfvPairL, ChangePairL, OLD_IN_OUT
import span.api.lattice as lattice
from span.api.lattice import LatticeLT, DataLT
import span.ir.cfg as cfg
import span.ir.tunit as irTUnit
import span.ir.constructs as constructs
import span.ir.ir as ir
from span.ir.ir import inferTypeOfVal
import span as span
import span.util.common_util as cutil

Reachability = bool
Reachable: Reachability = True
NotReachable: Reachability = False
IsNopT = bool

# BOUND START: Module_Storage__for__Optimization

Node__to__Nil__Name: str = analysis.AnalysisAT.Node__to__Nil.__name__
LhsVar__to__Nil__Name: str = analysis.AnalysisAT.LhsVar__to__Nil.__name__
Num_Var__to__Num_Lit__Name: str = analysis.AnalysisAT.Num_Var__to__Num_Lit.__name__
Cond__to__UnCond__Name: str = analysis.AnalysisAT.Cond__to__UnCond.__name__
Num_Bin__to__Num_Lit__Name: str = analysis.AnalysisAT.Num_Bin__to__Num_Lit.__name__
Deref__to__Vars__Name: str = analysis.AnalysisAT.Deref__to__Vars.__name__

ExRead_Instr__Name: str = analysis.AnalysisAT.ExRead_Instr.__name__
CondRead_Instr__Name: str = analysis.AnalysisAT.CondRead_Instr.__name__
Conditional_Instr__Name: str = analysis.AnalysisAT.Conditional_Instr.__name__
UnDefVal_Instr__Name: str = analysis.AnalysisAT.UnDefVal_Instr.__name__
Live_Instr__Name: str = analysis.AnalysisAT.Filter_Instr.__name__


# BOUND END  : Module_Storage__for__Optimization

AtIn  = True
AtOut = False

class AtomicDemand:
  """An instance of this class represents a logical demand
  for a single variable."""
  __slots__ : List[str] = ['func', 'node', 'atIn', 'demandVar', 'vType', 'dirn']


  def __init__(self,
      func: constructs.Func,
      node: cfg.CfgNode,
      atIn: bool, # True = at In, False = at Out
      demandVar: types.VarNameT,
      vType: types.Type,
      dirn: types.DirectionT,
  ) -> None:
    self.func = func
    self.node = node
    self.atIn = atIn
    self.demandVar = demandVar
    self.vType = vType
    self.dirn = dirn


  def isEmpty(self):
    return not bool(self.demandVar)


  def setEmpty(self):
    self.demandVar = None


  def __eq__(self, other) -> bool:
    """This method returns True if self and the other
    are the same demands.
    If both demands were raised from the same function for same node
    with same demandType, then we are merging those demands."""
    if self is other:
      return True
    if not isinstance(other, AtomicDemand):
      return NotImplemented

    equal = True
    if not self.node == other.node:
      equal = False
    elif not self.atIn == other.atIn:
      equal = False
    elif not self.demandVar == other.demandVar:
      equal = False
    elif not self.dirn == other.dirn:
      equal = False
    elif not self.func == other.func:
      equal = False
    return equal


  def __hash__(self) -> int:
    """This function returns a hash key of the self object.
    This function is necessary to efficiently use AtomicDemand objects
    in dictionaries and sets.
    """
    return hash((self.node.id, self.demandVar))


  def __str__(self):
    atIn = "AtIn" if self.atIn else "AtOut"
    return f"AtomicDemand({self.node.id}, {atIn}, ({self.demandVar}), {self.dirn})"


  def __repr__(self):
    return self.__str__()


class NodeInfo:
  """Information related to a CFG node"""
  __slots__ : List[str] = ["nid", "nop", "varNameSet", "atIn"]

  def __init__(self,
      nid: cfg.CfgNodeId,
      nop: bool = True,
      varNameSet: Opt[Set[types.VarNameT]] = None,
      atIn: bool = True, # varNameSet is needed at IN of the node
  ):
    self.nid = nid
    self.nop = nop
    self.varNameSet = varNameSet if varNameSet else set()
    self.atIn = atIn


  def getCopy(self):
    aCopy = copy(self)
    if self.varNameSet:
      aCopy.varNameSet = copy(self.varNameSet)
    return aCopy


  def update(self, other: 'NodeInfo') -> bool:
    assert isinstance(other, NodeInfo), f"{other}"
    assert self.nid == other.nid, f"{other}"

    updated = False
    newNop =  self.nop and other.nop    # once not an nop always so
    if newNop != self.nop:
      self.nop = newNop
      updated = True
    if not self.varNameSet >= other.varNameSet:
      self.varNameSet.update(other.varNameSet) # var set always grows
      updated = True
    return updated


  def __eq__(self, other):
    if self is other: return True
    if not isinstance(other, NodeInfo):
      return False
    if not self.nid == other.nid:
      return False
    if not self.nop == other.nop:
      return False
    if not self.varNameSet == other.varNameSet:
      return False
    if not self.atIn == other.atIn:
      return False
    return True


  def __hash__(self):
    return hash((self.nid, self.nop))


  def __str__(self):
    return f"{self.nid}{'.' if self.nop else ''}({self.varNameSet})"


  def __repr__(self):
    return str(self)


class NewSlice:
  """A NewSlice of the CFG."""
  __slots__ : List[str] = ['nodeMap']

  def __init__(self,
      nodeMap: Opt[Dict[cfg.CfgNode, NodeInfo]] = None,
  ):
    self.nodeMap = nodeMap if nodeMap else dict()


  def update(self, other: 'NewSlice') -> bool:
    updated = False
    for node, nInfo in other.nodeMap.items():
      updated = self.addNode(node, nInfo) or updated
    return updated


  def addNode(self, node: cfg.CfgNode, nInfo: NodeInfo) -> bool:
    if node in self.nodeMap:
      return self.nodeMap[node].update(nInfo)
    self.nodeMap[node] = nInfo.getCopy()
    return True # added a new node


  def __str__(self):
    lst = []
    for node in sorted(self.nodeMap.keys(), key=lambda node: node.id):
      lst.append(f"{self.nodeMap[node]}")
    lst.append("('.' == Nop)")
    return " ".join(lst)


  def __repr__(self):
    return str(self)



class Slice:
  """A Slice of the CFG."""
  __slots__ : List[str] = ['nodeMap']

  def __init__(self,
      nodeMap: Opt[Dict[cfg.CfgNode, bool]] = None,
  ):
    # nid ---> True   if nid has to be treated like a NopI()
    self.nodeMap = nodeMap if nodeMap else dict()


  def update(self, other: 'Slice') -> bool:
    updated, addNode, selfNodeMap = False, self.addNode, self.nodeMap
    for node, nop in other.nodeMap.items():
      #updated = addNode(node, nop) or updated
      if node in selfNodeMap:
        oldValue = selfNodeMap[node]
        newValue = oldValue and nop  # once not a nop, always the same
        if oldValue != newValue:
          selfNodeMap[node] = newValue
          updated = True
      else:
        selfNodeMap[node] = nop
        updated = True
    return updated


  def fastUpdate(self, other: 'Slice') -> bool:
    """Is slower than update() :( """
    updated, addNode = False, self.addNode
    selfKeys = self.nodeMap.keys()
    otherKeys = other.nodeMap.keys()

    for newKey in otherKeys - selfKeys:
      self.nodeMap[newKey] = other.nodeMap[newKey]
      updated = True
    for oldKey in otherKeys & selfKeys:
      oldValue = self.nodeMap[oldKey]
      newValue = oldValue and other.nodeMap[oldKey]  # once not a nop, always the same
      if oldValue != newValue:
        self.nodeMap[oldKey] = newValue
        updated = True
    return updated


  def addNode(self, node: cfg.CfgNode, nop: bool = False) -> bool:
    if node in self.nodeMap:
      oldValue = self.nodeMap[node]
      newValue = oldValue and nop  # once not a nop, always the same
      if oldValue != newValue:
        self.nodeMap[node] = newValue
        return True # only updated the value
      return False # node already present with the same value
    self.nodeMap[node] = nop
    return True # added a new node


  def __str__(self):
    lst = []
    for node in sorted(self.nodeMap.keys(), key=lambda node: node.id):
      # '.' represents a Nop status of a node
      suffix = "." if self.nodeMap[node] else ""
      lst.append(f"{node.id}{suffix}")
    lst.append("('.' == Nop)")
    return " ".join(lst)


class DdMethod:
  """Demand Driven Method class."""
  __slots__ : List[str] = [ "func", "cfg", "host", "validHost", "fe", "fe",
                "demandResult", "demandDep", "infNodeDep",
                "changedDemands", "timer"]

  def __init__(self,
      func: constructs.Func,
      host: Opt[Any] = None,  # initialized with span.sys.host.Host object
  ):
    assert func.cfg, f"{func}"
    self.func = func
    self.cfg = func.cfg
    self.host = host
    self.validHost = host is not None
    self.fe = self.host.ef if self.host\
      else cfg.FeasibleEdges(func.cfg, allFeasible=True)
    if not self.validHost:
      self.fe.initFeasibility()  # initialize

    self.demandResult: Dict[AtomicDemand, NewSlice] = dict()
    # demand1 ---> {demand2,...}  ({demand2...} depends on demand1)
    self.demandDep: Dict[AtomicDemand, Set[AtomicDemand]] = dict()
    # demands dependent on infeasible nodes
    self.infNodeDep: Dict[types.NodeIdT, Set[AtomicDemand]] = dict()

    # changed demands: records changed demands
    self.changedDemands: Set[AtomicDemand] = set()
    self.timer = cutil.Timer("DDM", start=False)


  #@functools.lru_cache(1000)
  def propagateDemand(self,
      demand: AtomicDemand,
  ) -> NewSlice:
    """External sources call this function."""
    slice = self._propagateDemand(demand, force=False)

    if LS: LOG.debug("InfeasibleNodeDependence: %s", self.infNodeDep)

    return slice


  def propagateDemandForced(self,
      demand: AtomicDemand,
  ) -> NewSlice:
    """External sources call this function."""
    slice = self._propagateDemand(demand, force=True)

    if LS: LOG.debug("InfeasibleNodeDependence: %s", self.infNodeDep)

    return slice


  def _propagateDemand(self,
      demand: AtomicDemand,
      force: bool = False, # skip cache and force recalculation
  ) -> NewSlice:
    """Propagate a demand through the CFG. If force is True,
    then skip the cache and re-compute result."""
    if demand.isEmpty():
      return NewSlice()

    if LS: LOG.debug("PropDemand:(DemandNode%s)(%s)(%s)(%s) Demand is %s",
                     demand.node.id, demand.node.insn,
                      "AtIn" if demand.atIn else "AtOut",
                      "Forced" if force else "NotForced", demand)

    if not force and demand in self.demandResult:
      slice = self.demandResult[demand]
      if LS: LOG.debug("PropDemand:(DemandNode%s)(%s)(%s) (cached) Slice is %s",
                       demand.node.id, demand.node.insn,
                        "AtIn" if demand.atIn else "AtOut", slice)
      return slice

    if demand not in self.demandResult:
      self.demandResult[demand]\
        = NewSlice({demand.node: NodeInfo(
                    demand.node.id, True,
                    {demand.demandVar} if demand.atIn else None)})  # initial value

    if demand.dirn == conv.Backward:
      slice =  self.propagateDemandBackward(demand)
    elif demand.dirn == conv.Forward:
      slice =  self.propagateDemandForward(demand)
    else: # demand.dirn == types.ForwBack
      slice =  self.propagateDemandForwBack(demand)

    updatedSlice = self.updateDemand(demand, slice)
    if LS: LOG.debug("PropDemand:(DemandNode%s)(%s)(%s) (calculated) Slice is %s",
                     demand.node.id, demand.node.insn,
                      "AtIn" if demand.atIn else "AtOut", slice)
    return updatedSlice


  #REF: https://medium.com/@circleoncircles/python-recursive-function-and-various-speedup-a19312e7cf06
  #@functools.lru_cache(2000)
  def updateDemand(self, demand, slice: NewSlice) -> NewSlice:
    """Update and propagate the change along the dependence graph."""
    # assert demand in self.demandResult, f"{demand}" #invariant

    cachedSlice = self.demandResult[demand]
    changed = cachedSlice.update(slice)

    if changed:
      demandDep, updateDemand = self.demandDep, self.updateDemand
      self.changedDemands.add(demand)  # self.recordChangedDemand(demand)
      if demand in demandDep: # update dependent demands
        for depDemand in demandDep[demand]:
          updateDemand(depDemand, cachedSlice)
    return cachedSlice


  def propagateDemandBackward(self, demand) -> NewSlice:
    # assert demand.dirn == types.Backward, f"{demand}"  #invariant
    if demand.atIn:
      slice = self.propagateDemandToPred(demand)
    else: # i.e. AtOut
      slice = self.propagateDemandThroughInstrBackward(demand)
    return slice


  def propagateDemandForward(self, demand) -> NewSlice:
    assert demand.dirn == conv.Forward, f"{demand}"
    raise NotImplementedError()


  def propagateDemandForwBack(self, demand) -> NewSlice:
    assert demand.dirn == conv.ForwBack, f"{demand}"
    raise NotImplementedError()


  #@functools.lru_cache(2000)
  def propagateDemandToPred(self, demand: AtomicDemand) -> NewSlice:
    #assert demand.atIn == AtIn and demand.dirn == conv.Backward, f"{demand}" #invariant
    slice, predEdges = NewSlice(), demand.node.predEdges
    isFeasibleEdge, addInfNodesDependence = self.fe.isFeasibleEdge, self.addInfNodesDependence
    for predEdge in predEdges:
      if not isFeasibleEdge(predEdge):
        if LS: LOG.debug("PropDemand:(DemandNode%s)(%s)(AtIn) (InfeasiblePredecessor)"
                          " Demand: %s",
                         demand.node.id, demand.node.insn, demand)
        addInfNodesDependence(predEdge.src.id, demand)
        continue
      propDemand = copy(demand)
      propDemand.atIn, propDemand.node = False, predEdge.src
      self.addDependence(demand, propDemand)
      slice.update(self._propagateDemand(propDemand))
    return slice


  def addInfNodesDependence(self, nid: types.NodeIdT, demand: AtomicDemand):
    if nid not in self.infNodeDep:
      self.infNodeDep[nid] = depDemands = set()  # type: ignore
    else:
      depDemands = self.infNodeDep[nid]
    depDemands.add(demand)


  def addDependence(self,
      demand: AtomicDemand,
      propDemand: AtomicDemand,
  ) -> None:
    """demand depends on propDemand"""
    if propDemand.isEmpty(): return # empty demand do nothing

    if propDemand not in self.demandDep:
      self.demandDep[propDemand] = depDemands = set()  # type: ignore
    else:
      depDemands = self.demandDep[propDemand]

    depDemands.add(demand)


  #@functools.lru_cache(1000)
  def propagateDemandThroughInstrBackward(self,
      demand: AtomicDemand,
  ) -> NewSlice:
    dn = demand.node
    insn, nid = dn.insn, dn.id

    if LS: LOG.debug("PropDemand:(DemandNode%s)(%s)(AtOut) Demand is %s",
                     nid, insn, demand)

    slice = NewSlice()
    propDemands, nop = self.processInstrBackward(insn, demand)
    for dem in propDemands:
      dem.atIn = True

    if LS: LOG.debug("PropDemand:(DemandNode%s)(%s)(AtIn) (%s) Demand is %s",
                     nid, insn, "TreatedAsNop" if nop else "NotAsNop", propDemands)

    if LS: LOG.debug("PropDemand:(DemandNode%s)(%s) Incomplete Slice: %s", nid, insn, slice)
    slice.addNode(demand.node, NodeInfo(
      demand.node.id, nop,
      {pd.demandVar for pd in propDemands if pd.demandVar}))
    addDependence, update = self.addDependence, slice.update
    for dem in propDemands:
      if dem.isEmpty(): continue
      addDependence(demand, dem)
      update(self._propagateDemand(dem))
    if LS: LOG.debug("PropDemand:(DemandNode%s)(%s)   Complete Slice: %s", nid, insn, slice)
    return slice


  #@functools.lru_cache(200) # not useful here
  def processInstrBackward(self,
      insn: instr.InstrIT,
      demand: AtomicDemand,
  ) -> Tuple[List[AtomicDemand], IsNopT]:
    if self.validHost:  # is self attached to a host?
      newInsn = self.simplifyInstruction(insn, demand)
      insn = insn if newInsn is None else newInsn

    ic = insn.instrCode

    if isinstance(insn, instr.AssignI):
      return self.processInstrBackwardAssignI(insn, demand)
    elif isinstance(insn, instr.III):
      return self.processInstrBackwardParallelI(insn, demand)
    elif ic == instr.COND_READ_INSTR_IC or ic == instr.EX_READ_INSTR_IC:
      propDemand = copy(demand)
      propDemand.atIn = True
      propDemand.setEmpty()  # block the demands
      return [propDemand], False
    else:
      return [copy(demand)], True


  def processInstrBackwardParallelI(self,
      insn: instr.III,
      demand: AtomicDemand,
  ) -> Tuple[List[AtomicDemand], IsNopT]:
    insns = insn.insns

    finalNop = True
    demands: List[AtomicDemand] = []
    processInstrBackward, extend = self.processInstrBackward, demands.extend
    for ins in insns:
      propDemands, nop = processInstrBackward(ins, demand)
      finalNop = nop and finalNop
      extend(propDemands)

    return demands, finalNop


  def processInstrBackwardAssignI(self,
      insn: instr.AssignI,
      demand: AtomicDemand,
  ) -> Tuple[List[AtomicDemand], IsNopT]:
    if demand.vType != insn.type and not instr.getCallExpr(insn):
      dd = copy(demand)
      dd.atIn = True
      return [dd], True  # treat the current insn as NopI()

    demandRhsNames: bool = False
    demandVar = demand.demandVar
    lhs = insn.lhs
    rhs = insn.rhs

    # Find out: should variables be marked live?
    if rhs.exprCode == expr.CALL_EXPR_EC:
      demandRhsNames = True

    lhsNames = set(ir.getNamesLValuesOfExpr(self.func, lhs))
    assert lhsNames, f"{lhs}"
    if LS: LOG.debug(f"{demandVar} in {lhsNames}: {demandVar in lhsNames}")
    if demandVar in lhsNames:
      demandRhsNames = True

    if LS: LOG.debug(f"lhsNames = {lhsNames} (demandRhs={demandRhsNames})")

    # Now take action
    if not demandRhsNames:
      dd = copy(demand)
      dd.atIn = True
      return [dd], True  # treat the current insn as NopI()
    else:
      rhsNames = self.getRhsNames(rhs)


      if len(lhsNames) == 1:
        return self._killGenBackward(demand, kill=lhsNames, gen=rhsNames)
      else:
        return self._killGenBackward(demand, gen=rhsNames)


  def getRhsNames(self, rhs) -> Set[types.VarNameT]:
    return ir.getNamesUsedInExprSyntactically(rhs) | \
           ir.getNamesInExprMentionedIndirectly(self.func, rhs)


  def _killGenBackward(self,
      demand: AtomicDemand,
      kill: Opt[Set[types.VarNameT]] = None,
      gen: Opt[Set[types.VarNameT]] = None,
  ) -> Tuple[List[AtomicDemand], IsNopT]:
    if LS: LOG.debug(f"KillGen: Kill={kill}, Gen={gen}, Demand is {demand}")

    demandVar = demand.demandVar

    demandSet = {demandVar}
    if kill: demandSet = demandSet - kill
    if gen: demandSet.update(gen)

    propDemands = []
    for varName in demandSet:
      d = copy(demand)
      d.demandVar = varName
      d.atIn = True
      d.vType = inferTypeOfVal(demand.func, varName)
      propDemands.append(d)

    if not propDemands: # return an empty demand
      d = copy(demand)
      d.setEmpty()
      d.atIn = True
      propDemands.append(d)

    return propDemands, False


  def updateInfNodeDepDemands(self, feasibleNodes: Opt[List[cfg.CfgNode]]):
    if not feasibleNodes: return None

    if LS: LOG.debug("AddingFeasibleNodes: %s", [n.id for n in feasibleNodes])
    for node in feasibleNodes:
      if node.id in self.infNodeDep:
        depDemands = self.infNodeDep[node.id]
        for demand in depDemands:
          self._propagateDemand(demand, force=True)

    self.cleanInfNodeDep(feasibleNodes)


  def cleanInfNodeDep(self, feasibleNodes: Opt[List[cfg.CfgNode]]):
    """Removes the dependence information of feasible nodes
    from self.infNodeDep """
    if not feasibleNodes: return None

    for node in feasibleNodes:
      if node.id in self.infNodeDep:
        del self.infNodeDep[node.id]


  def recordChangedDemand(self, demand):
    self.changedDemands.add(demand)


  def getChangedDemands(self):
    cd = copy(self.changedDemands)
    self.clearChangedDemands()
    return cd


  def clearChangedDemands(self):
    self.changedDemands.clear()


  #@functools.lru_cache(200)
  def getDemandForExprSim(self,
      func: constructs.Func,
      node: cfg.CfgNode,
      simName: analysis.SimNameT,
      e: expr.ExprET,
  ) -> List[AtomicDemand]:
    """Only covers backward simplifications. TODO: make simName sensitive."""
    varNames = ir.getNamesUsedInExprSyntactically(e)
    assert func.tUnit, f"{func}"

    demands = [
      AtomicDemand(func, node, AtIn, varName,
                   func.tUnit.inferTypeOfVal(varName), conv.Backward)
      for varName in varNames
    ]

    if LS: LOG.debug("DemandForExprSim (Node %s)(Sim %s)(Expr %s) Demand is %s",
                     node.id, simName, e, demands)

    return demands


  def simplifyInstruction(self,
      insn: instr.InstrIT,
      demand: AtomicDemand,
  ) -> instr.InstrIT:
    LLS = LS
    if LLS: LOG.debug("InstrValueType: %s, instrCode: %s", insn.type, insn.instrCode)
    assert self.host, f"{self}"

    newInsn = insn
    if isinstance(insn, instr.AssignI):
      lhs = insn.lhs
      rhs = insn.rhs
      lhsExprCode = lhs.exprCode
      rhsExprCode = rhs.exprCode
      if lhsExprCode == VAR_EXPR_EC:
        if rhsExprCode == DEREF_EXPR_EC:
          newInsn = self.host.getRhsDerefSimInstr(demand.node, insn, demand)
        elif rhsExprCode == MEMBER_EXPR_EC:  # lhsExprCode == VAR_EXPR_EC
          if rhs.hasDereference():
            newInsn = self.host.getRhsMemDerefSimInstr(demand.node, insn, demand)
      elif lhsExprCode == DEREF_EXPR_EC:
        newInsn = self.host.getLhsDerefSimInstr(demand.node, insn, demand)
      elif lhsExprCode == MEMBER_EXPR_EC:
        if lhs.hasDereference():
          newInsn = self.host.getLhsMemDerefSimInstr(demand.node, insn, demand)

    return newInsn


def ddmFilterInDfv(
    nDfv: DfvPairL,
    ddmVarNameSet: Opt[Set[types.VarNameT]],
) -> DfvPairL:
  """Filters away redundant variables w.r.t. the DDM demand set at IN of the node.
  A common filter function for ConstA, PointsToA, EvenOddA, IntervalA
  """
  dfvIn: Any = nDfv.dfvIn
  dfvClass = dfvIn.__class__
  newDfvIn = dfvIn

  if not ddmVarNameSet:
    newDfvIn = dfvClass(dfvIn.func, top=True)
  elif dfvIn.top:
    newDfvIn = dfvIn  # no change
  elif dfvIn.bot:
    valMap = {}
    for vName in ddmVarNameSet:
      valMap[vName] = dfvIn.componentBot
    newDfvIn = dfvClass(dfvIn.func, val=valMap)
  else:
    valMap = {}
    for vName in ddmVarNameSet:
      valMap[vName] = dfvIn.getVal(vName)
    newDfvIn = dfvClass(dfvIn.func, val=valMap)

  if newDfvIn is dfvIn:
    return nDfv
  else:
    return DfvPairL(newDfvIn, nDfv.dfvOut, nDfv.dfvOutTrue, nDfv.dfvOutFalse)


