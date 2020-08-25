#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Utility file to operate on the parts of the IR.
This module may import all other modules in `span.ir`.
(Thus to avoid cyclic dependence no other module in span.ir
should import this module)
"""
import io
from typing import List

import span.ir.tunit as tunit
from span.ir import graph, constructs, instr, expr, types


def generateCallGraph(tUnit: tunit.TranslationUnit) -> graph.CallGraph:
  """Generates and returns the CallGraph object of the tUnit."""
  cg = graph.CallGraph()
  for func in tUnit.yieldFunctions():
    callees = []
    if func.hasBody():
      callees = getCallees(func)
    cg.callGraph[func.name] = callees

  return cg


def getCallees(func: constructs.Func) -> List[graph.CalleeInfo]:
  """
  Return the list of callees of the given function.
  If a call is function pointer based, it returns all the
  functions with the same signature as the function pointer
  present in the translation unit.
  """
  callees: List[graph.CalleeInfo] = []
  tUnit = func.tUnit
  assert isinstance(tUnit, tunit.TranslationUnit), f"{tUnit}"

  for insn in func.yieldInstrSeq():
    callExpr = instr.getCallExpr(insn)
    if callExpr is not None:
      # there is a call expression in rhs
      if callExpr.isPointerCall():
        # a function pointer is used to make the call
        calleeTypeSig = callExpr.getCalleeSignature()
        calleeFuncs = tUnit.getFunctionsOfGivenSignature(calleeTypeSig)
        calleeFuncNames = [func.name for func in calleeFuncs]
        callees.append(
          graph.CalleeInfo(
            callExpr=callExpr,
            caller=func.name,
            calleeNames=calleeFuncNames
          )
        )
      else:
        callees.append(graph.CalleeInfo(
          callExpr=callExpr,
          caller=func.name,
          calleeNames=[callExpr.callee.name])
        )
  return callees


def getCallGraphDot(callGraph: graph.CallGraph) -> str:
  """ Returns Dot graph string of the given callGraph. """
  if not len(callGraph.callGraph):
    return "digraph{}"

  ret = None
  with io.StringIO() as sio:
    sio.write("digraph {\n  node [shape=box]\n")
    for funcName, callees in callGraph.callGraph.items():
      suffix = ""
      if not len(callees):
        suffix = ", color=blue, penwidth=4"
      content = f"""  "{funcName}" [label=\"{funcName}\"{suffix}];\n"""
      sio.write(content)
    sio.write("\n")

    for funcName, callees in callGraph.callGraph.items():
      for callee in callees:
        suffix = ""
        if callee.callExpr.isPointerCall():
          suffix = "[color=red, penwidth=2]"

        if not len(callee.calleeNames):
          content = f"""  "{funcName}" -> "None" [style=dotted, color=red];\n"""
          sio.write(content)
        else:
          for calleeName in callee.calleeNames:
            content = f"""  "{funcName}" -> "{calleeName}" {suffix};\n"""
            sio.write(content)

    sio.write("}\n")
    ret = sio.getvalue()
  return ret
