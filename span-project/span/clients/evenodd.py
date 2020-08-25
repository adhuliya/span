#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Even-Odd Analysis.

This (and every) analysis subclasses,
* span.sys.lattice.LatticeLT (to define its lattice)
* span.sys.analysis.AnalysisAT (to define the analysis)
"""

import logging

LOG = logging.getLogger("span")
from typing import Tuple, Dict, Set, List, Optional as Opt, Callable, cast
import io

import span.util.util as util
import span.util.messages as msg

import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.ir as ir

from span.api.lattice import DataLT, ChangeL, Changed, NoChange
import span.api.dfv as dfv
from span.api.dfv import NodeDfvL
import span.api.sim as sim
import span.api.analysis as analysis
import span.ir.tunit as irTUnit

Even = True
Odd = False


################################################
# BOUND START: evenodd_lattice
################################################

class ComponentL(dfv.ComponentL):
  """
      Top
     /   \
   Even Odd
     \   /
      Bot
  """

  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[bool] = None,  # True/False if Even/Odd
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val = val


  def meet(self,
      other: 'ComponentL'
  ) -> Tuple['ComponentL', ChangeL]:
    if self is other: return self, NoChange
    if self.bot: return self, NoChange
    if other.bot: return other, Changed
    if other.top: return self, NoChange
    if self.top: return other, Changed

    if other.val == self.val:
      return self, NoChange
    else:
      return ComponentL(self.func, bot=True), Changed


  def __lt__(self,
      other: 'ComponentL'
  ) -> bool:
    """A non-strict weaker-than test. See doc of super class."""
    if self.bot: return True
    if other.top: return True
    if other.bot: return False
    if self.top: return False

    return self.val == other.val


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, ComponentL):
      return NotImplemented

    sTop, sBot, oTop, oBot = self.top, self.bot, other.top, other.bot
    if sTop and oTop: return True
    if sBot and oBot: return True
    if sTop or sBot or oTop or oBot: return False

    return self.val == other.val


  def __hash__(self):
    return hash(self.func.name) ^ hash((self.val, self.top, self.bot))


  def getCopy(self) -> 'ComponentL':
    if self.top: ComponentL(self.func, top=True)
    if self.bot: ComponentL(self.func, bot=True)
    return ComponentL(self.func, self.val)


  def __str__(self):
    #return f"{self.top}, {self.bot}, {self.val}"
    if self.bot: return "Bot"
    if self.top: return "Top"
    output = "Even" if self.val else "Odd"
    return f"{output}"


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
    super().__init__(func, val, top, bot, ComponentL, "evenodd")
    # self.componentTop = ComponentL(self.func, top=True)
    # self.componentBot = ComponentL(self.func, bot=True)


################################################
# BOUND END  : evenodd_lattice
################################################

################################################
# BOUND START: evenodd_analysis
################################################

class EvenOddA(analysis.AnalysisAT):
  """Even-Odd (Parity) Analysis."""
  __slots__ : List[str] = ["componentTop", "componentBot", "componentEven", "componentOdd"]
  L: type = OverallL
  D: type = analysis.ForwardD
  simNeeded: List[Callable] = [sim.SimAT.Num_Var__to__Num_Lit,
                               sim.SimAT.Num_Bin__to__Num_Lit,
                               sim.SimAT.Deref__to__Vars,
                               sim.SimAT.LhsVar__to__Nil,
                               sim.SimAT.Cond__to__UnCond
                               ]


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func)
    self.componentTop: ComponentL = ComponentL(self.func, top=True)
    self.componentBot: ComponentL = ComponentL(self.func, bot=True)
    self.componentEven: ComponentL = ComponentL(self.func, val=Even)
    self.componentOdd: ComponentL = ComponentL(self.func, val=Odd)
    self.overallTop: OverallL = OverallL(self.func, top=True)
    self.overallBot: OverallL = OverallL(self.func, bot=True)


  def getIpaBoundaryInfo(self,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    dfvIn = cast(OverallL, nodeDfv.dfvIn.getCopy())
    dfvOut = cast(OverallL, nodeDfv.dfvOut.getCopy())
    dfvIn.func, dfvOut.func = self.func, self.func

    vNames = ir.getNamesEnv(self.func, numeric=True)

    if dfvIn.val:
      for value in dfvIn.val.values(): value.func = self.func
      for key in list(dfvIn.val.keys()):
        if key not in vNames: dfvIn.setVal(key, self.componentBot) # remove key
    if dfvOut.val:
      for value in dfvOut.val.values(): value.func = self.func
      for key in list(dfvOut.val.keys()):
        if key not in vNames: dfvOut.setVal(key, self.componentBot) # remove key

    return NodeDfvL(dfvIn, dfvOut)


  def getBoundaryInfo(self,
      inBi: Opt[DataLT] = None,
      outBi: Opt[DataLT] = None,
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
  # BOUND START: special_instructions
  ################################################

  def Nop_Instr(self,
      nodeId: types.Nid,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """An identity forward transfer function."""
    dfvIn = nodeDfv.dfvIn
    return NodeDfvL(dfvIn, dfvIn)


  def Filter_Instr(self,
      nodeId: types.Nid,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Filter away dead variables.
    The set of named locations that are dead."""
    dfvIn = cast(OverallL, nodeDfv.dfvIn)

    if not insn.varNames \
        or dfvIn.top:  # i.e. nothing to filter or no DFV to filter == Nop
      return self.Nop_Instr(nodeId, nodeDfv)

    newDfvOut = dfvIn.getCopy()

    newDfvOut.filterVals(ir.filterNamesNumeric(self.func, insn.varNames))

    return NodeDfvL(dfvIn, newDfvOut)


  def UnDefVal_Instr(self,
      nodeId: types.Nid,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if not insn.type.isNumeric():
      return self.Nop_Instr(nodeId, nodeDfv)

    oldIn = cast(OverallL, nodeDfv.dfvIn)

    newOut = oldIn.getCopy()
    newOut.setVal(insn.lhs, self.componentBot)

    return NodeDfvL(oldIn, newOut)


  ################################################
  # BOUND END  : special_instructions
  ################################################

  ################################################
  # BOUND START: normal_instructions
  ################################################

  def Num_Assign_Var_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Deref_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_CastVar_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_SizeOf_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_UnaryArith_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_BinArith_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Select_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Array_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Member_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Var_Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.rhs, nodeDfv.dfvIn)


  def Record_Assign_Var_Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Deref_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Deref_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Array_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Array_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Member_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Num_Assign_Member_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Conditional_Instr(self,
      nodeId: types.Nid,
      insn: instr.CondI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    oldIn = cast(OverallL, nodeDfv.dfvIn)
    # special case
    if isinstance(insn.arg.type, types.Ptr):
      return NodeDfvL(oldIn, oldIn)

    dfvFalse, dfvTrue = self.calcTrueFalseDfv(insn.arg, oldIn)

    return NodeDfvL(oldIn, None, dfvTrue, dfvFalse)


  def Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processCallE(insn.arg, nodeDfv.dfvIn)


  ################################################
  # BOUND END  : normal_instructions
  ################################################

  ################################################
  # BOUND START: simplifiers
  ################################################

  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[NodeDfvL] = None,
  ) -> sim.SimToNumL:
    """Specifically for expression: 'var % 2'."""
    # STEP 1: check if the expression can be evaluated
    if not e.opr is op.BO_MOD:
      return sim.SimToNumFailed
    if isinstance(e.arg2, expr.VarE):
      return sim.SimToNumFailed
    if isinstance(e.arg2, expr.LitE):
      if e.arg2.val != 2:
        return sim.SimToNumFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToNumPending

    assert isinstance(e.arg1, expr.VarE), f"{e}"
    arg1VName = e.arg1.name
    varDfv = cast(OverallL, nodeDfv.dfvIn).getVal(arg1VName)
    if varDfv.top: return sim.SimToNumPending
    if varDfv.bot: return sim.SimToNumFailed
    if varDfv.val == Even: return sim.SimToNumL(0)
    if varDfv.val == Odd: return sim.SimToNumL(1)

    raise ValueError(f"{e}: {nodeDfv}")


  # def Cond__to__UnCond(self,
  #     e: expr.VarE,
  #     nodeDfv: Opt[NodeDfvL] = None,
  # ) -> sim.SimToBoolL:
  #   # STEP 1: check if the expression can be evaluated
  #   exprType = e.type
  #   if not exprType.isNumeric():
  #     return sim.SimToBoolFailed

  #   # STEP 2: If here, eval may be possible, hence attempt eval
  #   if nodeDfv is None:
  #     return sim.SimToBoolPending

  #   val: ComponentL = nodeDfv.dfvIn.getVal(e.name)
  #   if val.top:
  #     return sim.SimToBoolPending  # can be evaluated, needs more info
  #   if val.bot:
  #     return sim.SimToBoolFailed  # cannot be evaluated
  #   assert val.val is not None, "val should not be None"
  #   if val.val:  # if Even
  #     return sim.SimToBoolFailed
  #   else:
  #     return sim.SimToBoolL(True)  # take true edge


  ################################################
  # BOUND END  : simplifiers
  ################################################

  ################################################
  # BOUND START: helper_functions
  ################################################

  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      dfvIn: DataLT
  ) -> NodeDfvL:
    """A common function to handle various IR instructions."""
    assert isinstance(dfvIn, OverallL), f"{type(dfvIn)}: {dfvIn}"

    # Very Special Case
    if dfvIn.bot and not isinstance(rhs, expr.LitE):
      return NodeDfvL(dfvIn, dfvIn)

    lhsvarNames = ir.getExprLValuesWhenInLhs(self.func, lhs)
    assert len(lhsvarNames) >= 1, msg.INVARIANT_VIOLATED

    # Yet another Very Special Case
    if dfvIn.bot and len(lhsvarNames) > 1:
      return NodeDfvL(dfvIn, dfvIn)

    rhsDfv = self.getExprDfv(rhs, dfvIn)

    outDfvValues = {}  # a temporary store of out dfvs
    updatedNameList = []
    if len(lhsvarNames) == 1:  # a must update
      for name in lhsvarNames:  # this loop only runs once
        updatedNameList.append(name)
        if ir.nameHasArray(self.func, name):  # may update arrays
          oldVal = dfvIn.getVal(name)
          newVal, _ = oldVal.meet(rhsDfv)
          outDfvValues[name] = newVal
        else:
          outDfvValues[name] = rhsDfv
    else:
      for name in lhsvarNames:  # do may updates (take meet)
        updatedNameList.append(name)
        oldDfv = dfvIn.getVal(name)
        updatedDfv, changed = oldDfv.meet(rhsDfv)
        outDfvValues[name] = updatedDfv

    if isinstance(rhs, expr.CallE):
      names = ir.getNamesUsedInExprNonSyntactically(self.func, rhs)
      names = ir.filterNamesInteger(self.func, names)
      for name in names:
        # updatedNameList.append(name)
        outDfvValues[name] = self.componentBot

    # decide whether to create a new Out Dfv object
    newValue = False
    for name, value in outDfvValues.items():
      if dfvIn.getVal(name) != value:
        newValue = True
        break

    newOut = dfvIn
    if newValue:
      newOut = cast(OverallL, dfvIn.getCopy())
      for name, value in outDfvValues.items():
        if dfvIn.getVal(name) != value:
          newOut.setVal(name, value)
    return NodeDfvL(dfvIn, newOut)


  def getExprDfv(self,
      rhs: expr.ExprET,
      dfvIn: OverallL
  ) -> ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects the rhs to be numeric."""
    value = self.componentTop

    if isinstance(rhs, expr.LitE):
      if int(rhs.val) == rhs.val:  # an integer
        return self.componentOdd if rhs.val % 2 else self.componentEven
      else:  # a floating point number
        return self.componentBot

    elif isinstance(rhs, expr.VarE):  # handles ObjectE, PseudoVarE
      return cast(ComponentL, dfvIn.getVal(rhs.name))

    elif isinstance(rhs, expr.DerefE):
      return self.componentBot
      # Optimize: overapproximate DerefE
      # names = ir.getNamesUsedInExprNonSyntactically(self.func, rhs)
      # for name in names:
      #   value, _ = value.meet(dfvIn.getVal(name))
      # print("IWASHERE:", rhs, value, names) #delit
      # return value

    elif isinstance(rhs, expr.CastE):
      return cast(ComponentL, dfvIn.getVal(rhs.arg.name))

    elif isinstance(rhs, expr.SizeOfE):
      return self.componentBot

    elif isinstance(rhs, expr.UnaryE):
      value, _ = value.meet(self.getExprDfv(rhs.arg, dfvIn))
      if value.top or value.bot:
        return value
      else:
        rhsOpCode = rhs.opr.opCode
        if rhsOpCode == op.UO_MINUS_OC:
          return value
        elif rhsOpCode == op.UO_BIT_NOT_OC:  # reverse the result
          return self.componentOdd if value.val == Even else self.componentEven
        elif rhsOpCode == op.UO_LNOT_OC:
          return self.componentOdd if value.val == Even else self.componentEven
        assert False, msg.CONTROL_HERE_ERROR

    elif isinstance(rhs, expr.BinaryE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      if val1.top or val2.top:
        return self.componentTop
      elif val1.bot or val2.bot:
        return self.componentBot
      else:
        same: bool = val1.val == val2.val
        oneEven: bool = True if val1.val or val2.val else False
        rhsOpCode = rhs.opr.opCode
        if rhsOpCode == op.BO_ADD_OC:
          return self.componentEven if same else self.componentOdd
        elif rhsOpCode == op.BO_SUB_OC:
          return self.componentEven if same else self.componentOdd
        elif rhsOpCode == op.BO_MUL_OC:
          return self.componentEven if oneEven else self.componentOdd
        elif rhsOpCode == op.BO_DIV_OC:
          return self.componentBot
        elif rhsOpCode == op.BO_MOD_OC:
          if same and val1.val == Even:
            return self.componentEven
          elif not same and val2.val == Even:
            return self.componentOdd
          return self.componentBot

        return self.componentBot  # conservative

    elif isinstance(rhs, expr.SelectE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      value, _ = val1.meet(val2)
      return value

    elif isinstance(rhs, (expr.ArrayE, expr.MemberE)):
      names = ir.getExprLValuesWhenInLhs(self.func, rhs)
      for name in names:
        value, _ = value.meet(cast(ComponentL, dfvIn.getVal(name)))
      return value

    elif isinstance(rhs, expr.CallE):
      return self.componentBot

    # control should not reach here
    assert False, f"class: {rhs.__class__} rhs: {rhs}, dfvIn: {dfvIn}"


  def processCallE(self,
      e: expr.ExprET,
      dfvIn: DataLT,
  ) -> NodeDfvL:
    assert isinstance(e, expr.CallE), f"{e}"
    assert isinstance(dfvIn, OverallL), f"{type(dfvIn)}"

    newOut = dfvIn.getCopy()

    names = ir.getNamesUsedInExprNonSyntactically(self.func, e)
    names = ir.filterNamesInteger(self.func, names)
    for name in names:
      newOut.setVal(name, self.componentBot)

    return NodeDfvL(dfvIn, newOut)


  def calcTrueFalseDfv(self,
      arg: expr.SimpleET,
      dfvIn: OverallL,
  ) -> Tuple[OverallL, OverallL]:  # dfvFalse, dfvTrue
    """Conditionally propagate data flow values."""
    assert isinstance(arg, expr.VarE), f"{arg}"

    varDfvTrue = varDfvFalse = None

    tmpExpr = ir.getTmpVarExpr(self.func, arg.name)
    argDfvFalse = ComponentL(self.func, True)  # always true

    varName = arg.name
    if tmpExpr and isinstance(tmpExpr, expr.BinaryE):
      opCode = tmpExpr.opr.opCode
      varDfv = self.getExprDfv(tmpExpr.arg1, dfvIn)
      if opCode == op.BO_EQ_OC and varDfv.bot:
        varDfvTrue = self.getExprDfv(tmpExpr.arg2, dfvIn)
      elif opCode == op.BO_NE_OC and varDfv.bot:
        varDfvFalse = self.getExprDfv(tmpExpr.arg2, dfvIn)

    if argDfvFalse or varDfvFalse:
      dfvFalse = cast(OverallL, dfvIn.getCopy())
      if argDfvFalse:
        dfvFalse.setVal(arg.name, argDfvFalse)
      if varDfvFalse:
        dfvFalse.setVal(varName, varDfvFalse)
    else:
      dfvFalse = dfvIn

    if varDfvTrue:
      dfvTrue = cast(OverallL, dfvIn.getCopy())
      dfvTrue.setVal(varName, varDfvTrue)
    else:
      dfvTrue = dfvIn

    return dfvFalse, dfvTrue

  ################################################
  # BOUND END  : helper_functions
  ################################################

################################################
# BOUND END  : evenodd_analysis
################################################
