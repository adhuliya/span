#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Reaching Def Analysis

This (and every) analysis subclasses,
* span.sys.lattice.LatticeLT (to define its lattice)
* span.sys.analysis.AnalysisAT (to define the analysis)
"""

import logging

LOG = logging.getLogger("span")
from typing import Tuple, Dict, List, Optional, Set
import io

import span.util.util as util
from span.util.util import LS, AS
import span.util.messages as msg

import span.ir.ir as ir
import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.api.sim as sim

from span.api.lattice import ChangeL, Changed, NoChange, DataLT
from span.api.dfv import NodeDfvL
import span.api.sim as ev
import span.api.analysis as analysis


################################################
# BOUND START: ReachingDef lattice.
################################################

class ComponentL(DataLT):


  def __init__(self,
      func: constructs.Func,
      val: Optional[Set[types.NodeIdT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)


  def meet(self,
      other: 'ComponentL'
  ) -> Tuple['ComponentL', ChangeL]:
    if self is other: return self, NoChange
    if self < other: return self, NoChange
    if other < self: return other, Changed

    new = self.getCopy()
    for nid in other.val:
      new.val.add(nid)
    return new, Changed


  def getCopy(self) -> 'ComponentL':
    if self.top: return ComponentL(self.func, top=True)
    if self.bot: return ComponentL(self.func, bot=True)

    return ComponentL(self.func, self.val.copy())


  def __len__(self):
    if self.top: return 0
    if self.bot: return 0x7FFFFFFF  # a large number

    assert len(self.val), "Defs should be one or more"
    return len(self.val)


  def __contains__(self, nid: types.NodeIdT):
    if self.top: return False
    if self.bot: return True
    return nid in self.val


  def addNodeId(self, nid: types.NodeIdT) -> None:
    if self.top:
      self.val = set()
      self.top = False

    self.val.add(nid)


  def removeNodeId(self, nid: types.NodeIdT) -> None:
    if self.top:
      return None

    self.val.remove(nid)
    if not len(self.val):
      self.top = True
      self.val = None


  def __lt__(self,
      other: 'ComponentL'
  ) -> bool:
    if self.bot: return True
    if other.top: return True
    if other.bot: return False
    if self.top: return False

    # other should be a subset
    return self.val >= other.val


  def __eq__(self,
      other: 'ComponentL'
  ) -> bool:
    if self.top and other.top: return True
    if self.bot and other.bot: return True
    if self.bot and other.top: return False
    if self.top and other.bot: return False

    return self.val == other.val


  def __hash__(self):
    return hash(self.func.name) ^ hash((self.val, self.top, self.bot))


  def __str__(self):
    if self.top: return "Top"
    if self.bot: return "Bot"
    return f"{self.val}"


  def __repr__(self):
    return self.__str__()


class OverallL(DataLT):


  def __init__(self,
      func: constructs.Func,
      val: Optional[Dict[types.VarNameT, ComponentL]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.componentTop = ComponentL(self.func, top=True)
    self.componentBot = ComponentL(self.func, bot=True)


  def meet(self,
      other: 'OverallL'
  ) -> Tuple['OverallL', ChangeL]:
    if self is other: return self, NoChange
    if self < other:  return self, NoChange
    if other < self:  return other, Changed

    ret: Dict[types.VarNameT, ComponentL] = {}
    top = self.componentTop
    vnames = {vName for vName in self.val}
    vnames.update({vName for vName in other.val})
    for vName in vnames:
      dfv1 = self.val.get(vName, top)
      dfv2 = other.val.get(vName, top)
      dfv3, _ = dfv1.meet(dfv2)
      ret[vName] = dfv3

    new = OverallL(self.func, val=ret)
    return new, Changed


  def __lt__(self,
      other: 'OverallL'
  ) -> bool:
    if self.bot: return True
    if other.top: return True
    if other.bot: return False
    if self.top: return False

    # self and other are proper values
    top = self.componentTop
    varSet = {var for var in self.val}
    varSet.update({var for var in other.val})
    for vName in varSet:
      dfv1 = self.val.get(vName, top)
      dfv2 = other.val.get(vName, top)
      if not dfv1 < dfv2:
        return False
    return True


  def __eq__(self, other: 'OverallL'):
    """strictly equal check."""
    if self.top and other.top: return True
    if self.bot and other.bot: return True
    if self.top or self.bot: return False
    if other.top or other.bot: return False

    # self and other are proper values
    top = self.componentTop
    varSet = {var for var in self.val}
    varSet.update({var for var in other.val})
    for vName in varSet:
      dfv1 = self.val.get(vName, top)
      dfv2 = other.val.get(vName, top)
      if not dfv1 == dfv2:
        return False
    return True


  def __hash__(self):
    val = {} if self.val is None else self.val
    hashThisVal = frozenset(val.items())
    return hash(self.func) ^ hash((hashThisVal, self.top, self.bot))


  def getVal(self,
      varName: types.VarNameT
  ) -> ComponentL:
    """returns entity lattice value."""
    if self.top: return self.componentTop
    if self.bot: return self.componentBot

    return self.val.get(varName, self.componentTop)


  def setVal(self,
      varName: types.VarNameT,
      val: ComponentL
  ) -> None:
    if not self.val:
      self.val = dict()
      self.top = self.bot = False

    self.val[varName] = val


  def getCopy(self) -> 'OverallL':
    if self.top: return OverallL(self.func, top=True)
    if self.bot: return OverallL(self.func, bot=True)

    ret = OverallL(self.func, dict())
    for vName, val in self.val.items():
      ret.val[vName] = val
    return ret


  def getNodeIdSet(self,
      varName: types.VarNameT
  ) -> Optional[Set[types.VarNameT]]:
    if self.val:
      return self.val.get(varName, set())


  def __str__(self):
    if self.top and self.bot: return "TopBot(!)"
    if self.top: return "Top"
    if self.bot: return "Bot"

    string = io.StringIO()
    string.write("{")
    prefix = None
    for key in self.val:
      # if not ir.isUserVar(key): # added for ACM Winter School
      #   continue
      if ir.isDummyVar(key):  # skip printing dummy variables
        continue
      if prefix:
        string.write(prefix)
      prefix = ", "
      name = types.simplifyName(key)
      string.write(f"{name}: {self.val[key]}")
    string.write("}")
    return string.getvalue()


  def __repr__(self):
    if self.top: return f"reachingdef.OverallL({self.func}, top=True)"
    if self.bot: return f"reachingdef.OverallL({self.func}, bot=True)"

    string = io.StringIO()
    string.write("reachingdef.OverallL({")
    prefix = None
    for key in self.val:
      if prefix:
        string.write(prefix)
      prefix = ", "
      string.write(f"{key!r}: {self.val[key]!r}")
    string.write("})")
    return string.getvalue()


################################################
# BOUND END  : ReachingDef lattice.
################################################


################################################
# BOUND START: ReachingDefAnalysis
################################################

class ReachingDefA(analysis.AnalysisAT):
  """Reaching Definitions Analysis"""
  # TODO: implement the analysis
  # QQ. How go give unique nodeId for IPA?
  L: type = OverallL  # the lattice ConstA uses
  D: type = analysis.ForwardD  # its a forward flow analysis
  simNeeded: List[type] = [sim.SimAT.Deref__to__Vars,
                           sim.SimAT.LhsVar__to__Nil,
                           sim.SimAT.Cond__to__UnCond,
                           ]


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func)
    self.componentTop = ComponentL(self.func, top=True)
    self.componentBot = ComponentL(self.func, bot=True)
    self.overallTop = OverallL(self.func, top=True)
    self.overallBot = OverallL(self.func, bot=True)


  def getBoundaryInfo(self,
      inBi: Optional[DataLT] = None,
      outBi: Optional[DataLT] = None,
  ) -> Tuple[OverallL, OverallL]:
    if inBi is None:
      # all locations are unknown at start of the function
      startBi = self.overallBot  # must
    else:
      startBi = self.overallBot  # TODO

    # No boundary information at out of end node,
    # since this analysis is forward only.
    endBi = self.overallTop

    return startBi, endBi


  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def Nop_Instr(self,
      nodeId: types.NodeIdT,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """An identity forward transfer function."""
    dfvIn = nodeDfv.dfvIn
    return NodeDfvL(dfvIn, dfvIn)


  def Filter_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Filter away dead variables.
    The set of named locations that are dead."""
    dfvIn: OverallL = nodeDfv.dfvIn

    if not insn.varNames \
        or dfvIn.top:  # i.e. nothing to filter or no DFV to filter == Nop
      return self.Nop_Instr(nodeId, nodeDfv)

    newDfvOut: OverallL = dfvIn.getCopy()

    newDfvOut.filterVals(ir.filterNamesNumeric(self.func, insn.varNames))

    return NodeDfvL(dfvIn, newDfvOut)


  def UnDefVal_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if not insn.type.isNumeric():
      return self.Nop_Instr(nodeId, nodeDfv)

    oldIn = nodeDfv.dfvIn

    newOut = oldIn.getCopy()
    newOut.setVal(insn.lhs, self.componentBot)

    return NodeDfvL(oldIn, newOut)


  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################

  def Num_Assign_Var_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Deref_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_CastVar_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_SizeOf_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_UnaryArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_BinArith_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Select_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Array_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Member_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.rhs, nodeDfv.dfvIn)


  def Record_Assign_Var_Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Deref_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Deref_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Array_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Array_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Member_Lit_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Member_Var_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Conditional_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    oldIn: OverallL = nodeDfv.dfvIn
    # special case
    if isinstance(insn.arg.type, types.Ptr):
      return NodeDfvL(oldIn, oldIn)

    dfvFalse, dfvTrue = self.calcTrueFalseDfv(insn.arg, oldIn)

    return NodeDfvL(oldIn, None, dfvTrue, dfvFalse)


  def Call_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.arg, nodeDfv.dfvIn)


  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Simplifiers
  ################################################

  def Num_Var__to__Num_Lit(self,
      e: expr.VarE,
      nodeDfv: Optional[NodeDfvL] = None,
  ) -> sim.SimToNumL:
    # STEP 1: check if the expression can be evaluated
    varType = e.type
    if not varType.isNumeric():
      return sim.SimToNumFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToNumPending

    val = nodeDfv.dfvIn.getVal(e.name)
    if val.bot: return sim.SimToNumFailed  # cannot be evaluated
    if val.top: return sim.SimToNumPending  # can be evaluated, needs more info
    return sim.SimToNumL(val.val)


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Optional[NodeDfvL] = None,
  ) -> sim.SimToNumL:
    # STEP 1: check if the expression can be evaluated
    exprType = e.type
    arg1Type = e.arg1.type
    arg2Type = e.arg2.type

    if not exprType.isNumeric():
      return sim.SimToNumFailed
    if not arg1Type.isNumeric() or not arg2Type.isNumeric():
      return sim.SimToNumFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToNumPending

    if isinstance(e.arg1, expr.VarE):
      val1 = nodeDfv.dfvIn.getVal(e.arg1.name)
    else:  # a literal
      val1 = ComponentL(self.func, val=e.arg1.val)

    if val1.bot: return sim.SimToNumFailed
    if val1.top: return sim.SimToNumPending

    if isinstance(e.arg2, expr.VarE):
      val2 = nodeDfv.dfvIn.getVal(e.arg2.name)
    else:  # a literal
      val2 = ComponentL(self.func, val=e.arg2.val)

    if val2.bot: return sim.SimToNumFailed
    if val2.top: return sim.SimToNumPending

    opCode = e.opr.opCode
    if opCode == op.BO_ADD_OC:
      return sim.SimToNumL(val1.val + val2.val)
    elif opCode == op.BO_SUB_OC:
      return sim.SimToNumL(val1.val - val2.val)
    elif opCode == op.BO_MUL_OC:
      return sim.SimToNumL(val1.val * val2.val)
    elif opCode == op.BO_DIV_OC:
      if val2.val == 0:
        if LS: LOG.critical("DivideByZero: expr: %s, dfv: %s",
                            e, nodeDfv.dfvIn)
        return sim.SimToNumFailed
      else:
        return sim.SimToNumL(val1.val / val2.val)
    elif opCode == op.BO_MOD_OC:
      return sim.SimToNumL(val1.val % val2.val)
    elif opCode == op.BO_GT_OC:
      val = 1 if val1.val > val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_GE_OC:
      val = 1 if val1.val >= val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_LT_OC:
      val = 1 if val1.val < val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_LE_OC:
      val = 1 if val1.val <= val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_EQ_OC:
      val = 1 if val1.val == val2.val else 0
      return sim.SimToNumL(val)
    elif opCode == op.BO_NE_OC:
      val = 1 if val1.val != val2.val else 0
      return sim.SimToNumL(val)

    return sim.SimToNumFailed


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Optional[NodeDfvL] = None
  ) -> sim.SimToBoolL:
    # STEP 1: check if the expression can be evaluated
    exprType = e.type
    if not exprType.isNumeric():
      return sim.SimToBoolFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToBoolPending

    val: ComponentL = nodeDfv.dfvIn.getVal(e.name)
    if val.bot: return sim.SimToBoolFailed  # cannot be evaluated
    if val.top:
      nameType = ir.inferTypeOfVal(self.func, e.name)
      if isinstance(nameType, types.Ptr):
        return sim.SimToBoolFailed
      else:
        return sim.SimToBoolPending  # can be evaluated, needs more info
    if val.val != 0:
      return sim.SimToBoolL(True)
    else:
      return sim.SimToBoolL(False)


  ################################################
  # BOUND END  : Simplifiers
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      dfvIn: OverallL
  ) -> NodeDfvL:
    """A common function to handle various IR instructions."""

    # Very Special Case
    if dfvIn.bot and not isinstance(rhs, expr.LitE):
      return NodeDfvL(dfvIn, dfvIn)

    lhsvarNames = ir.getExprLValueNames(self.func, lhs)
    assert len(lhsvarNames) >= 1, msg.INVARIANT_VIOLATED

    # Yet another Very Special Case
    if dfvIn.bot and len(lhsvarNames) > 1:
      return NodeDfvL(dfvIn, dfvIn)

    oldIn: OverallL = dfvIn
    newOut: OverallL = oldIn.getCopy()

    rhsDfv = self.getExprDfv(rhs, dfvIn)

    if len(lhsvarNames) == 1:  # a must update
      for name in lhsvarNames:  # this loop only runs once
        if ir.nameHasArray(self.func, name):  # may update arrays
          oldVal = oldIn.getVal(name)
          newVal, _ = oldVal.meet(rhsDfv)
          newOut.setVal(name, newVal)
        else:
          newOut.setVal(name, rhsDfv)
    else:
      for name in lhsvarNames:  # do may updates (take meet)
        oldDfv = newOut.getVal(name)
        updatedDfv, changed = oldDfv.meet(rhsDfv)
        if changed:
          newOut.setVal(name, updatedDfv)

    if isinstance(rhs, expr.CallE):
      names = ir.getNamesUsedInExprNonSyntactically(self.func, rhs)
      names = ir.filterNamesNumeric(self.func, names)
      for name in names:
        newOut.setVal(name, self.componentBot)

    return NodeDfvL(oldIn, newOut)


  def getExprDfv(self,
      rhs: expr.ExprET,
      dfvIn: OverallL
  ) -> ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects the rhs to be numeric."""
    value = self.componentTop

    if isinstance(rhs, expr.LitE):
      return ComponentL(self.func, val=rhs.val)

    elif isinstance(rhs, expr.VarE):  # handles ObjectE, PseudoVarE
      return dfvIn.getVal(rhs.name)

    elif isinstance(rhs, expr.DerefE):
      names = ir.getNamesUsedInExprNonSyntactically(self.func, rhs)
      for name in names:
        value, _ = value.meet(dfvIn.getVal(name))
      return value

    elif isinstance(rhs, expr.CastE):
      if rhs.arg.type.isNumeric():
        value, _ = value.meet(self.getExprDfv(rhs.arg, dfvIn))
        if value.top or value.bot:
          return value
        else:
          assert rhs.to.isNumeric()
          value.val = rhs.to.castValue(value.val)
          return value
      else:
        return self.componentBot

    elif isinstance(rhs, expr.SizeOfE):
      return self.componentBot

    elif isinstance(rhs, expr.UnaryE):
      value, _ = value.meet(self.getExprDfv(rhs.arg, dfvIn))
      if value.top or value.bot:
        return value
      else:
        rhsOpCode = rhs.opr.opCode
        if rhsOpCode == op.UO_MINUS_OC:
          value.val = -value.val  # not NoneType... pylint: disable=E
        elif rhsOpCode == op.UO_BIT_NOT_OC:
          value.val = ~value.val  # not NoneType... pylint: disable=E
        elif rhsOpCode == op.UO_LNOT_OC:
          value.val = int(not bool(value.val))
        return value

    elif isinstance(rhs, expr.BinaryE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      if val1.top or val2.top:
        return self.componentTop
      elif val1.bot or val2.bot:
        return self.componentBot
      else:
        rhsOpCode = rhs.opr.opCode
        if rhsOpCode == op.BO_ADD_OC:
          val = val1.val + val2.val
        elif rhsOpCode == op.BO_SUB_OC:
          val = val1.val - val2.val
        elif rhsOpCode == op.BO_MUL_OC:
          val = val1.val * val2.val
        elif rhsOpCode == op.BO_DIV_OC:
          if val2.val == 0: return self.componentBot
          val = val1.val / val2.val
        elif rhsOpCode == op.BO_MOD_OC:
          if val2.val == 0: return self.componentBot
          val = val1.val % val2.val
        else:
          val = None

        if val is not None:
          return ComponentL(self.func, val=val)
        else:
          return self.componentBot

    elif isinstance(rhs, expr.SelectE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      value, _ = val1.meet(val2)
      return value

    elif isinstance(rhs, (expr.ArrayE, expr.MemberE)):
      names = ir.getExprLValueNames(self.func, rhs)
      for name in names:
        value, _ = value.meet(dfvIn.getVal(name))
      return value

    elif isinstance(rhs, expr.CallE):
      return self.componentBot

    assert False, msg.CONTROL_HERE_ERROR


  def processCallE(self,
      e: expr.CallE,
      dfvIn: OverallL,
  ) -> NodeDfvL:
    newOut = dfvIn.getCopy()

    names = ir.getNamesUsedInExprNonSyntactically(self.func, e)
    names = ir.filterNamesNumeric(self.func, names)
    for name in names:
      newOut.setVal(name, self.componentBot)

    return NodeDfvL(dfvIn, newOut)


  def calcTrueFalseDfv(self,
      arg: expr.VarE,
      dfvIn: OverallL,
  ) -> Tuple[OverallL, OverallL]:  # dfvFalse, dfvTrue
    """Conditionally propagate data flow values."""
    argDfvFalse = varDfvTrue = varDfvFalse = None

    tmpExpr = ir.getTmpVarExpr(self.func, arg.name)
    if self.getExprDfv(arg, dfvIn).bot:
      argDfvFalse = ComponentL(self.func, 0)

    varName = None
    if tmpExpr and isinstance(tmpExpr, expr.BinaryE):
      opCode = tmpExpr.opr.opCode
      varName = tmpExpr.arg1.name
      varDfv = self.getExprDfv(tmpExpr.arg1, dfvIn)
      if opCode == op.BO_EQ_OC and varDfv.bot:
        varDfvTrue = self.getExprDfv(tmpExpr.arg2, dfvIn)
      elif opCode == op.BO_NE_OC and varDfv.bot:
        varDfvFalse = self.getExprDfv(tmpExpr.arg2, dfvIn)

    if argDfvFalse or varDfvFalse:
      dfvFalse = dfvIn.getCopy()
      if argDfvFalse:
        dfvFalse.setVal(arg.name, argDfvFalse)
      if varDfvFalse:
        dfvFalse.setVal(varName, varDfvFalse)
    else:
      dfvFalse = dfvIn

    if varDfvTrue:
      dfvTrue = dfvIn.getCopy()
      dfvTrue.setVal(varName, varDfvTrue)
    else:
      dfvTrue = dfvIn

    return dfvFalse, dfvTrue

  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : ReachingDefAnalysis
################################################
