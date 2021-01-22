#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Reachability analysis.

This (and every) analysis subclasses,
* span.api.lattice.LatticeLT (to define its lattice)
* span.api.analysis.AnalysisAT (to define the analysis)
"""

import logging

LOG = logging.getLogger("span")
from typing import Tuple, List, Optional as Opt

import span.ir.types as types
import span.ir.instr as instr
import span.ir.constructs as obj
import span.ir.tunit as irTUnit

from span.api.lattice import ChangeL, Changed, NoChange, DataLT
from span.api.dfv import NodeDfvL
import span.api.sim as sim
import span.api.analysis as analysis


################################################
# BOUND START: Reachability_Lattice
################################################

class OverallL(DataLT):


  def __init__(self,
      func: obj.Func,
      top: bool = False,
      bot: bool = False
  ) -> None:
    # if bot==True then reachable.
    super().__init__(func, val=bot, top=top, bot=bot)


  def __lt__(self,
      other: 'OverallL'
  ) -> bool:
    if self.bot: return True
    if other.bot: return False
    return True  # both are top


  def __eq__(self,
      other: 'OverallL'
  ) -> bool:
    if self.val == other.val: return True
    return False


  def meet(self,
      other: 'OverallL'
  ) -> Tuple['OverallL', ChangeL]:
    if self.bot: return self, NoChange
    if other.bot: return other, Changed
    return self, NoChange


  def getCopy(self):
    return self


  def __str__(self):
    if self.bot: return "Reachable."
    return "UnReachable."


  def __repr__(self):
    return self.__str__()


################################################
# BOUND END  : Reachability_Lattice
################################################

################################################
# BOUND START: Reachability_Analysis
################################################

class ReachA(analysis.AnalysisAT):
  """Reachability Analysis."""
  L: type = OverallL
  D: Opt[types.DirectionT] = Forward
  simNeeded: List[type] = []


  def __init__(self,
      func: obj.Func,
  ) -> None:
    self._theTop: OverallL = OverallL(func, top=True)  # unreachable
    self._theBot: OverallL = OverallL(func, bot=True)  # reachable
    self.tUnit: irTUnit.TranslationUnit = func.tUnit
    super().__init__(func)


  def getBoundaryInfo(self,
      inBi: Opt[DataLT] = None,
      outBi: Opt[DataLT] = None,
  ) -> Tuple[OverallL, OverallL]:
    if inBi is None:
      # in of start is always reachable
      startBi = self._theBot
    else:
      startBi = self._theBot  # TODO

    # no boundary information at out of end node
    # since this analysis is forward only
    endBi = self._theTop

    return startBi, endBi


  def Nop_Instr(self,
      nodeId: types.NodeIdT,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    dfvIn = nodeDfv.dfvIn
    return NodeDfvL(dfvIn, dfvIn)


  def Return_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return NodeDfvL(nodeDfv.dfvIn, self._theTop)


  def Return_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.ReturnI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return NodeDfvL(nodeDfv.dfvIn, self._theTop)


  def Node__to__Nil(self,
      nodeId: types.NodeIdT,
      nodeDfv: NodeDfvL,
  ) -> sim.SimToNilL:
    # sim.SimToNilPending is never returned
    if nodeDfv.dfvIn.bot: return sim.SimToNilFailed
    return sim.SimToNilSuccessful

################################################
# BOUND END  : Reachability_Analysis
################################################
