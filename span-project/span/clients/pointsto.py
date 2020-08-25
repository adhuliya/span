#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Points-to analysis.

This (and every) analysis subclasses,
* span.sys.lattice.LatticeLT (to define its lattice)
* span.sys.analysis.AnalysisAT (to define the analysis)
"""

import logging

LOG = logging.getLogger("span")
from typing import Tuple, Dict, List, Optional as Opt, Set, Callable, cast
import io

import span.util.util as util
from span.util.util import LS, AS
import span.util.messages as msg

import span.ir.ir as ir
import span.ir.types as types
import span.ir.conv as irConv
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.api.sim as sim

from span.api.lattice import ChangeL, Changed, NoChange, DataLT
import span.api.dfv as dfv
from span.api.dfv import NodeDfvL
import span.api.sim as simApi
import span.api.analysis as analysis

################################################
# BOUND START: Points-to lattice.
################################################

HasPointeesT = bool
HasPointees: HasPointeesT = True
NoPointees: HasPointeesT = False


class ComponentL(dfv.ComponentL):

  __slots__ : List[str] = []


  def __init__(self,
      func: constructs.Func,
      val: Opt[Set[types.VarNameT]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    # correct the state and type
    self.val: Opt[Set[types.VarNameT]] = val
    if self.val is not None and len(self.val) == 0:
      raise ValueError(f"{self}")


  def meet(self, other) -> Tuple['ComponentL', ChangeL]:
    assert isinstance(other, ComponentL), f"{other}"
    if self is other: return self, NoChange
    if self < other:  return self, NoChange
    if other < self:  return other, Changed

    new = self.getCopy()
    assert new.val and other.val
    new.val.update(other.val)
    return new, Changed


  def getCopy(self) -> 'ComponentL':
    if self.top: return ComponentL(self.func, top=True)
    if self.bot: return ComponentL(self.func, bot=True)

    assert self.val, f"{self}"
    return ComponentL(self.func, self.val.copy())


  def __len__(self):
    if self.top: return 0
    if self.bot: return 0x7FFFFFFF  # a large number

    assert self.val, f"Pointees should be one or more: {self}"
    return len(self.val)


  def __contains__(self, varName: types.VarNameT):
    return self.isPointee(varName)


  def isPointee(self,
      varName: types.VarNameT
  ) -> bool:
    """Given a valid varName, returns True if its a possible pointee."""
    if self.top:
      return False
    if self.bot:
      return True  # this is C, a pointer can point to anything

    assert self.val, f"{self}"
    return varName in self.val


  def addPointee(self,
      varName: types.VarNameT
  ) -> None:
    """Adds a given pointee."""
    if self.top:
      self.top = False
      self.val = set()
      self.val.add(varName)

    elif self.bot:
      pass  # bot includes varName

    else:
      assert self.val, f"{self}"
      self.val.add(varName)


  def addPointees(self,
      varNames: Set[types.VarNameT]
  ) -> None:
    """Adds the given set of pointees."""
    if self.top:
      self.top = False
      self.val = set(varNames)  # copy forced

    elif self.bot:
      pass  # bot includes varName

    else:
      assert self.val is not None
      self.val.update(varNames)


  # def removePointee(self, varName) .... cannot be implemented because,
  #   If the value is self.bot, this class has no type information
  #   to populate self.val with appropriate values.
  #   Given the nature of C pointers, they can point to anything.
  #   Moreover, removePointee() doesn't make sense in pointer analysis.

  def __lt__(self, other) -> bool:
    assert isinstance(other, ComponentL), f"{other}"
    if self.bot: return True
    if other.top: return True
    if other.bot: return False
    if self.top: return False

    assert self.val and other.val, f"{self}, {other}"
    return self.val >= other.val # other should be a subset


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, ComponentL):
      return NotImplemented

    sTop, sBot, oTop, oBot = self.top, self.bot, other.top, other.bot
    if sTop and oTop: return True
    if sBot and oBot: return True
    if sTop or sBot or oTop or oBot: return False

    assert self.val and other.val, f"{self}"
    return self.val == other.val


  def __hash__(self):
    val = frozenset(self.val) if self.val else None
    return hash(self.func.name) ^ hash((val, self.top, self.bot))


  def __str__(self):
    if self.top: return "Top"
    if self.bot: return "Bot"
    simpleName = {irConv.simplifyName(name) for name in self.val}
    return f"{simpleName}"


  def __repr__(self):
    return self.__str__()


class OverallL(dfv.OverallL):
  __slots__ : List[str] = []

  def __init__(self,
      func: constructs.Func,
      val: Opt[Dict[types.VarNameT, ComponentL]] = None,
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot, ComponentL, "interval")  # type: ignore
    self.val: Opt[Dict[types.VarNameT, ComponentL]] = val  # type: ignore


  def getAllVars(self) -> Set[types.VarNameT]:
    """Return a set of vars the analysis is tracking."""
    return ir.getNamesEnv(self.func, pointer=True)


################################################
# BOUND END  : Points-to lattice.
################################################

################################################
# BOUND START: Points-to Analysis.
################################################

class PointsToA(analysis.AnalysisAT):
  """Points-to Analysis."""
  __slots__ : List[str] = ["tUnit", "componentTop", "componentBot"]

  L: type = OverallL
  D: type = analysis.ForwardD
  simNeeded: List[Callable] = [sim.SimAT.Deref__to__Vars,
                               sim.SimAT.Cond__to__UnCond,
                               sim.SimAT.LhsVar__to__Nil,
                              ]


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func)
    assert func.tUnit, f"{func}"
    self.tUnit: ir.TranslationUnit = func.tUnit
    self.componentTop: ComponentL = ComponentL(self.func, top=True)
    self.componentBot: ComponentL = ComponentL(self.func, bot=True)
    self.overallTop: OverallL = OverallL(self.func, top=True)
    self.overallBot: OverallL = OverallL(self.func, bot=True)


  def getIpaBoundaryInfo(self,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return dfv.getIpaBoundaryInfo(self.func, nodeDfv,
                                  self.componentBot, self.getAllVars)


  def getAllVars(self) -> Set[types.VarNameT]:
    return ir.getNamesEnv(self.func, pointer=True)


  ################################################
  # BOUND START: Special_Instructions
  ################################################

  def Nop_Instr(self,
      nodeId: types.Nid,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """An identity transfer function."""
    dfvIn = nodeDfv.dfvIn
    if dfvIn is nodeDfv.dfvOut:  # to avoid creating objects
      return nodeDfv
    else:
      return NodeDfvL(dfvIn, dfvIn)


  def UnDefVal_Instr(self,
      nodeId: types.Nid,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    if not isinstance(insn.type, types.Ptr):
      return self.Nop_Instr(nodeId, nodeDfv)

    oldIn: OverallL = cast(OverallL, nodeDfv.dfvIn)
    if oldIn.bot: return NodeDfvL(oldIn, oldIn)

    newOut = oldIn.getCopy()
    newOut.setVal(insn.lhs, self.componentBot)
    return NodeDfvL(oldIn, newOut)


  def Filter_Instr(self,
      nodeId: types.Nid,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Filter away dead variables.
    The set of named locations that are never used ahead."""
    dfvIn = cast(OverallL, nodeDfv.dfvIn)

    if not insn.varNames or dfvIn.top:
      # i.e. nothing to filter or no DFV to filter == Nop
      return self.Nop_Instr(nodeId, nodeDfv)

    newDfvOut = dfvIn.getCopy()
    newDfvOut.filterVals(insn.varNames)

    return NodeDfvL(dfvIn, newDfvOut)


  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################

  def Ptr_Assign_Var_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_AddrOfVar_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_AddrOfArray_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_Array_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Array_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Array_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_AddrOfMember_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_AddrOfDeref_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_Member_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Member_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Member_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_CastVar_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_CastArr_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_AddrOfFunc_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_FuncName_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_Select_Instr(self,
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
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  # FIXME: handle Num_Assign_Var_Call_Instr and Record_Assign_Var_Call_Instr
  def Num_Assign_Var_Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    return self.Record_Assign_Var_Call_Instr(nodeId, insn, nodeDfv)


  def Record_Assign_Var_Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    oldIn = cast(OverallL, nodeDfv.dfvIn)
    newOut = cast(OverallL, oldIn.getCopy())

    callExpr = cast(expr.CallE, insn.rhs)
    names = self.namesPossiblyModifiedInCallE(callExpr, oldIn)
    if LS: LOG.debug("NamesSetToBot: %s", names)
    for name in names:
      newOut.setVal(name, self.componentBot)
    return NodeDfvL(oldIn, newOut)


  def Call_Instr(self,
      nodeId: types.Nid,
      insn: instr.CallI,
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    oldIn = cast(OverallL, nodeDfv.dfvIn)
    newOut = cast(OverallL, oldIn.getCopy())

    callExpr: expr.CallE = insn.arg
    names = self.namesPossiblyModifiedInCallE(callExpr, oldIn)
    if LS: LOG.debug("NamesSetToBot: %s", names)
    for name in names:
      newOut.setVal(name, self.componentBot)
    return NodeDfvL(oldIn, newOut)


  def Ptr_Assign_Deref_Lit_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Deref_Var_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_Deref_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  def Ptr_Assign_Var_BinArith_Instr(self,
      nodeId: types.Nid,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return self.processLhsRhs(insn.lhs, insn.rhs, nodeDfv.dfvIn)


  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Simplifiers
  ################################################

  def Deref__to__Vars(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
  ) -> simApi.SimToVarL:
    varName = e.name

    # STEP 1: check if the expression can be evaluated
    varType = ir.inferTypeOfVal(self.func, varName)

    if not isinstance(varType, (types.Ptr, types.ArrayT)):
      return simApi.SimToVarFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return simApi.SimToVarPending

    # special case (deref of array is the array itself)
    if isinstance(varType, types.ArrayT):
      if LS: LOG.info("WARN: Deref_of_Array: %s, %s", e, varType)
      return simApi.SimToVarL({varName})

    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    val = dfvIn.getVal(varName)
    if val.top:
      return simApi.SimToVarPending
    elif val.bot:
      return simApi.SimToVarFailed

    return simApi.SimToVarL(val.val)


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Opt[NodeDfvL] = None,
  ) -> sim.SimToBoolL:
    # STEP 1: check if the expression can be evaluated
    nameType = ir.inferTypeOfVal(self.func, e.name)
    if not isinstance(nameType, types.Ptr):
      return sim.SimToBoolFailed  # i.e. no eval possible for the expression

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToBoolPending  # i.e. given a dfv, eval may be possible

    dfvIn = cast(OverallL, nodeDfv.dfvIn)
    val = cast(ComponentL, dfvIn.getVal(e.name))
    if val.bot:
      return sim.SimToBoolFailed  # cannot be evaluated

    if val.top:
      return sim.SimToBoolPending  # can be evaluated, needs more info
    elif val.val and len(val.val) == 1 and irConv.NULL_OBJ_NAME in val.val:
      return sim.SimToBoolL(False)
    else:
      return sim.SimToBoolFailed


  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Opt[NodeDfvL] = None,
  ) -> sim.SimToNumL:
    """Specifically for expressions: x == y, x != y"""
    # STEP 1: check if the expression can be evaluated
    opCode = e.opr.opCode
    if opCode not in (op.BO_NE_OC, op.BO_EQ_OC):
      return sim.SimToNumFailed
    if not isinstance(e.arg1.type, types.Ptr):
      return sim.SimToNumFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToNumPending

    leftArgDfv = self.getExprDfv(e.arg1, cast(OverallL, nodeDfv.dfvIn))
    rightArgDfv = self.getExprDfv(e.arg2, cast(OverallL, nodeDfv.dfvIn))

    if leftArgDfv.top or rightArgDfv.top:
      return sim.SimToNumPending

    retVal: Opt[int] = None
    if leftArgDfv == rightArgDfv and leftArgDfv.val \
        and len(leftArgDfv.val) == 1:  # equal
      retVal = 1 if opCode == op.BO_EQ_OC else 0
    elif not (leftArgDfv.bot or rightArgDfv.bot):
      assert leftArgDfv.val and rightArgDfv.val
      if len(leftArgDfv.val & rightArgDfv.val) == 0:  # not equal
        retVal = 0 if opCode == op.BO_EQ_OC else 1

    if retVal is not None:
      return sim.SimToNumL(retVal)
    else:
      return sim.SimToNumFailed


  ################################################
  # BOUND END  : Simplifiers
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def processLhsRhs(self,
      lhs: expr.ExprET,
      rhs: expr.ExprET,
      dataDfvIn: DataLT
  ) -> NodeDfvL:
    """A common function to handle various assignment instructions."""
    dfvIn = cast(OverallL, dataDfvIn)

    # Very Special Case
    if (dfvIn.top or dfvIn.bot) and \
        not (isinstance(rhs, expr.LitE)
             or isinstance(rhs, expr.AddrOfE)
             or (isinstance(rhs, expr.VarE)
                 and rhs.type.isArray())
        ):
      return NodeDfvL(dfvIn, dfvIn)

    lhsVarNames = PointsToA.getNamesOfLValuesInExpr(self.func, lhs, dfvIn)
    assert len(lhsVarNames) >= 1, \
      f"{msg.INVARIANT_VIOLATED}: {lhsVarNames} {lhs}{dfvIn}"

    # Yet another Very Special Case
    if dfvIn.bot and len(lhsVarNames) > 1:
      return NodeDfvL(dfvIn, dfvIn)

    rhsDfv = self.getExprDfv(rhs, dfvIn)

    outDfvValues = {}  # a temporary store of out dfvs
    if len(lhsVarNames) == 1:  # a must update
      for name in lhsVarNames:  # this loop only runs once
        if ir.nameHasArray(self.func, name):  # MAY update arrays
          oldVal = dfvIn.getVal(name)
          newVal, _ = oldVal.meet(rhsDfv)
          if dfvIn.getVal(name) != newVal:
            outDfvValues[name] = newVal
        else:
          if dfvIn.getVal(name) != rhsDfv:
            outDfvValues[name] = rhsDfv
    else:
      for name in lhsVarNames:  # do MAY updates (take meet)
        oldDfv = dfvIn.getVal(name)
        updatedDfv, _ = oldDfv.meet(rhsDfv)
        if dfvIn.getVal(name) != updatedDfv:
          outDfvValues[name] = updatedDfv

    if isinstance(rhs, expr.CallE):
      names = self.namesPossiblyModifiedInCallE(rhs, dfvIn)
      for name in names:
        if not dfvIn.getVal(name).bot:
          outDfvValues[name] = self.componentBot

    newOut = dfvIn
    if outDfvValues:
      newOut = cast(OverallL, dfvIn.getCopy())
      for name, value in outDfvValues.items():
        newOut.setVal(name, value)
    return NodeDfvL(dfvIn, newOut)


  def namesPossiblyModifiedInCallE(self,
      e: expr.CallE,
      dfvIn: OverallL,
  ) -> Set[types.VarNameT]:
    """Pointers that may be modified in a call (conservative)."""
    names = PointsToA.getNamesUsedInExprNonSyntactically(self.func, e, dfvIn)
    names = ir.filterNamesPointer(self.func, names)
    return names


  def getExprDfv(self,
      rhs: expr.ExprET,
      dfvIn: OverallL
  ) -> dfv.ComponentL:
    """Returns the effective component dfv of the rhs.
    It expects the rhs to be pointer type or an array type."""
    value: dfv.ComponentL = self.componentTop
    rhsType = rhs.type
    assert isinstance(rhsType, (types.Ptr, types.ArrayT)), \
      f"{type(rhs)}: {rhsType}, {rhs}"

    if isinstance(rhs, expr.LitE):
      if rhs.isString():
        return ComponentL(self.func, val={rhs.name})
      elif rhs.val == 0:
        return ComponentL(self.func, val={ir.NULL_OBJ_NAME})
      else:
        return self.componentBot  # a sound over-approximation

    elif isinstance(rhs, expr.AddrOfE):
      arg = rhs.arg
      if isinstance(arg, expr.VarE):
        return ComponentL(self.func, val={arg.name})
      elif isinstance(arg, (expr.ArrayE, expr.MemberE, expr.DerefE)):
        names = PointsToA.getNamesOfLValuesInExpr(self.func, arg, dfvIn)
        return ComponentL(self.func, val=names)

    elif isinstance(rhs, expr.VarE):  # handles PseudoVarE too
      if isinstance(rhsType, types.Ptr):
        return dfvIn.getVal(rhs.name)
      elif isinstance(rhsType, types.ArrayT):
        return ComponentL(self.func, val={rhs.name})
      else:  # for all other types
        if LS: LOG.error("%s", rhsType)
        return self.componentBot

    elif isinstance(rhs, expr.SizeOfE):
      return self.componentBot

    elif isinstance(rhs, expr.CastE):
      if isinstance(rhsType, types.Ptr):
        return self.getExprDfv(rhs.arg, dfvIn)
      else:
        return self.componentBot

    elif isinstance(rhs, expr.DerefE):
      names = PointsToA.getNamesUsedInExprNonSyntactically(self.func, rhs, dfvIn)
      names = ir.filterNamesPointer(self.func, names)
      for name in names:
        value, _ = value.meet(dfvIn.getVal(name))
      return value

    elif isinstance(rhs, expr.UnaryE):
      return self.componentBot

    elif isinstance(rhs, expr.BinaryE):
      return self.getExprDfvBinArith(rhs, dfvIn)

    elif isinstance(rhs, expr.SelectE):
      val1 = self.getExprDfv(rhs.arg1, dfvIn)
      val2 = self.getExprDfv(rhs.arg2, dfvIn)
      value, _ = val1.meet(val2)
      return value

    elif isinstance(rhs, (expr.ArrayE, expr.MemberE)):
      names = PointsToA.getNamesOfLValuesInExpr(self.func, rhs, dfvIn)
      for name in names:
        value, _ = value.meet(dfvIn.getVal(name))
      return value

    elif isinstance(rhs, expr.CallE):
      return self.componentBot

    raise ValueError(f"{rhs}")


  def getExprDfvBinArith(self,
      binExpr: expr.BinaryE,
      dfvIn: OverallL
  ) -> dfv.ComponentL:
    """Processes binary expressions with ptr type."""
    if not isinstance(binExpr.type, types.Ptr):
      return self.componentBot

    arg1 = binExpr.arg1
    arg2 = binExpr.arg2
    ptrVarName: Opt[str] = None
    isArray = False

    # Assuming only one of the args is a pointer/array variable
    # Note: binary subtraction between two pointers results in an integer
    if isinstance(arg1, expr.VarE):
      ptrVarName = arg1.name
      if isinstance(arg1.type, types.ArrayT):
        isArray = True
    elif isinstance(arg2, expr.VarE):
      ptrVarName = arg2.name
      if isinstance(arg2.type, types.ArrayT):
        isArray = True

    assert ptrVarName is not None

    if isArray:  # arr + 1 etc. results in ptr to an element of arr
      return ComponentL(self.func, val={ptrVarName})

    # if here: no array is used in the expression
    newVal: dfv.ComponentL = self.componentTop

    pointees = dfvIn.getVal(ptrVarName)
    if pointees.top:
      newVal = self.componentTop
    elif pointees.bot:
      newVal = self.componentBot
    else:
      # Check if all the pointees are arrays.
      assert pointees.val
      for pointee in pointees.val:
        if not isinstance(ir.inferTypeOfVal(self.func, pointee), types.ArrayT):
          # return bot even if one pointee is not an array
          newVal = self.componentBot
          break
      else:
        # if here: all pointees are arrays
        newVal = pointees

    return newVal


  @staticmethod
  def getNamesOfLValuesInExpr(func: constructs.Func,
      e: expr.ExprET,
      dfvIn: OverallL = None
  ) -> Set[types.VarNameT]:
    """Returns the locations that may be modified,
    if this expression was on the LHS of an assignment."""
    if dfvIn is None:  # become conservative
      return set(ir.getExprLValuesWhenInLhs(func, e))

    names = set()

    if isinstance(e, expr.VarE):
      names.add(e.name)
      return names

    elif isinstance(e, expr.DerefE):
      assert isinstance(e.arg, expr.VarE), f"{e}"
      names.update(PointsToA.getNamesOfPointees(func, e.arg.name, dfvIn))
      return names

    elif isinstance(e, expr.ArrayE):
      if e.hasDereference():
        names.update(PointsToA.getNamesOfPointees(func, e.getArrayName(), dfvIn))
      else:
        names.add(e.getArrayName())
      return names

    elif isinstance(e, expr.MemberE):
      assert e.hasDereference(), f"{e}"
      pointeeNames = PointsToA.getNamesOfPointees(func, e.of.name, dfvIn)
      for name in pointeeNames:
        names.add(f"{name}.{e.name}")
      return names

    raise ValueError(f"{e}")


  @staticmethod
  def getNamesUsedInExprNonSyntactically(
      func: constructs.Func,
      e: expr.ExprET,
      dfvIn: OverallL = None,
  ) -> Set[types.VarNameT]:
    """
    This function returns the possible locations used in a DerefET/CallE
    expression conservatively/using the given points-to information.

    The function is designed in a way such that it can be called
    by other modules. The func arg has been specially added for this.
    """
    if dfvIn is None:  # default to conservative behavior
      return ir.getNamesUsedInExprNonSyntactically(func, e)

    varNames = set()

    if isinstance(e, expr.LitE) and e.isString():  # a string literal
      varNames.add(e.name)
      return varNames

    elif isinstance(e, expr.DerefE):
      assert isinstance(e.arg, expr.VarE), f"{e}"
      varNames.update(PointsToA.getNamesOfPointees(func, e.arg.name, dfvIn))
      return varNames

    elif isinstance(e, expr.ArrayE):
      if e.hasDereference():
        varNames.update(PointsToA.getNamesOfPointees(func, e.of.name, dfvIn))
      return varNames

    elif isinstance(e, expr.MemberE):
      assert e.hasDereference(), f"{e}"
      pointeeNames = PointsToA.getNamesOfPointees(func, e.of.name, dfvIn)
      for name in pointeeNames:
        varNames.add(f"{name}.{e.name}")
      return varNames

    elif isinstance(e, expr.CallE):  # FIXME: check the logic
      for arg in e.args:  # iterate over the call arguments
        argType = arg.type
        if isinstance(argType, types.ArrayT):
          argType = argType.getElementType()
        if isinstance(argType, types.Ptr): # only ptr arguments matter
          if isinstance(arg, expr.AddrOfE):
            assert isinstance(arg.arg, expr.VarE), f"{arg}"
            varNames.add(arg.arg.name)
            continue
          assert isinstance(arg, expr.VarE), f"{arg}"
          names: Set[types.VarNameT] = set()
          PointsToA._getNamesOfArgPointeesPtr(func, arg.name, names, dfvIn)
          varNames.update(names)
      varNames.update(ir.getNamesGlobal(func))  # non-pointer vars included
      return varNames

    return varNames


  @staticmethod
  def _getNamesOfArgPointeesPtr(func,
      varName: types.VarNameT,
      names: Set[types.VarNameT],
      dfvIn: OverallL = None,
  ) -> None:
    """
    Don't call this directly. Use:
    getNamesUsedInExprNonSyntactically()
    """
    assert names is not None
    pointeeNames = PointsToA.getNamesOfPointees(func, varName, dfvIn)
    ptrPointeeNames = ir.filterNamesPointer(func, pointeeNames)
    for ptrName in ptrPointeeNames:
      PointsToA._getNamesOfArgPointeesPtr(func, ptrName, names, dfvIn)
    names.update(ptrPointeeNames)


  @staticmethod
  def getNamesOfPointees(
      func: constructs.Func,
      varName: types.VarNameT,
      dfvIn: OverallL = None
  ) -> Set[types.VarNameT]:
    """Returns the pointee names of the given pointer name,
    if dfvIn is None it returns conservative value."""

    # Step 1: what type is the given name?
    varType = ir.inferTypeOfVal(func, varName)
    if isinstance(varType, types.ArrayT):
      varType = varType.getElementType()

    if not isinstance(varType, types.Ptr):
      raise ValueError(f"{varName}: {varType}")

    # Step 2: if here its a pointer, get its pointees
    pointeeType = varType.getPointeeType()

    if dfvIn is None:  # become conservative
      return ir.getNamesEnv(func, pointeeType)

    varDfv = dfvIn.getVal(varName)
    if varDfv.top:        # no result
      return set()
    elif varDfv.bot:      # conservative result
      return ir.getNamesEnv(func, pointeeType)
    else:                 # precise result
      assert varDfv.val, f"{varDfv}"
      return varDfv.val

  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : Points-to Analysis.
################################################
