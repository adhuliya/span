#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""
Defines a translation unit.

Following important things are available here,

  1. Actions to pre-processes IR before analysis can be done on the same,

     a. transforms the IR (Note that all transformations in the system
        can be found here, or invoked here: see preProcess())

     b. infers types of expressions and instructions

     c. caches information into data structures for faster access

  2. Provides API to fetch useful information from a translation unit.
"""
import functools
import logging
LOG = logging.getLogger(__name__)
LDB, LIN, LER, LWA = LOG.debug, LOG.info, LOG.error, LOG.warning

from typing import Dict, Set, Tuple, List, Callable, Any
from typing import Optional as Opt
import io

from span.util.util import LS, AS
import span.util.util as util

from span.ir.types import (
  FuncSig, Ptr, Void, Type, Info,
  VarNameT, FuncNameT, RecordNameT, TUnitNameT,
  FuncIdT, NodeIdT,
  RecordT, Struct, Union,
  ArrayT, ConstSizeArray, VarArray, IncompleteArray,
  Int, Float, Char, VarNameInfo,
  Int32, FLOAT16_TC, FLOAT128_TC, PTR_TC,
  NumericAny, IntegerAny, PointerAny, Float64, Int64, UInt64,
)

from span.ir.conv import (
  NAKED_PPMS_VAR_NAME, NAKED_STR_LIT_NAME,
  NULL_OBJ_NAME, NULL_OBJ_TYPE, NULL_OBJ_PTR_TYPE,
  PPMS_VAR_REGEX, DUMMY_VAR_NAME,
  START_END_BBIDS, COND_TMPVAR_GEN_STR,
  getSuffixes, setGlobalNodeIdBits, isFuncName, extractFuncName,
  getPrefixShortest, extractPureFuncName, isStringLitName, isTmpVar,
  simplifyName, isNormalTmpVar, isCondTmpVar, isGlobalName,
  GLOBAL_INITS_FUNC_NAME, GLOBAL_INITS_FUNC_ID,
  PPMS_VAR_TYPE,
  memAllocFunctions,
  FULL_PPMS_VAR_NAME, nameHasPpmsVar, nameHasNullVar, isPpmsVar,
  START_BB_ID, END_BB_ID, )

from span.ir.instr import (
  InstrIT, III, ExReadI, AssignI, CallI, CondI,
  CondReadI, LiveLocationsI, NopI, ReturnI, GotoI, UseI, UnDefValI,
  getFormalInstrStr, getCallExpr, getCalleeFuncName,
  FAILED_INSN_SIM, ASSIGN_INSTR_IC,
)

from span.ir.expr import (
  VarE, LitE, CallE, UnaryE, BinaryE,
  ExprET, ArrayE, MemberE, DerefE, CastE, SelectE,
  SimpleET, AddrOfE, LocationET, PpmsVarE, SizeOfE,
  getDefaultInitExpr, evalExpr, AllocE,
)

import span.ir.op as op
import span.ir.constructs as constructs
import span.ir.cfg as cfg


class Stats:
  def __init__(self, tunit: 'TranslationUnit', totalCfgNodes=0):
    self.tunit = tunit
    self.getNamesTimer = util.Timer("TUNIT:GetNames", start=False)

  def __str__(self):
    l1 = [f"{self.getNamesTimer}"]
    l1.append(f"TUnitSize: {util.getSize2(self.tunit)}")
    return "\n".join(l1)


class TranslationUnit:
  """A Translation Unit.

  It holds a complete '*.c' file's content,
  in its SPAN IR representation (converted from Clang AST).

  SPAN IR may undergo many iteration of changes here
  (see `TranslationUnit.preProcess`).
  """


  def __init__(self,
      name: TUnitNameT, # a unique name for this translation unit
      description: str, # human readable description
      allVars: Dict[VarNameT, Type], # all named variables and their types
      globalInits: Opt[List[InstrIT]], # list of global initializations
      allRecords: Dict[RecordNameT, RecordT], # all the structs/unions
      allFunctions: Dict[VarNameT, constructs.Func], # all the functions (decl & def)
      preProcess: bool = True,  # disables IR pre-processing (used in debugging)
  ) -> None:
    # analysis unit name and description
    self.stats = Stats(self)

    self.name = name  # used as key in hash maps
    self.description = description

    # whole of TU is contained in these three variables
    self.allVars = allVars
    self.allRecords = allRecords
    self.allFunctions: Dict[FuncNameT, constructs.Func] = allFunctions

    # all global inits are put into a special function
    self.allFunctions[GLOBAL_INITS_FUNC_NAME] = constructs.Func(
      name=GLOBAL_INITS_FUNC_NAME,
      instrSeq=globalInits if globalInits else [NopI()]
    )

    self.initialized: bool = False  # is set to True after preProcess()

    # Name information map (contains all possible named locations)
    self._nameInfoMap: Dict[VarNameT, VarNameInfo] = {}

    # new variables: variables introduced because of preProcess()
    self._newVarsMap: Dict[VarNameT, VarNameInfo] = {}

    # Set of all pseudo vars in this translation unit.
    # Note: pseudo vars represent memory allocation with a variable name.
    self._allPpmsVars: Set[VarNameT] = set()

    # stores the increasing counter for pseudo variables in the function
    # pseudo variables replace malloc/calloc calls as AddrOf(pseudoVar)
    self.ppmsCount = 0

    # The local pseudo variables in each function (TODO: remove?)
    self._localPpmsVars: Dict[FuncNameT, Set[VarNameT]] = {}

    # map (func, givenType) to vars of givenType accessible in the func (local+global)
    # (func, None) holds all types of vars accessible in the func (local+global)
    self._typeFuncEnvNamesMap: \
      Dict[Tuple[FuncNameT, Opt[Type]], Set[VarNameT]] = {}

    # only local variables
    self._typeFuncLocalNamesMap: \
      Dict[Tuple[FuncNameT, Opt[Type]], Set[VarNameT]] = {}

    # Set of all (actual) global vars in this translation unit.
    self._globalVarNames: Set[VarNameT] = set()

    # named locations whose address is taken
    self._addrTakenVarNames: Set[VarNameT] = set()

    # effective globals (actual globals + addr-taken set)
    self._globalsAndAddrTakenVarNames: Set[VarNameT] = set()

    # type based globals and address taken set categorization
    self._globalsAndAddrTakenSetMap: \
      Dict[Type, Set[VarNameT]] = dict()

    # function signature (funcsig) to function object list mapping
    self._funcSigToFuncListMap: \
      Dict[FuncSig, List[constructs.Func]] = {}

    # maps tmps assigned only once to the assigned expression
    self._tmpVarExprMap: Dict[VarNameT, ExprET] = {}

    # function id list: id is the index in the list
    self._indexedFuncList: List[constructs.Func] = []

    # used to allot unique name to string literals
    self._stringLitCount: int = 0

    if preProcess:
      self.preProcess()


  def preProcess(self):
    """Canonicalizes the translation unit before it can be used for analysis.
    ALL changes to SPAN IR before analysis are initiated from here.
    The relative positions of the transformations may be critical.
    """
    self.initialized = False

    self.logUsefulInfo()
    if util.LL1: LIN(f"PreProcessing_TUnit({self.name}): START.")

    # STEP 1: Legalize
    self.fillTheRecordTypes()  # MUST
    self.fillFuncParamTypes()  # MUST
    self.addThisTUnitRefToObjs()  # MUST
    self.inferAllInstrTypes()  # MUST
    self.convertNonDerefMemberE()  # MUST

    # STEP 2: Canonicalize
    self.canonicalize()  # MUST

    # STEP 3: Collect Information
    self.collectTmpVarAssignExprs()  # OPTIONAL
    self.collectAllVarNames()  # MUST
    if util.VV3: self.printNameInfoMap()  # OPTIONAL
    self.collectAddrTakenVars()  # MUST
    self.collectGlobalVarNames() # MUST

    # STEP 4: Misc ending steps
    # self.fillGlobalInitsFunction() # MUST (HERE)
    self.collectMiscStats() # MUST
    self.genCfgs()  # MUST
    self.assignFunctionIds() # MUST

    # STEP 5: Run Checks
    self.checkInvariants()  # IMPORTANT: checks the IR for basic correctness

    # STEP 6: Log Information
    self.logStats() # must be the last call (OPTIONAL)

    self.initialized = True
    if util.LL1: LOG.info(f"PreProcessing_TUnit({self.name}): END/DONE.")


  def collectGlobalVarNames(self):
    """Collects names whose naming format suggests a global scope.

    It doesn't collect addr-taken variables which have local naming formats.
    """
    names = set()

    for name, info in self._nameInfoMap.items():
      if isGlobalName(name):
        tmpNameSet = getSuffixes(None, name, info.type)
        names.update(tmpNameSet)

    self._globalVarNames = names


  def checkInvariants(self):
    """Checks the IR for basic correctness"""
    if not util.CC0:
      return

    for func in self.yieldFunctionsWithBody():
      func.checkInvariants()
      for insn in func.yieldInstrSeq():
        insn.checkInvariants()


  def assignFunctionIds(self):
    """Assigns a unique id to each function."""
    funcList = []

    # Handle global inits func first
    globalFunc = self.allFunctions[GLOBAL_INITS_FUNC_NAME]
    globalFunc.id = 0 # GLOBAL_INITS_FUNC_NAME has id 0
    funcList.append(globalFunc)

    # Initialize IDs for all other functions.
    funcId: FuncIdT = 1 # since 0 is occupied
    for func in self.yieldFunctions():
      func.id, funcId = funcId, funcId + 1
      funcList.append(func)

    self._indexedFuncList = funcList
    self.calcNodeSiteBits(funcList) # IMPORTANT


  def calcNodeSiteBits(self, funcList: List[constructs.Func]):
    assert funcList, f"{funcList}"
    totalFuncs = len(funcList)
    maxCfgNodes = self.maxCfgNodesInAFunction()
    setGlobalNodeIdBits(totalFuncs, maxCfgNodes)


  def maxCfgNodesInAFunction(self):
    """Returns the maximum cfg node count among all functions present."""
    maxNodes: int = 0
    for func in self.yieldFunctionsWithBody():
      nodesCount = func.cfg.getTotalNodes()
      maxNodes = nodesCount if nodesCount > maxNodes else maxNodes
    return maxNodes


  def collectAddrTakenVars(self):  # MUST
    """Collects the name of all the named locations whose
    address has been literally taken."""
    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        if isinstance(insn, AssignI):
          rhs = insn.rhs
          if isinstance(rhs, AddrOfE):
            # for statement: x = &z
            # Expr &(x->y) must have been preceded by x = &z.
            if isinstance(rhs.arg, VarE): # only addr of a var
              argName, argType = rhs.arg.name, rhs.arg.type
              self._addrTakenVarNames.update(getSuffixes(None, argName, argType))
          if isinstance(rhs, VarE) and isinstance(rhs.type, ArrayT):
            # x = y, where y is an array is equivalent to x = &y.
            rhsName, rhsType = rhs.name, rhs.type
            self._addrTakenVarNames.update(getSuffixes(None, rhsName, rhsType))

        callE = getCallExpr(insn)
        if callE:
          for arg in callE.args:
            if isinstance(arg, VarE) and isinstance(arg.type, ArrayT):
              argName, argType = arg.name, arg.type
              self._addrTakenVarNames.update(getSuffixes(None, argName, argType))

    self._addrTakenVarNames.add(NULL_OBJ_NAME)


  def convertNonDerefMemberE(self):
    """Converts member expression with non member deref to VarE"""

    def convertMemberExprToVarExpr(e: MemberE) -> ExprET:
      if e.hasDereference():
        return e
      else:
        varExpr = VarE(e.getFullName(), info=e.info)
        varExpr.type = e.type
        return varExpr

    exprPredicate = lambda e: isinstance(e, MemberE)

    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        self.findAndConvertExprInInstr(
          insn, exprPredicate, convertMemberExprToVarExpr)


  def findAndConvertExprInInstr(self,
      insn: InstrIT,
      exprPredicate: Callable,
      convertExpr: Callable,
  ) -> None:
    """It searches the given instruction for the expression
    using the given predicate and replaces it with the
    convertExpr function."""
    if isinstance(insn, AssignI):
      lhs = self.findAndConvertExpr(insn.lhs, exprPredicate, convertExpr)
      rhs = self.findAndConvertExpr(insn.rhs, exprPredicate, convertExpr)
      assert isinstance(lhs, LocationET), f"{lhs}"
      insn.lhs, insn.rhs = lhs, rhs
    elif isinstance(insn, CondI):
      arg = self.findAndConvertExpr(insn.arg, exprPredicate, convertExpr)
      assert isinstance(arg, SimpleET)
      insn.arg = arg
    elif isinstance(insn, CallI):
      arg = self.findAndConvertExpr(insn.arg, exprPredicate, convertExpr)
      assert isinstance(arg, CallE)
      insn.arg = arg
    elif isinstance(insn, ReturnI):
      if insn.arg is not None:
        arg = self.findAndConvertExpr(insn.arg, exprPredicate, convertExpr)
        assert isinstance(arg, SimpleET)
        insn.arg = arg
    elif isinstance(insn, (NopI, GotoI)):
      pass
    else:
      assert False, f"{insn}"


  def findAndConvertExpr(self,
      e: ExprET,
      exprPredicate: Callable,
      convertExpr: Callable
  ) -> ExprET:
    if exprPredicate(e):
      return convertExpr(e)
    if isinstance(e, SimpleET):
      return e

    if isinstance(e, BinaryE):
      arg1 = self.findAndConvertExpr(e.arg1, exprPredicate, convertExpr)
      arg2 = self.findAndConvertExpr(e.arg2, exprPredicate, convertExpr)
      assert isinstance(arg1, SimpleET) and isinstance(arg2, SimpleET), f"{e}"
      e.arg1, e.arg2 = arg1, arg2
    elif isinstance(e, DerefE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      assert isinstance(arg, VarE), f"{e}"
      e.arg = arg
    elif isinstance(e, AddrOfE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      assert isinstance(arg, LocationET), f"{e}"
      e.arg = arg
    elif isinstance(e, MemberE):
      of = self.findAndConvertExpr(e.of, exprPredicate, convertExpr)
      assert isinstance(of, VarE), f"{e}"
      e.of = of
    elif isinstance(e, CallE):
      callee = self.findAndConvertExpr(e.callee, exprPredicate, convertExpr)
      assert isinstance(callee, VarE), f"{e}: {callee}"
      e.callee = callee
      newArgs: List[SimpleET] = []
      for arg in e.args:
        newArg = self.findAndConvertExpr(arg, exprPredicate, convertExpr)
        assert isinstance(newArg, SimpleET), f"{e}: {arg}"
        newArgs.append(newArg)
      e.args = newArgs
    elif isinstance(e, UnaryE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      assert isinstance(arg, SimpleET), f"{e}"
      e.arg = arg
    elif isinstance(e, CastE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      e.arg = arg
    elif isinstance(e, ArrayE):
      of = self.findAndConvertExpr(e.of, exprPredicate, convertExpr)
      index = self.findAndConvertExpr(e.index, exprPredicate, convertExpr)
      assert isinstance(of, LocationET) and isinstance(index, SimpleET), f"{e}"
      e.of, e.index = of, index
    elif isinstance(e, SelectE):
      cond = self.findAndConvertExpr(e.cond, exprPredicate, convertExpr)
      arg1 = self.findAndConvertExpr(e.arg1, exprPredicate, convertExpr)
      arg2 = self.findAndConvertExpr(e.arg2, exprPredicate, convertExpr)
      assert isinstance(arg1, SimpleET) and isinstance(arg2, SimpleET),\
        f"{cond}, {arg1}, {arg2}"
      e.cond, e.arg1, e.arg2 = cond, arg1, arg2
    elif isinstance(e, AllocE):
      arg = self.findAndConvertExpr(e.arg, exprPredicate, convertExpr)
      e.arg = arg
    else:
      assert False, f"{e} {type(e)}"

    return e


  def logStats(self):
    """Logs some important stats of the translation unit.
    Should be called after all the various pre-processing is done."""
    if not LS: return

    ld = LOG.debug

    sio = io.StringIO()
    for vName in sorted(self.allVars.keys()):
      sio.write(f"    {vName!r}: {self.allVars[vName]},\n")
    ld("InputVariables(total %s):\n%s", len(self.allVars), sio.getvalue())

    sio = io.StringIO()
    for vName in sorted(self._nameInfoMap.keys()):
      sio.write(f"    {vName!r}: {self._nameInfoMap[vName]},\n")
    ld("ProcessedVariables(total %s):\n%s", len(self._nameInfoMap), sio.getvalue())

    sio = io.StringIO()
    for vName in sorted(self._newVarsMap.keys()):
      sio.write(f"    {vName!r}: {self._newVarsMap[vName]},\n")
    ld("NewVariables(total %s):\n%s", len(self._newVarsMap), sio.getvalue())

    sio = io.StringIO()
    for vName in sorted(self._addrTakenVarNames):
      sio.write(f"    {vName!r},\n")
    ld("AddrTakenVariables(total %s):\n%s", len(self._addrTakenVarNames), sio.getvalue())

    sio = io.StringIO()
    for vName in sorted(self._globalsAndAddrTakenVarNames):
      sio.write(f"    {vName!r},\n")
    ld("GlobalsAndAddrTakenVariables(total %s):\n%s",
       len(self._globalsAndAddrTakenVarNames), sio.getvalue())

    sio = io.StringIO()
    for rName in sorted(self.allRecords.keys()):
      sio.write(f"    {rName!r},\n")
    ld("AllRecords(Structs/Unions)(total %s):\n%s",
       len(self.allRecords), sio.getvalue())

    sio = io.StringIO()
    for fName in sorted(self.allFunctions.keys()):
      sio.write(f"    {fName!r},\n")
    ld("AllFunctions(total %s):\n%s",
       len(self.allFunctions), sio.getvalue())


  def canBeGloballyAccessed(self, name: str):
    """Returns True (over-approximated) if a name can be
    potentially accessed globally (either directly or by pointer deref)"""
    return name in self._globalsAndAddrTakenVarNames


  def getPossiblePointees(self,
      t: Opt[Ptr] = None,
      cache: bool = True
  ) -> Set[VarNameT]:
    """Returns the possible pointees a type 't' var may point to."""
    if t is None: return self._globalsAndAddrTakenVarNames

    pointeeType = t.getPointeeType()
    if pointeeType in self._globalsAndAddrTakenSetMap:
      return self._globalsAndAddrTakenSetMap[t]

    names = []
    for varName in self._globalsAndAddrTakenVarNames:
      if isFuncName(varName):
        nameType = self.allFunctions[varName].sig
      else:
        nameType = self._nameInfoMap[varName].type
      if nameType == pointeeType:
        names.append(varName)
      elif isinstance(nameType, ArrayT) \
        and nameType.getElementTypeFinal() == pointeeType:
        names.append(varName)

    namesSet = set(names)
    if cache:
      self._globalsAndAddrTakenSetMap[pointeeType] = namesSet

    return namesSet


  def getNode(self,
      funcName: FuncNameT,
      nid: NodeIdT
  ) -> Opt[cfg.CfgNode]:
    """Returns the node object."""
    func = self.getFuncObj(funcName)
    nodeMap = func.cfg.nodeMap
    if nid in nodeMap:
      return nodeMap[nid]
    return None


  def getTheFunctionOfVar(self,
      varName: VarNameT
  ) -> Opt[constructs.Func]:
    """Returns the constructs.Func object the varName belongs to.
    For global variables it returns None."""
    funcName = extractFuncName(varName)
    func: Opt[constructs.Func] = None
    if funcName:
      if funcName in self.allFunctions:
        func = self.allFunctions[funcName]
    return func


  def collectAllVarNames(self):
    """It extracts all the object names possible in
    a translation unit and caches the result."""
    for varName, objType in self.allVars.items():
      self.addVarNames(varName, objType)
    assert self.allVars.keys() <= self._nameInfoMap.keys(),\
           f"{self.allVars.keys()} is not <= {self._nameInfoMap.keys()}"


  def addVarNames(self,
      varName: VarNameT,
      objType: Type,
      new: bool = False, # True if variable is added by SPAN
  ) -> None:
    """Add the varName into `_nameInfoMap` along
    with all its sub-names if its an array (of records) or a record."""
    nameInfos = objType.getNamesOfType(None, varName)
    for nameInfo in nameInfos:
      self._nameInfoMap[nameInfo.name] = nameInfo   # cache the results
      if new:
        nameInfo.bySpan = True
        self._newVarsMap[nameInfo.name] = nameInfo  # record a new variable


  def printNameInfoMap(self):
    """A convenience function to print names in
    self._nameInfoMap for debugging."""
    print("The names in the IR:")
    for name in sorted(self._nameInfoMap.keys()):
      print(f"  {name}:", self._nameInfoMap[name])


  def replaceZeroWithNullPtr(self):
    """Replace statements assigning Zero to pointers,
    with a special NULL_OBJ."""
    # Add the special null object.
    self.addVarNames(NULL_OBJ_NAME, NULL_OBJ_TYPE, True)

    for func in self.yieldFunctionsWithBody():
      for bb in func.basicBlocks.values():
        for i in range(len(bb)):
          insn = bb[i]
          if isinstance(insn, AssignI) and insn.type.isPointer():
            rhs = insn.rhs
            if isinstance(rhs, CastE):
              arg = rhs.arg
              if isinstance(arg, LitE):
                if arg.type.isNumeric() and arg.val == 0:
                  rhs = AddrOfE(VarE(NULL_OBJ_NAME, rhs.info), rhs.info)
                  insn.rhs, rhs.type = rhs, NULL_OBJ_PTR_TYPE
            elif isinstance(rhs, LitE):
              if rhs.type.isNumeric() and rhs.val == 0:
                rhs = AddrOfE(VarE(NULL_OBJ_NAME, rhs.info), rhs.info)
                insn.rhs, rhs.type = rhs, NULL_OBJ_PTR_TYPE


  def addThisTUnitRefToObjs(self):  # IMPORTANT (MUST)
    """Sets `span.ir.constructs.Func.tUnit` to this TUnit instance.

    It cannot be done in `span.ir.constructs.Func`,

      1. due to lack of info in the `span.ir.constructs` module.
      2. to avoid circular dependency btw the two modules.
    """
    for func in self.yieldFunctions():
      # Point func.tUnit to this TUnit object
      func.tUnit = self


  def genCfgs(self) -> None:
    """Generates CFG for each function with body in the translation unit.

    Fills `span.ir.constructs.Func`'s `span.ir.constructs.Func.cfg` field
    to contain a proper CFG graph.

    CFGs are constructed once the IR is in canonical form and optimized enough.
    """
    for func in self.yieldFunctionsWithBody():
      func.cfg = cfg.Cfg(func.name, func.basicBlocks, func.bbEdges)


  def yieldFunctions(self):
    """Yields all the functions (with or without body) in the TUnit."""
    for func in sorted(self.allFunctions.values(), key=lambda x: x.name):
      yield func


  def yieldFunctionsWithBody(self):
    """Yields all the functions in the TUnit with body."""
    for func in self.yieldFunctions():
      if func.hasBody():
        yield func


  def yieldFunctionsWithoutBody(self):
    """Yields all the functions in the TUnit without body."""
    for func in self.yieldFunctions():
      if not func.hasBody():
        yield func


  def yieldInstructions(self):
    """Yields all the `span.ir.instr.InstrIT` in the IR in no specific order."""
    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        yield insn


  def yieldFunctionsForAnalysis(self):
    """Yields all the functions in the TUnit with body
    that can be analyzed.

    Uses the predicate `span.ir.constructs.Func.canBeAnalyzed`.
    """
    for func in self.yieldFunctions():
      if func.canBeAnalyzed():
        yield func


  def yieldRecords(self):
    """Yields all the `span.ir.types.RecordT` in the TUnit. """
    for record in sorted(self.allRecords.values(), key=lambda x: x.name):
      if isinstance(record, (Union, Struct)):
        yield record


  def yieldStructs(self):
    """Yields all the `span.ir.types.Struct` in the TUnit. """
    for record in self.yieldRecords():
      if isinstance(record, Struct):
        yield record


  def yieldUnions(self):
    """Yields all the `span.ir.types.Union` in the TUnit. """
    for record in self.yieldRecords():
      if isinstance(record, Union):
        yield record


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
        try:
          self.inferTypeOfInstr(insn)
        except Exception as e:
          raise Exception(f"{insn}: {e}")


  ################################################
  # BOUND START: Type_Inference
  ################################################

  def inferTypeOfVal(self, val) -> Type:
    """Returns the type for the given value.
    In case of a function, it returns its signature.
    """

    if isinstance(val, str):
      if val in self._nameInfoMap:  # IMPORTANT (most likely case)
        return self._nameInfoMap[val].type

      if nameHasPpmsVar(val) or nameHasNullVar(val):
        return Void

      if val in self.allFunctions:
        return self.allFunctions[val].sig # type signature of func

      if val in self.allVars:  # IMPORTANT for initial use in preProcess()
        return self.allVars[val]

    elif type(val) == int:
      return Int

    elif type(val) == float:
      return Float

    raise ValueError(f"{val}, {self._nameInfoMap}")


  def getMemberType(self, fullMemberName: str) -> Type:
    """Takes names like x.y.z and returns the type"""
    names = fullMemberName.split(".")
    currType = self.inferTypeOfVal(names[0])  # could be RecordT, ArrayT or Ptr
    # get the record type
    if isinstance(currType, ArrayT):
      currType = currType.getElementTypeFinal()
    while not isinstance(currType, RecordT):
      if isinstance(currType, Ptr):
        currType = currType.getPointeeType()

    count = len(names)
    for i in range(1, count):
      assert isinstance(currType, RecordT)
      currType = currType.getMemberType(names[i])
      if i + 1 != count: # hence more members to come
        # get the record type
        if isinstance(currType, ArrayT):
          currType = currType.getElementType()
        if isinstance(currType, Ptr):
          currType = currType.getPointeeTypeFinal()
    return currType


  def processStringLiteral(self, e: LitE) -> ConstSizeArray:
    """Takes a string literal and gives it a variable like name
    and a type of ConstSizeArray of char."""

    assert isinstance(e.val, str)
    if e.name:
      eType = self._nameInfoMap[e.name].type
      assert isinstance(eType, ConstSizeArray), f"{e}, {e.name}, {eType}"
      return eType

    # since "XXX" is suffixed to every string literal
    # "XXX" is suffixed to a string literal since some
    # strings end with '"' and '""""' is an invalid end of string in python
    e.val = e.val[:-3]  # type: ignore
    eType = ConstSizeArray(of=Char, size=len(e.val))

    if not e.name:
      self._stringLitCount += 1
      e.name = NAKED_STR_LIT_NAME.format(count=self._stringLitCount)
      self._nameInfoMap[e.name] = VarNameInfo(e.name, eType, True, True)

    return eType


  def inferTypeOfExpr(self, e: ExprET) -> Type:
    """Infer expr type, store the type info
    in the object and return the type."""
    eType = e.type

    if not eType.isVoid(): return eType # type already set

    if isinstance(e, VarE):
      # for some pseduo vars like '1p.x', e.type is already set to avoid errors
      eType = e.type if e.type != Void else self.inferTypeOfVal(e.name)

    elif isinstance(e, LitE):
      if type(e.val) == str:
        eType = self.processStringLiteral(e)
      else:
        eType = self.inferTypeOfVal(e.val)

    elif isinstance(e, CastE):
      self.inferTypeOfExpr(e.arg)
      eType = e.to  # type its casted to

    elif isinstance(e, UnaryE):
      opCode = e.opr.opCode
      argType = self.inferTypeOfExpr(e.arg)
      # opCode will never be UO_DEREF_OC
      if opCode == op.UO_LNOT_OC:  # logical not
        eType = Int32
      else:
        eType = argType  # for all other unary ops

    elif isinstance(e, BinaryE):
      opCode = e.opr.opCode
      if op.BO_NUM_START_OC <= opCode <= op.BO_NUM_END_OC:
        itype1 = self.inferTypeOfExpr(e.arg1)
        itype2 = self.inferTypeOfExpr(e.arg2)
        # FIXME: conversion rules are too broad
        if itype1.isFloat() or itype2.isFloat():
          eType = Float64   # an over-approximation
        elif itype1.isUnsigned() or itype2.isUnsigned():
          eType = UInt64    # an over-approximation
        elif itype1.isPointer():
          eType = itype1
        elif itype2.isPointer():
          eType = itype2
        else:
          eType = itype1

      elif op.BO_LT_OC <= opCode <= op.BO_GT_OC:
        _ = self.inferTypeOfExpr(e.arg1)
        _ = self.inferTypeOfExpr(e.arg2)
        eType = Int32

    elif isinstance(e, ArrayE):
      subEType = self.inferTypeOfExpr(e.of)
      if isinstance(subEType, Ptr):
        eType = subEType.getPointeeType()
      elif isinstance(subEType, ArrayT):
        eType = subEType.of

    elif isinstance(e, DerefE):
      argType = self.inferTypeOfExpr(e.arg)
      if isinstance(argType, Ptr):
        eType = argType.getPointeeType()
      elif isinstance(argType, ArrayT):
        eType = argType.of
      elif isinstance(argType, FuncSig):
        eType = argType # remains the same (weird C semantics)
      else:
        raise ValueError(f"{e}, {type(e)}, {argType}")

    elif isinstance(e, MemberE):
      fieldName = e.name
      of = e.of
      ofType = self.inferTypeOfExpr(of)
      if isinstance(ofType, Ptr):
        ofType = ofType.getPointeeType()
      elif isinstance(ofType, ArrayT):
        ofType = ofType.getElementTypeFinal()
      assert isinstance(ofType, RecordT)
      eType = ofType.getMemberType(fieldName)

    elif isinstance(e, SelectE):
      self.inferTypeOfExpr(e.cond)
      self.inferTypeOfExpr(e.arg1)
      eType2 = self.inferTypeOfExpr(e.arg2)
      eType = eType2  # type of 1 and 2 should be the same.

    elif isinstance(e, AllocE):
      eType = Ptr(to=Void)

    elif isinstance(e, AddrOfE):
      eType = Ptr(to=self.inferTypeOfExpr(e.arg))

    elif isinstance(e, CallE):
      calleeType = self.inferTypeOfExpr(e.callee)
      if isinstance(calleeType, FuncSig):
        eType = calleeType.returnType
      elif isinstance(calleeType, Ptr):
        funcSig = calleeType.getPointeeType()
        assert isinstance(funcSig, FuncSig), f"{funcSig}"
        eType = funcSig.returnType
      for arg in e.args:
        _ = self.inferTypeOfExpr(arg)

    else:
      # assert False, f"Unkown expression: {e} {type(e)}"
      if LS: LOG.error("Unknown_Expr_For_TypeInference: %s.", e)

    e.type = eType
    return eType


  def inferTypeOfInstr(self,
      insn: InstrIT,
  ) -> Type:
    """Infer instruction type from the type of the expressions.
    After IR preprocessing, any newly created
    instruction should have its type inferred
    before any other work is done on it.
    """
    iType = insn.type

    if not iType.isVoid(): return iType # type already set

    if isinstance(insn, AssignI):
      t1 = self.inferTypeOfExpr(insn.lhs)
      t2 = self.inferTypeOfExpr(insn.rhs)
      iType = t1
      if AS and t1 != t2:
        LOG.debug(f"Lhs and Rhs types differ: {insn}, lhstype = {t1}, rhstype = {t2}.")

    elif isinstance(insn, UseI):
      for var in insn.vars:
        iType = self.inferTypeOfVal(var)

    elif isinstance(insn, LiveLocationsI):
      pass

    elif isinstance(insn, CondReadI):
      iType = self.inferTypeOfVal(insn.lhs)

    elif isinstance(insn, UnDefValI):
      iType = self.inferTypeOfVal(insn.lhsName)

    elif isinstance(insn, CondI):
      _ = self.inferTypeOfExpr(insn.arg)

    elif isinstance(insn, ReturnI):
      if insn.arg is not None:
        iType = self.inferTypeOfExpr(insn.arg)

    elif isinstance(insn, CallI):
      iType = self.inferTypeOfExpr(insn.arg)

    elif isinstance(insn, NopI):
      pass  # i.e. types.Void

    elif isinstance(insn, ExReadI):
      pass  # i.e. types.Void

    elif isinstance(insn, III):
      for ins in insn.yieldInstructions():
        iType = self.inferTypeOfInstr(ins)

    else:
      if util.LL1: LOG.error("Unknown_Instr_For_TypeInference: %s.", insn)

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

    This is an important step. While conversion from the Clang AST,
    many places simply refer to the structure by its unique name only.
    This makes conversion (serialization) easy.
    Moreover, if structures are self-referential
    then the name based self-reference is unavoidable.

    Once the python object for the record type is made, then these
    name based references are replaced by the actual record obj reference.
    """
    # STEP 1. Complete/Correct all the record types.
    for record in self.yieldRecords():
      newFields = []
      for fName, fType in record.members:
        newType = self.findAndFillTheRecordTypes(fType)
        newFields.append((fName, newType))
      record.members = newFields

    # STEP 2. Complete/Correct all the variable types.
    for varName in self.allVars.keys():
      varType = self.allVars[varName]
      completedVarType = self.findAndFillTheRecordTypes(varType)
      self.allVars[varName] = completedVarType


  def findAndFillTheRecordTypes(self, varType: Type):
    """Recursively finds the record type and replaces them with
    the reference to the complete definition in self.allRecords."""
    if isinstance(varType, (Struct, Union)):
      return self.allRecords[varType.name]

    elif isinstance(varType, Ptr):
      ptrTo = self.findAndFillTheRecordTypes(varType.getPointeeTypeFinal())
      return Ptr(to=ptrTo, indlev=varType.indlev)

    elif isinstance(varType, ArrayT):
      arrayOf = self.findAndFillTheRecordTypes(varType.of)
      if isinstance(varType, ConstSizeArray):
        return ConstSizeArray(of=arrayOf, size=varType.size)
      elif isinstance(varType, VarArray):
        return VarArray(of=arrayOf)
      elif isinstance(varType, IncompleteArray):
        return IncompleteArray(of=arrayOf)

    elif isinstance(varType, FuncSig):
      retType = self.findAndFillTheRecordTypes(varType.returnType)
      paramTypes = []
      for paramType in varType.paramTypes:
        paramTypes.append(self.findAndFillTheRecordTypes(paramType))
      return FuncSig(retType, paramTypes, varType.variadic)

    return varType  # by default return the same type


  def canonicalize(self) -> None:
    """Transforms SPAN IR to a canonical form."""
    self.replaceMemAllocations()
    # self.replaceZeroWithNullPtr()  # FIXME: should be used?

    self.removeNopInsns()  # (OPTIONAL)
    for func in self.yieldFunctionsWithBody():
      self.evaluateConstantExprs(func)  # (MUST)
      self.removeRedundantTypeCasts(func)  # (MUST)
      self.evaluateConstIfStmts(func)  # (MUST)
      self.removeNopBbs(func)  # (OPTIONAL)
      self.removeUnreachableBbs(func)  # (OPTIONAL)

    self.canonicalizeExpressions()  # MUST


  def fillGlobalInitsFunction(self):
    """Fill the special global inits function.

    It adds the initializations of uninitialized global variables.
    """

    globalInitsFunc = self.allFunctions[GLOBAL_INITS_FUNC_NAME]
    globalVarNamesInitialized = self.collectGlobalVarNamesInitialized()
    globalVarNames: Set[VarNameT] = self._globalVarNames

    newInsns: List[AssignI] = []

    nonInitializedGlobals = globalVarNames - globalVarNamesInitialized
    for varName in sorted(nonInitializedGlobals):
      if isStringLitName(varName):
        continue #avoid string literals
      objType = self.inferTypeOfVal(varName)
      defaultInitExpr = getDefaultInitExpr(objType)
      if defaultInitExpr is not None:
        insn = AssignI(VarE(name=varName), defaultInitExpr)
        self.inferTypeOfInstr(insn)
        newInsns.append(insn)

    allInsns = []
    allInsns.extend(newInsns)
    allInsns.extend(globalInitsFunc.instrSeq)

    globalInitsFunc.setNewInstructionSequence(allInsns)


  def collectMiscStats(self):
    self._globalsAndAddrTakenVarNames |= self._globalVarNames
    self._globalsAndAddrTakenVarNames |= self._addrTakenVarNames
    self._globalsAndAddrTakenVarNames |= self._allPpmsVars


  def collectGlobalVarNamesInitialized(self) -> Set[VarNameT]:
    """Extracts names of globals initialized
    in the global inits function."""
    func: constructs.Func = self.allFunctions[GLOBAL_INITS_FUNC_NAME]
    varNames: Set[VarNameT] = set()

    for insn in func.yieldInstrSeq():
      if isinstance(insn, NopI): continue
      assert isinstance(insn, AssignI)
      # assert isinstance(insn.lhs, VarE), f"{insn.lhs}"
      if isinstance(insn.lhs, VarE):
        varNames.add(insn.lhs.name)
      elif isinstance(insn.lhs, ArrayE):
        varNames.add(insn.lhs.getFullName())
      elif isinstance(insn.lhs, MemberE):
        pass # TODO: see what to do?
      else:
        raise ValueError(f"{insn}")

    return varNames


  def getGlobalInitsFunction(self) -> constructs.Func:
    return self.allFunctions[GLOBAL_INITS_FUNC_NAME]


  def removeRedundantTypeCasts(self, func: constructs.Func) -> None:
    """Remove redundant casts.

    Following types of casts are removed:

    * `(types.Ptr(types.Int8, 1)) "string literal"`
    * FIXME: identify and add more cases
    """
    assignInstrCode = ASSIGN_INSTR_IC
    for bbId, bb in func.yieldBasicBlocks():
      for index in range(len(bb)):
        if bb[index].instrCode == assignInstrCode:
          insn: AssignI = bb[index]
          rhs = insn.rhs
          newRhs = rhs
          if isinstance(rhs, CastE):
            arg = rhs.arg
            if isinstance(arg, LitE):
              if arg.isString(): # i.e. cast of a string literal
                newRhs = arg
          if newRhs is not rhs:
            insn.rhs = newRhs
            self.inferTypeOfInstr(insn)


  def evaluateConstantExprs(self, func: constructs.Func) -> None:
    """Reduces/solves all binary/unary constant expressions."""
    assignInstrCode = ASSIGN_INSTR_IC
    for bbId, bb in func.yieldBasicBlocks():
      for index in range(len(bb)):
        if bb[index].instrCode == assignInstrCode:
          insn: AssignI = bb[index]
          rhs = evalExpr(insn.rhs)
          if rhs is not insn.rhs:
            insn.rhs = rhs
            self.inferTypeOfInstr(insn)


  def removeNopInsns(self) -> None:
    """Removes NopI() from bbs with more than one instruction."""
    for func in self.yieldFunctionsWithBody():
      bbIds = func.basicBlocks.keys()

      for bbId in bbIds:
        bb = func.basicBlocks[bbId]
        newBb = [insn for insn in bb if not isinstance(insn, NopI)]

        if bbId == START_BB_ID:
          newBb.insert(0, NopI())  # IMPORTANT

        if len(newBb) == 0:
          newBb.append(NopI())  # let one NopI be (such BBs are removed later)

        func.basicBlocks[bbId] = newBb


  def removeUnreachableBbs(self, func: constructs.Func) -> None:
    """Removes BBs that are not reachable from StartBB."""
    allBbIds = func.basicBlocks.keys()

    # collect all dest bbIds
    destBbIds = {START_BB_ID}  # start bbId is always reachable
    for bbEdge in func.bbEdges:
      destBbIds.add(bbEdge[1])
    unreachableBbIds = allBbIds - destBbIds

    # remove all edges going out of unreachable bbs
    takenEdges = []
    for bbEdge in func.bbEdges:
      if bbEdge[0] in unreachableBbIds:
        continue
      takenEdges.append(bbEdge)
    func.bbEdges = takenEdges

    # remove unreachableBbIds one by one
    for bbId in unreachableBbIds:
      del func.basicBlocks[bbId]

    if unreachableBbIds:
      # go recursive, since there could be new unreachable bb ids
      return self.removeUnreachableBbs(func)


  def genCondTmpVar(self, func: constructs.Func, t: Type) -> VarE:
    """Generates a new cond tmp var and adds it to the variables map."""
    number: int = 90
    fName = extractPureFuncName(func.name)

    while True:
      name = f"v:{fName}:" + COND_TMPVAR_GEN_STR.format(number=number)
      if name not in self.allVars:
        break
      number += 1

    # if here the name is new and good to go
    self.addVarNames(name, t, True)
    e = VarE(name)
    e.type = t
    return e


  def evaluateConstIfStmts(self, func: constructs.Func) -> None:
    """Changes if stmt on a const value, to use a tmp variable.
    It may lead to some unreachable BBs."""

    for bbId, bbInsns in func.basicBlocks.items():
      if not bbInsns: continue  # if bb is blank
      ifInsn = bbInsns[-1] # conditional must be the last instruction
      if isinstance(ifInsn, CondI):
        arg = ifInsn.arg
        if isinstance(arg, LitE):
          if type(arg.val) == str:
            t: Type = Ptr(to=Char)
          else:
            t = self.inferTypeOfVal(arg.val)

          tmpVarExpr = self.genCondTmpVar(func, t)
          tmpVarExpr.info = arg.info
          tmpAssignI = AssignI(tmpVarExpr, arg, info=arg.info)
          tmpAssignI.type = t

          bbInsns.insert(-1, tmpAssignI)
          ifInsn.arg = tmpVarExpr


  def removeNopBbs(self, func: constructs.Func) -> None:
    """Remove BBs that only have NopI(). Except START and END."""

    for bbId in func.basicBlocks.keys():
      if bbId in START_END_BBIDS:
        continue  # leave START and END BBs as it is.

      onlyNop = True
      for insn in func.basicBlocks[bbId]:
        if isinstance(insn, NopI):
          continue
        onlyNop = False

      if onlyNop:
        # then remove this bb and related edges
        retainedEdges, predEdges, succEdges = [], [], []
        for bbEdge in func.bbEdges:
          if bbEdge[0] == bbId:
            succEdges.append(bbEdge)  # ONLY ONE EDGE
          elif bbEdge[1] == bbId:
            predEdges.append(bbEdge)
          else:
            retainedEdges.append(bbEdge)

        assert len(succEdges) == 1, f"{succEdges}"

        for predEdge in predEdges:
          newEdge = (predEdge[0], succEdges[0][1], predEdge[2])
          retainedEdges.append(newEdge)
        func.bbEdges = retainedEdges


  def replaceMemAllocations(self) -> None:
    """Replace calloc(), malloc() with addr-taken of Ppms variables.
    """
    for func in self.yieldFunctionsWithBody():
      for bb in func.basicBlocks.values():
        for i in range(len(bb)):
          insn = bb[i]
          # SPAN IR separates a call and its cast into two statements.
          if isinstance(insn, AssignI) and isinstance(insn.rhs, CallE):
            rhs = insn.rhs
            if self.isMemoryAllocationCall(rhs):
              ppmsVarE = self.addNewPpmsVar(func.name, rhs.info, insn)
              # replace rhs: malloc() with `&ppmsVarE`
              insn.rhs = AddrOfE(ppmsVarE, info=rhs.info)


#   def replaceMemAllocations(self) -> None:
#     """Replace calloc(), malloc() with pseudo variables of type array.
#     Should be called when types for expressions have been inferred.
#     """
#     for func in self.yieldFunctionsWithBody():
#       for bb in func.basicBlocks.values():
#         for i in range(len(bb) - 1):
#           insn = bb[i]
#           # SPAN IR separates a call and its cast into two statements.
#           if isinstance(insn, AssignI) and isinstance(insn.rhs, CallE):
#             if self.isMemoryAllocationCall(insn.rhs):
#               memAllocInsn: AssignI = insn
#               if isTmpVar(memAllocInsn.lhs.name):  # stored in a void* temporary
#                 # then next insn must be a cast and store to a non tmp variable
#                 castInstr = bb[i + 1]
#                 newInstr = self.conditionallyAddPseudoVar(func.name, castInstr, memAllocInsn)
#                 if newInstr is not None:  # hence pseudo var has been added
#                   bb[i] = NopI()  # i.e. remove current instruction
#                   bb[i + 1] = newInstr
#               else:
#                 newInstr = self.conditionallyAddPseudoVar(func.name, memAllocInsn)
#                 if newInstr:
#                   bb[i] = newInstr
#
#
#   def conditionallyAddPseudoVar(self,
#       funcName: FuncNameT,
#       insn: AssignI,
#       prevInsn: AssignI = None,
#   ) -> Opt[InstrIT]:
#     """Modifies rhs to address of a pseudo var with the correct type.
#     Only two instruction forms should be in insn:
#       <ptr_var> = (<type>*) <tmp_var>; // cast insn
#       <ptr_var> = <malloc/calloc>(...); // memory alloc insn
#     """
#     lhs = insn.lhs
#     assert isinstance(lhs, VarE), f"{lhs}"
#     # if isTmpVar(lhs.name): return None
#
#     rhs = insn.rhs
#     if isinstance(rhs, CastE):
#       if not isTmpVar(rhs.arg.name):
#         return None
#       # if here, assume that the tmp var is assigned a heap location
#
#     if isinstance(rhs, (CastE, CallE)):
#       # assume it is malloc/calloc (it should be) if it is a CallE
#       lhsType = lhs.type
#       assert isinstance(lhsType, Ptr), f"{lhsType}"
#       pVar = self.genPseudoVar(funcName, rhs.info,
#                                lhsType.getPointeeType(), insn, prevInsn)
#       newInsn = AssignI(lhs, AddrOfE(pVar, rhs.info))
#       self.inferTypeOfInstr(newInsn)
#       if util.LL1: LDB(f"NewPseudoVar(Instr): {newInsn}, {pVar}, {funcName},"
#                        f" {pVar.insns}, {pVar.info}")
#       return newInsn
#
#     return None


  def addNewPpmsVar(self,
      funcName: FuncNameT,
      info: Opt[Info],
      insn: AssignI,
  ) -> PpmsVarE:
    self.ppmsCount += 1

    nakedPpmsVarName = NAKED_PPMS_VAR_NAME.format(count=self.ppmsCount)
    pureFuncName = extractPureFuncName(funcName)
    ppmsVarName = FULL_PPMS_VAR_NAME.format(
      fName=pureFuncName, name=nakedPpmsVarName)

    self._allPpmsVars.add(ppmsVarName)

    pvType = PPMS_VAR_TYPE
    if util.LL1: LDB(f"NewPpmsVar(Var): {ppmsVarName}, {pvType},"
                     f" (Insn: {insn})")
    self.addVarNames(ppmsVarName, pvType, True)

    pVarE = PpmsVarE(ppmsVarName, info=info, insn=insn)
    pVarE.type = pvType

    return pVarE


  def getMemAllocSizeExpr(self, insn: AssignI) -> ExprET:
    """Returns the expression deciding the size of memory allocated."""
    callE = getCallExpr(insn)
    assert callE, f"{insn}"
    calleeName = callE.callee.name

    if calleeName == "f:malloc":
      sizeExpr: ExprET = callE.args[0]  # the one and only argument is the size expr
    elif calleeName == "f:calloc":
      sizeExpr = BinaryE(callE.args[0], op.BO_MUL,
                              callE.args[1], info=callE.args[0].info)
      self.inferTypeOfExpr(sizeExpr)
    else:
      raise ValueError()

    return sizeExpr


  def getMemAllocSizeExprValue(self, sizeExpr: ExprET) -> Opt[int]:
    if isinstance(sizeExpr, LitE):
      assert isinstance(sizeExpr.val, int)
      return sizeExpr.val
    return None


  def isMemoryAllocationCall(self,
      callExpr: CallE,
  ) -> bool:
    memAllocCall = False
    calleeName = callExpr.callee.name
    if calleeName in memAllocFunctions:
      func: constructs.Func = self.allFunctions[calleeName]
      if func.sig == memAllocFunctions[calleeName]:
        memAllocCall = True

    return memAllocCall


  def getTmpVarExpr(self,
      vName: VarNameT,
  ) -> Opt[ExprET]:
    """Returns the expression the given tmp var is assigned.
    It only tracks some tmp vars, e.g. ones like 3t, 1if, 2if ...
    The idea is to map the tmp vars that are assigned only once.
    """
    if vName in self._tmpVarExprMap:
      return self._tmpVarExprMap[vName]
    return None  # None if tmp var is not tracked


  def collectTmpVarAssignExprs(self) -> None:
    """Extract temporary variables that are assigned only once,
    and the unique expressions they hold the value of.

    It caches the result in a global map.
    """

    tmpExprMap = self._tmpVarExprMap

    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        if insn.instrCode == ASSIGN_INSTR_IC:
          assert isinstance(insn, AssignI), f"{insn}"
          if isinstance(insn.lhs, VarE):
            name = insn.lhs.name
            if isNormalTmpVar(name) or isCondTmpVar(name):
              tmpExprMap[name] = insn.rhs


  def getNameInfo(self,
      name: VarNameT
  ) -> Opt[VarNameInfo]:
    """Returns the NameTypeInfo of a name or None if there is none"""
    assert name in self._nameInfoMap, f"{name}, {self._nameInfoMap}"
    return self._nameInfoMap[name]


  def nameHasArray(self,
      name: VarNameT
  ) -> Opt[bool]:
    """Returns true if the name contains array access."""
    nim = self._nameInfoMap
    if name in nim:
      return nim[name].hasArray
    # return Void  #default #FIXME

    varType, shortestPrefix = None, getPrefixShortest(name)
    if shortestPrefix in nim:
      varType = nim[shortestPrefix]
      return varType.hasArray
    elif shortestPrefix == NULL_OBJ_NAME: #FIXME: why is this needed?
      return True
    raise ValueError(f"{name}, {shortestPrefix}, {varType}, {nim}")


  def getNames(self,
      givenType: Type
  ) -> Set[VarNameT]:
    """Gets names of givenType in the whole tUnit (irrespective of scope)."""
    names = set()
    for objInfo in self._nameInfoMap.values():
      objType = objInfo.type
      if givenType == objType:
        names.add(objInfo.name)
      elif isinstance(objType, ArrayT):
        if givenType == objType.getElementTypeFinal():
          names.add(objInfo.name)
    return names


  def _getGlobalVarNames(self) -> Set[VarNameT]:
    """Returns names whose naming format suggests a global scope.

    It doesn't return addr-taken variables which have local naming formats.
    """
    names = set()
    for name, info in self._nameInfoMap.items():
      if isGlobalName(name):
        tmpNameSet = getSuffixes(None, name, info.type)
        names.update(tmpNameSet)
    return names


  def getNamesGlobal(self,
      givenType: Opt[Type] = None,
      cacheResult: bool = True,  # set to False in a very special case
      numeric: bool = False,
      integer: bool = False,
      pointer: bool = False,
  ) -> Set[VarNameT]:
    """Returns list of global variable names.
    Without givenType it returns all the variables accessible.
    Note: this method handles function signatures also.
    """
    self.stats.getNamesTimer.start()
    key = givenType
    if numeric: key = NumericAny
    if integer: key = IntegerAny
    if pointer: key = PointerAny

    if key in self._globalsAndAddrTakenSetMap:
      self.stats.getNamesTimer.stop()
      return self._globalsAndAddrTakenSetMap[key]

    names: Set[VarNameT] = set()
    if isinstance(givenType, FuncSig):
      names.update(func.name for func in self.getFunctionsOfGivenSignature(givenType))
    else:
      for objName in self._globalsAndAddrTakenVarNames:
        objType = self.inferTypeOfVal(objName)
        nameInfos = objType.getNamesOfType(givenType, objName)
        for nameInfo in nameInfos:
          names.add(nameInfo.name)

    if numeric: names = self.filterNamesNumeric(names)
    if integer: names = self.filterNamesInteger(names)
    if pointer: names = self.filterNamesPointer(names)

    if cacheResult:
      self._globalsAndAddrTakenSetMap[key] = names  # cache the result

    self.stats.getNamesTimer.stop()
    return names


  def getNamesLocalStrict(self,
      func: constructs.Func,
      givenType: Type = None,
      cacheResult: bool = True,  # set to False in a very special case
      numeric: bool = False,
      integer: bool = False,
      pointer: bool = False,
  ) -> Set[VarNameT]:
    """Returns names which are strictly local.
    Since some local names are global (addr-taken), so they are removed.
    """
    names = self.getNamesLocal(func, givenType, cacheResult,
                               numeric, integer, pointer)
    names -= self.getNamesGlobal(givenType, cacheResult,
                                 numeric, integer, pointer)
    return names


  def getNamesLocal(self,
      func: constructs.Func,
      givenType: Type = None,
      cacheResult: bool = True,  # set to False in very special case
      numeric: bool = False,
      integer: bool = False,
      pointer: bool = False,
  ) -> Set[VarNameT]:
    """Returns set of variable names local to a function.
    Without givenType it returns all the variables accessible.
    Since some local names are global (addr-taken), they are included too.
    """
    self.stats.getNamesTimer.start()
    if isinstance(givenType, FuncSig):
      self.stats.getNamesTimer.stop()
      return set()  # FuncSig is never local

    funcName = func.name
    key = givenType
    if numeric: key = NumericAny
    if integer: key = IntegerAny
    if pointer: key = PointerAny
    tup = (funcName, key)

    if tup in self._typeFuncLocalNamesMap:
      self.stats.getNamesTimer.stop()
      return self._typeFuncLocalNamesMap[tup]

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
      self._typeFuncLocalNamesMap[tup] = names  # cache the result

    self.stats.getNamesTimer.stop()
    return names


  def getNamesPpmsLocal(self,
      func: constructs.Func,
  ) -> Set[VarNameT]:
    """Returns set of pseudo variable names local to a function."""
    self.stats.getNamesTimer.start()
    funcName = func.name
    if funcName in self._localPpmsVars:
      self.stats.getNamesTimer.stop()
      return self._localPpmsVars[funcName]

    # use getLocalVars() to do most work
    localVars: Set[VarNameT] = self.getNamesLocal(func)

    vNameSet = set()
    for vName in localVars:
      if PPMS_VAR_REGEX.fullmatch(vName):
        vNameSet.add(vName)

    self._localPpmsVars[funcName] = vNameSet  # cache the result
    self.stats.getNamesTimer.stop()
    return vNameSet


  def getNamesEnv(self,
      func: constructs.Func,
      givenType: Type = None,
      cacheResult: bool = True,  # set to False in a very special case
      numeric: bool = False,
      integer: bool = False,
      pointer: bool = False,
  ) -> Set[VarNameT]:
    """Returns set of variables accessible in a given function (of the given type).
    Without givenType it returns all the variables accessible."""
    # TODO: add all heap locations (irrespective of the function) too
    self.stats.getNamesTimer.start()
    fName = func.name
    key = givenType
    if numeric: key = NumericAny
    if integer: key = IntegerAny
    if pointer: key = PointerAny

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


  def getNamesPpmsAll(self) -> Set[VarNameT]:
    """Returns set of all PPMS var names in the translation unit."""
    self.stats.getNamesTimer.start()
    if self._allPpmsVars is not None:
      self.stats.getNamesTimer.stop()
      return self._allPpmsVars

    varNames = set()
    for vName in self._nameInfoMap.keys():
      if PPMS_VAR_REGEX.fullmatch(vName):
        varNames.add(vName)

    self._allPpmsVars = varNames
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
      givenSignature: FuncSig
  ) -> List[constructs.Func]:
    """Returns functions with the given signature."""
    if givenSignature in self._funcSigToFuncListMap:
      return self._funcSigToFuncListMap[givenSignature]

    funcList: List[constructs.Func] = []
    for func in self.yieldFunctions():
      if givenSignature.isEqualOrVoid(func.sig):
        funcList.append(func)

    self._funcSigToFuncListMap[givenSignature] = funcList
    return funcList


  def getNamesOfPointees(self,
      func: constructs.Func,
      var: VarE,
      pointeeMap: Opt[Dict[VarNameT, Any]] = None,
  ) -> Set[VarNameT]:
    """Returns the pointee names of the given pointer name,
    if `pointeeMap` is None it returns a conservative value."""

    # Step 1: what type is the given name?
    varName, varType = var.name, var.type
    assert varType.isPointer(), f"{varName}, {varType}, {func}"

    if isinstance(varType, ArrayT):
      varType = varType.getElementTypeFinal()

    if not isinstance(varType, Ptr):
      raise ValueError(f"{varName}: {varType}")

    # Step 2: if here its a pointer, get its pointees
    pointeeType = varType.getPointeeType()

    if pointeeMap is None or varName not in pointeeMap:  # become conservative
      return self.getNamesEnv(func, pointeeType)

    pointees = pointeeMap[varName].val
    assert pointees, f"{varName}, {pointees}, {pointeeMap}"
    return pointees


  def getNamesRValuesOfExpr(self,
      func: constructs.Func,
      e: ExprET,
      pointeeMap: Opt[Dict[VarNameT, Any]] = None,
  ) -> Set[VarNameT]:
    """Returns the locations whose value is finally read
    by a assignment statement, as if this expr was
    on the RHS of an assignment. (excluding the call expression)

    For example,
     * in '*x' the pointees of x would be finally read.
     * in 'a ? b : c' the variables b and c would be read.
     * in 'a + b' there are NO rvalue names, but the value of the expr.
     * in '-a' there are NO rvalue names, but the value of the expr.

    Note: If the RValue(s) is a RecordT type, then the analysis
    should handle the names specially since a record assignment
    can be viewed as a sequence of member wise assignments.
    """
    assert not isinstance(e, CallE), f"{func}, {e}"

    if isinstance(e, SelectE):
      names = self.getNamesRValuesOfExpr(func, e.arg1, pointeeMap) \
                | self.getNamesRValuesOfExpr(func, e.arg2, pointeeMap)
    elif isinstance(e, LitE):
      return {e.name} if e.isString() else set() # non-str lit have no names
    else:
      names = self.getNamesLValuesOfExpr(func, e, pointeeMap)

    return names


  def getNamesLValuesOfExpr(self,
      func: constructs.Func,
      e: ExprET,
      pointeeMap: Opt[Dict[VarNameT, Any]] = None,
  ) -> Set[VarNameT]:
    """Returns the locations that may be modified,
    if this expression was on the LHS of an assignment.

    Note: If the LValue(s) is a RecordT type, then the analysis
    should handle the names specially since a record assignment
    can be viewed as a sequence of member wise assignments.
    """
    names = set()
    assert not isinstance(e, (CallE, LitE)), f"{func}, {e}"

    if isinstance(e, VarE):
      names.add(e.name)
      return names

    elif isinstance(e, DerefE):
      names.update(self.getNamesOfPointees(func, e.arg, pointeeMap))
      return names

    elif isinstance(e, ArrayE):
      if e.hasDereference():
        names.update(self.getNamesOfPointees(func, e.of, pointeeMap))
      else:
        names.add(e.getFullName())
      return names

    elif isinstance(e, MemberE):
      of, memName = e.of, e.name
      assert isinstance(of.type, Ptr), f"{e}: {of.type}"
      for name in self.getNamesOfPointees(func, of, pointeeMap):
        names.add(f"{name}.{memName}")
      return names

    raise ValueError(f"{e}")


  def getNamesPossiblyModifiedViaCallExpr(self,
      func: constructs.Func,  # the caller
      e: CallE,
  ) -> Set[VarNameT]:
    """E.g. in call: func(a, b, p)
    An over-approximation.
    """
    names = set()
    for arg in e.args:
      if isinstance(arg, AddrOfE):
        assert isinstance(arg.arg, VarE), f"{arg}, {e}, {e.info}"
        arg = arg.arg
        names.add(arg.name)
      if isinstance(arg, VarE):
        names |= self.getNamesPossiblyModifiedViaCallArg(func, arg.name, True)

    addGlobals, calleeName = True, e.getFuncName()
    if calleeName:
      tUnit: TranslationUnit = func.tUnit
      calleeFunc = tUnit.getFuncObj(calleeName)
      addGlobals = not calleeFunc.hasBody() # Assumption: only func with body modify globals
    if addGlobals: names.update(self.getNamesGlobal())
    return names


  def getNamesPossiblyModifiedViaCallArg(self,
      func: constructs.Func,  # the caller
      argName: VarNameT,
      passByValue: bool = True,
  ) -> Set[VarNameT]:
    """Conservatively returns the set of names that can be
    possibly modified by passing the argument named argName
    to a function call. This function is recursive.

    All variables whose address has been taken can be modified.

      * If p is pointer to integers, then all the integer variables
      * visible in the caller can be modified.
      * If p is ptr-to ptr-to int, then all the ptr-to int and int variables
      * visible in the caller can be modified.
    """
    names = set()
    argType = self.inferTypeOfVal(argName)

    # CASE 1: if arg is a record or an array
    if argType.isRecord():
      varNameInfos = argType.getNamesOfType(None, prefix=argName)
      for vnInfo in varNameInfos:
        if passByValue and not vnInfo.type.isPointer(): continue
        if not passByValue: names.add(vnInfo.name) #i.e. the name can also be modified
        names.update(self.getNamesPossiblyModifiedViaCallArg(func, vnInfo.name, True))

    # CASE 2: if arg is a pointer
    nameSet = None
    while argType.isPointer(): # transitively add pointees
      added, argType = False, argType.getPointeeType()
      e = self.getTmpVarExpr(argName)
      if e and isinstance(e, AddrOfE) and isinstance(e.arg, VarE):
          added, nameSet = True, {e.arg.name}
          names.update(nameSet)
      if not added:
        nameSet = self.getNamesEnv(func, argType) # over-approximate
        names.update(nameSet)

    # CASE 3: After case 2, check if the pointer lead to a record type
    if nameSet and argType.isRecord():
      for vName in nameSet:
        names.update(self.getNamesPossiblyModifiedViaCallArg(func, vName, False))

    return names


  def filterNamesNumeric(self,
      names: Set[VarNameT]
  ) -> Set[VarNameT]:
    """Remove names which are not numeric."""
    filteredNames = set()
    for name in names:
      objType = self.inferTypeOfVal(name)
      if objType.isNumericOrVoid():
        filteredNames.add(name)
      elif isinstance(objType, ArrayT):
        arrayElementType = objType.getElementTypeFinal()
        if arrayElementType.isNumericOrVoid():
          filteredNames.add(name)

    return filteredNames


  def filterNamesInteger(self,
      names: Set[VarNameT]
  ) -> Set[VarNameT]:
    names = self.filterNamesNumeric(names)
    filteredNames = set()
    for name in names:
      objType = self.inferTypeOfVal(name)
      if objType.isIntegerOrVoid():
        filteredNames.add(name)
      elif isinstance(objType, ArrayT):
        arrayElementType = objType.getElementTypeFinal()
        if arrayElementType.isIntegerOrVoid():
          filteredNames.add(name)

    return filteredNames


  def filterNamesPointer(self,
      names: Set[VarNameT],
      addFunc: bool = False, # adds function names too
  ) -> Set[VarNameT]:
    """Remove names which are not pointers.
    An array containing pointers is also considered as pointer."""
    filteredNames = set()
    for name in names:
      nameType = self.inferTypeOfVal(name)
      if nameType.isPointerOrVoid():
        filteredNames.add(name)
      elif addFunc and nameType.isFuncSig():
        # This is useful in case where: x = *arr;
        # where arr is an array of func pointers.
        # In that case *arr will resolve to a set of function names,
        # which shouldn't be removed since they are not pointers.
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


  def getNamesInExprMentionedIndirectly(self,
      func: constructs.Func,
      e: ExprET,
      includeAddrTaken: bool = False, # in &(*x) includes '*x' names.
  ) -> Set[VarNameT]:
    """
    This function returns the possible locations which
    may be used for their value indirectly (due to dereference)
    by the use of the given expression.
    """
    if isinstance(e, VarE): # most likely case
      return set()

    elif isinstance(e, (DerefE, ArrayE, MemberE)):
      if not e.hasDereference(): return set() # can happen in ArrayE
      return self.getNamesLValuesOfExpr(func, e)

    elif isinstance(e, AddrOfE):
      if not includeAddrTaken or not e.hasDereference(): set()
      return self.getNamesInExprMentionedIndirectly(func, e.arg)

    elif isinstance(e, CallE):
      return self.getNamesPossiblyModifiedViaCallExpr(func, e)

    else:
      # Returns an emptyset here, since all other expressions
      # only have syntactic reference.
      return set()  # empty set


  def canonicalizeExpressions(self):
    """Canonicalize all expressions in SPAN IR.

    e.g. For all commutative expressions:

    *  0 == x to x == 0. (variable names first)
    *  b + a  to a + b.   (sort by variable name)
    """

    for func in self.yieldFunctionsWithBody():
      for insn in func.yieldInstrSeq():
        if isinstance(insn, AssignI):
          swapArguments = False
          rhs = insn.rhs
          if isinstance(rhs, BinaryE):
            if rhs.opr.isCommutative() or rhs.opr.isRelationalOp():
              arg1 = rhs.arg1
              arg2 = rhs.arg2

              if isinstance(rhs.arg1, LitE):
                swapArguments = True
              elif isinstance(rhs.arg2, LitE):
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


  def getFuncObj(self,
      funcName: Opt[FuncNameT] = None,
      funcId: Opt[FuncIdT] = None,
      varName: Opt[VarNameT] = None,
  ) -> constructs.Func:
    """Returns the function object either using the name or id,
    or the local var name."""
    assert funcName or funcId is not None, f"{funcName}, {funcId}"
    assert self._indexedFuncList, f"{self._indexedFuncList}"

    if funcName:
      if funcName in self.allFunctions:
        return self.allFunctions[funcName]
    elif funcId is not None and funcId == GLOBAL_INITS_FUNC_ID:
      return self.getGlobalInitsFunction()
    elif funcId is not None:
      assert funcId < len(self._indexedFuncList),\
        f"{funcId}, {len(self._indexedFuncList)}"
      return self._indexedFuncList[funcId]
    elif varName:
      funcName = extractFuncName(varName)
      assert funcName, f"{varName}"

    raise ValueError(f"{funcName}, {funcId}")


  def underApproxFunc(self,
      func: constructs.Func,
  ) -> bool:
    """Returns True if the function can be completely under-approximated.
    This is used to increase the precision.
    """
    funcName = func.name
    underApprox = True

    if func.hasBody():
      underApprox = False
    elif "scanf" in funcName:
      underApprox = False
    elif "f:fgets" in funcName:
      underApprox = False
    elif "f:strcpy" in funcName:
      underApprox = False
    elif "f:stat" == funcName:
      underApprox = False


    return underApprox


  def hasAbstractVars(self,
      varNameSet: Opt[Set[VarNameT]],
  ) -> bool:
    """Returns True if at least one abstract variable exists in the given set.

    As this function needs to check the type of the variable,
    it needs to be in this class.
    """

    if not varNameSet:
      return False

    for vName in varNameSet:
      vType = self.inferTypeOfVal(vName)
      if vType.isArray() or isPpmsVar(vName):
        return True

    return False


