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

from typing import Tuple, Dict, List, Optional as Opt, Set, Callable, cast
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
from span.api.dfv import NodeDfvL
import span.api.analysis as analysis
from span.api.analysis import AnalysisAT, ValueAnalysisAT, ForwardD
from span.ir.conv import (simplifyName, isCorrectNameFormat, genFuncNodeId, getNodeId,
                          GLOBAL_INITS_FUNC_ID, isGlobalName, getFuncNodeIdStr,
                          getFuncId)

GLOBAL_INITS_FNID = genFuncNodeId(GLOBAL_INITS_FUNC_ID, 1)  # initialized global

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
    string = io.StringIO()
    string.write("{")
    prefix, funcId = "", self.func.id
    for val in self.val:
      # string.write(f"{getFuncNodeIdStr(val)}")
      if getFuncId(val) == funcId:
        string.write(f"{prefix}{getNodeId(val)}")
      else:
        string.write(f"{prefix}{getFuncNodeIdStr(val)}")
      if not prefix: prefix = ", "
    string.write("}")
    return string.getvalue()


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
    if varName is None: return None # None tells default is not Top/Bot

    assert isCorrectNameFormat(varName), f"{varName}"
    func = self.func
    if func.isParamName(varName):
      # this default value is only used in intra-procedural analysis
      # in inter-procedural analysis, params are defined in the caller,
      # and only in case of main() function this is useful.
      fNid = genFuncNodeId(func.id, 1)  # as node 1 is always NopI()
    elif func.isLocalName(varName):
      fNid = genFuncNodeId(func.id, 0)  # i.e. uninitialized
    elif isGlobalName(varName):
      fNid = GLOBAL_INITS_FNID
    else: # assume an address taken global
      fNid = GLOBAL_INITS_FNID
    return ComponentL(func, val={fNid})



  def getAllVars(self) -> Set[types.VarNameT]:
    """Return a set of vars the analysis is tracking.
    One must override this method if variables are other
    than numeric.
    """
    return ir.getNamesEnv(self.func)


################################################
# BOUND END  : ReachingDef lattice.
################################################

################################################
# BOUND START: ReachingDef_Analysis
################################################

class ReachingDefA(AnalysisAT):
  """Constant Propagation Analysis."""
  __slots__ : List[str] = ["defaultDfv"]
  L: type = OverallL  # the lattice used
  D: type = ForwardD  # its a forward flow analysis
  simNeeded: List[Callable] = [AnalysisAT.Deref__to__Vars,
                               AnalysisAT.LhsVar__to__Nil,
                               AnalysisAT.Cond__to__UnCond,
                               #AnalysisAT.Node__to__Nil,
                               ]


  def __init__(self,
      func: constructs.Func,
  ) -> None:
    super().__init__(func)
    # self.componentTop: dfv.ComponentL = componentL(self.func, top=True)
    # self.componentBot: dfv.ComponentL = componentL(self.func, bot=True)
    self.overallTop: OverallL = OverallL(self.func, top=True)
    self.overallBot: OverallL = OverallL(self.func, bot=True)
    self.defaultDfv: OverallL = OverallL(self.func, val=None)


  def needsRhsDerefSim(self):
    """No need for rhs dereference simplification"""
    return False


  def getBoundaryInfo(self,
      nodeDfv: Opt[NodeDfvL] = None,
      ipa: bool = False,
  ) -> NodeDfvL:
    if ipa and not nodeDfv:
      raise ValueError(f"{ipa}, {nodeDfv}")

    inBi, outBi = self.defaultDfv, self.overallTop
    getDefaultVal = self.overallTop.getDefaultVal
    if ipa:
      return dfv.getBoundaryInfoIpa(self.func, nodeDfv,
                                    getDefaultVal, self.getAllVars)
    if nodeDfv:
      inBi, outBi = nodeDfv.dfvIn, nodeDfv.dfvOut
    return NodeDfvL(inBi, outBi)  # good to create a copy


  def getAllVars(self) -> Set[types.VarNameT]:
    """Gets all the variables of the accepted type."""
    return ir.getNamesEnv(self.func)

  ################################################
  # BOUND START: Special_Instructions
  ################################################
  def Filter_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.FilterI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    return dfv.Filter_Vars(self.func, insn.varNames, nodeDfv)


  def UnDefVal_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.UnDefValI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    func = self.func
    newOut = dfvIn = cast(OverallL, nodeDfv.dfvIn)
    fNid = genFuncNodeId(func.id, nodeId)
    val, varName = ComponentL(func, val={fNid}), insn.lhsName
    if val != dfvIn.getVal(varName):
      newOut = dfvIn.getCopy()
      newOut.setVal(varName, val)
    return NodeDfvL(dfvIn, newOut)


  ################################################
  # BOUND END  : Special_Instructions
  ################################################

  ################################################
  # BOUND START: Normal_Instructions
  ################################################

  def Num_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: numeric: lhs = rhs.
    Convention:
      Type of lhs and rhs is numeric.
    """
    return self.processLhs(nodeId, insn, nodeDfv)


  def Ptr_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: pointer: lhs = rhs.
    Convention:
      Type of lhs and rhs is a record.
    """
    return self.processLhs(nodeId, insn, nodeDfv)


  def Record_Assign_Instr(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """Instr_Form: record: lhs = rhs.
    Convention:
      Type of lhs and rhs is a record.
    """
    return self.processLhs(nodeId, insn, nodeDfv)


  ################################################
  # BOUND END  : Normal_Instructions
  ################################################

  ################################################
  # BOUND START: Helper_Functions
  ################################################

  def processLhs(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      nodeDfv: NodeDfvL
  ) -> NodeDfvL:
    """A common function to handle various assignment instructions.
    This is a common function to all the value analyses.
    """
    lhs, rhs = insn.lhs, insn.rhs
    dfvIn = nodeDfv.dfvIn
    assert isinstance(dfvIn, OverallL), f"{type(dfvIn)}"
    if LS: LOG.debug("ProcessingAssignInstr: %s, iType: %s",
                     insn, insn.type)

    lhsType = lhs.type
    dfvInGetVal = cast(Callable[[types.VarNameT], dfv.ComponentL], dfvIn.getVal)
    outDfvValues: Dict[types.VarNameT, dfv.ComponentL] = {}

    if isinstance(lhsType, types.RecordT):
      outDfvValues = self.processLhsRecordType(nodeId, lhs, dfvInGetVal)
    else:
      func = self.func
      lhsVarNames = ir.getExprLValueNames(func, lhs)
      assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
      mustUpdate = len(lhsVarNames) == 1

      rhsDfv = ComponentL(func, val={genFuncNodeId(func.id, nodeId)})
      if LS: LOG.debug("RhsDfvOfExpr: '%s' is %s, lhsVarNames are %s",
                       rhs, rhsDfv, lhsVarNames)

      for name in lhsVarNames: # loop enters only once if mustUpdate == True
        newVal, oldVal = rhsDfv, dfvInGetVal(name)
        if not mustUpdate or ir.nameHasArray(func, name):
          newVal, _ = oldVal.meet(newVal) # do a may update
        if newVal != oldVal:
          outDfvValues[name] = newVal

    if isinstance(rhs, expr.CallE):
      outDfvValues.update(self.processCallE(nodeId, rhs, dfvIn))
    nDfv = self.genNodeDfvL(outDfvValues, nodeDfv)
    return nDfv


  def processLhsRecordType(self,
      nodeId: types.NodeIdT,
      insn: instr.AssignI,
      dfvInGetVal: Callable[[types.VarNameT], dfv.ComponentL],
  ) -> Dict[types.VarNameT, dfv.ComponentL]:
    """Processes assignment instruction with RecordT"""
    lhs, rhs, iType, func = insn.lhs, insn.rhs, insn.type, self.func
    assert isinstance(iType, types.RecordT), f"{lhs}, {rhs}: {iType}"

    allMemberInfo = iType.getNamesOfType(None)

    lhsVarNames = ir.getExprLValueNames(func, lhs)
    assert len(lhsVarNames) >= 1, f"{lhs}: {lhsVarNames}"
    mustUpdate: bool = len(lhsVarNames) == 1

    val = ComponentL(func, val={genFuncNodeId(func.id, nodeId)})

    outDfvValues: Dict[types.VarNameT, dfv.ComponentL] = {}
    for memberInfo in allMemberInfo:
      memName = memberInfo.name
      for lhsName in lhsVarNames:
        fullMemName = f"{lhsName}.{memName}"
        for name in (lhsName, fullMemName): # handle both names
          newVal, oldVal = val, dfvInGetVal(name)
          if not mustUpdate or ir.nameHasArray(func, name):
            newVal, _ = oldVal.meet(newVal) # do a may update
          if newVal != oldVal:
            outDfvValues[name] = newVal

    return outDfvValues


  def genNodeDfvL(self,
      outDfvValues: Dict[types.VarNameT, dfv.ComponentL],
      nodeDfv: NodeDfvL,
  ) -> NodeDfvL:
    """A convenience function to create and return the NodeDfvL."""
    dfvIn = newOut = nodeDfv.dfvIn
    if outDfvValues:
      newOut = cast(dfv.OverallL, dfvIn.getCopy())
      newOutSetVal = newOut.setVal
      for name, val in outDfvValues.items():
        newOutSetVal(name, val)
    return NodeDfvL(dfvIn, newOut)


  def processCallE(self,
      nodeId: types.NodeIdT,
      e: expr.ExprET,
      dfvIn: DataLT,
  ) -> Dict[types.VarNameT, dfv.ComponentL]:
    assert isinstance(e, expr.CallE), f"{e}"
    assert isinstance(dfvIn, dfv.OverallL), f"{type(dfvIn)}"

    func = self.func
    names = ir.getNamesPossiblyModifiedInCallExpr(func, e)

    val = ComponentL(func, val={genFuncNodeId(func.id, nodeId)})
    dfvInGetVal = dfvIn.getVal
    outDfvValues: Dict[types.VarNameT, dfv.ComponentL] = {}
    for name in names:
      oldVal = dfvInGetVal(name)
      newVal, _ = oldVal.meet(val) # do a may update
      if newVal != oldVal:
        outDfvValues[name] = newVal

    return outDfvValues


  ################################################
  # BOUND END  : Helper_Functions
  ################################################

################################################
# BOUND END  : ReachingDef_Analysis
################################################
