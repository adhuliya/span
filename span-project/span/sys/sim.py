#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""Simplification related utilities..."""

import logging
_LOG = logging.getLogger(__name__)
LDB = _LOG.debug

from typing import List, Set, Dict
from typing import Optional as Opt

from span.sys.clients import getAnObj

from span.api.dfv import DfvPairL
from span.ir import cfg
from span.ir.constructs import Func
from span.ir.expr import ExprET
from span.ir.types import AnNameT
import span.util.util as util

from span.api.analysis import SimPending, SimFailed, SimNameT


class SimRecord:


  def __init__(self,
      simName: SimNameT,
      sim: Opt[List] = None,
  ) -> None:
    self.simName = simName
    self._sim = sim


  def hasFailedValue(self):
    return self._sim is SimFailed


  def getSim(self):
    """Returns the simplification and also ensures that the
    client asking the sim is also added in the set of clients."""
    return self._sim


  def setSimValue(self, value: Opt[List]) -> bool:
    """Returns true if the value has changed."""
    # TODO: add monotonicity check
    changed = False
    if self._sim != value:
      changed = True
    self._sim = value
    return changed


  def __bool__(self):
    return self._sim is not SimFailed


  def __eq__(self, other) -> bool:
    if self is other: return True
    if not isinstance(other, SimRecord):
      return False
    elif not self.simName == other.simName:
      return False
    elif not self._sim == other._sim:
      return False
    return True


  def __hash__(self):
    ss = self._sim
    return hash((self.simName, len(ss) if ss else 0))


  def __str__(self):
    return f"SimRecord({self.simName}, {self._sim})"


  def __repr__(self):
    return self.__str__()


def computeSimAlgo04(
    func: Func,
    node: cfg.CfgNode,
    simName: SimNameT,
    nodeDfvs: Dict[AnNameT, DfvPairL], # data flow values
    e: Opt[ExprET] = None,  # could be None (in case of Node__to__Nil)
    transform: bool = False, # False = by default use SPAN
) -> Opt[Set]:  # A None value indicates failed sim
  """Collects and merges the simplification by various analyses.
  Step 1: Select one working simplification from any one analysis.
  Step 2: Refine the simplification.
  This function automatically handles Lerner and Cascading as both
  depend on the data flow value computed and the transform flag.
  TODO: Test this function.
  """
  if not nodeDfvs:
    if util.LL4: LDB("SimplifyingExpr(%s): for sim %s: Failed since no dfvs.",
                     e, simName)
    return SimFailed  # no sim analyses -- hence fail

  anNames = sorted(nodeDfvs.keys())

  # Step 1: Find the first useful result
  if util.LL4: LDB("SimplifyingExpr(%s): for sim %s: with %s.",
                   e, simName, anNames)
  sim: Opt[Set] = SimFailed
  for anName in anNames:    # loop to select the first working sim
    anObj = getAnObj(anName, func)
    simFunc = getattr(anObj, simName, None)
    if simFunc:
      sim = simFunc(e, nodeDfvs[anName])
      if sim is not SimFailed:
        break # break at the first useful value

  # Step 2: Refine the simplification
  if sim not in (SimPending, SimFailed): # failed/pending values can never be refined
    if util.LL4: LDB("SimplifyingExpr(%s): Refining(Start): %s.", sim)
    for anName in anNames:
      anObj = getAnObj(anName, func)
      simFunc = getattr(anObj, simName, None)
      if simFunc:
        sim = simFunc(e, nodeDfvs[anName], sim)
      assert sim != SimFailed, f"{anName}, {simName}, {node}, {e}, {sim}"
      if sim == SimPending:
        break  # no use to continue
    if util.LL4: LDB("SimplifyingExpr(%s): Refining(End): %s.", sim)

  # Step 3: Disable some sims that are not possible in transformation.
  if transform and sim and len(sim) > 1:
    sim = SimFailed
    if util.LL4: LDB("SimplifyingExpr(%s): Transform: %s became SimFailed.", sim)

  return sim  # a refined result


