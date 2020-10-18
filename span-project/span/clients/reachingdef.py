#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Reaching Def Analysis

This (and every) analysis subclasses,
* span.sys.lattice.DataLT (to define its lattice)
* span.sys.analysis.AnalysisAT (to define the analysis)
"""

import logging
LOG = logging.getLogger("span")

from typing import Tuple, Dict, List, Optional as Opt, Set
import io

import span.util.util as util
from span.util.util import LS, AS
import span.util.data as data

import span.ir.ir as ir
import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs

from span.api.lattice import (ChangedT, Changed, DataLT,
                              basicLessThanTest, basicEqualTest)
import span.api.dfv as dfv
import span.api.analysis as analysis
from span.ir.conv import (simplifyName, isCorrectNameFormat, genFuncNodeId,
                          GLOBAL_INITS_FUNC_ID)


################################################
# BOUND START: ReachingDef lattice.
################################################

class ComponentL(DataLT):


  def __init__(self,
      func: constructs.Func,
      val: Opt[Set[types.FuncNodeIdT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)


  def meet(self,
      other: 'ComponentL'
  ) -> Tuple['ComponentL', ChangedT]:
    tup = self.basicMeetOp(other)
    if tup: return tup

    new = self.getCopy()
    new.val.update(other.val)
    return new, Changed


  def __lt__(self,
      other: 'ComponentL'
  ) -> bool:
    lt = basicLessThanTest(self, other)
    return self.val >= other.val if lt is None else lt


  def getCopy(self) -> 'ComponentL':
    if self.top: return ComponentL(self.func, top=True)
    if self.bot: return ComponentL(self.func, bot=True)

    return ComponentL(self.func, self.val.copy())


  def __len__(self):
    if self.top: return 0
    if self.bot: return 0x7FFFFFFF  # a large number

    assert len(self.val), "Defs should be one or more"
    return len(self.val)


  def __contains__(self, fNid: types.FuncNodeIdT):
    if self.top: return False
    if self.bot: return True
    return fNid in self.val


  def addVal(self, fNid: types.FuncNodeIdT) -> None:
    if self.top:
      self.val = set()
      self.top = False
    self.val.add(fNid)


  def delVal(self, fNid: types.FuncNodeIdT) -> None:
    if self.top:
      return None

    self.val.remove(fNid)
    if not len(self.val):
      self.top = True
      self.val = None


  def __eq__(self,
      other: 'ComponentL'
  ) -> bool:
    if not isinstance(other, ComponentL):
      return NotImplemented
    equal = basicEqualTest(self, other)
    return self.val == other.val if equal is None else equal


  def __hash__(self):
    val = frozenset(self.val) if self.val else None
    return hash((self.func.name, val, self.top, self.bot))


  def __str__(self):
    if self.top: return "Top"
    if self.bot: return "Bot"
    return f"{self.val}"


  def __repr__(self):
    return self.__str__()


class OverallL(dfv.OverallL):
  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[types.VarNameT, dfv.ComponentL]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot, ComponentL, "const")
    # self.componentTop = ComponentL(self.func, top=True)
    # self.componentBot = ComponentL(self.func, bot=True)


  def getDefaultVal(self,
      varName: Opt[types.VarNameT] = None
  ) -> Opt[ComponentL]:
    if varName is None: return None

    assert isCorrectNameFormat(varName), f"{varName}"
    if self.func.isParamName(varName):
      # this default value is only used in intra-procedural analysis
      # in inter-procedural analysis, params are defined in the caller,
      # and only in case of main() function this is useful.
      fNid = genFuncNodeId(self.func.id, 1)  # node 1 is always NopI()
    elif self.func.isLocalName(varName):
      fNid = genFuncNodeId(self.func.id, 0)  # i.e. uninitialized
    else:
      # assume a global variable ("g:..." or an address taken global)
      fNid = genFuncNodeId(GLOBAL_INITS_FUNC_ID, 1)  # initialized global
    return ComponentL(self.func, val={fNid})


  def getAllVars(self) -> Set[types.VarNameT]:
    """Return a set of vars the analysis is tracking.
    One must override this method if variables are other
    than numeric.
    """
    return ir.getNamesEnv(self.func)


################################################
# BOUND END  : ReachingDef lattice.
################################################

