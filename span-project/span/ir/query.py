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
    if isinstance(insn, instr.AssignI):
      derefs += int(insn.lhs.hasDereference())
  return derefs


#@functools.lru_cache(200)
def countDerefsUsedRhs(func: constructs.Func) -> int:
  """Returns the number of deref expressions in a function."""
  derefs = 0
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.AssignI):
      derefs += int(insn.rhs.hasDereference())
  return derefs


def countModOperators(func: constructs.Func) -> int:
  """Count of expressions with mod ("%") operator in them."""
  modCount = 0
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.AssignI):
      if isinstance(insn.rhs, expr.BinaryE):
        if insn.rhs.opr == op.BO_MOD:
          modCount += 1
  return modCount


def countModByTwoOperators(func: constructs.Func) -> int:
  """Count of expressions with mod by 2 ("% 2") in them."""
  modCount = 0
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.AssignI):
      if isinstance(insn.rhs, expr.BinaryE):
        if insn.rhs.opr == op.BO_MOD\
            and isinstance(insn.rhs.arg2, expr.LitE)\
            and insn.rhs.arg2.val == 2:
          modCount += 1
  return modCount


def countMemoryAllocations(func: constructs.Func) -> int:
  """Returns count of memory allocations done in the function."""
  memallocs = 0
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.AssignI):
      if isinstance(insn.rhs, expr.AddrOfE):
        if isinstance(insn.rhs.arg, expr.PseudoVarE):
          memallocs += 1
      elif instr.getCalleeFuncName(insn) in ("f:calloc", "f:malloc"):
        memallocs += 1
  return memallocs


def countMemoryAllocationsPseudoVar(func: constructs.Func) -> int:
  """Returns count of memory allocations done with pseudo var."""
  memallocs = 0
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.AssignI):
      if isinstance(insn.rhs, expr.AddrOfE):
        if isinstance(insn.rhs.arg, expr.PseudoVarE):
          memallocs += 1
  return memallocs


def countMemoryAllocationsWithoutPseudoVar(func: constructs.Func) -> int:
  """Returns count of memory allocations done without pseudo vars."""
  memallocs = 0
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.AssignI):
      if instr.getCalleeFuncName(insn) in ("f:calloc", "f:malloc"):
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


def countOnFunctions(
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
  lst = tunit.yieldFunctionsWithBody if funcWithBody else tunit.yieldFunctions
  return sum(map(counter, lst()))

################################################################
# BLOCK END  : queries_on_translation_unit
################################################################


def executeAllQueries(tUnit: TranslationUnit):
  p = print
  p(f"Query Results on translation unit '{tUnit.name}'")
  p("TotalFunctions:", countOnFunctions(tUnit, lambda _: 1))
  p("TotalFunctions(WithDef):", countOnFunctions(tUnit, hasDefinition))
  p("TotalFunctions(WithoutDef):",
    countOnFunctions(tUnit, lambda x: not hasDefinition(x)))
  p("TotalFunctions(Variadic):", countOnFunctions(tUnit, isVariadic, FUNC_WITH_BODY))
  p("Nodes(total):", countOnFunctions(tUnit, countNodes, FUNC_WITH_BODY))
  p("Nodes(maxInAFunc):", tUnit.maxCfgNodesInAFunction())
  p("DerefsUsed(all):", countOnFunctions(tUnit, countDerefsUsed, FUNC_WITH_BODY))
  p("DerefsUsed(Lhs):", countOnFunctions(tUnit, countDerefsUsedLhs, FUNC_WITH_BODY))
  p("DerefsUsed(Rhs):", countOnFunctions(tUnit, countDerefsUsedRhs, FUNC_WITH_BODY))
  p("TotalModOperations:", countOnFunctions(tUnit, countModOperators, FUNC_WITH_BODY))
  p("TotalModByTwoOperations:", countOnFunctions(tUnit, countModByTwoOperators, FUNC_WITH_BODY))
  p("TotalFuncWithModByTwoOperations:",
    len(filterFunctions(tUnit, lambda x: bool(countModByTwoOperators(x)))))
  p("TotalMemAllocations:", countOnFunctions(tUnit, countMemoryAllocations, FUNC_WITH_BODY))
  p("TotalMemAllocationsPseudoVar:",
    countOnFunctions(tUnit, countMemoryAllocationsPseudoVar, FUNC_WITH_BODY))
  p("TotalMemAllocationsWithoutPseudoVar:",
    countOnFunctions(tUnit, countMemoryAllocationsWithoutPseudoVar, FUNC_WITH_BODY))
  p("TotalFuncWithMemAllocations:",
    #len(filterFunctions(tUnit, lambda x: bool(countMemoryAllocations(x)))))
    list(map(lambda x: x.name, filterFunctions(tUnit, lambda x: bool(countMemoryAllocations(x))))))


