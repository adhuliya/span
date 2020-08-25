#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Inter-Procedural Analysis (IPA) IR module.
Prepares the IR for the IPA.
"""

import logging

LOG = logging.getLogger("span")

from typing import Dict, Tuple, Set, List, Callable
from typing import Optional as Opt
from collections import deque
import time
import io

from span.ir import expr, instr, constructs, tunit
from span.ir import graph
from span.ir import types


# mainentry for IPA preProcess
def preProcess(tUnit: tunit.TranslationUnit):
  """
  This function prepares the TranslationUnit object for IPA.
  Basically it augments the caller function's basic block
  with param assign and return value assign instructions.
  """
  prepareFunctionsForIpa(tUnit)
  # NOTE: add all IPA related operations here


def generateCallSiteParamAssigns(callE: expr.CallE,
    tUnit: tunit.TranslationUnit,
) -> Opt[List[instr.AssignI]]:
  """
  Returns the sequence of param assigment
  instructions for a call site.
  For a pointer based call it returns None.
  """

  if callE.isPointerCall():
    return None  # IMPORTANT

  func: constructs.Func = tUnit.getFunctionObj(callE.callee.name)

  if func.sig.variadic:
    return None  # FIXME: we don't handle variadic function calls

  insns: List[instr.AssignI] = []
  for i, arg in enumerate(callE.args):
    assert len(callE.args) == len(func.paramNames), f"{callE}: {func.paramNames}"
    insn = instr.AssignI(lhs=expr.VarE(name=func.paramNames[i], info=arg.info),
                         rhs=arg,
                         info=arg.info)
    tUnit.inferTypeOfInstr(insn)
    insns.append(insn)

  return insns


def generateCallSiteReturnAssigns(insn: instr.AssignI,
    tUnit: tunit.TranslationUnit,
) -> Opt[instr.InstrIT]:
  """
  If a call's value is assigned to a variable, then
  return a list of assignments corresponding to the
  possible returned values from the called function.
  If its a pointer based call, then return None.
  """
  assert isinstance(insn, instr.AssignI), f"{insn}"

  callE = insn.rhs
  assert isinstance(callE, expr.CallE), f"{insn.rhs}"
  if callE.isPointerCall():
    return None

  func = tUnit.getFunctionObj(callE.callee.name)
  returnExprs = getReturnExprList(func)
  if returnExprs is None:
    return None
  if len(returnExprs) == 0:  #FIXME: remove this if and correct slang checker
    return None

  assert len(returnExprs) > 0, f"{returnExprs} {func.name}"
  if len(returnExprs) == 1:
    ins: instr.InstrIT = instr.AssignI(lhs=insn.lhs,
                                       rhs=returnExprs[0], info=insn.lhs.info)
  else:
    ins = instr.ParallelI.genPrallelMultiAssign(lhs=insn.lhs,
                                                rhsList=returnExprs)  # type: ignore

  tUnit.inferTypeOfInstr(ins)
  return ins


def getReturnExprList(func: constructs.Func) -> Opt[List[expr.SimpleET]]:
  """
  Returns the expressions (which are always of type expr.UnitET)
  that the function returns.
  If the function's return type is void, it returns None
  FIXME: process only those returns that are reachable (for precision)
  TODO: cache the results.
  """
  if func.sig.returnType == types.Void or not func.hasBody():
    # a void function has no return expression
    # and so does a function with no body
    return None

  exprSet: Set[expr.SimpleET] = set()
  for insn in func.yieldInstrSeq():
    if isinstance(insn, instr.ReturnI):
      assert insn.arg is not None, f"{func.name}: {insn}"
      exprSet.add(insn.arg)  # arg cannot be None
  return list(exprSet)


def prepareFunctionsForIpa(tUnit: tunit.TranslationUnit):
  """
  It prepares the functions for the inter-procedural analysis (ipa)
  Basically it augments the caller function's basic block
  with param assign and return value assign instructions.
  """

  for func in tUnit.yieldFunctionsWithBody():
    bbMap = func.basicBlocks
    print(func.name)  # delit
    changed = insertIpaInstructions(bbMap, tUnit)
    if changed:
      func.cfg = graph.Cfg(func.name, bbMap, func.bbEdges)  # bbEdges dont change


def insertIpaInstructions(
    bbMap: Dict[types.BasicBlockIdT, List[instr.InstrIT]],
    tUnit: tunit.TranslationUnit
) -> bool:
  """
  Adds the inter-procedural analysis (ipa) instructions:
    1. Call parameter assignments
    2. Return value assignments
  to the basic blocks
  Returns true if any basic block is changed.
  """

  changed = False

  for bbId in bbMap.keys():
    bb = bbMap[bbId]
    newBb = []

    for insn in bb:
      callE = instr.getCallExpr(insn)
      if callE is None:
        newBb.append(insn)
        continue

      # If here, then a call expression has been encountered,
      # now generate the ipa instructions around it
      paramAssigns = generateCallSiteParamAssigns(callE, tUnit)
      returnAssign = None
      if isinstance(insn, instr.AssignI):
        returnAssign = generateCallSiteReturnAssigns(insn, tUnit)

      # STEP 1: Now add the ipa instructions around the call site
      if paramAssigns:
        changed = True
        newBb.extend(paramAssigns)

      # STEP 2: add the original call instruction
      newBb.append(insn)

      # STEP 3: Now add the return assignment, if relevant
      if returnAssign:
        changed = True
        newBb.append(returnAssign)

    bbMap[bbId] = newBb  # update the new bb

  return changed
