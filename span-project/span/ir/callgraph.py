#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Program abstraction: Call Graph.
This module may import all other modules in `span.ir`,
except `span.ir.util` and `span.ir.query` module.
(Thus to avoid cyclic dependence other modules in span.ir
should not import this module)
"""

import logging

from span.ir import tunit, constructs, instr, expr

LOG = logging.getLogger("span")
from typing import List, Dict, Set, Tuple
from typing import Optional as Opt
import io

from span.util.util import LS
from span.ir.types import EdgeLabelT, BasicBlockIdT, FuncNameT
from span.ir.conv import FalseEdge, TrueEdge, UnCondEdge, simplifyName
import span.ir.types as types
import span.util.consts as consts
from span.ir.constructs import Func


class CalleeInfo:

  __slots__ : List[str] = ["callExpr", "caller", "calleeNames"]

  def __init__(self,
      caller: Func,  # the caller function
      callExpr: expr.CallE,  # the call expr that invokes the call
      calleeNames: List[FuncNameT]  # the callee(s) - if function ptr
  ):
    self.callExpr = callExpr
    self.caller = caller
    self.calleeNames = calleeNames


  def isIndeterministicCall(self):
    """The call is in-deterministic if its made using a variable name."""
    return not self.callExpr.callee.hasFunctionName()


class CallGraphNode:
  """A Node in the call graph representing a function."""

  def __init__(self,
      func: Func,
      calleeInfos: List[CalleeInfo],
  ):
    self.func = func
    self.calleeInfos: List[CalleeInfo] = calleeInfos  # the list of call-site & callees
    # Tarjan's Algo: https://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
    self.index = None     # for Tarjan's Algo
    self.lowIndex = None  # for Tarjan's Algo
    self.onStack = False  # for Tarjan's Algo
    self.selfRecursive = False


  def yieldCalleeFuncNames(self):
    """Enumerates all the function names."""
    for ci in self.calleeInfos:
      for funcName in ci.calleeNames:
        yield funcName


  def isSelfRecursive(self):
    """Does the function call itself?"""
    name = self.func.name
    for calleeNames in self.yieldCalleeFuncNames():
      if name == calleeNames:
        self.selfRecursive = True
        break
    else:
      self.selfRecursive = False


  def __eq__(self, other):
    if not isinstance(other, CallGraphNode):
      return False
    return self.func == other.func


  def __hash__(self):
    return hash(self.func)


  def __str__(self):
    return f"CallGraphNode({self.func.name})"


  def __repr__(self): return self.__str__()


class CallGraph:
  """Call graph of the given translation unit.
  This can work for inter-procedural level also.
  """


  def __init__(self):
    self.callGraph: Dict[FuncNameT, CallGraphNode] = {}
    # entryFunctions is calculated from the callgraph dictionary
    self.entryFunctions: Opt[Set[FuncNameT]] = None
    self.index = 0 # for Tarjan's algo
    self.sccList: Opt[List[Set[CallGraphNode]]] = None


  def preProcess(self):
    """Do some preprocessing calculations."""
    assert self.callGraph, f"CALL_GRAPH: Uninitialized/Unpopulated"
    self.findSCCs()
    self.findPossibleEntryFunctions()


  def getCountEdges(self) -> int:
    count = 0
    for node in self.callGraph.values():
      count += len(list(node.yieldCalleeFuncNames()))
    return count


  def getCountNodes(self) -> int:
    return len(self.callGraph)


  def genAndPrintSCCs(self):
    # STEP 1: Discover SCCs
    self.findSCCs() # sets self.sccList
    self.printSccList(self.sccList)


  def getCallGraphNode(self, funcName: types.FuncNameT) -> CallGraphNode:
    return self.callGraph[funcName]


  def findPossibleEntryFunctions(self):
    """Returns the possible entry functions in the call graph."""
    calleeFuncSet = set()
    for node in self.callGraph.values():
      for calleeInfo in node.calleeInfos:
        calleeFuncSet.update(calleeInfo.calleeNames)

    allFuncsSet = set(self.callGraph.keys())
    self.entryFunctions = allFuncsSet - calleeFuncSet  # store for future use
    return self.entryFunctions


  def findSCCs(self) -> List[Set[CallGraphNode]]:
    """Finds the strongly connected components (SCCs) of the graph.
    This uses Tarjan's algo.
    REF: https://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
    output: list of strongly connected components (sets of vertices)
    """
    self.index = 0  # initial index
    stack = []  # empty stack
    sccList = [] # list of SCCs
    for node in self.callGraph.values():
      if node.index is None:
        self.strongConnect(node, stack, sccList)

    self.sccList = sccList
    return sccList


  def strongConnect(self,
      node: CallGraphNode,
      stack: List[CallGraphNode],
      sccList: List[Set[CallGraphNode]],
  ) -> None:
    """Tarjan's strong connect algorithm."""
    node.index = self.index
    node.lowIndex =  self.index
    self.index += 1
    stack.append(node)
    node.onStack = True

    # Consider successors of v
    for calleeName in node.yieldCalleeFuncNames():
      calleeNode = self.getCallGraphNode(calleeName)
      if calleeNode.index is None:
        # not visited yet, hence visit first
        self.strongConnect(calleeNode, stack, sccList)
        node.lowIndex = min(node.lowIndex, calleeNode.lowIndex)
      elif calleeNode.onStack:
        node.lowIndex = min(node.lowIndex, calleeNode.index)

    if node.lowIndex == node.index:
      # the node is the root of the SCC
      scc = set()
      stackNode = stack.pop()
      scc.add(stackNode)
      while stackNode != node:
        stackNode = stack.pop()
        scc.add(stackNode)
      sccList.append(scc)  # save the scc found


  def printSccList(self, sccList: List[Set[CallGraphNode]]):
    """Prints the list of SCCs discovered"""
    print("\nSTART: Strongly_Connected_Components:")
    for i, scc in enumerate(sccList):
      if len(scc) == 1 and not all(map(lambda x: x.isSelfRecursive(), scc)):
        continue  # avoid printing single non-recursive functions
      print(f"  {i}: ", end="")
      for node in scc:
        print(f"{node.func.name} ", end="")
      print()
    print("END  : Strongly_Connected_Components.\n")


  def getCallGraphDot(self) -> str:
    """ Returns Dot graph string of the given callGraph. """
    if not len(self.callGraph):
      return "digraph{}"

    self.genAndPrintSCCs()  # FIXME: put it in a better place

    ret = None
    with io.StringIO() as sio:
      sio.write("digraph {\n  node [shape=box]\n")
      # STEP 1/2: Create the nodes.
      for funcName, node in self.callGraph.items():
        suffix = ""
        if not len(node.calleeInfos):
          suffix = ", color=blue, penwidth=4"
        elif funcName in self.entryFunctions:
          suffix = ", color=green, penwidth=4"

        fName = simplifyName(funcName)
        content = f"""  "{fName}" [label=\"{fName}\"{suffix}];\n"""
        sio.write(content)
      sio.write("\n")

      # STEP 2/2: Connect the nodes.
      for funcName, node in self.callGraph.items():
        fName = simplifyName(funcName)
        for calleeInfo in node.calleeInfos:
          suffix = ""
          if calleeInfo.callExpr.isPointerCall():
            suffix = "[color=red, penwidth=2]"  # style of the call arrow

          if not len(calleeInfo.calleeNames):
            content = f"""  "{fName}" -> "None" [style=dotted, color=red];\n"""
            sio.write(content)
          else:
            for calleeName in calleeInfo.calleeNames:
              content = f"""  "{fName}" -> "{simplifyName(calleeName)}" {suffix};\n"""
              sio.write(content)

      sio.write("}\n")
      ret = sio.getvalue()
    return ret


def generateCallGraph(tUnit: tunit.TranslationUnit) -> CallGraph:
  """Generates and returns the CallGraph object of the tUnit."""
  cg = CallGraph()

  for func in tUnit.yieldFunctions():
    if func.hasBody():
      calleeInfos = getFuncCalleeInfos(func)
    else:
      calleeInfos = []
    node = CallGraphNode(func, calleeInfos)
    cg.callGraph[func.name] = node

  cg.preProcess()
  return cg


def getExprCallees(
    func: Func,
    callExpr: expr.CallE
) -> List[FuncNameT]:
  """
  Return the list of callee names of the given call expression.
  If a call is function pointer based, it returns all the
  functions with the same signature as the function pointer
  present in the translation unit.
  """
  if callExpr.hasDereference():
    calleeTypeSig = callExpr.getCalleeSignature()
    calleeFuncs = func.tUnit.getFunctionsOfGivenSignature(calleeTypeSig)
    calleeFuncNames = [func.name for func in calleeFuncs]
  else:
    calleeFuncNames = [callExpr.getFuncName()]

  assert calleeFuncNames != [None], f"{func.name}, {callExpr}, {callExpr.info}"
  return calleeFuncNames


def getFuncCalleeInfos(func: constructs.Func) -> List[CalleeInfo]:
  """
  Return the list of callees of the given function.
  If a call is function pointer based, it returns all the
  functions with the same signature as the function pointer
  present in the translation unit.
  """
  callees: List[CalleeInfo] = []
  tUnit = func.tUnit
  assert isinstance(tUnit, tunit.TranslationUnit), f"{tUnit}"

  for callExpr in map(lambda x: instr.getCallExpr(x), func.yieldInstrSeq()):
    if callExpr is not None:
      callees.append(CalleeInfo(
        caller=func,
        callExpr=callExpr,
        calleeNames=getExprCallees(func, callExpr),
      ))
  return callees

