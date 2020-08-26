#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Defines a translation unit.
Following important things are available here,

  1. Actions to pre-processes IR before analysis can be done on the same,

     a. transforms the IR (Note that all transformations in the system
        can be found here, or invoked here: see preProcess())

     b. infers types of expressions and instructions

     c. caches information into data structures for easy access

  2. Provides API to fetch useful information from a translation unit.
"""

import logging

LOG = logging.getLogger("span")
from typing import Dict, Set, Tuple, List, Callable
from typing import Optional as Opt
import io
import re

from span.util.util import LS, AS
import span.util.common_util as cutil

import span.ir.types as types
import span.ir.conv as irConv
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.graph as graph
import span.util.messages as msg

class Stats:
  def __init__(self, tunit: 'TranslationUnit', totalCfgNodes=0):
    self.tunit = tunit
    self.getNamesTimer = cutil.Timer("TUNIT:GetNames", start=False)

  def __str__(self):
    l1 = [f"{self.getNamesTimer}"]
    l1.append(f"TUnitSize: {cutil.getSize(self.tunit)}")
    return "\n".join(l1)


class TranslationUnit:
  """A Translation Unit.
  It holds the complete C file (converted from Clang AST).
  SPAN IR may undergo many iteration of changes here
  (see self.preProcess()).
  """


  def __init__(self,
      name: types.TUnitNameT,
      description: str,
      allVars: Dict[types.VarNameT, types.Type],
      globalInits: Opt[List[instr.InstrIT]],
      allRecords: Dict[types.RecordNameT, types.RecordT],
      allFunctions: Dict[types.VarNameT, constructs.Func],
      preProcess: bool = True,  # disables IR pre-processing
  ) -> None:
    # analysis unit name and description
    self.stats = Stats(self)

    self.name = name  # used as key in hash maps
    self.description = description

    # whole of TU is contained in these three variables
    self.allVars = allVars
    self.allRecords = allRecords
    self.allFunctions = allFunctions
    self.allFunctions[irConv.GLOBAL_INITS_FUNC_NAME] = constructs.Func(
      name=irConv.GLOBAL_INITS_FUNC_NAME,
      instrSeq=globalInits if globalInits else [instr.NopI()]
    )

    self.initialized: bool = False  # is set to True after preProcess()

    # new variables: variables introduces because of preProcess()
    self._newVarsMap: \
      Dict[types.VarNameT, types.VarNameInfo] = {}

    # Name information map (contains all possible named locations)
    self._nameInfoMap: \
      Dict[types.VarNameT, types.VarNameInfo] = {}

    # Set of all global vars in this translation unit.
    self._globalVarNames: \
      Set[types.VarNameT] = set()

    # Set of all global vars categorized by types
    self._globalTypeVarNamesMap: \
      Dict[Opt[types.Type], Set[types.VarNameT]] = {}

    # The local pseudo variables in each function
    self._localPseudoVars: \
      Dict[types.FuncNameT, Set[types.VarNameT]] = {}

    # All the pseudo variables in the translation unit
    self._allPseudoNames: \
      Opt[Set[types.VarNameT]] = None

    # map (func, givenType) to vars of givenType accessible in the func (local+global)
    # (func, None) holds all types of vars accessible in the func (local+global)
    self._typeFuncEnvNamesMap: \
      Dict[Tuple[types.FuncNameT, Opt[types.Type]], Set[types.VarNameT]] = {}

    # only local variables
    self._typeFuncLocalNameMap: \
      Dict[Tuple[types.FuncNameT, Opt[types.Type]], Set[types.VarNameT]] = {}

    # Set of all pseudo vars in this translation unit.
    # Note: pseudo vars hide memory allocation with a variable name.
    self._pseudoVars: \
      Set[types.VarNameT] = set()

    # function signature (funcsig) to function object mapping
    self._funcSigToFuncObjMap: \
      Dict[types.FuncSig, List[constructs.Func]] = {}

    # maps tmps assigned only once to the assigned expression
    self._funcTmpExprMap: \
      Dict[types.VarNameT, expr.ExprET] = {}

    # stores the increasing counter for pseudo variables in the function
    # pseudo variables replace malloc/calloc calls as addressOf(pseudoVar)
    self._funcPseudoCountMap: \
      Dict[types.FuncNameT, int] = {}

    # used to allot unique name to string literals
    self._stringLitCount: int = 0
    self._dummyVarCount: int = 0

    # named locations whose address is taken
    self._addrTakenSet: Set[types.VarNameT] = set()

    # effective globals (actual globals + addr taken set)
    self._globalsAndAddrTakenSet: Set[types.VarNameT] = set()
    # pointee cache
    self._globalsAndAddrTakenSetMap:\
      Dict[types.Type, Set[types.VarNameT]] = dict()

    # function id list: id is the index in the list
    self._funcIdToFuncList: List[constructs.Func] = []

    if preProcess:
      self.preProcess()


  def preProcess(self):
    """Canonicalizes the translation unit before it can be used for analysis.
    ALL changes to SPAN IR before analysis are initiated from here.
    The relative positions of the transformations may be critical.
    """
    self.initialized = False

    self.logUsefulInfo()
    if LS: LOG.info(f"PreProcessing_TUnit({self.name}): START.")

    # STEP 1: Fill the gaps in the SPAN IR
    self.fillTheRecordTypes()  # IMPORTANT (MUST)
    self.fillFuncParamTypes()  # IMPORTANT (MUST)
    self.addThisTUnitRefToObjs()  # IMPORTANT (MUST)
    # self.genBasicBlocks()             # IMPORTANT (MUST)
    self.inferAllInstrTypes()  # IMPORTANT (MUST)
    self.convertNonDerefMemberE()  # IMPORTANT

    # STEP 2: Canonicalize the IR
    self.canonicalize()  # CANONICALIZE SPAN IR (MUST)
    if LS: LOG.debug("NameInfoObjects:\n %s", self._nameInfoMap)

    # STEP 3: Extract and cache the information on the IR
    self.extractTmpVarAssignExprs()  # IMPORTANT
    self.extractAllVarNames()  # (MUST)

    # STEP 4: Misc
    self.fillGlobalInitsFunction()  # MUST
    self.collectAddrTakenVars()  # MUST
    self.addDummyObjects()  # MUST (after extractAllVarNames())
    self.genCfgs()  # MUST

    self.assignFunctionIds()
    self.logStats() # must be the last call (OPTIONAL)

    self.initialized = True
    if LS: LOG.info(f"PreProcessing_TUnit({self.name}): END/DONE.")


  def assignFunctionIds(self):
    """Assigns a unique id to each function."""
    funcId: types.FuncIdT = 0
    for func in self.yieldFunctions():
      func.id = funcId
      self._funcIdToFuncList.append(func)
      funcId += 1


  def collectAddrTakenVars(self):  # MUST
    """Collects the name of all the named locations whose
    address has been literally taken."""
    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        if isinstance(insn, instr.AssignI):
          rhs = insn.rhs
          if isinstance(rhs, expr.AddrOfE):
            # for statement: x = &z
            if isinstance(rhs.arg, expr.VarE): # only addr of a var
              argName, argType = rhs.arg.name, rhs.arg.type
              self._addrTakenSet.update(irConv.getSuffixes(None, argName, argType))
          if isinstance(rhs, expr.VarE) and isinstance(rhs.type, types.ArrayT):
            # x = y, where y is an array is equivalent to x = &y.
            rhsName, rhsType = rhs.name, rhs.type
            self._addrTakenSet.update(irConv.getSuffixes(None, rhsName, rhsType))

          # Expr &(x->y) must have been preceded by x = &z.
    self._addrTakenSet.add(irConv.NULL_OBJ_NAME)

    self._globalsAndAddrTakenSet = self._globalVarNames | self._addrTakenSet


  def convertNonDerefMemberE(self):
    """Converts member expression with non member deref to VarE"""


    def convertMemberEToVarE(e: expr.MemberE) -> expr.ExprET:
      if e.hasDereference():
        return e
      else:
        return expr.VarE(e.getFullName(), info=e.info)


    exprPredicate = lambda e: isinstance(e, expr.MemberE)

    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        self.findAndConvertExprInInstr(insn, exprPredicate, convertMemberEToVarE)


  def findAndConvertExprInInstr(self,
      insn: instr.InstrIT,
      exprPredicate: Callable,
      convertExpr: Callable,
  ) -> None:
    """It searches the given instruction for the expression
    using the given predicate and replaces it with the
    convertExpr function."""
    if isinstance(insn, instr.AssignI):
      lhs = self.findAndConvertExpr(insn.lhs, exprPredicate, convertExpr)
      rhs = self.findAndConvertExpr(insn.rhs, exprPredicate, convertExpr)
      assert isinstance(lhs, expr.LocationET), f"{lhs}"
      insn.lhs, insn.rhs = lhs, rhs
    elif isinstance(insn, instr.CondI):
      arg = self.findAndConvertExpr(insn.arg, exprPredicate, convertExpr)
      assert isinstance(arg, expr.SimpleET)
      insn.arg = arg
    elif isinstance(insn, instr.CallI):
      arg = self.findAndConvertExpr(insn.arg, exprPredicate, convertExpr)
      assert isinstance(arg, expr.CallE)
      insn.arg = arg
    elif isinstance(insn, instr.ReturnI):
      if insn.arg is not None:
        arg = self.findAndConvertExpr(insn.arg, exprPredicate, convertExpr)
        assert isinstance(arg, expr.SimpleET)
        insn.arg = arg
    elif isinstance(insn, (instr.NopI, instr.GotoI)):
      pass
    else:
      assert False, f"{insn}"


  def findAndConvertExpr(self,
      e: expr.ExprET,
      exprPredicate: Callable,
      convertExpr: Callable
  ) -> expr.ExprET:
    if exprPredicate(e):
      return convertExpr(e)
    if isinstance(e, expr.SimpleET):
      return e

    if isinstance(e, expr.BinaryE):
      arg1 = self.findAndConvertExpr(e.arg1, exprPredicate, convertExpr)
      arg2 = self.findAndConvertExpr(e.arg2, exprPredicate, convertExpr)
      assert isinstance(arg1, expr.SimpleET) and isinstance(arg2, expr.SimpleET)
      e.arg1, e.arg2 = arg1, arg2
    elif isinstance(e, expr.DerefE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      assert isinstance(arg, expr.VarE)
      e.arg = arg
    elif isinstance(e, expr.AddrOfE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      assert isinstance(arg, expr.LocationET)
      e.arg = arg
    elif isinstance(e, expr.MemberE):
      of = self.findAndConvertExpr(e.of, exprPredicate, convertExpr)
      assert isinstance(of, expr.VarE)
      e.of = of
    elif isinstance(e, expr.CallE):
      callee = self.findAndConvertExpr(e.callee, exprPredicate, convertExpr)
      assert isinstance(callee, expr.VarE)
      e.callee = callee
      newArgs: List[expr.SimpleET] = []
      for arg in e.args:
        newArg = self.findAndConvertExpr(arg, exprPredicate, convertExpr)
        assert isinstance(newArg, expr.SimpleET)
        newArgs.append(newArg)
      e.args = newArgs
    elif isinstance(e, expr.UnaryE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      assert isinstance(arg, expr.SimpleET)
      e.arg = arg
    elif isinstance(e, expr.CastE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      assert isinstance(arg, expr.LocationET)
      e.arg = arg
    elif isinstance(e, expr.ArrayE):
      of = self.findAndConvertExpr(e.of, exprPredicate, convertExpr)
      index = self.findAndConvertExpr(e.index, exprPredicate, convertExpr)
      assert isinstance(of, expr.LocationET) and isinstance(index, expr.SimpleET)
      e.of, e.index = of, index
    elif isinstance(e, expr.SelectE):
      cond = self.findAndConvertExpr(e.cond, exprPredicate, convertExpr)
      arg1 = self.findAndConvertExpr(e.arg1, exprPredicate, convertExpr)
      arg2 = self.findAndConvertExpr(e.arg2, exprPredicate, convertExpr)
      assert isinstance(cond, expr.VarE) and isinstance(arg1, expr.SimpleET) \
             and isinstance(arg2, expr.SimpleET)
      e.cond, e.arg1, e.arg2 = cond, arg1, arg2
    else:
      assert False, f"{e}"

    return e


  def logStats(self):
    """Logs some important stats of the translation unit.
    Should be called after all the various pre-processing is done."""
    if not LS: return

    ld = LOG.debug

    sio = io.StringIO()
    for vName, t in self.allVars.items():
      sio.write(f"    {vName!r}: {t},\n")
    ld("InputVariables(total %s):\n%s", len(self.allVars), sio.getvalue())

    sio = io.StringIO()
    for vName, info in self._nameInfoMap.items():
      sio.write(f"    {vName!r}: {info},\n")
    ld("ProcessedVariables(total %s):\n%s", len(self._nameInfoMap), sio.getvalue())

    sio = io.StringIO()
    for vName, info in self._newVarsMap.items():
      sio.write(f"    {vName!r}: {info},\n")
    ld("NewVariables(total %s):\n%s", len(self._newVarsMap), sio.getvalue())

    sio = io.StringIO()
    for vName in self._addrTakenSet:
      sio.write(f"    {vName!r},\n")
    ld("AddrTakenVariables(total %s):\n%s", len(self._addrTakenSet), sio.getvalue())

    sio = io.StringIO()
    for vName in self._globalsAndAddrTakenSet:
      sio.write(f"    {vName!r},\n")
    ld("GlobalsAndAddrTakenVariables(total %s):\n%s",
       len(self._globalsAndAddrTakenSet), sio.getvalue())

    ld("TotalRecords(total %s): Not printed.", len(self.allRecords))
    ld("TotalFunctions(total %s): Not printed.", len(self.allFunctions))


  def getPossiblePointees(self,
      t: Opt[types.Ptr] = None,
      cache: bool = True
  ) -> Set[types.VarNameT]:
    """Returns the possible pointees a type 't' var may point to."""
    if t is None: return self._globalsAndAddrTakenSet

    pointeeType = t.getPointeeType()
    if pointeeType in self._globalsAndAddrTakenSetMap:
      return self._globalsAndAddrTakenSetMap[t]

    names = []
    for varName in self._globalsAndAddrTakenSet:
      varInfo = self._nameInfoMap[varName]
      if varInfo.type == pointeeType:
        names.append(varName)
      elif isinstance(varInfo.type, types.ArrayT) \
        and varInfo.type.getElementType() == pointeeType:
        names.append(varName)

    if cache:
      self._globalsAndAddrTakenSetMap[pointeeType] = set(names)

    return set(names)


  def addDummyObjects(self):
    """It adds dummy objects of the pointee type
    of pointer variables whose pointee type
    object doesn't exist in the tunit."""
    for varName, objType in self.allVars.items():
      tmpType = objType
      while isinstance(tmpType, types.Ptr):
        names = self.getPossiblePointees(tmpType, cache=False)
        if len(names) < 2: # at least two names to point to
          self.createAndAddGlobalDummyVar(tmpType.getPointeeType())
          if not len(names):
            self.createAndAddGlobalDummyVar(tmpType.getPointeeType())

        tmpType = tmpType.getPointeeType()
        # end while


  def getTheFunctionOfVar(self,
      varName: types.VarNameT
  ) -> Opt[constructs.Func]:
    """Returns the constructs.Func object the varName belongs to.
    For global variables it returns None."""
    funcName = irConv.extractFuncName(varName)
    func: Opt[constructs.Func] = None
    if funcName:
      if funcName in self.allFunctions:
        func = self.allFunctions[funcName]
    return func


  def extractAllVarNames(self):
    """It extracts all the object names possible in
    a translation unit and caches the result."""
    for varName, objType in self.allVars.items():
      self.addVarNames(varName, objType)
    assert self.allVars.keys() <= self._nameInfoMap.keys(),\
           f"{self.allVars.keys()} is not <= {self._nameInfoMap.keys()}"


  def addVarNames(self,
      varName: types.VarNameT,
      objType: types.Type,
      new: bool = False, # True if variable is added by SPAN
  ) -> None:
    """Add the varName into self._nameInfoMap along
    with all its sub-names if its an array or a record."""
    nameInfos = objType.getNamesOfType(None, varName)

    for nameInfo in nameInfos:
      self._nameInfoMap[nameInfo.name] = nameInfo   # cache the results
      if new:
        self._newVarsMap[nameInfo.name] = nameInfo  # record a new variable


  def printNameInfoMap(self):
    """A convenience function to print names in
    self._nameInfoMap for debugging."""
    print("The names in the IR:")
    for name in sorted(self._nameInfoMap.keys()):
      print(f"{name}:", self._nameInfoMap[name])


  def replaceZeroWithNullPtr(self):
    """Replace statements assigning Zero to pointers,
    with a special NULL_OBJ."""
    # Add the special null object.
    self.addVarNames(irConv.NULL_OBJ_NAME, irConv.NULL_OBJ_TYPE, True)

    for func in self.yieldFunctionsWithBody():
      for bb in func.basicBlocks.values():
        for i in range(len(bb) - 1):
          insn = bb[i]
          if isinstance(insn, instr.AssignI) and \
              insn.type.typeCode == types.PTR_TC:
            rhs = insn.rhs
            if isinstance(rhs, expr.CastE):
              arg = rhs.arg
              if isinstance(arg, expr.LitE):
                if arg.type.isNumeric() and arg.val == 0:
                  rhs = expr.AddrOfE(expr.VarE(irConv.NULL_OBJ_NAME, rhs.info), rhs.info)
                  insn.rhs = rhs
            if isinstance(rhs, expr.LitE):
              if rhs.type.isNumeric() and rhs.val == 0:
                rhs = expr.AddrOfE(expr.VarE(irConv.NULL_OBJ_NAME, rhs.info), rhs.info)
                insn.rhs = rhs


  def addThisTUnitRefToObjs(self):  # IMPORTANT (MUST)
    """sets func.tUnit to this TUnit here,
    It cannot be done in obj.Func since,
      1. due to lack of info in the constructs module
      2. to avoid circular dependency btw constructs and this module"""
    for func in self.yieldFunctions():
      # Point func.tUnit to TUnit object it belongs to i.e. this
      func.tUnit = self


  def genCfgs(self) -> None:
    """Fills constructs.Func's self.cfg field to contain a proper CFG graph.
    Its done only for functions with body.
    """
    for func in self.yieldFunctionsWithBody():
      func.cfg = graph.Cfg(func.name, func.basicBlocks, func.bbEdges)


  def yieldFunctions(self):
    """Yields all the functions in the TUnit."""
    for _, func in self.allFunctions.items():
      yield func


  def yieldFunctionsWithBody(self):
    """Yields all the functions in the TUnit with body."""
    for func in self.yieldFunctions():
      if func.hasBody():
        yield func


  def yieldRecords(self, rType=types.RecordT):
    """Yields all the records in the TUnit"""
    assert rType in (types.RecordT, types.Struct, types.Union), f"{rType}"
    for _, record in self.allRecords.items():
      if isinstance(record, rType):
        yield record


  def genBasicBlocks(self) -> None:
    """Generates basic blocks if function objects are initialized by
    instruction sequence only."""
    for func in self.yieldFunctions():
      if not func.basicBlocks and func.instrSeq:
        # i.e. basic blocks don't exist and the function has a instr seq body
        func.basicBlocks, func.bbEdges = constructs.Func.genBasicBlocks(func.instrSeq)


  def fillFuncParamTypes(self):
    """If function's param type list is empty, fill it."""
    for func in self.yieldFunctions():
      if not func.sig.paramTypes:
        paramTypes = func.sig.paramTypes = []
        for paramName in func.paramNames:
          paramTypes.append(self.inferTypeOfVal(paramName))


  def inferAllInstrTypes(self):
    """Fills type field of the instruction (and expressions in it)."""
    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        self.inferTypeOfInstr(insn)


  ################################################
  # BOUND START: Type_Inference
  ################################################

  def inferTypeOfVal(self, val) -> types.Type:
    """Returns the type for the given value.
    In case of a function, it returns its signature.
    """

    if type(val) == int:    return types.Int
    if type(val) == float:  return types.Float

    if isinstance(val, types.VarNameT):
      if val in self._nameInfoMap:  # IMPORTANT
        return self._nameInfoMap[val].type

      if val in self.allVars:  # IMPORTANT for initial use in preProcess()
        return self.allVars[val]

      if val in self.allFunctions:
        func: constructs.Func = self.allFunctions[val]
        return func.sig

    if AS:
      print(val, self._nameInfoMap)
      assert False, msg.INVARIANT_VIOLATED
    raise ValueError(f"{val}")


  def getMemberType(self, fullMemberName: str) -> types.Type:
    """Takes names like x.y.z and returns the type"""
    names = fullMemberName.split(".")
    currType = self.inferTypeOfVal(names[0])  # could be RecordT, ArrayT or Ptr
    # get the record type
    if isinstance(currType, types.ArrayT):
      currType = currType.getElementType()
    while not isinstance(currType, types.RecordT):
      if isinstance(currType, types.Ptr):
        currType = currType.getPointeeType()

    count = len(names)
    for i in range(1, count):
      assert isinstance(currType, types.RecordT)
      currType = currType.getMemberType(names[i])
      if i + 1 != count: # hence more members to come
        # get the record type
        if isinstance(currType, types.ArrayT):
          currType = currType.getElementType()
        if isinstance(currType, types.Ptr):
          currType = currType.getPointeeTypeFinal()
    return currType


  def processStringLiteral(self, e: expr.LitE) -> types.ConstSizeArray:
    """Takes a string literal and gives it a variable like name
    and a type of ConstSizeArray of char."""

    assert isinstance(e.val, str)
    # since "XXX" is suffixed to every string literal
    # "XXX" is suffixed to a string literal since some
    # strings end with '"' and '""""' is an invalid end of string in python
    e.val = e.val[:-3]  # type: ignore
    eType = types.ConstSizeArray(of=types.Char, size=len(e.val))
    # eType = types.Char # its not the correct type

    if e.name is None:
      self._stringLitCount += 1
      e.name = irConv.NAKED_STR_LIT_NAME.format(count=self._stringLitCount)
      self._nameInfoMap[e.name] = types.VarNameInfo(e.name, eType, True)

    return eType


  def inferTypeOfExpr(self, e: expr.ExprET) -> types.Type:
    """Infer expr type, store the type info
    in the object and return the type."""
    eType = types.Void
    exprCode = e.exprCode
    lExpr = expr  # for speed

    if isinstance(e, lExpr.VarE):
      eType = self.inferTypeOfVal(e.name)
      # assert not isinstance(eType, types.FuncSig), msg.INVARIANT_VIOLATED

    elif isinstance(e, lExpr.LitE):
      if type(e.val) == str:
        eType = self.processStringLiteral(e)
      else:
        eType = self.inferTypeOfVal(e.val)

    elif isinstance(e, lExpr.CastE):
      self.inferTypeOfExpr(e.arg)
      eType = e.to  # type its casted to

    elif isinstance(e, lExpr.UnaryE):
      opCode = e.opr.opCode
      argType = self.inferTypeOfExpr(e.arg)
      # opCode will never be UO_DEREF_OC
      if opCode == op.UO_LNOT_OC:  # logical not
        eType = types.Int32
      else:
        eType = argType  # for all other unary ops

    elif isinstance(e, lExpr.BinaryE):
      opCode = e.opr.opCode
      if op.BO_NUM_START_OC <= opCode <= op.BO_NUM_END_OC:
        itype1 = self.inferTypeOfExpr(e.arg1)
        itype2 = self.inferTypeOfExpr(e.arg2)
        # FIXME: conversion rules
        if itype1.bitSize() >= itype2.bitSize():
          if types.FLOAT16_TC <= itype2.typeCode <= types.FLOAT128_TC:
            eType = itype2
          else:
            eType = itype1
        else:
          eType = itype1

      elif op.BO_REL_START_OC <= opCode <= op.BO_REL_END_OC:
        etype1 = self.inferTypeOfExpr(e.arg1)
        etype2 = self.inferTypeOfExpr(e.arg2)
        eType = types.Int32

    elif isinstance(e, lExpr.ArrayE):
      subEType = self.inferTypeOfExpr(e.of)
      if isinstance(subEType, types.Ptr):
        eType = subEType.getPointeeType()
      elif isinstance(subEType, types.ArrayT):
        eType = subEType.of

    elif isinstance(e, lExpr.DerefE):
      argType = self.inferTypeOfExpr(e.arg)
      if isinstance(argType, types.Ptr):
        eType = argType.getPointeeType()
      elif isinstance(argType, types.ArrayT):
        eType = argType.getElementType()
      else:
        assert False, msg.CONTROL_HERE_ERROR

    elif isinstance(e, lExpr.MemberE):
      fieldName = e.name
      of = e.of
      ofType = self.inferTypeOfExpr(of)
      if isinstance(ofType, types.Ptr):
        ofType = ofType.getPointeeType()
      elif isinstance(ofType, types.ArrayT):
        ofType = ofType.getElementType()
      assert isinstance(ofType, types.RecordT)
      eType = ofType.getMemberType(fieldName)

    elif isinstance(e, lExpr.SelectE):
      self.inferTypeOfExpr(e.cond)
      self.inferTypeOfExpr(e.arg1)
      eType2 = self.inferTypeOfExpr(e.arg2)
      eType = eType2  # type of 1 and 2 should be the same.

    elif isinstance(e, lExpr.AllocE):
      eType = types.Ptr(to=types.Void)

    elif isinstance(e, lExpr.AddrOfE):
      eType = types.Ptr(to=self.inferTypeOfExpr(e.arg))

    elif isinstance(e, lExpr.CallE):
      calleeType = self.inferTypeOfExpr(e.callee)
      if isinstance(calleeType, types.FuncSig):
        eType = calleeType.returnType
      elif isinstance(calleeType, types.Ptr):
        funcSig = calleeType.getPointeeType()
        assert isinstance(funcSig, types.FuncSig), f"{funcSig}"
        eType = funcSig.returnType

    else:
      # assert False, f"Unkown expression: {e} {type(e)}"
      if LS: LOG.error("Unknown_Expr_For_TypeInference: %s.", e)

    e.type = eType
    return eType


  def inferTypeOfInstr(self,
      insn: instr.InstrIT,
  ) -> types.Type:
    """Infer instruction type from the type of the expressions.
    After IR preprocessing, any newly created
    instruction should have its type inferred
    before any other work is done on it.
    """
    iType = types.Void
    _instr = instr  # for efficiency

    if isinstance(insn, _instr.AssignI):
      t1 = self.inferTypeOfExpr(insn.lhs)
      t2 = self.inferTypeOfExpr(insn.rhs)
      iType = t1
      if AS and t1 != t2:
        LOG.debug(f"Lhs and Rhs types differ: {insn}, lhstype = {t1}, rhstype = {t2}.")

    elif isinstance(insn, _instr.UseI):
      for var in insn.vars:
        iType = self.inferTypeOfVal(var)

    elif isinstance(insn, _instr.FilterI):
      pass

    elif isinstance(insn, _instr.CondReadI):
      iType = self.inferTypeOfVal(insn.lhs)

    elif isinstance(insn, _instr.UnDefValI):
      iType = self.inferTypeOfVal(insn.lhs)

    elif isinstance(insn, _instr.CondI):
      _ = self.inferTypeOfExpr(insn.arg)

    elif isinstance(insn, _instr.ReturnI):
      if insn.arg is not None:
        iType = self.inferTypeOfExpr(insn.arg)

    elif isinstance(insn, _instr.CallI):
      iType = self.inferTypeOfExpr(insn.arg)

    elif isinstance(insn, _instr.NopI):
      pass  # i.e. types.Void

    elif isinstance(insn, _instr.ExReadI):
      pass  # i.e. types.Void

    elif isinstance(insn, instr.ParallelI):
      for ins in insn.yieldInstructions():
        iType = self.inferTypeOfInstr(ins)

    else:
      if LS: LOG.error("Unknown_Instr_For_TypeInference: %s.", insn)

    insn.type = iType
    return iType


  ################################################
  # BOUND END  : Type_Inference
  ################################################

  def logUsefulInfo(self) -> None:
    """Logs useful information of this translation unit."""
    if LS: LOG.debug("\nINITIALIZING_TRANSLATION_UNIT:"
                      "Name: %s, Vars#: %s, Records#: %s, Functions#: %s.\n",
                     self.name, len(self.allVars), len(self.allRecords),
                     len(self.allFunctions))
    if LS: LOG.debug("TU_Description: %s", self.description)

    with io.StringIO() as sio:
      sio.write(f"VarDict (Total: {len(self.allVars)}), {{var name: "
                f"var type}}:\n")
      for varName in sorted(self.allVars):
        sio.write(f"  {varName!r}: {self.allVars[varName]}.\n")
      if LS: LOG.debug("%s", sio.getvalue())

    with io.StringIO() as sio:
      sio.write(f"Functions (Total: {len(self.allFunctions)}):\n")
      for func in self.yieldFunctions():
        sio.write(f"  {func.name!r}: returns: {func.sig.returnType}, params: "
                  f"{func.paramNames}.\n")
      for record in self.yieldRecords():
        sio.write(f"{record}\n")

      if LS: LOG.debug("%s", sio.getvalue())


  def fillTheRecordTypes(self, ):
    """Completes the record types.
    E.g. if only types.Struct("s:node") is present, it replaces it
    with the reference to the complete definition of the Struct.
    """
    # STEP 1. Complete/Correct all the record types.
    for record in self.yieldRecords():
      newFields = []
      for field in record.members:
        newType = self.findAndFillRecordType(field[1])
        newFields.append((field[0], newType))
      record.members = newFields

    # STEP 2. Complete/Correct all the variable types.
    for varName in self.allVars.keys():
      varType = self.allVars[varName]
      completedVarType = self.findAndFillRecordType(varType)
      self.allVars[varName] = completedVarType


  def findAndFillRecordType(self, varType: types.Type):
    """Recursively finds the record type and replaces them with
    the reference to the complete definition in self.allRecords."""
    if isinstance(varType, (types.Struct, types.Union)):
      return self.allRecords[varType.name]

    elif isinstance(varType, types.Ptr):
      ptrTo = self.findAndFillRecordType(varType.getPointeeTypeFinal())
      return types.Ptr(to=ptrTo, indlev=varType.indlev)

    elif isinstance(varType, types.ArrayT):
      arrayOf = self.findAndFillRecordType(varType.of)
      if isinstance(varType, types.ConstSizeArray):
        return types.ConstSizeArray(of=arrayOf, size=varType.size)
      elif isinstance(varType, types.VarArray):
        return types.VarArray(of=arrayOf)
      elif isinstance(varType, types.IncompleteArray):
        return types.IncompleteArray(of=arrayOf)

    return varType  # by default return the same type


  def canonicalize(self) -> None:
    """Optimizes SPAN IR"""
    self.replaceMemAllocations()
    self.replaceZeroWithNullPtr()  # FIXME: should be used?

    self.removeNopInsns()  # (OPTIONAL)
    for func in self.yieldFunctionsWithBody():
      self.evaluateConstantExprs(func)  # (MUST)
      self.evaluateCastOfConstants(func)  # (MUST)
      self.evaluateConstIfStmts(func)  # (MUST)
      self.removeNopBbs(func)  # (OPTIONAL)
      self.removeUnreachableBbs(func)  # (OPTIONAL)

    self.canonicalizeExpressions()  # MUST
    self.createAndAddGlobalDummyVar(irConv.DUMMY_VAR_TYPE)


  def fillGlobalInitsFunction(self):
    """Fill the special global inits function,
    that holds the initializations of global variables,
    with initialization to default values of variables
    that are not present in it."""

    func: constructs.Func = self.allFunctions[irConv.GLOBAL_INITS_FUNC_NAME]
    objsInitialized: Set[types.VarNameT] = self.extractInitializedGlobals()
    self._globalVarNames = self._getNamesGlobal()
    globalObjs: Set[types.VarNameT] = self._globalVarNames

    newInsns: List[instr.AssignI] = []

    nonInitGlobals = globalObjs - objsInitialized
    for varName in sorted(nonInitGlobals):
      objType = self.inferTypeOfVal(varName)
      defaultInitExpr = expr.getDefaultInitExpr(objType)
      if defaultInitExpr is not None:
        lhsExpr = expr.VarE(name=varName)
        rhsExpr = defaultInitExpr
        insn = instr.AssignI(lhsExpr, rhsExpr)
        self.inferTypeOfInstr(insn)
        newInsns.append(insn)

    allInsns = []
    allInsns.extend(newInsns)
    allInsns.extend(func.instrSeq)

    # replace old function with new that has all global inits
    newFunc = constructs.Func(
      name=irConv.GLOBAL_INITS_FUNC_NAME,
      instrSeq=allInsns
    )
    newFunc.tUnit = self  # IMPORTANT
    # newFunc.basicBlocks, newFunc.bbEdges = \
    #   constructs.Func.genBasicBlocks(newFunc.instrSeq)
    self.allFunctions[irConv.GLOBAL_INITS_FUNC_NAME] = newFunc


  def extractInitializedGlobals(self) -> Set[types.VarNameT]:
    """Extracts names of globals initialized
    in the global inits function."""
    func: constructs.Func = self.allFunctions[irConv.GLOBAL_INITS_FUNC_NAME]
    varNames: Set[types.VarNameT] = set()

    for insn in func.yieldInstrSeq():
      if isinstance(insn, instr.NopI): continue
      assert isinstance(insn, instr.AssignI)
      assert isinstance(insn.lhs, expr.VarE), f"{insn.lhs}"
      varNames.add(insn.lhs.name)

    return varNames


  def getGlobalInitFunction(self) -> constructs.Func:
    return self.allFunctions[irConv.GLOBAL_INITS_FUNC_NAME]


  def evaluateCastOfConstants(self, func: constructs.Func) -> None:
    """Remove casts like:
    (types.Ptr(types.Int8, 1)) "string literal"
    FIXME: identify and add more cases
    """
    assignInstrCode = instr.ASSIGN_INSTR_IC
    for bbId, bb in func.yieldBasicBlocks():
      for index in range(len(bb)):
        if bb[index].instrCode == assignInstrCode:
          insn: instr.AssignI = bb[index]
          rhs = insn.rhs
          newRhs = rhs
          if isinstance(rhs, expr.CastE):
            arg = rhs.arg
            if isinstance(arg, expr.LitE):
              if arg.isString():
                newRhs = arg
          if newRhs is not rhs:
            insn.rhs = newRhs
            self.inferTypeOfInstr(insn)


  def evaluateConstantExprs(self, func: constructs.Func) -> None:
    """Reduces/solves all binary/unary constant expressions."""
    assignInstrCode = instr.ASSIGN_INSTR_IC
    for bbId, bb in func.yieldBasicBlocks():
      for index in range(len(bb)):
        if bb[index].instrCode == assignInstrCode:
          insn: instr.AssignI = bb[index]
          rhs = self.reduceConstExpr(insn.rhs)
          if rhs is not insn.rhs:
            insn.rhs = rhs
            self.inferTypeOfInstr(insn)


  def reduceConstExpr(self, e: expr.ExprET) -> expr.ExprET:
    """Converts: 5 + 6, 6 > 7, -5, +6, !7, ~9, ... to a single literal."""
    newExpr = e  # default value on return

    if isinstance(e, expr.BinaryE):
      arg1 = e.arg1
      arg2 = e.arg2
      opCode = e.opr.opCode

      if isinstance(arg1, expr.LitE) and isinstance(arg2, expr.LitE):
        if opCode == op.BO_ADD_OC:
          newExpr = expr.LitE(arg1.val + arg2.val, info=arg1.info)  # type: ignore
        elif opCode == op.BO_SUB_OC:
          newExpr = expr.LitE(arg1.val - arg2.val, info=arg1.info)  # type: ignore
        elif opCode == op.BO_MUL_OC:
          newExpr = expr.LitE(arg1.val * arg2.val, info=arg1.info)  # type: ignore
        elif opCode == op.BO_DIV_OC:
          newExpr = expr.LitE(arg1.val / arg2.val, info=arg1.info)  # type: ignore
        elif opCode == op.BO_MOD_OC:
          newExpr = expr.LitE(arg1.val % arg2.val, info=arg1.info)  # type: ignore

        elif opCode == op.BO_LT_OC:
          newExpr = expr.LitE(int(arg1.val < arg2.val), info=arg1.info)  # type: ignore
        elif opCode == op.BO_LE_OC:
          newExpr = expr.LitE(int(arg1.val <= arg2.val), info=arg1.info)  # type: ignore
        elif opCode == op.BO_EQ_OC:
          newExpr = expr.LitE(int(arg1.val == arg2.val), info=arg1.info)  # type: ignore
        elif opCode == op.BO_NE_OC:
          newExpr = expr.LitE(int(arg1.val != arg2.val), info=arg1.info)  # type: ignore
        elif opCode == op.BO_GE_OC:
          newExpr = expr.LitE(int(arg1.val >= arg2.val), info=arg1.info)  # type: ignore
        elif opCode == op.BO_GT_OC:
          newExpr = expr.LitE(int(arg1.val > arg2.val), info=arg1.info)  # type: ignore

    elif isinstance(e, expr.UnaryE):
      arg = e.arg
      opCode = e.opr.opCode

      if isinstance(arg, expr.LitE):
        if opCode == op.UO_PLUS_OC:
          newExpr = e.arg
        elif opCode == op.UO_MINUS_OC:
          newExpr = expr.LitE(e.arg.val * -1, info=arg.info)  # type: ignore
        elif opCode == op.UO_LNOT_OC:
          newExpr = expr.LitE(int(not (bool(arg.val))), info=arg.info)
        elif opCode == op.UO_BIT_NOT_OC:
          newExpr = expr.LitE(~arg.val, info=arg.info)  # type: ignore

    return newExpr


  def removeNopInsns(self) -> None:
    """Removes NopI() from bbs with more than one instruction."""
    for func in self.yieldFunctionsWithBody():
      bbIds = func.basicBlocks.keys()

      for bbId in bbIds:
        bb = func.basicBlocks[bbId]
        newBb = [insn for insn in bb if not isinstance(insn, instr.NopI)]
        if bbId == -1: # start bb
          newBb.insert(0, instr.NopI())  # IMPORTANT

        if len(newBb) == 0:
          newBb.append(instr.NopI())  # let one NopI be (such BBs are removed later)
        func.basicBlocks[bbId] = newBb


  def removeUnreachableBbs(self, func: constructs.Func) -> None:
    """Removes BBs that are not reachable from StartBB."""
    allBbIds = func.basicBlocks.keys()

    # collect all dest bbIds
    destBbIds = {-1}  # start bbId is always reachable
    for bbEdge in func.bbEdges:
      destBbIds.add(bbEdge[1])
    unreachableBbIds = allBbIds - destBbIds

    # remove all edges going out of reachable bbs
    takenEdges = []
    for bbEdge in func.bbEdges:
      if bbEdge[0] in unreachableBbIds: continue
      takenEdges.append(bbEdge)
    func.bbEdges = takenEdges

    # remove unreachableBbIds one by one
    for bbId in unreachableBbIds:
      del func.basicBlocks[bbId]

    if unreachableBbIds:
      # go recursive, since there could be new unreachable bb ids
      return self.removeUnreachableBbs(func)


  def genCondTmpVar(self, func: constructs.Func, t: types.Type) -> expr.VarE:
    """Generates a new cond tmp var and adds its to the
    variables map."""
    number: int = 90
    fName = irConv.extractOriginalFuncName(func.name)

    while True:
      name = f"v:{fName}:" + irConv.COND_TMPVAR_GEN_STR.format(number=number)
      if name not in self.allVars:
        break
      number += 1

    # if here the name is new and good to go
    self.addVarNames(name, t, True)
    e = expr.VarE(name)
    e.type = t
    return e


  def evaluateConstIfStmts(self, func: constructs.Func) -> None:
    """Changes if stmt on a const value to, to use a tmp variable.
    It may lead to some unreachable BBs."""

    for bbId, bbInsns in func.basicBlocks.items():
      if not bbInsns: continue  # if bb is blank
      ifInsn = bbInsns[-1]
      if isinstance(ifInsn, instr.CondI):
        arg = ifInsn.arg
        if isinstance(arg, expr.LitE):
          if type(arg.val) == str:
            t: types.Type = types.Ptr(to=types.Char)
          else:
            t = self.inferTypeOfVal(arg.val)

          tmpVarExpr = self.genCondTmpVar(func, t)
          tmpVarExpr.info = arg.info
          tmpAssignI = instr.AssignI(tmpVarExpr, arg, info=arg.info)
          tmpAssignI.type = t

          bbInsns.insert(-1, tmpAssignI)
          ifInsn.arg = tmpVarExpr


  def removeNopBbs(self, func: constructs.Func) -> None:
    """Remove BBs that only have instr.NopI(). Except START and END."""

    bbIds = func.basicBlocks.keys()
    for bbId in bbIds:
      if bbId in [-1, 0]: continue  # leave START and END BBs as it is.

      onlyNop = True
      for insn in func.basicBlocks[bbId]:
        if isinstance(insn, instr.NopI): continue
        onlyNop = False

      if onlyNop:
        # then remove this bb and related edges
        retainedEdges = []
        predEdges = []
        succEdges = []
        for bbEdge in func.bbEdges:
          if bbEdge[0] == bbId:
            succEdges.append(bbEdge)  # ONLY ONE EDGE
          elif bbEdge[1] == bbId:
            predEdges.append(bbEdge)
          else:
            retainedEdges.append(bbEdge)

        if AS: assert len(succEdges) == 1, msg.SHOULD_BE_ONLY_ONE_EDGE

        for predEdge in predEdges:
          newEdge = (predEdge[0], succEdges[0][1], predEdge[2])
          retainedEdges.append(newEdge)
        func.bbEdges = retainedEdges


  def replaceMemAllocations(self) -> None:
    """Replace calloc(), malloc() with pseudo variables of type array.
    Should be called when types for expressions have been inferred.
    """
    for func in self.yieldFunctionsWithBody():
      for bb in func.basicBlocks.values():
        for i in range(len(bb) - 1):
          insn = bb[i]
          # SPAN IR separates a call and its cast into two statements.
          if isinstance(insn, instr.AssignI) and isinstance(insn.rhs, expr.CallE):
            if self.isMemoryAllocationCall(insn.rhs):
              memAllocInsn: instr.AssignI = insn
              if irConv.isTmpVar(memAllocInsn.lhs.name):  # stored in a void* temporary
                # then next insn must be a cast and store to a non tmp variable
                castInstr = bb[i + 1]
                newInstr = self.conditionallyAddPseudoVar(func.name, castInstr, memAllocInsn)
                if newInstr is not None:  # hence pseudo var has been added
                  bb[i] = instr.NopI()  # i.e. remove current instruction
                  bb[i + 1] = newInstr
              else:
                newInstr = self.conditionallyAddPseudoVar(func.name, memAllocInsn)
                if newInstr:
                  bb[i] = newInstr


  def conditionallyAddPseudoVar(self,
      funcName: types.FuncNameT,
      insn: instr.AssignI,
      prevInsn: instr.AssignI = None,
  ) -> Opt[instr.InstrIT]:
    """Modifies rhs to address of a pseudo var with the correct type.
    Only two instruction forms should be in insn:
      <ptr_var> = (<type>*) <tmp_var>; // cast insn
      <ptr_var> = <malloc/calloc>(...); // memory alloc insn
    """
    lhs = insn.lhs
    assert isinstance(lhs, expr.VarE), f"{lhs}"
    # if isTmpVar(lhs.name): return None

    rhs = insn.rhs
    if isinstance(rhs, expr.CastE):
      if not irConv.isTmpVar(rhs.arg.name):
        return None
      # if here, assume that the tmp var is assigned a heap location

    if isinstance(rhs, (expr.CastE, expr.CallE)):
      # assume it is malloc/calloc (it should be) if it is a CallE
      lhsType = lhs.type
      assert isinstance(lhsType, types.Ptr), f"{lhsType}"
      pVar = self.genPseudoVar(funcName, rhs.info,
                               lhsType.getPointeeType(), insn, prevInsn)
      newInsn = instr.AssignI(lhs, expr.AddrOfE(pVar, rhs.info))
      self.inferTypeOfInstr(newInsn)
      return newInsn

    return None


  def genPseudoVar(self,
      funcName: types.FuncNameT,
      info: Opt[types.Info],
      varType: types.Type,
      insn: instr.AssignI,
      prevInsn: instr.AssignI = None,
  ) -> expr.PseudoVarE:
    if funcName not in self._funcPseudoCountMap:
      self._funcPseudoCountMap[funcName] = 1
    currCount = self._funcPseudoCountMap[funcName]
    self._funcPseudoCountMap[funcName] = currCount + 1

    nakedPvName = irConv.NAKED_PSEUDO_VAR_NAME.format(count=currCount)
    pureFuncName = funcName.split(":")[1]
    pvName = f"v:{pureFuncName}:{nakedPvName}"

    self.addVarNames(pvName, irConv.PSEUDO_VAR_TYPE(of=varType), True)

    # self._nameInfoMap[pvName] = types.NameInfo(
    #   pvName, types.PSEUDO_VAR_TYPE(of=varType))

    self._pseudoVars.add(pvName)
    if prevInsn is None:  # insn can never be None
      sizeExpr = self.getMemAllocSizeExpr(insn)
      insns = [insn]
    else:
      sizeExpr = self.getMemAllocSizeExpr(prevInsn)
      insns = [prevInsn, insn]

    pVarE = expr.PseudoVarE(pvName, info=info, insns=insns, sizeExpr=sizeExpr)
    pVarE.type = varType

    return pVarE


  def getMemAllocSizeExpr(self, insn: instr.AssignI) -> expr.ExprET:
    """Returns the expression deciding the size of memory allocated."""
    rhs = insn.rhs
    assert isinstance(rhs, expr.CallE), f"{rhs}"
    calleeName = rhs.callee.name

    if calleeName == "f:malloc":
      sizeExpr: expr.ExprET = rhs.args[0]  # the one and only argument is the size expr
    elif calleeName == "f:calloc":
      sizeExpr = expr.BinaryE(rhs.args[0], op.BO_MUL, rhs.args[1], info=rhs.args[0].info)
      self.inferTypeOfExpr(sizeExpr)
    else:
      raise ValueError()

    return sizeExpr


  def isMemoryAllocationCall(self,
      callExpr: expr.CallE,
  ) -> bool:
    memAllocCall = False
    calleeName = callExpr.callee.name
    if calleeName in irConv.memAllocFunctions:
      # memAllocCall = True
      func: constructs.Func = self.allFunctions[calleeName]
      if func.sig == irConv.memAllocFunctions["f:malloc"] or \
          func.sig == irConv.memAllocFunctions["f:calloc"]:
        memAllocCall = True

    return memAllocCall


  def getTmpVarExpr(self,
      vName: types.VarNameT,
  ) -> Opt[expr.ExprET]:
    """Returns the expression the given tmp var is assigned.
    It only tracks some tmp vars, e.g. ones like 3t, 1if, 2if ...
    The idea is to map the tmp vars that are assigned only once.
    """
    if vName in self._funcTmpExprMap:
      return self._funcTmpExprMap[vName]
    return None  # None if tmp var is not tracked


  def extractTmpVarAssignExprs(self) -> None:
    """Extract temporary variables and the unique expressions
    they hold the value of.
    It caches the result in a global map."""

    tmpExprMap = self._funcTmpExprMap

    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        if insn.instrCode == instr.ASSIGN_INSTR_IC:
          assert isinstance(insn, instr.AssignI), f"{insn}"
          if isinstance(insn.lhs, expr.VarE):
            name = insn.lhs.name
            if irConv.isNormalTmpVar(name) or irConv.isCondTmpVar(name):
              tmpExprMap[name] = insn.rhs


  def getNameInfo(self,
      name: types.VarNameT
  ) -> Opt[types.VarNameInfo]:
    """Returns the NameTypeInfo of a name or None if there is none"""
    if AS: assert name in self._nameInfoMap, msg.INVARIANT_VIOLATED
    return self._nameInfoMap[name]


  def nameHasArray(self,
      name: types.VarNameT
  ) -> Opt[bool]:
    """Returns true if the name contains array access"""
    if name in self._nameInfoMap:
      return self._nameInfoMap[name].hasArray
    else:
      assert False, f"{msg.INVARIANT_VIOLATED}: {name}"


  def getNamesLocal(self,
      func: constructs.Func,
      givenType: types.Type = None,
      cacheResult: bool = True,  # set to False in very special case
      numeric: bool = False,
      integer: bool = False,
      pointer: bool = False,
  ) -> Set[types.VarNameT]:
    """Returns set of variable names local to a function.
    Without givenType it returns all the variables accessible."""
    self.stats.getNamesTimer.start()
    if isinstance(givenType, types.FuncSig):
      self.stats.getNamesTimer.stop()
      return set()  # FuncSig is never local

    funcName = func.name
    key = givenType
    if numeric: key = types.NumericAny
    if integer: key = types.IntegerAny
    if pointer: key = types.PointerAny
    tup = (funcName, key)

    if tup in self._typeFuncLocalNameMap:
      self.stats.getNamesTimer.stop()
      return self._typeFuncLocalNameMap[tup]

    names = set()
    nakedFuncName = funcName.split(":")[1]
    prefix = f"v:{nakedFuncName}"
    for objInfo in self._nameInfoMap.values():
      if objInfo.name.startswith(prefix):
        objType = objInfo.type
        nameInfos = objType.getNamesOfType(givenType, objInfo.name)
        for nameInfo in nameInfos:
          names.add(nameInfo.name)

    if numeric: names = self.filterNamesNumeric(names)
    if integer: names = self.filterNamesInteger(names)
    if pointer: names = self.filterNamesPointer(names)

    if cacheResult:
      self._typeFuncLocalNameMap[tup] = names  # cache the result

    self.stats.getNamesTimer.stop()
    return names


  def _getNamesGlobal(self) -> Set[types.VarNameT]:
    names = set()
    for name, info in self._nameInfoMap.items():
      if irConv.isGlobalName(name):
        tmpNameSet = irConv.getSuffixes(None, name, info.type)
        names.update(tmpNameSet)
    return names


  def getNamesGlobal(self,
      givenType: Opt[types.Type] = None,
      cacheResult: bool = True,  # set to False in very special case
      numeric: bool = False,
      integer: bool = False,
      pointer: bool = False,
  ) -> Set[types.VarNameT]:
    """Returns list of global variable names.
    Without givenType it returns all the variables accessible.
    Note: this method handles function signatures also.
    """
    self.stats.getNamesTimer.start()
    key = givenType
    if numeric: key = types.NumericAny
    if integer: key = types.IntegerAny
    if pointer: key = types.PointerAny

    if key in self._globalTypeVarNamesMap:
      self.stats.getNamesTimer.stop()
      return self._globalTypeVarNamesMap[key]

    names: Set[types.VarNameT] = set()
    if isinstance(givenType, types.FuncSig):
      names.update(func.name for func in self.getFunctionsOfGivenSignature(givenType))
    else:
      for objName in self._globalsAndAddrTakenSet:
        objType = self.inferTypeOfVal(objName)
        nameInfos = objType.getNamesOfType(givenType, objName)
        for nameInfo in nameInfos:
          names.add(nameInfo.name)

    if numeric: names = self.filterNamesNumeric(names)
    if integer: names = self.filterNamesInteger(names)
    if pointer: names = self.filterNamesPointer(names)

    if cacheResult:
      self._globalTypeVarNamesMap[key] = names  # cache the result

    self.stats.getNamesTimer.stop()
    return names


  def createAndAddLocalDummyVar(self,
      func: constructs.Func,
      givenType: types.Type
  ) -> types.VarNameT:
    funcName = irConv.extractOriginalFuncName(func.name)
    newDummyName = f"v:{funcName}:{self._dummyVarCount}d"
    self.addVarNames(newDummyName, givenType, True)
    self._dummyVarCount += 1
    return newDummyName


  def createAndAddGlobalDummyVar(self,
      givenType: types.Type
  ) -> types.VarNameT:
    newDummyName = f"g:{self._dummyVarCount}d"
    # self.allVars[newDummyName] = givenType
    self.addVarNames(newDummyName, givenType, True)
    self._globalsAndAddrTakenSet.add(newDummyName)
    self._dummyVarCount += 1
    return newDummyName


  def getNames(self,
      givenType: types.Type
  ) -> Set[types.VarNameT]:
    """Gets names of givenType in the tUnit."""
    names = set()
    for objInfo in self._nameInfoMap.values():
      if givenType == objInfo.type:
        names.add(objInfo.name)
      elif isinstance(objInfo.type, types.ArrayT):
        if givenType == objInfo.type.getElementType():
          names.add(objInfo.name)
    return names


  def getNamesEnv(self,
      func: constructs.Func,
      givenType: types.Type = None,
      cacheResult: bool = True,  # set to False in a very special case
      numeric: bool = False,
      integer: bool = False,
      pointer: bool = False,
  ) -> Set[types.VarNameT]:
    """Returns set of variables accessible in a given function (of the given type).
    Without givenType it returns all the variables accessible."""
    # TODO: add all heap locations (irrespective of the function) too
    self.stats.getNamesTimer.start()
    fName = func.name
    key = givenType
    if numeric: key = types.NumericAny
    if integer: key = types.IntegerAny
    if pointer: key = types.PointerAny

    tup = (fName, key)
    if tup in self._typeFuncEnvNamesMap:
      self.stats.getNamesTimer.stop()
      return self._typeFuncEnvNamesMap[tup]

    envVars = self.getNamesGlobal(givenType, cacheResult,
                                  numeric=numeric, integer=integer, pointer=pointer) \
              | self.getNamesLocal(func, givenType, cacheResult,
                                   numeric=numeric, integer=integer, pointer=pointer)
    if cacheResult:
      self._typeFuncEnvNamesMap[tup] = envVars  # cache the result

    self.stats.getNamesTimer.stop()
    return envVars


  def getNamesPseudoLocal(self,
      func: constructs.Func,
  ) -> Set[types.VarNameT]:
    """Returns set of pseudo variable names local to a function."""
    self.stats.getNamesTimer.start()
    funcName = func.name
    if funcName in self._localPseudoVars:
      self.stats.getNamesTimer.stop()
      return self._localPseudoVars[funcName]

    # use getLocalVars() to do most work
    localVars: Set[types.VarNameT] = self.getNamesLocal(func)

    vNameSet = set()
    for vName in localVars:
      if irConv.PSEUDO_VAR_REGEX.fullmatch(vName):
        vNameSet.add(vName)

    self._localPseudoVars[funcName] = vNameSet  # cache the result
    self.stats.getNamesTimer.stop()
    return vNameSet


  def getNamesPseudoAll(self) -> Set[types.VarNameT]:
    """Returns set of all pseudo var names in the translation unit."""
    self.stats.getNamesTimer.start()
    if self._allPseudoNames is not None:
      self.stats.getNamesTimer.stop()
      return self._allPseudoNames

    varNames = set()
    for vName in self._nameInfoMap.keys():
      if irConv.PSEUDO_VAR_REGEX.fullmatch(vName):
        varNames.add(vName)

    self._allPseudoNames = varNames
    self.stats.getNamesTimer.stop()
    return varNames


  def __eq__(self, other) -> bool:
    """This method is elaborate to assist testing."""
    if self is other:
      return True
    if not isinstance(other, TranslationUnit):
      return NotImplemented
    return self.name == other.name


  def __hash__(self):
    return hash(self.name)


  def isEqual(self,
      other: 'TranslationUnit'
  ) -> bool:
    """This method is elaborate to assist testing."""
    equal = True
    if not isinstance(other, TranslationUnit):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      equal = False
    if not self.name == other.name:
      if LS: LOG.debug("NamesDiffer: %s, %s", self.name, other.name)
      equal = False

    selfAllVarNames = self.allVars.keys()
    otherAllVarNames = other.allVars.keys()
    matchVariables = True
    if not len(selfAllVarNames) == len(otherAllVarNames):
      if LS: LOG.error("NumOfVarsDiffer: (TUnit: '%s')", self.name)
      equal = False
      matchVariables = False
    if not self.allVars == other.allVars:
      if LS: LOG.error("VarDetailsDiffer: (TUnit: '%s') (Self: %s) (Other: %s)",
                       self.name, selfAllVarNames, otherAllVarNames)
      equal = False
      matchVariables = False
    if matchVariables:
      for varName in selfAllVarNames:
        selfVarType = self.allVars[varName]
        otherVarType = other.allVars[varName]
        if not selfVarType == otherVarType:
          if LS: LOG.error("VarTypesDiffer: (Var: '%s')", varName)
          equal = False


    def checkDictEquality(dict1: dict, dict2: dict, string: str) -> bool:
      isEqual = True
      matchObjs = True
      keys1 = dict1.keys()
      keys2 = dict2.keys()
      if not len(keys1) == len(keys2):
        if LS: LOG.error(f"NumOf{string}Differ: (TUnit: '%s')", string)
        isEqual = False
        matchObjs = False

      if matchObjs:
        for key in (keys1 | keys2):
          if key not in dict1:
            return False
          if key not in dict2:
            return False
          val1 = dict1[key]
          val2 = dict1[key]
          if not isinstance(val2, val1.__class__):
            if LS: LOG.error("ObjectTypesDiffer: (Obj: '%s')", key)
            isEqual = False

          if not val1.isEqual(val2):
            if LS: LOG.error(f"{string}ObjectDiffer: (Obj: '%s')", key)
            isEqual = False

      return isEqual


    if not checkDictEquality(self.allRecords, other.allRecords, "Record"):
      equal = False

    if not checkDictEquality(self.allFunctions, other.allFunctions, "Function"):
      equal = False

    if not equal:
      if LS: LOG.error("TUnitsDiffer: (TUnit: '%s')", self.name)

    return equal


  def getFunctionsOfGivenSignature(self,
      givenSignature: types.FuncSig
  ) -> List[constructs.Func]:
    """Returns functions with the given signature."""
    if givenSignature in self._funcSigToFuncObjMap:
      return self._funcSigToFuncObjMap[givenSignature]

    funcList: List[constructs.Func] = []
    for func in self.yieldFunctions():
      if func.sig == givenSignature:
        funcList.append(func)

    self._funcSigToFuncObjMap[givenSignature] = funcList
    return funcList


  def getExprLValuesWhenInLhs(self,
      func: constructs.Func,
      e: expr.ExprET
  ) -> List[types.VarNameT]:
    """Returns the locations that may be modified,
    if this expression was on the LHS of an assignment."""
    names = []

    if isinstance(e, expr.VarE):
      names.append(e.name)
      return names

    elif isinstance(e, expr.DerefE):
      names.extend(self.getNamesEnv(func, e.type))
      return names

    elif isinstance(e, expr.ArrayE):
      if e.hasDereference():
        names.extend(self.getNamesEnv(func, e.type))
      else:
        names.append(e.getFullName())
      return names

    elif isinstance(e, expr.MemberE):
      of = e.of.type
      assert isinstance(of, types.Ptr), f"{e}: {of}"
      for name in self.getNamesEnv(func, of.getPointeeType()):
        names.append(f"{name}.{e.name}")
      return names

    raise ValueError(f"{e}")


  def getExprLValuesForCallExpr(self,
      func: constructs.Func,  # the caller
      e: expr.CallE
  ) -> Set[types.VarNameT]:
    """E.g. in call: func(a, b, p)
    An over-approximation.
    All variables whose address has been taken can be modified.

    # If p is pointer to integers, then all the integer variables
    # visible in the caller can be modified.
    # If p is ptr-to ptr-to int, then all the ptr-to int and int variables
    # visible in the caller can be modified.
    """
    # names = set()

    # for arg in e.args:
    #   names |= self.getExprLValuesForCallArgument(func, arg)

    # names.update(self.getNamesGlobal())
    # return names
    return self.getNamesGlobal()


  def getExprLValuesForCallArgument(self,
      func: constructs.Func,  # the caller
      arg: expr.ExprET, # only LitE, VarE or AddrOfE (&a form only)
  ) -> Set[types.VarNameT]:
    """Conservatively returns the set of names that can be
    possibly modified by passing the argument named varName or &varName to
    a function call.
    """
    names = set()

    def addNamesThatCanBeModified(argType, names):
      if isinstance(argType, (types.RecordT, types.ArrayT)):
        varNames = self.getNamesGlobal(argType)
        for varName in varNames:
          varNameInfos = argType.getNamesOfType(None, prefix=varName)
          for vnInfo in varNameInfos:
            names.add(vnInfo.name)

    argType = arg.type
    if isinstance(arg, expr.AddrOfE):
      names.add(arg.arg.getFullName())
      argType = arg.arg.type

    while isinstance(argType, types.Ptr):
        argType = argType.getPointeeType()
        names.update(self.getNamesEnv(func, argType))

    addNamesThatCanBeModified(argType, names)
    return names


  def filterNamesNumeric(self,
      names: Set[types.VarNameT]
  ) -> Set[types.VarNameT]:
    """Remove names which are not numeric."""
    filteredNames = set()
    for name in names:
      objType = self.inferTypeOfVal(name)
      if objType.isNumeric():
        filteredNames.add(name)
      elif isinstance(objType, types.ArrayT):
        arrayElementType = objType.getElementType()
        if arrayElementType.isNumeric():
          filteredNames.add(name)

    return filteredNames


  def filterNamesInteger(self,
      names: Set[types.VarNameT]
  ) -> Set[types.VarNameT]:
    names = self.filterNamesNumeric(names)
    filteredNames = set()
    for name in names:
      objType = self.inferTypeOfVal(name)
      if objType.isInteger():
        filteredNames.add(name)
      elif isinstance(objType, types.ArrayT):
        arrayElementType = objType.getElementType()
        if arrayElementType.isInteger():
          filteredNames.add(name)

    return filteredNames


  def filterNamesPointer(self,
      names: Set[types.VarNameT]
  ) -> Set[types.VarNameT]:
    """Remove names which are not pointers.
    An array containing pointers is also considered as pointer."""
    filteredNames = set()
    for name in names:
      nameType = self.inferTypeOfVal(name)
      if nameType.isPointer():
        filteredNames.add(name)
      elif isinstance(nameType, types.ArrayT):
        arrayElementType = nameType.getElementType()
        if arrayElementType.isPointer():
          filteredNames.add(name)

    return filteredNames


  def dumpIr(self) -> str:
    """Dump the current IR (translation unit).
    This output can be re-read by SPAN.
    It helps confirm that SPAN can reproduce the IR it read.
    """
    return repr(self)


  def __repr__(self):
    allVars = io.StringIO()
    allVars.write("{\n")
    for vName in sorted(self.allVars.keys()):
      allVars.write(f"    {repr(vName)}: {repr(self.allVars[vName])},\n")
    allVars.write("  }")

    allRecords = io.StringIO()
    allRecords.write("{\n")
    for record in self.yieldRecords():
      allRecords.write(f"    {repr(record.name)}: {repr(record)}, "
                       f"# end record {repr(record.name)}\n\n")
    allRecords.write("  }")

    allFunctions = io.StringIO()
    allFunctions.write("{\n")
    for func in self.yieldRecords():
      allFunctions.write(f"    {repr(func.name)}: {repr(func)}, "
                         f"# end function {repr(func.name)}\n\n")
    allFunctions.write("  }")

    return f"tunit.TranslationUnit(\n" \
           f"  name= {repr(self.name)},\n" \
           f"  description= {repr(self.description)},\n" \
           f"  allVars= {allVars.getvalue()}, # end allVars\n\n" \
           f"  allRecords= {allRecords.getvalue()}, # end allRecords\n" \
           f"  allFunctions= {allFunctions.getvalue()}, # end allFunctions\n" \
           f")"


  @staticmethod
  def getNamesUsedInExprSyntactically(e: expr.ExprET,
      forLiveness = True,
  ) -> Set[types.VarNameT]:
    """Returns the names syntactically present in the expression.
    Note if forLiveness if false,
      It will also return the function name in a call.
      The name of variable whose address is taken.
    """
    thisFunction = TranslationUnit.getNamesUsedInExprSyntactically

    if isinstance(e, expr.LitE):
      return set()  # empty set

    elif isinstance(e, expr.VarE):  # covers PseudoVarE too
      return {e.name}

    elif isinstance(e, expr.SizeOfE):
      return {e.arg.name}

    elif isinstance(e, expr.CastE):
      return thisFunction(e.arg, forLiveness)

    elif isinstance(e, expr.AddrOfE):
      if forLiveness and isinstance(e.arg, expr.VarE):
        return set()  # i.e. in '&a' discard 'a'
      else:
        return thisFunction(e.arg, forLiveness)

    elif isinstance(e, expr.DerefE):
      return thisFunction(e.arg, forLiveness)

    elif isinstance(e, expr.MemberE):
      assert e.hasDereference(), f"{e}"
      return thisFunction(e.of, forLiveness)

    elif isinstance(e, expr.ArrayE):
      return thisFunction(e.of, forLiveness)\
             | thisFunction(e.index, forLiveness)

    elif isinstance(e, expr.UnaryE):
      return thisFunction(e.arg, forLiveness)

    elif isinstance(e, expr.BinaryE):
      return thisFunction(e.arg1, forLiveness)\
             | thisFunction(e.arg2, forLiveness)

    elif isinstance(e, expr.SelectE):
      return thisFunction(e.cond, forLiveness)\
             | thisFunction(e.arg1, forLiveness)\
             | thisFunction(e.arg2, forLiveness)

    elif isinstance(e, expr.CallE):
      if forLiveness and e.callee.hasFunctionName():
        varNames = set()  # i.e. in 'f(a,b)' don't include 'f'
      else:
        varNames = thisFunction(e.callee, forLiveness)  # i.e. in 'f(a,b)' include 'f'
      for arg in e.args:
        varNames |= thisFunction(arg, forLiveness)
      return varNames

    assert False, msg.CONTROL_HERE_ERROR


  def getNamesUsedInExprNonSyntactically(self,
      func: constructs.Func,
      e: expr.ExprET,
  ) -> Set[types.VarNameT]:
    """
    This function returns the possible locations which
    may be used for their value indirectly (due to dereference)
    by the use of the given expression.
    """
    varNames = set()

    if isinstance(e, (expr.DerefE, expr.ArrayE, expr.MemberE)):
      varNames.update(self.getExprLValuesWhenInLhs(func, e))
      return varNames

    elif isinstance(e, expr.CallE):
      return self.getExprLValuesForCallExpr(func, e)

    else:
      # Returns an emptyset here, since all other expressions
      # only have syntactic reference.
      return varNames  # empty set


  def canonicalizeExpressions(self):
    """Canonicalize all expressions in SPAN IR.
    e.g. For all commutative expressions:
      0 == x to x == 0. (variable names first)
      b + a  to a + b.   (sort by variable name)
    """

    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        if isinstance(insn, instr.AssignI):
          swapArguments = False
          rhs = insn.rhs
          if isinstance(rhs, expr.BinaryE):
            if rhs.opr.isCommutative() or rhs.opr.isRelationalOp():
              arg1 = rhs.arg1
              arg2 = rhs.arg2

              if isinstance(rhs.arg1, expr.LitE):
                swapArguments = True
              elif isinstance(rhs.arg2, expr.LitE):
                pass
              else:
                # if here, both are variables (since both can't be literals)
                vNames = [arg1.name, arg2.name]
                vNames.sort()
                if vNames[0] == arg2.name:
                  swapArguments = True

              if swapArguments:
                arg = rhs.arg1
                rhs.arg1 = rhs.arg2
                rhs.arg2 = arg
                if rhs.opr.isRelationalOp():
                  rhs.opr = op.getFlippedRelOp(rhs.opr)


  def getFunctionObj(self,
      funcName: Opt[types.FuncNameT] = None,
      funcId: Opt[types.FuncIdT] = None
  ) -> constructs.Func:
    """Returns the function object either using the name or id."""
    assert funcName or funcId is not None, f"{funcName}, {funcId}"
    assert self._funcIdToFuncList, f"{self._funcIdToFuncList}"

    if funcName:
      if funcName in self.allFunctions:
        return self.allFunctions[funcName]
    elif funcId < len(self._funcIdToFuncList):
      return self._funcIdToFuncList[funcId]
    raise ValueError(f"{funcName}, {funcId}")


  def filterAwayCalleesWithNoBody(self,
      callSiteNodes: Opt[List[graph.CfgNode]],
  ) -> Opt[List[graph.CfgNode]]:
    """Filter away nodes with calls to functions with no body!"""
    if not callSiteNodes:
      return None

    newNodeList = []
    for node in callSiteNodes:
      callE = instr.getCallExpr(node.insn)
      assert callE is not None, f"{node}"
      func = self.getFunctionObj(callE.callee.name)
      if func.hasBody():
        # only add nodes with calls to functions which have body!
        newNodeList.append(node)

    return newNodeList
