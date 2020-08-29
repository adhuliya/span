#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Sign Analysis

TODO: later -- range analysis will subsume sign analysis.
This (and every) analysis subclasses,
* span.sys.lattice.LatticeLT (to define its lattice)
* span.sys.analysis.AnalysisAT (to define the analysis)
"""

import logging

LOG = logging.getLogger("span")
from typing import Tuple, Dict, Set, List, Optional
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
from span.api.dfv import NodeDfvL
import span.api.sim as sim
import span.api.analysis as analysis
import span.ir.tunit as irTUnit

Even = True
Odd = False


################################################
# BOUND START: evenodd_lattice
################################################

class ComponentL(DataLT):
  """
       Top
     /  |  \
   -ve  0  +ve
     \ /  \ |
     -ve0  +ve0
       \   /
        Bot
  """


  def __init__(self,
      func: constructs.Func,
      val: Optional[bool] = None,  # True/False if Even/Odd
      top: bool = False,
      bot: bool = False
  ) -> None:
    super().__init__(func, val, top, bot)
    self.val: bool = val


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


  def __eq__(self,
      other: 'ComponentL'
  ) -> bool:
    if self.bot and other.bot: return True
    if self.top and other.top: return True

    if not (self.top or self.bot) and \
        not (other.top or other.bot):
      return self.val == other.val
    return False


  def __hash__(self):
    return hash(self.func.name) ^ hash((self.val, self.top, self.bot))


  def getCopy(self) -> 'ComponentL':
    if self.top: ComponentL(self.func, top=True)
    if self.bot: ComponentL(self.func, bot=True)
    return ComponentL(self.func, self.val)


  def __str__(self):
    if self.bot: return "Bot"
    if self.top: return "Top"
    output = "Even" if self.val else "Odd"
    return f"{output}"


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
    self.val: Optional[Dict[types.VarNameT, ComponentL]] = val
    self.componentTop = ComponentL(self.func, top=True)
    self.componentBot = ComponentL(self.func, bot=True)


  def meet(self,
      other: 'OverallL'
  ) -> Tuple['OverallL', ChangeL]:
    if self is other: return self, NoChange
    if self.bot: return self, NoChange
    if other.top: return self, NoChange
    if other.bot: return other, Changed
    if self.top: return other, Changed

    assert self.val and other.val
    if self.val == other.val: return self, NoChange

    # take meet of individual entities (variables)
    meet_val: Dict[types.VarNameT, ComponentL] = {}
    vars_set = {vName for vName in self.val.keys()}
    vars_set.update({vName for vName in other.val.keys()})
    top = self.componentTop
    for vName in vars_set:
      dfv1 = self.val.get(vName, top)
      dfv2 = other.val.get(vName, top)
      dfv3, _ = dfv1.meet(dfv2)
      meet_val[vName] = dfv3

    value = OverallL(self.func, val=meet_val)
    value.explicate()
    return value, Changed


  def __lt__(self,
      other: 'OverallL'
  ) -> bool:
    if self.bot: return True
    if other.top: return True
    if other.bot: return False
    if self.top: return False

    assert self.val and other.val

    vnames = {vName for vName in self.val}
    vnames.update({vName for vName in other.val})
    top = self.componentTop
    for vName in vnames:
      dfv1 = self.val.get(vName, top)
      dfv2 = other.val.get(vName, top)
      if not dfv1 < dfv2: return False

    return True


  def __eq__(self, other: 'OverallL'):
    """strictly equal check."""
    if self.top and other.top: return True
    if self.bot and other.bot: return True
    if self.top or self.bot or other.top or other.bot: return False

    # self and other are proper values
    var_set = {var for var in self.val}
    var_set.update({var for var in other.val})
    top = OverallL(self.func, top=True)
    for vName in var_set:
      dfv1 = self.val.get(vName, top)
      dfv2 = other.val.get(vName, top)
      if not dfv1 == dfv2: return False

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
    """Mutates current object."""
    if self.top and val.top: return
    if self.bot and val.bot: return

    if self.val is None: self.val = dict()
    if self.bot:
      for varName in ir.filterNamesNumeric(self.func, ir.getNamesEnv(self.func)):
        self.val[varName] = self.componentBot
    self.top = self.bot = False  # if it was top/bot, then obviously its no more.
    if val.top:
      if varName in self.val:
        del self.val[varName]  # since default is top
        if not self.val:
          self.top = True
          self.bot = False
          self.val = None
    else:
      self.val[varName] = val

    self.explicate()


  def getCopy(self) -> 'OverallL':
    if self.top:
      return OverallL(self.func, top=True)
    if self.bot:
      return OverallL(self.func, bot=True)

    return OverallL(self.func, self.val.copy())


  def getAllVars(self) -> Set[types.VarNameT]:
    """Return a set of vars the analysis is tracking."""
    vars = ir.getNamesEnv(self.func)
    vars = ir.filterNamesInteger(self.func, vars)
    return vars


  def explicate(self):
    """Mutates self object.
    Checks self.val to mark the current object top/bot.
    Corrects/completes the data flow value after operation."""
    if not self.val:
      assert (self.top and not self.bot) or (not self.top and self.bot)
      self.val = None
      return

    allBot = allTop = True
    for _, objVal in self.val.items():
      if not objVal.top:
        allTop = False
      if not objVal.bot:
        allBot = False
    assert not (allTop and allBot), msg.INVARIANT_VIOLATED

    if allBot:
      allNumericNames = ir.filterNamesNumeric(self.func, ir.getNamesEnv(self.func))
      if len(self.val.keys()) == len(allNumericNames):
        self.top = False
        self.bot = True
        self.val = None
    if allTop:
      self.top = True
      self.bot = False
      self.val = None


  def filterVals(self, varNames: Set[types.VarNameT]):
    if self.top:
      return

    self.val = self.val if self.val else dict()
    if self.bot:
      self.bot = False
      for varName in ir.filterNamesNumeric(self.func, ir.getNamesEnv(self.func)):
        self.val[varName] = self.componentBot

    common = self.val.keys() & varNames
    val = self.val
    _ = [val.pop(key) for key in common]
    if not val:
      self.val, self.top, self.bot = None, True, False

    self.explicate()


  def __str__(self):
    if self.top:
      return "Top"
    if self.bot:
      return "Bot"

    string = io.StringIO()
    string.write("{")
    prefix = None
    for key in self.val:
      # if not ir.isUserVar(key): # added for ACM Winter School
      #   continue
      if ir.isDummyVar(key):  # skip printing dummy variables
        continue
      if prefix: string.write(prefix)
      prefix = ", "
      name = types.simplifyName(key)
      string.write(f"{name}: {self.val[key]}")
    string.write("}")
    return string.getvalue()


  def __repr__(self):
    if self.top:
      return f"evenodd.OverallL({self.func}, top=True)"
    if self.bot:
      return f"evenodd.OverallL({self.func}, bot=True)"

    string = io.StringIO()
    string.write("const.OverallL({")
    prefix = None
    for key in self.val:
      if prefix:
        string.write(prefix)
      prefix = ", "
      string.write(f"{key!r}: {self.val[key]!r}")
    string.write("})")
    return string.getvalue()


################################################
# BOUND END  : evenodd_lattice
################################################

################################################
# BOUND START: evenodd_analysis
################################################

class EvenOddA(analysis.AnalysisAT):
  """Even-Odd (Parity) Analysis."""
  L: type = OverallL
  D: type = analysis.ForwardD
  simNeeded: List[type] = [sim.SimAT.Num_Var__to__Num_Lit,
                           sim.SimAT.Num_Bin__to__Num_Lit,
                           sim.SimAT.Deref__to__Vars,
                           sim.SimAT.LhsVar__to__Nil,
                           sim.SimAT.Cond__to__UnCond
                           ]


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func)
    self.componentTop = ComponentL(self.func, top=True)
    self.componentBot = ComponentL(self.func, bot=True)
    self.componentEven = ComponentL(self.func, val=Even)
    self.componentOdd = ComponentL(self.func, val=Odd)
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
  # BOUND START: special_instructions
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
  # BOUND END  : special_instructions
  ################################################

  ################################################
  # BOUND START: normal_instructions
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
  # BOUND END  : normal_instructions
  ################################################

  ################################################
  # BOUND START: simplifiers
  ################################################

  def Num_Bin__to__Num_Lit(self,
      e: expr.BinaryE,
      nodeDfv: Optional[NodeDfvL] = None,
  ) -> sim.SimToNumL:
    """Specifically for expression: 'var % 2'."""
    # STEP 1: check if the expression can be evaluated
    if not e.opr.opCode == op.BO_MOD_OC:
      return sim.SimToNumFailed
    if isinstance(e.arg2, expr.VarE):
      return sim.SimToNumFailed

    litVal = e.arg2.val
    if litVal != 2:
      return sim.SimToNumFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToNumPending

    arg1VName = e.arg1.name
    varDfv = nodeDfv.dfvIn.getVal(arg1VName)
    if varDfv.top: return sim.SimToNumPending
    if varDfv.bot: return sim.SimToNumFailed
    if varDfv.val == Even: return sim.SimToNumL(0)
    if varDfv.val == Odd: return sim.SimToNumL(1)


  def Cond__to__UnCond(self,
      e: expr.VarE,
      nodeDfv: Optional[NodeDfvL] = None,
  ) -> sim.SimToBoolL:
    # STEP 1: check if the expression can be evaluated
    exprType = e.type
    if not exprType.isNumeric():
      return sim.SimToBoolFailed

    # STEP 2: If here, eval may be possible, hence attempt eval
    if nodeDfv is None:
      return sim.SimToBoolPending

    val: ComponentL = nodeDfv.dfvIn.getVal(e.name)
    if val.top:
      return sim.SimToBoolPending  # can be evaluated, needs more info
    if val.bot:
      return sim.SimToBoolFailed  # cannot be evaluated
    assert val.val is not None, "val should not be None"
    if val.val:  # if Even
      return sim.SimToBoolFailed
    else:
      return sim.SimToBoolL(True)  # take true edge


  ################################################
  # BOUND END  : simplifiers
  ################################################

  ################################################
  # BOUND START: helper_functions
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
      names = ir.filterNamesInteger(self.func, names)
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
      if int(rhs.val) == rhs.val:  # an integer
        return self.componentOdd if rhs.val % 2 else self.componentEven
      else:  # a floating point number
        return self.componentBot

    elif isinstance(rhs, expr.VarE):  # handles ObjectE, PseudoVarE
      return dfvIn.getVal(rhs.name)

    elif isinstance(rhs, expr.DerefE):
      names = ir.getNamesUsedInExprNonSyntactically(self.func, rhs)
      for name in names:
        value, _ = value.meet(dfvIn.getVal(name))
      return value

    elif isinstance(rhs, expr.CastE):
      return dfvIn.getVal(rhs.arg.name)

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
      names = ir.getExprLValueNames(self.func, rhs)
      for name in names:
        value, _ = value.meet(dfvIn.getVal(name))
      return value

    elif isinstance(rhs, expr.CallE):
      return self.componentBot

    # control should not reach here
    assert False, f"class: {rhs.__class__} rhs: {rhs}, dfvIn: {dfvIn}"


  def processCallE(self,
      e: expr.CallE,
      dfvIn: OverallL,
  ) -> NodeDfvL:
    newOut = dfvIn.getCopy()

    names = ir.getNamesUsedInExprNonSyntactically(self.func, e)
    names = ir.filterNamesInteger(self.func, names)
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
      argDfvFalse = ComponentL(self.func, True)

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
  # BOUND END  : helper_functions
  ################################################

################################################
# BOUND END  : evenodd_analysis
################################################
