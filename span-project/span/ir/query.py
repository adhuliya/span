#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
This file has utility functions for syntactic queries on the IR.
"""

import logging

LOG = logging.getLogger("span")

from typing import Dict, List, Callable, Any
import functools

from span.util.logger import LS
import span.ir.types as types
import span.ir.instr as instr
import span.ir.expr as expr
import span.ir.op as op
from span.ir.tunit import TranslationUnit

import span.ir.constructs as constructs

FUNC_WITH_BODY = True

################################################################
# BLOCK START: queries_on_a_function
################################################################

################################################
# BLOCK START: counting_queries
################################################

#@functools.lru_cache(200)
def countFunctionCalls(func: constructs.Func) -> int:
  """
  Returns the count of call sites in the function body.
  Functions with no function calls are leaf nodes in a call graph.
  """
  calls = 0
  for insn in func.yieldInstrSeq():
    if instr.getCallExpr(insn):
      calls += 1
  return calls


#@functools.lru_cache(200)
def countDerefsUsed(func: constructs.Func) -> int:
  """Returns the number of deref expressions in a function."""
  derefs = 0
  for insn in func.yieldInstrSeq():
    if instr.getDerefExpr(insn):
      derefs += 1
  return derefs


#@functools.lru_cache(200)
def countDerefsUsedLhs(func: constructs.Func) -> int:
  """Returns the number of deref expressions in a function."""
  derefs = 0
  for insn in func.yieldInstrSeq():
    if insn.needsLhsDerefSim():
      derefs += 1
  return derefs


#@functools.lru_cache(200)
def countDerefsUsedRhs(func: constructs.Func) -> int:
  """Returns the number of deref expressions in a function."""
  derefs = 0
  for insn in func.yieldInstrSeq():
    if insn.needsRhsDerefSim():
      derefs += 1
  return derefs


def countModOperators(func: constructs.Func) -> int:
  modCount = 0
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.AssignI):
      if isinstance(insn.rhs, expr.BinaryE):
        if insn.rhs.opr == op.BO_MOD:
          modCount += 1
  return modCount


def countMemoryAllocations(func: constructs.Func) -> int:
  """Returns count of memory locations done in the function."""
  memallocs = 0
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.AssignI):
      if isinstance(insn.rhs, expr.AddrOfE):
        if isinstance(insn.rhs.arg, expr.PseudoVarE):
          memallocs += 1
  return memallocs

def countNodes(func: constructs.Func) -> int:
  """Returns the total number of nodes in the func cfg"""
  if func.hasBody():
    assert func.cfg is not None, f"{func}"
    return len(func.cfg.nodeMap)
  return 0

################################################
# BLOCK END  : counting_queries
################################################

################################################
# BLOCK START: boolean_queries
################################################

# boolean queries

def hasDefinition(func: constructs.Func) -> bool:
  return func.hasBody()


def isVariadic(func: constructs.Func) -> bool:
  return func.sig.variadic


def hasPointerReturnType(func: constructs.Func) -> bool:
  return isinstance(func.sig.returnType, types.Ptr)


################################################
# BLOCK END  : boolean_queries
################################################

################################################
# BLOCK START: other_queries
################################################

def getPointerParameters(
    func: constructs.Func,
) -> List[types.VarNameT]:
  """Returns list of the function parameters which are pointers."""
  ptrParams = []
  for paramType, paramName in zip(func.sig.paramTypes, func.paramNames):
    if isinstance(paramType, types.Ptr):
      ptrParams.append(paramName)
  return ptrParams

################################################
# BLOCK END  : other_queries
################################################

################################################################
# BLOCK END  : queries_on_a_function
################################################################


################################################################
# BLOCK START: queries_on_translation_unit
################################################################

def filterFunctions(
    tunit: TranslationUnit,
    predicate: Callable
) -> List[constructs.Func]:
  """Returns the list of functions that satisfy the predicate."""
  return list(filter(predicate, tunit.yieldFunctions()))


def totalCountOnFunctions(
    tunit: TranslationUnit,
    counter: Callable,
    funcWithBody: bool = False, # True if the counter needs func with body only
) -> int:
  """Sums the count given by counter() on each function in the translation unit.

  Args:
    tunit: The Translation Unit object.
    counter: A callable counter that counts a specific thing.
    funcWithBody: Select functions with body (default False)
  Returns:
    The sum of all the return values of counter() on each function.
  """
  count = 0
  for func in tunit.yieldFunctions():
    if funcWithBody and not func.hasBody():
      continue
    count += counter(func)
  return count

################################################################
# BLOCK END  : queries_on_translation_unit
################################################################


def executeAllQueries(tUnit: TranslationUnit):
  p = print
  p(f"Query Results on translation unit '{tUnit.name}'")
  p("TotalFunctions:", totalCountOnFunctions(tUnit, lambda _: 1))
  p("TotalFunctions(WithDef):", totalCountOnFunctions(tUnit, hasDefinition))
  p("TotalFunctions(WithoutDef):",
    totalCountOnFunctions(tUnit, lambda x: not hasDefinition(x)))
  p("TotalFunctions(Variadic):", totalCountOnFunctions(tUnit, isVariadic, FUNC_WITH_BODY))
  p("Nodes(total):", totalCountOnFunctions(tUnit, countNodes, FUNC_WITH_BODY))
  p("Nodes(maxInAFunc):", tUnit.maxCfgNodesInAFunction())
  p("DerefsUsed(all):", totalCountOnFunctions(tUnit, countDerefsUsed, FUNC_WITH_BODY))
  p("DerefsUsed(Lhs):", totalCountOnFunctions(tUnit, countDerefsUsedLhs, FUNC_WITH_BODY))
  p("DerefsUsed(Rhs):", totalCountOnFunctions(tUnit, countDerefsUsedRhs, FUNC_WITH_BODY))


