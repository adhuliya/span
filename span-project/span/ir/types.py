#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""All types available in the IR and many other places.

Some types are defined in other modules where they make more sense.
This module is imported by almost all
other modules in the source. Hence this
module should only import third party modules or
modules from SPAN's `span.util` package.
"""

# FIXME: make all Type objects immutable. Till then assume immutable.

import logging
LOG = logging.getLogger(__name__)

from typing import TypeVar, List, Optional as Opt, Tuple, Dict,\
  Set, Union as TypingUnion
import functools

from span.util import util
from span.util.util import LS
import span.util.consts as consts
from span.util.consts import PTR_INDLEV_INVALID

################################################
# BOUND START: useful_types
################################################

T = TypeVar("T")  # a generic data type

FileNameT = str

VarNameT = str  # names like x, x.y.z etc.
FuncNameT = str # function names can also be VarNameT type
TUnitNameT = str
LabelNameT = str
RecordNameT = str  # Record = Struct/Union
StructNameT = str
UnionNameT = str
MemberNameT = str  # a struct/union member name

AnNameT = str  # AnalysisNameT

InstrIndexT = int

TypeCodeT = int  # each type has a numeric code

OpSymbolT = str  # operator symbol
OpNameT = str  # operator name

NumericT = TypingUnion[int, float]
LitT = TypingUnion[int, float, str]

NodeIdT = int  # Node id (CFG) (18 bit) (>=0,<2^18)
FuncIdT = int  # Function id (14 bit) (>=0,<2^14)

GlobalNodeIdT = int
"""A (FuncId || NodeId) (32 bit) unsigned integer.

It uniquely identifies a node, and is also used to track a callsite."""

BasicBlockIdT = int

LineNumT = int
ColumnNumT = int

EdgeLabelT = str  # edge labels (see span.ir.conv)

OpCodeT = int  # operator codes type
ExprCodeT = int  # expression codes type
InstrCodeT = int  # instruction codes type

DirectionT = str  # analysis direction (see span.ir.conv)

FormalStrT = str

TopBotT = bool # E.g. False == Bot, True == Top

################################################
# BOUND END  : useful_types
################################################


################################################
# BOUND START: type_codes
################################################

# the order and ascending sequence is important
VOID_TC: TypeCodeT = 0

INT1_TC: TypeCodeT = 10  # bool
INT8_TC: TypeCodeT = 11  # char
INT16_TC: TypeCodeT = 12  # short
INT32_TC: TypeCodeT = 13  # int
INT64_TC: TypeCodeT = 14  # long long
INT128_TC: TypeCodeT = 15  # ??

UINT8_TC: TypeCodeT = 20  # unsigned char
UINT16_TC: TypeCodeT = 21  # unsigned short
UINT32_TC: TypeCodeT = 22  # unsigned int
UINT64_TC: TypeCodeT = 23  # unsigned long long
UINT128_TC: TypeCodeT = 24  # ??

FLOAT16_TC: TypeCodeT = 50  # ??
FLOAT32_TC: TypeCodeT = 51  # float
FLOAT64_TC: TypeCodeT = 52  # double
FLOAT80_TC: TypeCodeT = 53  # ??
FLOAT128_TC: TypeCodeT = 54  # ??

# PTR_TC: TypeCodeT = 100  # pointer type code (assumes 64 bit)
PTR32_TC: TypeCodeT = 101  # pointer type code 32 bit
PTR64_TC: TypeCodeT = 102  # pointer type code 64 bit
PTR128_TC: TypeCodeT = 103  # pointer type code 128 bit
PTR_TC = PTR64_TC  # default pointer type code (assumes 64 bit)
ARR_TC: TypeCodeT = 105  # array type code
CONST_ARR_TC: TypeCodeT = 106  # const size array type code
VAR_ARR_TC: TypeCodeT = 107  # variable array type code
INCPL_ARR_TC: TypeCodeT = 108  # incomplete array type code

FUNC_TC: TypeCodeT = 200  # function type code
FUNC_SIG_TC: TypeCodeT = 201  # a function signature type code
STRUCT_TC: TypeCodeT = 300  # structure type code
UNION_TC: TypeCodeT = 400  # union type code

# special_abstract_types
NUMERIC_TC: TypeCodeT = 500
INTEGER_TC: TypeCodeT = 510
POINTER_TC: TypeCodeT = 520


################################################
# BOUND END  : type_codes
################################################

################################################
# BOUND START: properties_associated_with_an_entity
################################################
# These properties don't logically belong to 'types'
# module, but are needed for dependence purposes.

class Loc:
  """Location type : line, col."""

  __slots__ : List[str] = ["line", "col"]


  def __init__(self,
      line: LineNumT = 0,
      col: ColumnNumT = 0
  ) -> None:
    super().__init__()
    self.line = line
    self.col = col


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, Loc):
      return NotImplemented
    equal = True
    if not self.line == other.line:
      equal = False
    elif not self.col == other.col:
      equal = False
    return equal


  def isEqual(self,
      other: 'Loc'
  ) -> bool:
    equal = True
    if not isinstance(other, Loc):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.line == other.line:
      if LS: LOG.error("LineNumsDiffer: %s, %s", self, other)
      equal = False
    if not self.col == other.col:
      if LS: LOG.error("ColNumsDiffer: %s, %s", self, other)
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __lt__(self, other):
    return self.line <= other.line and self.col <= other.col


  def __le__(self, other):
    return self.line <= other.line and self.col <= other.col


  def __str__(self):
    return f"Loc({self.line},{self.col})"


  def __repr__(self):
    """It expects eval()uator to import this class as follows:
      from span.ir.types import Loc
    """
    return f"Loc({self.line},{self.col})"


class Info:
  """Information associated with a syntactic entity.
  This class also holds the source location."""

  __slots__ : List[str] = ["loc", "misc"]

  def __init__(self,
      loc: Loc,
      misc: int = 0,  # misc info
  ) -> None:
    super().__init__()
    self.loc = loc
    """To store any other useful misc information."""
    self.misc = misc


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, Info):
      return NotImplemented
    equal = True
    if not self.loc == other.loc:
      equal = False
    elif not self.misc == other.misc:
      equal = False
    return equal


  def isEqual(self, other) -> bool:
    equal = True
    if not isinstance(other, Info):
      if LS: LOG.debug("ObjectsIncomparable: %s, %s", self, other)
      return False
    if self.loc and not self.loc.isEqual(other.loc):
      equal = False
    if not self.misc == other.misc:
      if LS: LOG.debug("MiscInfoDiffers: %s, %s", self, other)
      equal = False

    if not equal and LS:
      LOG.debug("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __str__(self):
    return f"Info({repr(self.loc)},{self.misc})"


  def __repr__(self):
    """It expects eval()uator to import this class as follows:
      from span.ir.types import Info
    """
    return f"Info({repr(self.loc)},{self.misc})"


################################################
# BOUND END  : properties_associated_with_an_entity
################################################



class Type:
  """Class to represent types. It is super class for all compound types.
  It is directly used to represent the basic types.
  """

  __slots__ : List[str] = ["typeCode"]

  def __init__(self,
      typeCode: TypeCodeT
  ) -> None:
    self.typeCode = typeCode


  def isIntegerOrVoid(self) -> bool:
    tc = self.typeCode
    return INT1_TC <= tc <= UINT128_TC or tc == VOID_TC


  def isSignedOrVoid(self) -> bool:
    tc = self.typeCode
    return INT1_TC <= tc <= INT128_TC or tc == VOID_TC


  def isUnsignedOrVoid(self) -> bool:
    tc = self.typeCode
    return UINT8_TC <= tc <= UINT128_TC or tc == VOID_TC


  def isFloatOrVoid(self) -> bool:
    tc = self.typeCode
    return FLOAT16_TC <= tc <= FLOAT128_TC or tc == VOID_TC


  def isNumericOrVoid(self) -> bool:
    """Returns bool(isInteger() or isFloat())."""
    tc = self.typeCode
    return INT1_TC <= tc <= FLOAT128_TC or tc == VOID_TC


  def isPointerOrVoid(self) -> bool:
    """Should return True for any type that the
    points-to analysis needs to track the pointees of.
    Currently only user-defined pointers and array of pointers
    are considered a pointer here.
    Override to change its behavior.
    """
    tc = self.typeCode
    return PTR32_TC <= tc <= PTR128_TC or tc == VOID_TC


  def isFuncOrVoid(self) -> bool:
    tc = self.typeCode
    return tc == FUNC_TC or tc == VOID_TC


  def isFuncSigOrVoid(self) -> bool:
    tc = self.typeCode
    return tc == FUNC_SIG_TC or tc == VOID_TC


  def isRecordOrVoid(self) -> bool:
    tc = self.typeCode
    return tc in (STRUCT_TC, UNION_TC) or tc == VOID_TC


  def isStructOrVoid(self) -> bool:
    tc = self.typeCode
    return tc == STRUCT_TC or tc == VOID_TC


  def isUnionOrVoid(self) -> bool:
    tc = self.typeCode
    return tc == UNION_TC or tc == VOID_TC


  def isArrayOrVoid(self) -> bool:
    """This function is appropriately overridden by `ArrayT`."""
    if self.typeCode == VOID_TC:
      return True
    else:
      return self.isArray()


  def isInteger(self) -> bool:
    tc = self.typeCode
    return INT1_TC <= tc <= UINT128_TC


  def isSigned(self) -> bool:
    tc = self.typeCode
    return INT1_TC <= tc <= INT128_TC


  def isUnsigned(self) -> bool:
    tc = self.typeCode
    return UINT8_TC <= tc <= UINT128_TC


  def isFloat(self) -> bool:
    tc = self.typeCode
    return FLOAT16_TC <= tc <= FLOAT128_TC


  def isNumeric(self) -> bool:
    """Returns bool(isInteger() or isFloat())."""
    tc = self.typeCode
    return INT1_TC <= tc <= FLOAT128_TC


  def isPointer(self) -> bool:
    """Should return True for any type that the
    points-to analysis needs to track the pointees of.
    Currently only user-defined pointers and array of pointers
    are considered a pointer here.
    Override to change its behavior.
    """
    tc = self.typeCode
    return PTR32_TC <= tc <= PTR128_TC


  def isFunc(self) -> bool:
    tc = self.typeCode
    return tc == FUNC_TC


  def isFuncSig(self) -> bool:
    tc = self.typeCode
    return tc == FUNC_SIG_TC


  def isRecord(self) -> bool:
    tc = self.typeCode
    return tc in (STRUCT_TC, UNION_TC)


  def isStruct(self) -> bool:
    tc = self.typeCode
    return tc == STRUCT_TC


  def isUnion(self) -> bool:
    tc = self.typeCode
    return tc == UNION_TC


  def isArray(self) -> bool:
    """This function is appropriately overridden by `ArrayT`."""
    return False


  def isVoid(self) -> bool:
    return self.typeCode == VOID_TC


  def isEqualOrVoid(self, other: 'Type') -> bool:
    """Adds the logic of Void being equal to any Type."""
    if self is other: return True
    if not isinstance(other, Type):
      raise NotImplementedError()
    if VOID_TC in (self.typeCode, other.typeCode):
      return True # the void equal case
    return self == other  # for normal cases (invokes __eq__)


  def getPointeeType(self) -> 'Type':
    raise NotImplementedError(f"{self}")


  def getFormalStr(self) -> FormalStrT:
    if self.isNumeric():
      fstr = "Num"
    elif self.isPointer():
      fstr = "Ptr"
    elif self.isRecord():
      fstr = "Record"
    else:
      fstr = "Void"  # FIXME: to avoid error
      # assert False, f"{self}"
    return fstr


  #@functools.lru_cache(256)
  def getNamesOfType(self,
      givenType: Opt['Type'],
      prefix: str,  # the name of the array
      bySpan: bool = False,
  ) -> Set['VarNameInfo']:
    """Returns the fully qualified (with prefix) member names
    if the type is a record, or an array with record elements.
    This method must be appropriately overridden
    by ArrayT and RecordT classes.

    In the default implementation it returns the prefix as it is
    if the givenType is None or matches this type or else
    an empty set.
    """
    if givenType is None or self.isEqualOrVoid(givenType):
      return {VarNameInfo(prefix, self, False, bySpan)}
    else:
      return set()


  def castValue(self, value: NumericT) -> NumericT:
    # FIXME: make it more precise
    if isinstance(self, Ptr):
      return value

    assert self.isNumeric(), f"{self}"
    assert isinstance(value, (int, float))

    selfIsInteger = self.isInteger()
    selfIsFloat = self.isFloat()
    valueIsInteger = isinstance(value, int)
    valueIsFloat = isinstance(value, float)

    if selfIsInteger and valueIsInteger:
      if self.isInRange(value):
        return value
      else:
        return self.getMaxValue()  # FIXME: undefined behavior?
    elif selfIsInteger and valueIsFloat:
      try:
        return int(value)
      except:  # possible if +inf/-inf
        return 0  # undefined behavior
    elif selfIsFloat and valueIsInteger:
      return float(value)
    elif selfIsFloat and valueIsFloat:
      return float(value)


  def isInRange(self, value: NumericT):
    assert self.isNumeric()
    assert isinstance(value, (int, float))
    return self.getMinValue() <= value <= self.getMaxValue()


  def getMinValue(self):
    assert self.isNumeric()
    minValue = 0
    tc = self.typeCode

    if tc == INT1_TC:
      minValue = 0
    elif tc == INT8_TC:
      minValue = -(1 << (8 - 1))
    elif tc == INT16_TC:
      minValue = -(1 << (16 - 1))
    elif tc == INT32_TC:
      minValue = -(1 << (32 - 1))
    elif tc == INT64_TC:
      minValue = -(1 << (64 - 1))
    elif tc == INT128_TC:
      minValue = -(1 << (128 - 1))
    elif tc == UINT8_TC:
      minValue = 0
    elif tc == UINT16_TC:
      minValue = 0
    elif tc == UINT32_TC:
      minValue = 0
    elif tc == UINT64_TC:
      minValue = 0
    elif tc == UINT128_TC:
      minValue = 0
    elif tc == FLOAT16_TC:
      minValue = - self.getMaxValue()
    elif tc == FLOAT32_TC:
      minValue = - self.getMaxValue()
    elif tc == FLOAT64_TC:
      minValue = - self.getMaxValue()
    elif tc == FLOAT80_TC:
      minValue = - self.getMaxValue()
    elif tc == FLOAT128_TC:
      minValue = - self.getMaxValue()
    elif tc in (PTR32_TC, PTR64_TC, PTR128_TC):
      minValue = 0

    return minValue


  def getMaxValue(self):
    assert self.isNumeric()
    maxValue = 0
    tc = self.typeCode

    if tc == INT1_TC:
      maxValue = 1
    elif tc == INT8_TC:
      maxValue = (1 << (8 - 1)) - 1
    elif tc == INT16_TC:
      maxValue = (1 << (16 - 1)) - 1
    elif tc == INT32_TC:
      maxValue = (1 << (32 - 1)) - 1
    elif tc == INT64_TC:
      maxValue = (1 << (64 - 1)) - 1
    elif tc == INT128_TC:
      maxValue = (1 << (128 - 1)) - 1
    elif tc == UINT8_TC:
      maxValue = (1 << 8) - 1
    elif tc == UINT16_TC:
      maxValue = (1 << 16) - 1
    elif tc == UINT32_TC:
      maxValue = (1 << 32) - 1
    elif tc == UINT64_TC:
      maxValue = (1 << 64) - 1
    elif tc == UINT128_TC:
      maxValue = (1 << 128) - 1
    elif tc == FLOAT16_TC:
      maxValue = 65504
    elif tc == FLOAT32_TC:
      maxValue = 3.4028234664e+38   # approximate
    elif tc == FLOAT64_TC:
      maxValue = 1.797693e+308      # approximate
    elif tc == FLOAT80_TC:
      maxValue = 1.797693e+308      # approximate (FIXME: same as 64 bit)
    elif tc == FLOAT128_TC:
      maxValue = 1.18973149535723176502e+4932  # approximate (FIXME: confirm it)
    elif tc == PTR32_TC:
      maxValue = (1 << 32) - 1
    elif tc == PTR64_TC:
      maxValue = (1 << 64) - 1
    elif tc == PTR128_TC:
      maxValue = (1 << 128) - 1

    return maxValue


  def hasKnownBitSize(self) -> bool:
    # Types that don't have a constant size
    # should return False
    return True


  def sizeInBytes(self) -> int:
    return self.sizeInBits() >> 3


  def sizeInBits(self) -> int:
    """Returns size in bits for builtin types.
    For other types, see respective overrides of this method.
    """
    size = 0
    tc = self.typeCode

    if tc == INT1_TC:
      size = 1
    elif tc == INT8_TC:
      size = 8
    elif tc == INT16_TC:
      size = 16
    elif tc == INT32_TC:
      size = 32
    elif tc == INT64_TC:
      size = 64
    elif tc == INT128_TC:
      size = 128
    elif tc == UINT8_TC:
      size = 8
    elif tc == UINT16_TC:
      size = 16
    elif tc == UINT32_TC:
      size = 32
    elif tc == UINT64_TC:
      size = 64
    elif tc == UINT128_TC:
      size = 128
    elif tc == FLOAT16_TC:
      size = 16
    elif tc == FLOAT32_TC:
      size = 32
    elif tc == FLOAT64_TC:
      size = 64
    elif tc == FLOAT80_TC:
      size = 80
    elif tc == FLOAT128_TC:
      size = 128
    elif tc == PTR32_TC:
      size = 32
    elif tc == PTR64_TC:
      size = 64
    elif tc == PTR128_TC:
      size = 128

    return size


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, Type):
      return NotImplemented
    if VOID_TC in (self.typeCode, other.typeCode): #special case
      return True # Void matches all types
    return self.typeCode == other.typeCode


  def isEqual(self,
      other: 'Type'
  ) -> bool:
    equal = True
    if not isinstance(other, Type):
      if LS: LOG.debug("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.typeCode == other.typeCode:
      if LS: LOG.debug("TypeCodesDiffer: %s, %s", self.typeCode, other.typeCode)
      equal = False

    if not equal and LS:
      LOG.debug("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self) -> int:
    return hash(self.typeCode)


  def __str__(self) -> str:
    ss = ""
    tc = self.typeCode

    if tc == VOID_TC:
      ss = "VOID"
    elif tc == INT1_TC:
      ss = "INT1"
    elif tc == INT8_TC:
      ss = "INT8"
    elif tc == INT16_TC:
      ss = "INT16"
    elif tc == INT32_TC:
      ss = "INT32"
    elif tc == INT64_TC:
      ss = "INT64"
    elif tc == INT128_TC:
      ss = "INT128"
    elif tc == UINT8_TC:
      ss = "UINT8"
    elif tc == UINT16_TC:
      ss = "UINT16"
    elif tc == UINT32_TC:
      ss = "UINT32"
    elif tc == UINT64_TC:
      ss = "UINT64"
    elif tc == UINT128_TC:
      ss = "UINT128"
    elif tc == FLOAT16_TC:
      ss = "FLOAT16"
    elif tc == FLOAT32_TC:
      ss = "FLOAT32"
    elif tc == FLOAT64_TC:
      ss = "FLOAT64"
    elif tc == FLOAT80_TC:
      ss = "FLOAT80"
    elif tc == FLOAT128_TC:
      ss = "FLOAT128"
    elif tc == PTR_TC:
      ss = "PTR"
    elif tc == FUNC_TC:
      ss = "FUNC"
    elif tc == FUNC_SIG_TC:
      ss = "FUNC_SIG"
    elif tc == STRUCT_TC:
      ss = "STRUCT"
    elif tc == UNION_TC:
      ss = "UNION"

    return ss


  def __repr__(self) -> str:
    """It expects the eval()uator to import this module as:
       import span.ir.types as types
    """
    tc = self.typeCode

    if tc == VOID_TC:
      return "types.Void"
    elif tc == INT1_TC:
      return "types.Int1"
    elif tc == INT8_TC:
      return "types.Int8"
    elif tc == INT16_TC:
      return "types.Int16"
    elif tc == INT32_TC:
      return "types.Int32"
    elif tc == INT64_TC:
      return "types.Int64"
    elif tc == INT128_TC:
      return "types.Int128"
    elif tc == UINT8_TC:
      return "types.UInt8"
    elif tc == UINT16_TC:
      return "types.UInt16"
    elif tc == UINT32_TC:
      return "types.UInt32"
    elif tc == UINT64_TC:
      return "types.UInt64"
    elif tc == UINT128_TC:
      return "types.UInt128"
    elif tc == FLOAT16_TC:
      return "types.Float16"
    elif tc == FLOAT32_TC:
      return "types.Float32"
    elif tc == FLOAT64_TC:
      return "types.Float64"
    elif tc == FLOAT80_TC:
      return "types.Float80"
    elif tc == FLOAT128_TC:
      return "types.Float128"
    # for the rest override the __repr__() function
    #   elif tc == PTR_TC:        ss = "PTR"
    #   elif tc == FUNC_TC:       ss = "FUNC"
    #   elif tc == FUNC_SIG_TC:   ss = "FUNC_SIG"
    #   elif tc == STRUCT_TC:     ss = "STRUCT"
    #   elif tc == UNION_TC:      ss = "UNION"

    raise ValueError(f"{tc}")


class ConstructT(Type):
  """Represents IR constructs like functions, structs and unions
  which can be their own types."""

  __slots__ : List[str] = []

  def __init__(self, typeCode: TypeCodeT):
    super().__init__(typeCode)



################################################
# BOUND START: basic_type_objects
################################################

Void = Type(VOID_TC)

Int1 = Type(INT1_TC)
Int8 = Type(INT8_TC)
Int16 = Type(INT16_TC)
Int32 = Type(INT32_TC)
Int64 = Type(INT64_TC)
Int128 = Type(INT128_TC)

UInt8 = Type(UINT8_TC)
UInt16 = Type(UINT16_TC)
UInt32 = Type(UINT32_TC)
UInt64 = Type(UINT64_TC)
UInt128 = Type(UINT128_TC)

Float16 = Type(FLOAT16_TC)
Float32 = Type(FLOAT32_TC)
Float64 = Type(FLOAT64_TC)
Float80 = Type(FLOAT80_TC)
Float128 = Type(FLOAT128_TC)

# special_abstract_types
NumericAny = Type(NUMERIC_TC)
IntegerAny = Type(INTEGER_TC)
PointerAny = Type(POINTER_TC)

# for convenience
Int = Int32
Char = UInt8
Float = Float32
Double = Float64


################################################
# BOUND END  : basic_type_objects
################################################

class VarNameInfo:  # IMPORTANT: don't change its position
  """Holds the information of all names,
  including compound names
  like x.y.z, x[].y.z etc. (which don't have any pointer dereference)
  The name of an object cannot contain a pointer dereference.
  """

  __slots__ : List[str] = ["name", "type", "hasArray", "bySpan", "id", "scope", "funcName"]

  def __init__(self,
      name: VarNameT,
      t: Type,
      hasArray: bool = False,
      bySpan: bool = False,  # True if name generated by SPAN
  ) -> None:
    self.name: VarNameT = name
    self.type: Type = t
    self.hasArray: bool = hasArray
    self.bySpan = bySpan

    self.id: int = 0
    """A unique id of this variable."""
    self.scope: consts.VarScope = consts.VarScope.LOCAL
    """Scope of the variable."""
    self.funcName: Opt[FuncNameT] = None
    """If local, which function does it belong to."""


  def mayUpdate(self) -> bool:
    """Should this name be `may` updated?
    Write logic to return a boolean value.
    Currently arrays and heap locations (represented as arrays)
    are the only possibilities."""
    return self.hasArray


  def __hash__(self) -> int:
    return hash(self.name)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, VarNameInfo):
      return NotImplemented
    equal = True
    if not self.name == other.name:
      equal = False
    elif not self.type == other.type:
      equal = False
    elif not self.hasArray == other.hasArray:
      equal = False
    elif not self.bySpan == other.bySpan:
      equal = False
    return equal


  def isEqual(self, other: 'VarNameInfo') -> bool:
    equal = True
    if not isinstance(other, VarNameInfo):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.name == other.name:
      if LS: LOG.error("NamesDiffer: %s, %s", self.name, other.name)
      equal = False
    if not self.type.isEqual(other.type):
      equal = False
    if not self.hasArray == other.hasArray:
      if LS: LOG.error("HasArrayDiffers: %s, %s", self.hasArray, other.hasArray)
      equal = False
    if not self.bySpan == other.bySpan:
      if LS: LOG.error("BySpanDiffers: %s, %s", self.bySpan, other.bySpan)
      equal = False

    if not equal and LS:
      LOG.debug("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __str__(self):
    hasArray = "HasArray" if self.hasArray else "NoArray"
    bySpan = "BySpan" if self.bySpan else "NotBySpan"
    return f"({self.name} : ({self.type}, {hasArray}, {bySpan}))"


  def __repr__(self):
    """It expects eval()uator to import this class as follows:
      from span.ir.types import VarNameInfo
    """
    return f"VarNameInfo({repr(self.name)}, {repr(self.type)}, " \
           f"{repr(self.hasArray)}, {repr(self.bySpan)})"



################################################
# BOUND START: compound_types
################################################

class Ptr(Type):
  """Concrete Pointer type.

  Instantiate this class to denote pointer types.
  E.g. types.Ptr(types.Char, 2) is a ptr-to-ptr-to-char
  """

  __slots__ : List[str] = ["to", "indlev"]

  def __init__(self,
      to: Type,
      indlev: int = 1
  ) -> None:
    super().__init__(PTR_TC)
    if indlev < 1: raise ValueError(f"{indlev}: {PTR_INDLEV_INVALID}")
    self.to = to # type of the object pointed to
    self.indlev = indlev # indirection level to the object

    # correct a recursive pointer
    while isinstance(self.to, Ptr):
      self.indlev += 1
      self.to = self.to.to


  def isEqualOrVoid(self, other: 'Type') -> bool:
    if self is other: return True
    if not isinstance(other, Type):
      raise NotImplementedError()
    if VOID_TC in (self.typeCode, other.typeCode):
      return True # the void equal case
    if not isinstance(other, Ptr):
      return False
    if not self.indlev == other.indlev:
      return False
    return self.to.isEqualOrVoid(other.to)


  def getPointeeType(self) -> Type:
    if self.indlev > 1:
      return Ptr(self.to, self.indlev - 1)
    return self.to


  def getPointeeTypeFinal(self) -> Type:
    """E.g. if its ptr-to ptr-to int, it returns int."""
    return self.to


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, Ptr):
      return NotImplemented
    equal = True
    if not self.typeCode == other.typeCode:
      equal = False
    elif not self.indlev == other.indlev:
      equal = False
    elif isinstance(self.to, RecordT):  # special case to avoid infinite recursion
      # special case to avoid infinite recursion when
      # a record contains a pointer to itself (or indirectly to itself)
      if not isinstance(other.to, RecordT) or not self.to.name == other.to.name:
        equal = False
    elif not self.to == other.to:  # use of elif is correct
      equal = False
    return equal


  def isEqual(self, other: 'Type') -> bool:
    equal = True
    if not isinstance(other, Ptr):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.typeCode == other.typeCode:
      if LS: LOG.error("TypeCodesDiffer: %s, %s", self.typeCode, other.typeCode)
      equal = False
    if not self.indlev == other.indlev:
      if LS: LOG.error("IndLevsDiffer: %s, %s", self.indlev, other.indlev)
      equal = False
    if isinstance(self.to, RecordT):
      # special case to avoid infinite recursion when
      # a record contains a pointer to itself (or indirectly to itself)
      if not isinstance(other.to, RecordT) or not self.to.name == other.to.name:
        if LS: LOG.error("DestTypesDiffer: %s, %s", self.to, other.to)
        equal = False
    elif not self.to.isEqual(other.to):  # use of elif is correct
      if LS: LOG.error("DestTypesDiffer: %s, %s", self.to, other.to)
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    return hash((self.typeCode, self.to, self.indlev))


  def __str__(self):
    return f"Ptr({str(self.to)}, {self.indlev})"


  def __repr__(self):
    """It expects the eval()uator to import this module as:
       import span.ir.types as types
    """
    if isinstance(self.to, RecordT):  # special case
      return f"types.Ptr({str(self.to)}, {self.indlev})"
    else:
      return f"types.Ptr({repr(self.to)}, {self.indlev})"


class ArrayT(Type):
  """A superclass for all arrays.
  Not to be instantiated (note the suffix `T`)

  The array type is a special type. It is special
  in the sense that, an array of Int32 is also
  considered to be of type Int32.
  (This conforms well with the over-approximation
  of the arrays done in most analyses.)
  """

  __slots__ : List[str] = ["of"]


  def __init__(self,
      of: Type,
      typeCode: TypeCodeT = ARR_TC,
  ) -> None:
    super().__init__(typeCode)
    self.of = of


  def isEqualOrVoid(self, other: 'Type') -> bool:
    if self is other: return True
    if not isinstance(other, Type):
      raise NotImplementedError()
    if VOID_TC in (self.typeCode, other.typeCode):
      return True # the void equal case
    if not isinstance(other, ArrayT):
      return False
    return self.of.isEqualOrVoid(other.of)


  #@functools.lru_cache(256)
  def getNamesOfType(self,
      givenType: Opt[Type],
      prefix: Opt[str] = None,  # the name of the array
      bySpan: bool = False,
  ) -> Set[VarNameInfo]:
    """If givenType is None, return all possible names.
    For e.g., if its an array of records.
    `prefix` should be the array name in the source or
    record element which is an array.
    """
    assert prefix, f"{givenType}, {prefix} and {self}"

    nameInfos = set()  # IMPORTANT
    of = self.of
    if isinstance(of, (ArrayT, RecordT)):
      nameInfos.update(of.getNamesOfType(givenType, prefix, bySpan=True))
      for nameInfo in nameInfos:
        nameInfo.hasArray = True  # the name has array!

    if givenType in (None, self, of) and prefix:
      nameInfos.add(VarNameInfo(prefix, self, True, bySpan))

    assert nameInfos is not None, f"{givenType}, {prefix} and {self}"
    return nameInfos  # must not return None


  def getElementTypeFinal(self) -> Type:
    """Returns the type of lowest elements this array holds.
    e.g. int a[4][5]; has leaf element of type int.
    """
    if isinstance(self.of, ArrayT):
      return self.of.getElementTypeFinal()
    return self.of


  def getElementType(self) -> Type:
    """Returns the type of the array element."""
    return self.of


  def isIntegerOrVoid(self) -> bool:
    return self.of.isIntegerOrVoid()


  def isSignedOrVoid(self) -> bool:
    return self.of.isSignedOrVoid()


  def isUnsignedOrVoid(self) -> bool:
    return self.of.isUnsignedOrVoid()


  def isFloatOrVoid(self) -> bool:
    return self.of.isFloatOrVoid()


  def isNumericOrVoid(self) -> bool:
    """Returns bool(isInteger() or isFloat())."""
    return self.of.isNumericOrVoid()


  def isPointerOrVoid(self) -> bool:
    """Should return True for any type that the
    points-to analysis needs to track the pointees of.
    Currently only user-defined pointers and array of pointers
    are considered a pointer here.
    Override to change its behavior.
    """
    return self.of.isPointerOrVoid()


  def isFuncOrVoid(self) -> bool:
    return self.of.isFuncOrVoid()


  def isFuncSigOrVoid(self) -> bool:
    return self.of.isFuncSigOrVoid()


  def isRecordOrVoid(self) -> bool:
    return self.of.isRecordOrVoid()


  def isStructOrVoid(self) -> bool:
    return self.of.isStructOrVoid()


  def isUnionOrVoid(self) -> bool:
    return self.of.isUnionOrVoid()


  def isInteger(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isInteger()


  def isUnsigned(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isUnsigned()


  def isFloat(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isFloat()


  def isNumeric(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isNumeric()


  def isPointer(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isPointer()


  def isFunc(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isFunc()


  def isRecord(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isRecord()


  def isStruct(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isStruct()


  def isUnion(self) -> bool:
    """Checks the property of the array element."""
    return self.of.isUnion()


  def isArray(self):
    """Checks the property of the array element."""
    return True


  def getPointeeType(self) -> Type:
    assert self.isPointer(), f"{self}"
    return self.of.getPointeeType()


  def sizeInBits(self) -> int:
    # Only specializations of ArrayT should
    # implement this method.
    raise NotImplementedError()


  def __str__(self):
    return NotImplemented


  def __repr__(self):
    return NotImplemented


class ConstSizeArray(ArrayT):
  """Concrete array type.

  Instantiate this class to denote array types.
  E.g. a 2x3 array of chars is,
    types.ConstSizeArray(types.ConstSizeArray(types.Char, 3), 2)
  """

  __slots__ : List[str] = ["size"]

  def __init__(self,
      of: Type,
      size: int,
  ) -> None:
    super().__init__(of=of, typeCode=CONST_ARR_TC)
    self.size = size


  def hasKnownBitSize(self) -> bool:
    return True


  def sizeInBits(self) -> int:
    """Returns size in bits of this array."""
    size = self.of.sizeInBits()
    size = self.size * size
    return size


  def isEqualOrVoid(self, other: 'Type') -> bool:
    if self is other: return True
    if not isinstance(other, Type):
      raise NotImplementedError()
    if VOID_TC in (self.typeCode, other.typeCode):
      return True # the void equal case
    if not isinstance(other, ConstSizeArray):
      return False
    if not self.size == other.size:
      return False
    return self.of.isEqualOrVoid(other.of)


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, ConstSizeArray):
      return NotImplemented
    equal = True
    if not self.typeCode == other.typeCode:
      equal = False
    elif not self.size == other.size:
      equal = False
    elif not self.of == other.of:
      equal = False
    return equal


  def isEqual(self,
      other: 'Type'
  ) -> bool:
    equal = True
    if not isinstance(other, ConstSizeArray):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.typeCode == other.typeCode:
      if LS: LOG.debug("TypeCodesDiffer: %s, %s", self.typeCode, other.typeCode)
      equal = False
    if not self.size == other.size:
      if LS: LOG.debug("SizesDiffer: %s, %s", self.size, other.size)
      equal = False
    if not self.of.isEqual(other.of):
      if LS: LOG.debug("ElementTypesDiffer: %s, %s", self.of, other.of)
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    return hash((self.typeCode, self.of, self.size))


  def __str__(self):
    return self.__repr__()


  def __repr__(self):
    """It expects the eval()uator to import this module as:
       import span.ir.types as types
    """
    return f"types.ConstSizeArray({repr(self.of)}, {self.size})"


class VarArray(ArrayT):
  """an array with variable size: e.g. int arr[x*20+y];"""

  __slots__ : List[str] = []

  def __init__(self,
      of: Type,
  ) -> None:
    super().__init__(of=of, typeCode=VAR_ARR_TC)


  def hasKnownBitSize(self) -> bool:
    return False


  def sizeInBits(self) -> int:
    raise NotImplementedError(f"{self}")  # no size of a VarArray !!


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, VarArray):
      return NotImplemented
    equal = True
    if not self.typeCode == other.typeCode:
      equal = False
    elif not self.of == other.of:
      equal = False
    return equal


  def isEqual(self,
      other: 'Type'
  ) -> bool:
    equal = True
    if not isinstance(other, VarArray):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.typeCode == other.typeCode:
      if LS: LOG.error("TypeCodesDiffer: %s, %s", self.typeCode, other.typeCode)
      equal = False
    if not self.of.isEqual(other.of):
      if LS: LOG.error("ElementTypesDiffer: %s, %s", self.of, other.of)
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    return hash(self.of) * hash(self.typeCode)


  def __str__(self):
    return self.__repr__()


  def __repr__(self):
    """It expects the eval()uator to import this module as:
       import span.ir.types as types
    """
    return f"VarArray({repr(self.of)})"


class IncompleteArray(ArrayT):
  """An array with no size: e.g. int arr[];"""

  __slots__ : List[str] = []

  def __init__(self,
      of: Type,
  ) -> None:
    super().__init__(of=of, typeCode=INCPL_ARR_TC)
    self.of = of


  def hasKnownBitSize(self) -> bool:
    return False


  def sizeInBits(self) -> int:
    raise NotImplementedError()  # no size of an IncompleteArray !!


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, IncompleteArray):
      return NotImplemented
    equal = True
    if not self.typeCode == other.typeCode:
      equal = False
    elif not self.of == other.of:
      equal = False
    return equal


  def isEqual(self,
      other: 'Type'
  ) -> bool:
    equal = True
    if not isinstance(other, IncompleteArray):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.typeCode == other.typeCode:
      if LS: LOG.error("TypeCodesDiffer: %s, %s", self.typeCode, other.typeCode)
      equal = False
    if not self.of.isEqual(other.of):
      if LS: LOG.error("ElementTypesDiffer: %s, %s", self.of, other.of)
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    return hash(self.of) + hash(self.typeCode)


  def __str__(self):
    return f"IncompleteArray({self.of})"


  def __repr__(self):
    """It expects the eval()uator to import this module as:
       import span.ir.types as types
    """
    return f"types.IncompleteArray({repr(self.of)})"


class RecordT(ConstructT):
  """A record type (base class to Struct and Union types)
  Anonymous records are also given a unique name."""

  __slots__ : List[str] = ["name", "members", "info"]

  def __init__(self,
      name: RecordNameT,
      members: Opt[List[Tuple[MemberNameT, Type]]],
      info: Opt[Info],
      typeCode: TypeCodeT,
  ) -> None:
    super().__init__(typeCode)
    self.name = name
    self.members = members if members else []
    self.info = info


  def getMemberType(self,
      memberName: MemberNameT
  ) -> Type:
    if not self.members:
      raise ValueError(f"{memberName} not present in {self}")
    for mName, fType in self.members:
      if mName == memberName:
        return fType
    raise ValueError(f"{memberName} not present in {self}")


  #@functools.lru_cache(256)
  def getNamesOfType(self,
      givenType: Opt[Type],
      prefix: Opt[str] = None,
      bySpan: bool = False,
  ) -> Set[VarNameInfo]:
    """A wrapper function for _getNamesOfType
    to have control over an external `prefix`.
    It caches the result."""
    nameInfos = self._getNamesOfType(givenType)

    prefixedNameInfos = nameInfos
    if prefix:
      prefixedNameInfos = set()
      for nameInfo in nameInfos:
        prefixedName = f"{prefix}.{nameInfo.name}"
        # IMPORTANT: create new NameInfo object
        prefixedNameInfo = VarNameInfo(prefixedName, nameInfo.type,
                                       nameInfo.hasArray, bySpan=True)
        prefixedNameInfos.add(prefixedNameInfo)

    if prefix and givenType in (None, self):
      prefixedNameInfos.add(VarNameInfo(prefix, self, False, bySpan))
    return prefixedNameInfos


  #@functools.lru_cache(64)
  def _getNamesOfType(self,
      givenType: Opt[Type],
  ) -> Set[VarNameInfo]:
    """Set of member names of the given type (recursive).
    This function caches the results.
    This method is private.
    """
    memberInfos: Set[VarNameInfo] = set()
    assert self.members is not None, f"{self}"
    for memberName, memberType in self.members:
      if givenType is None:  # then add all possible names
        memberInfos.add(VarNameInfo(memberName, memberType))
        if isinstance(memberType, (ArrayT, RecordT)):  # search deeper
          memberInfos.update(memberType.getNamesOfType(None, memberName))
      elif givenType == memberType: # add the current member
        memberInfos.add(VarNameInfo(memberName, memberType))
      elif isinstance(memberType, (ArrayT, RecordT)):  # search deeper
        memberInfos.update(memberType.getNamesOfType(givenType, memberName))

    assert memberInfos is not None, f"{memberInfos}: {self}"
    return memberInfos  # Should never be None


  def __hash__(self):
    return hash(self.name)


  def __str__(self):
    if self.typeCode == STRUCT_TC:
      return f"Struct('{self.name}')"
    elif self.typeCode == UNION_TC:
      return f"Union('{self.name}')"
    raise ValueError(f"Record is neither a struct nor a union: {self}")


class Struct(RecordT):
  """A structure type.
  Anonymous structs are also given a unique name."""

  __slots__ : List[str] = []

  def __init__(self,
      name: StructNameT,
      members: Opt[List[Tuple[MemberNameT, Type]]] = None,
      info: Opt[Info] = None,
  ) -> None:
    super().__init__(name, members, info, STRUCT_TC)
    self.name = name
    self.members = members


  def sizeInBits(self):
    """Returns size in bits of this structure."""
    size = 0

    for memberName, memberType in self.members:
      assert memberType.hasKnownBitSize()
      size += memberType.sizeInBits()
    return size


  def isEqualOrVoid(self, other: 'Type') -> bool:
    if self is other: return True
    if not isinstance(other, Type):
      raise NotImplementedError()
    if VOID_TC in (self.typeCode, other.typeCode):
      return True # the void equal case
    if not isinstance(other, Struct):
      return False
    if not self.typeCode == other.typeCode:
      return False
    if not self.name == other.name:
      return False
    if not len(self.members) == len(other.members):
      return False
    for selfMem, otherMem in zip(self.members, other.members):
      if not selfMem[0] == otherMem[0] or\
          not selfMem[1].isEqualOrVoid(otherMem[1]): # same name and type
        return False
    else:
      return True


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, Struct):
      return NotImplemented
    equal = True
    if not self.typeCode == other.typeCode:
      equal = False
    elif not self.name == other.name:
      equal = False
    elif not self.members == other.members:
      equal = False
    return equal


  def isEqual(self, other: 'Type') -> bool:
    equal = True
    if not isinstance(other, Struct):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.typeCode == other.typeCode:
      if LS: LOG.error("TypeCodesDiffer: %s, %s", self.typeCode, other.typeCode)
      equal = False
    if not self.name == other.name:
      if LS: LOG.error("NamesDiffer: %s, %s", self.name, other.name)
      equal = False
    assert self.members is not None\
           and other.members is not None, f"{self}, {other}"
    if not len(self.members) == len(other.members):
      if LS: LOG.error("NumOfMembersDiffer: %s, %s",
                       len(self.members), len(other.members))
      equal = False
    else:
      for i in range(len(self.members)):
        if not self.members[i][0] == other.members[i][0]:
          if LS: LOG.error("MemberNamesDiffer: %s, %s",
                           self.members[i][0], other.members[i][0])
          equal = False
        if not self.members[i][1].isEqual(other.members[i][1]):
          if LS: LOG.error("MemberTypesDiffer: %s, %s",
                           self.members[i][1], other.members[i][1])
          equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    return hash(self.name) + hash(self.typeCode)


  def __str__(self):
    return f"Struct('{self.name}')"


  def __repr__(self):
    """It expects the eval()uator to import this module as:
       import span.ir.types as types
       from span.ir.types import Loc, Info
    """
    return f"types.Struct({repr(self.name)}, " \
           f"{repr(self.members)}, {repr(self.info)})"


class Union(RecordT):
  """A union type.
  Anonymous unions are also given a unique name."""

  __slots__ : List[str] = []

  def __init__(self,
      name: UnionNameT,
      members: Opt[List[Tuple[MemberNameT, Type]]] = None,
      info: Opt[Info] = None,
  ) -> None:
    super().__init__(name, members, info, UNION_TC)


  def sizeInBits(self) -> int:
    """Returns size in bits of this union."""
    size = 0
    assert self.members, f"{self}"
    for memberName, memberType in self.members:
      assert memberType.hasKnownBitSize()
      memberBitSize = memberType.sizeInBits()
      size = memberBitSize if size < memberBitSize else size
    return size


  def isEqualOrVoid(self, other: 'Type') -> bool:
    if self is other: return True
    if not isinstance(other, Type):
      raise NotImplementedError()
    if VOID_TC in (self.typeCode, other.typeCode):
      return True # the void equal case
    if not isinstance(other, Union):
      return False
    if not self.typeCode == other.typeCode:
      return False
    if not self.name == other.name:
      return False
    if not len(self.members) == len(other.members):
      return False
    for selfMem, otherMem in zip(self.members, other.members):
      if not selfMem[0] == otherMem[0] or \
          not selfMem[1].isEqualOrVoid(otherMem[1]): # same name and type
        return False
    else:
      return True


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, Union):
      return NotImplemented
    equal = True
    if not self.typeCode == other.typeCode:
      equal = False
    elif not self.members == other.members:
      equal = False
    elif not self.name == other.name:
      equal = False
    return equal


  def isEqual(self,
      other: 'Type'
  ) -> bool:
    equal = True
    if not isinstance(other, Union):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.typeCode == other.typeCode:
      if LS: LOG.error("TypeCodesDiffer: %s, %s", self.typeCode, other.typeCode)
      equal = False
    if not self.name == other.name:
      if LS: LOG.error("NamesDiffer: %s, %s", self.name, other.name)
      equal = False
    assert self.members and other.members, f"{self}, {other}"
    if not len(self.members) == len(other.members):
      if LS: LOG.error("NumOfMembersDiffer: %s, %s",
                       len(self.members), len(other.members))
      equal = False
    else:
      for i in range(len(self.members)):
        if not self.members[i][0] == other.members[i][0]:
          if LS: LOG.error("MemberNamesDiffer: %s, %s",
                           self.members[i][0], other.members[i][0])
          equal = False
        if not self.members[i][1].isEqual(other.members[i][1]):
          if LS: LOG.error("MemberTypesDiffer: %s, %s",
                           self.members[i][1], other.members[i][1])
          equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    return hash(self.name) + hash(self.typeCode)


  def __str__(self):
    return f"Union('{self.name}')"


  def __repr__(self):
    """It expects the eval()uator to import this module as:
       import span.ir.types as types
       from span.ir.types import Loc, Info
    """
    return f"types.Union({repr(self.name)}, " \
           f"{repr(self.members)}, {repr(self.info)})"


class FuncSig(Type):
  """A function signature (necessary for function pointer types)."""

  __slots__ : List[str] = ["returnType", "paramTypes", "variadic"]

  def __init__(self,
      returnType: Type,
      paramTypes: Opt[List[Type]] = None,
      variadic: bool = False
  ) -> None:
    super().__init__(FUNC_SIG_TC)
    self.returnType = returnType
    self.paramTypes = paramTypes if paramTypes else []
    self.variadic = variadic


  def hasKnownBitSize(self) -> bool:
    return False


  def sizeInBits(self) -> int:
    raise NotImplementedError()  # no size of a FuncSig !!


  def isEqualOrVoid(self, other: 'Type') -> bool:
    if self is other: return True
    if not isinstance(other, Type):
      raise NotImplementedError()
    if VOID_TC in (self.typeCode, other.typeCode):
      return True # the void equal case
    if not isinstance(other, FuncSig):
      return False
    if not self.typeCode == other.typeCode:
      return False
    if isinstance(self.returnType, Ptr) and isinstance(other.returnType, Ptr):
      if not self.returnType.isEqualOrVoid(other.returnType):
        return False
    if not self.returnType == other.returnType: # void case not applicable here
      return False
    if not len(self.paramTypes) == len(other.paramTypes):
      return False
    for selfPType, otherPType in zip(self.paramTypes, other.paramTypes):
      if not selfPType.isEqualOrVoid(otherPType):
        return False
    else:
      return True


  def __eq__(self, other) -> bool:
    if self is other:
      return True
    if not isinstance(other, FuncSig):
      return NotImplemented
    equal = True
    if not self.typeCode == other.typeCode:
      equal = False
    elif not self.returnType == other.returnType:
      equal = False
    elif not self.paramTypes == other.paramTypes:
      equal = False
    elif not self.variadic == other.variadic:
      equal = False
    return equal


  def isEqual(self,
      other: 'Type'
  ) -> bool:
    equal = True
    if not isinstance(other, FuncSig):
      if LS: LOG.error("ObjectsIncomparable: %s, %s", self, other)
      return False
    if not self.typeCode == other.typeCode:
      if LS: LOG.error("TypeCodesDiffer: %s, %s", self.typeCode, other.typeCode)
      equal = False
    if not self.returnType.isEqual(other.returnType):
      if LS: LOG.error("ReturnTypesDiffer: %s, %s",
                       self.returnType, other.returnType)
      equal = False
    if not self.paramTypes == other.paramTypes:
      if LS: LOG.error("ParamTypesDiffer: %s, %s",
                       self.paramTypes, other.paramTypes)
      equal = False
    if not self.variadic == other.variadic:
      if LS: LOG.error("VariadicnessDiffers: %s, %s",
                       self.variadic, other.variadic)
      equal = False

    if not equal and LS:
      LOG.error("ObjectsDiffer: %s, %s", self, other)

    return equal


  def __hash__(self):
    hsh = hash(self.returnType)
    increment = 170
    for tp in self.paramTypes:
      hsh = hsh ^ (hash(tp) + increment)
      increment += 17
    return hsh


  def __str__(self):
    return self.__repr__()


  def __repr__(self):
    """It expects the eval()uator to import this module as:
       import span.ir.types as types
    """
    return f"types.FuncSig({repr(self.returnType)}, " \
           f"{repr(self.paramTypes)}, {repr(self.variadic)})"


################################################
# BOUND END  : compound_types
################################################

