#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Serialize/Deserialize SPAN IR to/from proto format"""

from typing import List, Tuple, Set

import span.ir.tunit as tunit
from span.ir import graph, constructs, instr, expr, types
from span.ir.types import BasicBlockIdT, EdgeLabelT, FalseEdge, TrueEdge, UnCondEdge

import span.ir.spanir_pb2 as pb  # protobuf generated module


class ProtoSerializer(types.AnyT):


  def __init__(self,
      tUnit: tunit.TranslationUnit
  ) -> None:
    """This class has methods to convert in-memory SPANIR
    to spanir.proto data structures for serialization"""
    self.tUnit = tUnit
    # set of ptr ids already in the proto format
    self.ptrTypeIds: Set[int] = set()


  def serializeTUnit(self,
      fileName: str
  ) -> None:
    """Convert tunit.TranslationUnit to a byte stream."""
    pbTUnit = pb.TranslationUnit()

    # START converting the data structure
    pbTUnit.name = self.tUnit.name
    pbTUnit.description = self.tUnit.description

    for varName, varType in self.tUnit.allVars.items():
      pbVar = pbTUnit.vars.add()
      pbVar.name = varName
      self.serializeType(varType, pbVar.type, pbTUnit)

    for func in self.tUnit.yieldFunctions():
      pbFunc = pbTUnit.functions.add()
      self.serializeFunc(func, pbFunc, pbTUnit)

    with open(fileName, "wb") as file:
      file.write(pbTUnit.SerializeToString())


  def serializeFunc(self,
      func: constructs.Func,
      pbFunc: pb.Function,
      pbTUnit: pb.TranslationUnit
  ) -> None:
    # Set Name
    pbFunc.name = func.name

    # Add function signature
    funcSig = pb.FuncSigType()
    self.serializeType(func.sig.returnType, funcSig.returnType, pbTUnit)
    for paramType in func.sig.paramTypes:
      pbType = funcSig.paramTypes.add()
      self.serializeType(paramType, pbType, pbTUnit)
    funcSig.variadic = func.sig.variadic

    # Add param names
    for paramName in func.paramNames:
      pbFunc.paramNames.add(paramName)

    # Add cfg
    for bbId, bb in func.basicBlocks.items():
      pbBB = pbFunc.cfg.basicBlocks.add()
      pbBB.id = bbId
      for insn in bb:
        pbInsn = pbBB.insns.add()
        self.serializeInstruction(insn, pbInsn, pbTUnit)

    for bbEdge in func.bbEdges:
      pbBbEdge = pbFunc.cfg.bbEdges.add()
      self.serializeBBEdge(bbEdge, pbBbEdge)


  def serializeType(self,
      varType: types.Type,
      pbType: pb.Type,
      pbTUnit: pb.TranslationUnit
  ) -> None:
    if varType.typeCode == types.VOID_TC:
      pbType.typeKind = pb.TY_VOID

    if varType.typeCode == types.INT1_TC:
      pbType.typeKind = pb.TY_INT1
    elif varType.typeCode == types.INT8_TC:
      pbType.typeKind = pb.TY_INT8
    elif varType.typeCode == types.INT16_TC:
      pbType.typeKind = pb.TY_INT16
    elif varType.typeCode == types.INT32_TC:
      pbType.typeKind = pb.TY_INT32
    elif varType.typeCode == types.INT64_TC:
      pbType.typeKind = pb.TY_INT64

    elif varType.typeCode == types.UINT8_TC:
      pbType.typeKind = pb.TY_UINT8
    elif varType.typeCode == types.UINT16_TC:
      pbType.typeKind = pb.TY_UINT16
    elif varType.typeCode == types.UINT32_TC:
      pbType.typeKind = pb.TY_UINT32
    elif varType.typeCode == types.UINT64_TC:
      pbType.typeKind = pb.TY_UINT64

    elif varType.typeCode == types.FLOAT16_TC:
      pbType.typeKind = pb.TY_FLOAT16
    elif varType.typeCode == types.FLOAT32_TC:
      pbType.typeKind = pb.TY_FLOAT32
    elif varType.typeCode == types.FLOAT64_TC:
      pbType.typeKind = pb.TY_FLOAT64
    elif varType.typeCode == types.FLOAT128_TC:
      pbType.typeKind = pb.TY_FLOAT128

    elif varType.typeCode == types.PTR_TC:
      pbType.typeKind = pb.TY_PTR
      # TODO: add the pointer object to basic types
      pbType.typeId = self.serializeTypePtr(varType, pbTUnit)

    else:
      assert False, f"Cannot handle type: {varType}."


  def serializeTypePtr(self,
      varType: types.Ptr,
      pbTUnit: pb.TranslationUnit
  ) -> int:
    ptrTypeId = id(varType)
    if ptrTypeId not in self.ptrTypeIds:  # add only the new objects
      pbPtrType = pbTUnit.ptrTypes.add()

      pbPtrType.id = ptrTypeId
      self.serializeType(varType.to, pbPtrType.to, pbTUnit)
      pbPtrType.indlev = varType.indlev

      self.ptrTypeIds.add(ptrTypeId)

    return ptrTypeId


  def serializeBBEdge(self,
      bbEdge: Tuple[BasicBlockIdT, BasicBlockIdT, EdgeLabelT],
      pbBbEdge: pb.BBEdge
  ) -> None:
    pbBbEdge.start = bbEdge[0]
    pbBbEdge.end = bbEdge[1]
    if bbEdge[2] == FalseEdge:
      pbBbEdge.edgeKind = pb.BBEdge.EdgeKind.FALSE_EDGE
    elif bbEdge[2] == TrueEdge:
      pbBbEdge.edgeKind = pb.BBEdge.EdgeKind.TRUE_EDGE
    elif bbEdge[2] == UnCondEdge:
      pbBbEdge.edgeKind = pb.BBEdge.EdgeKind.UNCOND_EDGE


  def serializeInstruction(self,
      insn: instr.InstrIT,
      pbInsn: pb.Instruction,
      pbTUnit: pb.TranslationUnit
  ) -> None:
    if isinstance(insn, instr.ReturnI):
      self.serializeExpression(insn.arg, pbInsn.returnInsn.arg, pbTUnit)
    elif isinstance(insn, instr.AssignI):
      self.serializeExpression(insn.lhs, pbInsn.assignInsn.lhs, pbTUnit)
      self.serializeExpression(insn.rhs, pbInsn.assignInsn.rhs, pbTUnit)
    elif isinstance(insn, instr.NopI):
      pbInsn.nopInsn.dummy = 0
    else:
      assert False, f"Instruction {insn} not handled"


  def serializeExpression(self,
      e: expr.ExprET,
      pbExpr: pb.Expression,
      pbTUnit: pb.TranslationUnit
  ) -> None:
    if isinstance(e, expr.LitE):
      pbExpr.litExpr.intVal = e.val
    elif isinstance(e, expr.VarE):
      pbExpr.varExpr.name = e.name
    else:
      assert False, f"Expr {e} not handled."


class ProtoDeserializer(types.AnyT):


  def __init__(self):
    """This class has methods to deserialize spanir.proto data structures
    to in-memory SPANIR data structures."""
    pass


  def deserializeTUnit(self, fileName: str) -> tunit.TranslationUnit:
    """Convert byte stream to tunit.TranslationUnit."""
    pbTUnit = pb.TranslationUnit()
    with open(fileName, "rb") as file:
      pbTUnit.ParseFromString(file.read())

    tUnit = tunit.TranslationUnit(pbTUnit.name, pbTUnit.description, {}, {})

    self.deserializeVars(pbTUnit, tUnit)
    self.deserializeConstructs(pbTUnit, tUnit)

    return tUnit


  def deserializeVars(self,
      pbTUnit: pb.TranslationUnit,
      tUnit: tunit.TranslationUnit
  ) -> None:
    for pbVar in pbTUnit.vars:
      tUnit.allVars[pbVar.name] = self.deserializeType(pbVar.type)


  def deserializeType(self,
      pbType: pb.Type) -> types.Type:
    pbTypeKind = pbType.typeKind
    if pbTypeKind == pb.TY_INT32:
      return types.Int32
    elif pbTypeKind == pb.TY_INT64:
      return types.Int64


  def deserializeConstructs(self,
      pbTUnit: pb.TranslationUnit,
      tUnit: tunit.TranslationUnit
  ) -> None:
    pass
