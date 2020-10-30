#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Conventions and related utility functions in SPAN IR.
This module only imports `span.ir.types` module in the `span.ir` package.
Hence, except `span.ir.types` module all other modules can import this module.
"""

import logging
LOG = logging.getLogger("span")

from typing import Optional as Opt, Set, List
from span.util.util import LS
import re
import functools

from . import types


FalseEdge: types.EdgeLabelT = "FalseEdge"
TrueEdge: types.EdgeLabelT = "TrueEdge"
UnCondEdge: types.EdgeLabelT = "UnCondEdge"

Forward: types.DirectionT = "Forward"
Backward: types.DirectionT = "Backward"
ForwBack: types.DirectionT = "ForwBack"

# these values change dynamically see (setNodeSiteBits())
NodeSiteTotalBitLen   = 32
NodeSiteFuncIdBitLen  = 14
NodeSiteNodeIdBitLen  = 18


################################################
# BOUND START: special_vars_values_and_types_of_spanir
################################################

# FIXME: how to match size_t (assuming types.UInt64 for now)
#   Possible Fix: Get the concrete type of size_t from Clang for
#                 the current translation unit.
memAllocFunctions = {
  # void* malloc (size_t size); // real declaration
  "f:malloc": types.FuncSig(returnType=types.Ptr(to=types.Void),
                      variadic=False,
                      paramTypes=[types.UInt64]),

  # void* calloc (size_t num, size_t size); // real declaration
  "f:calloc": types.FuncSig(returnType=types.Ptr(to=types.Void),
                      variadic=False,
                      paramTypes=[types.UInt64, types.UInt64]),

  # NOTE: realloc and free are written here for reference only.
  # NOTE: There is no need for them to be in this dictionary.
  # void* realloc (void* ptr, size_t size); // real declaration
  # "f:realloc": types.FuncSig(returnType=types.Ptr(to=types.Void),
  #                          variadic=False,
  #                          paramTypes=[types.Ptr(to=types.Void), types.UInt64]),

  # void free (void* ptr); // real declaration
}

TRANSFORM_INFO_FILE_NAME = "{cFileName}.span.trinfo"

GLOBAL_INITS_FUNC_ID = 0
"""Function id of the artificial global inits function."""

GLOBAL_INITS_FUNC_NAME = "f:1_global_inits"
"""All global declarations go into this artificial function."""

NAME_SEP = ":"
"""The top level separator used in object names."""

ANY_TMPVAR_REGEX = re.compile(r"^(.*:|)\d+(t|if|L)$")
"""Regex to detect all types of temporary variable names."""
NORMAL_TMPVAR_REGEX = re.compile(r"^(.*:|)\d+t$")
"""Regex to detect the most basic temporary variable name."""

COND_TMPVAR_REGEX = re.compile(r"^(.*:|)\d+if$")
"""Regex to detect the conditional temporary variable name."""
COND_TMPVAR_GEN_STR = "{number}if"
"""Format string to generate a conditional temporary variable name."""

LOGICAL_TMPVAR_REGEX = re.compile(r"^(.*:|)\d+L$")
"""Regex to detect the logical test temporary variable name."""
USER_VARIABLE_REGEX = re.compile(r"^(.*:|)\D[.\w]*$")
"""Regex to detect the user defined variable name."""

# Both these variables are inter-related
# One assigns a name the other detects the name.
NAKED_PSEUDO_VAR_NAME = "{count}p"
"""Format string to generate pseudo variable name."""
PSEUDO_VAR_REGEX = re.compile(r"^(.*:|)\d+p$")
"""Regex to detect pseudo variable name."""
PSEUDO_VAR_REGEX2 = re.compile(r"(:|^)\d+p(\.|$)")
"""Regex to detect pseudo variable name."""
PSEUDO_VAR_TYPE = types.VarArray
"""Default pseudo variable type."""

# String literal name regex (they are globals)
NAKED_STR_LIT_NAME = "g:{count}str"
STR_LIT_NAME_REGEX = re.compile(r"(:|^)\d+str$")

"""
The null pointer is considered a null object
of type Void. This object is used in place of
zero or NULL/nullptr assignment to a pointer.
"""
NULL_OBJ_NAME = "g:00"
NULL_OBJ_TYPE = types.Void  ## Null object type is Void
NULL_OBJ_PTR_TYPE = types.Ptr(NULL_OBJ_TYPE)

DUMMY_VAR_REGEX = re.compile(r"^(.*:|)\d+d$")
"""A dummy var name regex. Also see: `span.ir.tunit.addDummyObjects(self)`"""
DUMMY_VAR_TYPE = types.Void
"""The default dummy var type is types.Void"""

MEMBER_EXPR_REGEX = re.compile(r"\..+$")
"""
Regex to detect a member expression name.
It just checks if there is a dot in the name.
PS: Thus a dot in a name is reserved for member access only.
"""

"""
Regex for a record name
"""
RECORD_NAME_REGEX = re.compile(r"^[su]:.+")

FUNC_NAME_REGEX = re.compile(r"^f:.+")


def isUserVar(vName: types.VarNameT) -> bool:
  """Is it a variable created by user?"""
  if USER_VARIABLE_REGEX.fullmatch(vName):
    return True
  return False


def isTmpVar(vName: types.VarNameT) -> bool:
  """Is it a tmp var (of any form)"""
  if ANY_TMPVAR_REGEX.fullmatch(vName):
    return True
  return False


def isNormalTmpVar(vName: types.VarNameT) -> bool:
  """Is it a normal tmp var"""
  if NORMAL_TMPVAR_REGEX.fullmatch(vName):
    return True
  return False


def isCondTmpVar(vName: types.VarNameT) -> bool:
  """Is a tmp var used in if statements."""
  if COND_TMPVAR_REGEX.fullmatch(vName):
    return True
  return False


def isLogicalTmpVar(vName: types.VarNameT) -> bool:
  """Is a tmp var used to break logical expressions: &&, ||"""
  if LOGICAL_TMPVAR_REGEX.fullmatch(vName):
    return True
  return False


def isPseudoVar(vName: types.VarNameT) -> bool:
  """Is it a pseudo var? (used to hide malloc/calloc)"""
  if PSEUDO_VAR_REGEX.fullmatch(vName):
    return True
  return False


def isDummyVar(vName: types.VarNameT) -> bool:
  """Is it a dummy var?"""
  if DUMMY_VAR_REGEX.fullmatch(vName):
    return True
  return False


def getNullvarName() -> str:
  """Returns the standard name to be used for a null object."""
  return NULL_OBJ_NAME


def extractFuncName(varName: types.VarNameT) -> Opt[types.FuncNameT]:
  assert isCorrectNameFormat(varName), f"Wrong variable name format: {varName}"
  if isLocalVarName(varName):
    bareFuncName = varName.split(':')[1]
    canonicalizeFuncName(bareFuncName)
  return None


def isGlobalName(name: str):
  return name.startswith("g:")


def isCorrectNameFormat(name: str) -> bool:
  """
  Returns true if the name is a valid
  1. Global Variable Name
  2. Local Variable Name
  3. Function Name
  4. Record Name
  """
  colonCount = name.count(NAME_SEP)
  colonCount3 = colonCount > 2
  if colonCount3: return False  # no name has more than two colons

  colonCount1 = colonCount == 1
  if isGlobalName(name): return colonCount1
  if isFuncName(name): return colonCount1
  if isRecordName(name): return colonCount1
  if isLocalVarName(name): return colonCount == 2

  assert False, f"Unknown name: {name}"


def isRecordName(recordName: types.RecordNameT) -> bool:
  return bool(RECORD_NAME_REGEX.fullmatch(recordName))


def isLocalVarName(varName: types.VarNameT) -> bool:
  """Returns true if varName's format is valid for a local var."""
  colonCount = varName.count(NAME_SEP)
  if varName.startswith("v:"):
    return colonCount == 2
  return False


def isNullvarName(name: str) -> bool:
  """Is the given name that of the null object?"""
  return name.startswith(NULL_OBJ_NAME)


def isStringLitName(name: str) -> bool:
  if STR_LIT_NAME_REGEX.search(name):
    return True
  return False


def isMemberName(varName: types.VarNameT) -> bool:
  """Is the given name of type: x.y.z?"""
  if MEMBER_EXPR_REGEX.search(varName):
    return True
  return False


def isFuncName(varName: types.VarNameT) -> bool:
  """Is the given name that of a function?"""
  if FUNC_NAME_REGEX.search(varName):
    return True
  return False


def nameHasPseudoVar(varName: types.VarNameT) -> bool:
  """Does the name like x.y.z contain a psudo variable?"""
  return bool(PSEUDO_VAR_REGEX2.search(varName))


def getPrefixes(varName: types.VarNameT) -> Set[types.VarNameT]:
  """If names has as dot, create all its valid prefixes.
  E.g: If input is 'x.y.z', it returns {'x.y.z', 'x.y', 'x'}
  See also: getSuffixes()
  """
  split = varName.split(".")

  if len(split) == 1:
    return {varName}  # its a normal name

  names = set()
  start = ""
  for s in split:
    dot = "" if not start else "."
    start = f"{start}{dot}{s}"
    names.add(start)
  return names  # all non-empty prefixes


def getSuffixes(
    givenType: Opt[types.Type],
    varName: types.VarNameT,
    objType: types.Type,
) -> Set[types.VarNameT]:
  """If a name represents a Record (array of records included)
  append its member accesses of the givenType as well.
  If givenType is None then add all member accesses."""

  names = {varName}
  if isinstance(objType, (types.RecordT, types.ArrayT)):
    names.update(ni.name for ni in objType.getNamesOfType(givenType, varName))
  return names


################################################
# BOUND END  : special_vars_values_and_types_of_spanir
################################################


################################################
# BOUND START: system_wide_assumption_based_utilities
################################################

def simplifyName(name: str):
  """Given names 'v:main:b'/'f:b'/'s:b'/'u:b' it returns 'b'"""
  return name.split(NAME_SEP)[-1]


def canonicalizeFuncName(funcName: str) -> types.FuncNameT:
  if FUNC_NAME_REGEX.fullmatch(funcName):
    return funcName  # already in canonical form
  else:
    return f"f:{funcName}"  # just prefix "f:" to make it canonical


def extractOriginalFuncName(funcName: str) -> types.FuncNameT:
  return simplifyName(funcName)


def genLocalName(funcName: str, varName: str):
  if NAME_SEP in varName:
    return varName
  simpleFuncName = simplifyName(funcName)
  simpleVarName = simplifyName(varName)
  return f"v:{simpleFuncName}:{simpleVarName}"


def genGlobalName(varName: str):
  if NAME_SEP in varName:
    return varName
  return f"g:{varName}"


def setNodeSiteBits(totalFuncs: int, maxCfgNodesInAFunction: int):
  global NodeSiteTotalBitLen, NodeSiteFuncIdBitLen, NodeSiteNodeIdBitLen
  NodeSiteFuncIdBitLen = totalFuncs.bit_length()
  # add some room for nodeid bits (might help when adding nodes)
  NodeSiteNodeIdBitLen = maxCfgNodesInAFunction.bit_length() + 2 # extra bits
  NodeSiteTotalBitLen = NodeSiteFuncIdBitLen + NodeSiteNodeIdBitLen
  if LS and NodeSiteTotalBitLen > 32:
    LOG.info("WARN: NodeSiteTotalBitLen > 32 bits: %s bits.",
             NodeSiteTotalBitLen)


#@functools.lru_cache(500)
def genFuncNodeId(
    funcId: types.FuncIdT,
    nid: types.NodeIdT,
) -> types.FuncNodeIdT:
  assert funcId.bit_length() <= NodeSiteFuncIdBitLen, f"{nid}, {NodeSiteFuncIdBitLen}"
  assert nid.bit_length() <= NodeSiteNodeIdBitLen, f"{nid}, {NodeSiteNodeIdBitLen}"
  return (funcId << NodeSiteNodeIdBitLen) | nid


def getFuncId(funcNodeId: types.FuncNodeIdT):
  return funcNodeId >> NodeSiteNodeIdBitLen


def getNodeId(funcNodeId: types.FuncNodeIdT):
  return funcNodeId & ((1 << NodeSiteNodeIdBitLen) - 1)


def getFuncNodeIdStr(
    fNid: types.FuncNodeIdT,
) -> str:
  return f"({getFuncId(fNid)}, {getNodeId(fNid)})"


################################################
# BOUND END  : system_wide_assumption_based_utilities
################################################


