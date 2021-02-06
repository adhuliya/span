#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
This is a convenience module that brings the scattered API
of the SPAN IR at one place.

The API here is useful in writing an analysis/diagnosis.
The idea is that the user should only need to import this
module for all the IR needs.

Note about circular dependency:
  * No other module in span.ir package should import this module.
  * This module uses all other modules in `span.ir` package.
"""

import logging

LOG = logging.getLogger("span")
from typing import Dict, Set, Tuple, Optional, List, Callable, cast
import subprocess as subp
import functools

import span.ir.types as types
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.tunit as tunit

import span.util.util as util
import span.util.consts as consts
from span.util.util import LS

"""
This import allows these function to be called
using this module's scope like: `ir.isTmpVar("v:main:1t")`
"""
import span.ir.conv as irConv
from span.ir.conv import \
  (isUserVar,
   isTmpVar,
   isCondTmpVar,
   isLogicalTmpVar,
   isDummyVar,
   isNormalTmpVar,
   getNullvarName,
   isNullvarName,
   isPseudoVar,
   getPrefixes,
   DUMMY_VAR_REGEX,
   MEMBER_EXPR_REGEX,
   PSEUDO_VAR_REGEX,
   PSEUDO_VAR_REGEX2,
   NULL_OBJ_NAME,
   GLOBAL_INITS_FUNC_NAME,
   )

from span.ir.tunit import \
  TranslationUnit

from span.ir.constructs import \
  Func

from span.ir.cfg import \
  (EdgeLabelT,
   FalseEdge,
   TrueEdge,
   UnCondEdge,
   BasicBlockIdT,
   BbEdge,
   BB,
   CfgNodeId,
   CfgEdge,
   CfgNode,
   Cfg,
   )

from span.ir.callgraph import \
  (CallGraph,
   CallGraphNode,
  )


# try:
#   # some machines may not have proto library
#   from span.ir.serialize import \
#     (ProtoSerializer,
#      ProtoDeserializer, )
# except ImportError as ie:
#   if LS: _log.error("ImportError(Protobuf):\n %s", ie)
#   print("ERROR: google protobuf library not found.", file=sys.stderr)
# except Exception as e:
#   if LS: _log.error("ERROR(Protobuf):\n %s", e)
#   print("ERROR: in protobuf span.ir.serialize module.", file=sys.stderr)


@functools.lru_cache(200)
def inferTypeOfVal(func: constructs.Func, val) -> types.Type:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.inferTypeOfVal(val)


def inferTypeOfExpr(func: constructs.Func, e: expr.ExprET) -> types.Type:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.inferTypeOfExpr(e)


def inferTypeOfInstr(func: constructs.Func, insn: instr.InstrIT) -> types.Type:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.inferTypeOfInstr(insn)


@functools.lru_cache(200)
def getTmpVarExpr(func: constructs.Func,
    vName: types.VarNameT,
) -> Optional[expr.ExprET]:
  """Returns the expression the given tmp var is assigned.
  It only tracks some tmp vars, e.g. ones like 3t, 1if, 2if ...
  The idea is to map the tmp vars that are assigned only once.
  (hence tmp vars 1L, 5L, ... are not tracked.)
  """
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getTmpVarExpr(vName)


@functools.lru_cache(200)
def getFunctionsOfGivenSignature(
    tUnit: tunit.TranslationUnit,
    givenSignature: types.FuncSig
) -> List[constructs.Func]:
  """Returns functions of the signature given."""
  return tUnit.getFunctionsOfGivenSignature(givenSignature)


@functools.lru_cache(200)
def containsPointer(e: expr.ExprET) -> bool:
  """Does the given expression has a pointer?"""
  if isinstance(e.type, types.Ptr):
    return True
  elif isinstance(e, expr.ArrayE):
    return containsPointer(e.of)
  elif isinstance(e, expr.MemberE):
    return containsPointer(e.of)
  else:
    return False


def hasArrayExpression(memberExpr: expr.MemberE) -> bool:
  """Is the expression like: a[9].y, a.y[3].z, ... ?"""
  if isinstance(memberExpr.of, expr.ArrayE):
    return True
  elif isinstance(memberExpr.of, expr.MemberE):
    return hasArrayExpression(memberExpr.of)
  else:
    return False


def hasMemberExpression(arrayExpr: expr.ArrayE) -> bool:
  """Is the expression like: y.a[9], a.y[3], ... ?"""
  if isinstance(arrayExpr.of, expr.ArrayE):
    return hasMemberExpression(arrayExpr.of)
  elif isinstance(arrayExpr.of, expr.MemberE):
    return True
  else:
    return False


def hasArrayExprOrPseudoVar(e: expr.ExprET) -> bool:
  """Does the given expression (mostly a name)
  contain an array expression or a pseudo var?"""
  if isinstance(e, expr.PseudoVarE):
    return True
  elif isinstance(e, expr.ArrayE):
    return True
  elif isinstance(e, expr.MemberE):
    return hasArrayExprOrPseudoVar(e.of)
  else:
    return False


def getNameInfo(func: constructs.Func,
    name: types.VarNameT,
) -> Optional[types.VarNameInfo]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getNameInfo(name)


def nameHasArray(func: constructs.Func,
    name: types.VarNameT
) -> Optional[types.VarNameT]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.nameHasArray(name)


def dumpIr(tUnit: tunit.TranslationUnit) -> str:
  return tUnit.dumpIr()


def getExprRValueNames(func: constructs.Func,
    e: expr.ExprET
) -> Set[types.VarNameT]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getExprRValueNames(func, e)


def getExprLValueNames(func: constructs.Func,
    e: expr.ExprET
) -> Set[types.VarNameT]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getExprLValueNames(func, e)


def getNamesPossiblyModifiedInCallExpr(func: constructs.Func,
    e: expr.CallE
) -> Set[types.VarNameT]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getNamesPossiblyModifiedInCallExpr(func, e)


@functools.lru_cache(200)
def getNamesLocal(func: constructs.Func,
    givenType: Optional[types.Type] = None,
    numeric: bool = False,
    integer: bool = False,
    pointer: bool = False,
) -> Set[types.VarNameT]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getNamesLocal(func, givenType, numeric=numeric,
                                  integer=integer, pointer=pointer)


@functools.lru_cache(200)
def getNamesGlobal(func: constructs.Func,
    givenType: Optional[types.Type] = None,
    numeric: bool = False,
    integer: bool = False,
    pointer: bool = False,
) -> Set[types.VarNameT]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getNamesGlobal(givenType, numeric=numeric,
                                   integer=integer, pointer=pointer)


def getNamesEnv(func: constructs.Func,
    givenType: Optional[types.Type] = None,
    numeric: bool = False,
    integer: bool = False,
    pointer: bool = False,
) -> Set[types.VarNameT]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getNamesEnv(func, givenType, numeric=numeric,
                                integer=integer, pointer=pointer)


def filterNamesNumeric(func: constructs.Func,
    names: Set[types.VarNameT]
) -> Set[types.VarNameT]:
  """Remove names which are not numeric."""
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.filterNamesNumeric(names)


def filterNamesInteger(func: constructs.Func,
    names: Set[types.VarNameT]
) -> Set[types.VarNameT]:
  """Remove names which are not integer."""
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.filterNamesInteger(names)


def filterNamesPointer(func: constructs.Func,
    names: Set[types.VarNameT]
) -> Set[types.VarNameT]:
  """Remove names which are not pointers."""
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.filterNamesPointer(names)


def filterNames(func: constructs.Func,
    names: Set[types.VarNameT],
    nameTest: Callable[[types.Type, types.VarNameT], bool],
) -> Set[types.VarNameT]:
  inferType = cast(tunit.TranslationUnit, func.tUnit).inferTypeOfVal
  augmentedTest = lambda name: nameTest(inferType(name), name)
  return set(filter(augmentedTest,  names))


@functools.lru_cache(1024)
def getNamesUsedInExprSyntactically(e: expr.ExprET
) -> Set[types.VarNameT]:
  return set(expr.getNamesUsedInExprSyntactically(e, forLiveness=True))


def getNamesUsedInExprNonSyntactically(
    func: constructs.Func,
    e: expr.ExprET
) -> Set[types.VarNameT]:
  assert func.tUnit is not None, f"{func}"
  return func.tUnit.getNamesUsedInExprNonSyntactically(func, e)


def getSuffixes(func: constructs.Func,
    varName: types.VarNameT
) -> Set[types.VarNameT]:
  """If a name represents a Record (array of records included)
  append its member accesses as well."""
  objType = inferTypeOfVal(func, varName)

  return irConv.getSuffixes(None, varName, objType)


def yieldFunctionsWithBody(tUnit: TranslationUnit):
  yield from tUnit.yieldFunctionsWithBody()


def yieldFunctions(tUnit: TranslationUnit):
  yield from tUnit.yieldFunctions()


def readSpanIr(fileName: types.FileNameT) -> TranslationUnit:
  """Reads span ir from the given file.
  Always use this function for reading the SPAN IR,
  as it includes all the necessary imports."""
  # redundant imports here are necessary to eval the input span ir file
  import span.ir.types      as types
  import span.ir.op         as op
  import span.ir.expr       as expr
  import span.ir.instr      as instr
  import span.ir.constructs as constructs
  import span.ir.tunit      as tunit
  from span.ir.types import Loc, Info

  content = util.readFromFile(fileName)
  tUnit: TranslationUnit = eval(content)
  return tUnit


def convertCFile(cFileName: str) -> str:
  """Converts the given C file to SPANIR.
  On success a file named: {cFileName}.spanir should be created
  in the current directory.
  It returns the SpanIr File name.
  """
  cmd = consts.CMD_F_GEN_SPANIR.format(cFileName=cFileName)
  status, output = subp.getstatusoutput(cmd)
  if status != 0:
    print(output)
    print(consts.MSG_C2SPANIR_FAILED.format(cFileName=cFileName, cmd=cmd))
    raise IOError()
  return f"{cFileName}.spanir"


def genTranslationUnit(cFileName: str) -> TranslationUnit:
  """Generates the translation unit and returns it as a python object.
  Along with the status of success or failure (0 is success).
  """
  spanirFile = convertCFile(cFileName)
  tUnit = readSpanIr(spanirFile)
  return tUnit


def isDummyGlobalFunc(func: constructs.Func):
  """Returns true if the function given is the dummy global function."""
  return func.name == GLOBAL_INITS_FUNC_NAME



