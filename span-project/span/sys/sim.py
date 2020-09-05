#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Simplification related utilities..."""

import logging

LOG = logging.getLogger("span")

from typing import Dict, Tuple, Set, List, Callable
from typing import Optional as Opt
from collections import deque
import time
import io

import span.ir.types as types
import span.ir.expr as expr
import span.api.sim as simApi
from span.api.sim import SimPending, SimFailed, SimNameT
from span.api.analysis import AnalysisNameT

# simpliciation names
Node__to__Nil__Name: str = simApi.SimAT.Node__to__Nil.__name__
LhsVar__to__Nil__Name: str = simApi.SimAT.LhsVar__to__Nil.__name__
Num_Var__to__Num_Lit__Name: str = simApi.SimAT.Num_Var__to__Num_Lit.__name__
Cond__to__UnCond__Name: str = simApi.SimAT.Cond__to__UnCond.__name__
Num_Bin__to__Num_Lit__Name: str = simApi.SimAT.Num_Bin__to__Num_Lit.__name__
Deref__to__Vars__Name: str = simApi.SimAT.Deref__to__Vars.__name__


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


