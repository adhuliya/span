#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The analysis' simplification(Sim)/evaluation interface."""

import logging

LOG = logging.getLogger("span")
from span.util.logger import LS

from typing import List, Optional as Opt, Dict, Set
from span.ir.types import VarNameT, NumericT, NodeIdT
from span.ir.conv import Forward, Backward
import span.ir.expr as expr
from span.api.dfv import NodeDfvL
import span.ir.conv as conv

# simplification function names (that contain '__to__' in their name)
SimNameT = str
SimT = Opt[Set]
SimFailed: SimT = None  # None represents a simplification failure
SimPending: SimT = set()  # an empty set represents sim is pending

ValueTypeT = str
NumValue: ValueTypeT = "Num"
BoolValue: ValueTypeT = "Bool"
NameValue: ValueTypeT = "VarName"


################################################
# BOUND START: Simplification_base_class.
################################################

class SimAT:
  """Simplification functions to be (optionally) overridden.

  For convenience, analysis.AnalysisAT inherits this class.
  So the user may only inherit AnalysisAT class, and
  override functions in this class only if the
  analysis works as a simplifier too.

  The second argument, nodeDfv, if its None,
  means that the return value should be either
  Pending if the expression provided
  can be possibly simplified by the analysis,
  or Failed if the expression cannot be simplified
  given any data flow value.
  """

  __slots__: List[str] = []


  def Node__to__Nil(self,
      node: NodeIdT,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[bool] = None,
  ) -> Opt[bool]:
    """Node is simplified to Nil if its basically unreachable."""
    raise NotImplementedError()


  def LhsVar__to__Nil(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[bool]] = None,
  ) -> Opt[List[bool]]:
    """Returns a set of live variables at out of the node."""
    raise NotImplementedError()


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[NumericT]] = None,
  ) -> Opt[List[NumericT]]:
    """Simplify to a single literal if the expr can take that value."""
    raise NotImplementedError()


  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[NumericT]] = None,
  ) -> Opt[List[NumericT]]:
    """Simplify to a single literal if the variable can take that value."""
    raise NotImplementedError()


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[bool] = None,
  ) -> Opt[bool]:
    """Simplify conditional jump to unconditional jump."""
    raise NotImplementedError()


  def Deref__to__Vars(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
      values: Opt[List[VarNameT]] = None
  ) -> Opt[List[VarNameT]]:
    """Simplify a deref expr de-referencing varName
    to a set of var pointees."""
    raise NotImplementedError()


################################################
# BOUND END  : Simplification_base_class.
################################################

def extractSimNames() -> Set[str]:
  """returns set of expr simplification func names (these names have `__to__` in them)."""
  tmp = set()
  for memberName in SimAT.__dict__:
    if memberName.find("__to__") >= 0:
      tmp.add(memberName)
  return tmp


simNames: Set[str] = extractSimNames()

Node__to__Nil__Name: str = SimAT.Node__to__Nil.__name__
LhsVar__to__Nil__Name: str = SimAT.LhsVar__to__Nil.__name__
Num_Var__to__Num_Lit__Name: str = SimAT.Num_Var__to__Num_Lit.__name__
Cond__to__UnCond__Name: str = SimAT.Cond__to__UnCond.__name__
Num_Bin__to__Num_Lit__Name: str = SimAT.Num_Bin__to__Num_Lit.__name__
Deref__to__Vars__Name: str = SimAT.Deref__to__Vars.__name__

simDirnMap = {  # the IN/OUT information needed for the sim
  Node__to__Nil__Name:        conv.Forward,  # means dfv at IN is needed
  Num_Var__to__Num_Lit__Name: conv.Forward,
  Cond__to__UnCond__Name:     conv.Forward,
  Num_Bin__to__Num_Lit__Name: conv.Forward,
  Deref__to__Vars__Name:      conv.Forward,
  LhsVar__to__Nil__Name:      conv.Backward,  # means dfv at OUT is needed
}
