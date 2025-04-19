package spir

// This file defines the types of instructions in the SPAN IR.

type InsnId EntityId

// A 5 bit opcode is used to identify the instruction type.
// The instruction type decides the encoding used for the instruction.
type InstructionKind uint8

const InstructionKindPosition32 uint32 = 0x01F00000
const InstructionKindPosition64 uint64 = 0x01F0000000000000
const InstructionIdPosition32 uint64 = 0x3FFFFFFF
const InstructionIdPosition64 uint64 = 0x3FFFFFFF00000000

//go:generate stringer -type=InstructionKind
const (
	INSN_ASSIGN_SIMPLE         InstructionKind = 1 // var = simple_value; simple_value is variable or a constant
	INSN_ASSIGN_BINARY_OP      InstructionKind = 2 // var = simple_value BOP simple_value; Except array dereference.
	INSN_ASSIGN_UNARY_OP       InstructionKind = 3 // var = UOP simple_value; Except dereference.
	INSN_ASSIGN_RHS_DEREF      InstructionKind = 4 // var = *simple_value;
	INSN_ASSIGN_LHS_DEREF      InstructionKind = 5 // *var = simple_value;
	INSN_ASSIGN_RHS_ARRAY_EXPR InstructionKind = 6 // var = var[simple_value];
	INSN_ASSIGN_LHS_ARRAY_EXPR InstructionKind = 7 // var[simple_value] = simple_value;
	INSN_ASSIGN_CALL           InstructionKind = 8 // var = call_target(simple_value,...); A call_target is a function or a pointer to it
	INSN_ASSING_PHI            InstructionKind = 9 // var = phi(simple_value,...); A phi instruction is used to select a value from a set of values

	INSN_CALL         InstructionKind = 10 // call_target(simple_value,...);
	INSN_GOTO         InstructionKind = 11 // goto label;
	INSN_IF_THEN_ELSE InstructionKind = 12 // if (simple_value) goto labelTrue else goto labelFalse;
	INSN_LABEL        InstructionKind = 13 // A label is a target for a goto or if instruction

	INSN_RESERVE_14 InstructionKind = 14 // Reserved for use at runtime
	INSN_RESERVE_15 InstructionKind = 15 // Reserved for use at runtime
	INSN_RESERVE_16 InstructionKind = 16 // Reserved for use at runtime
	INSN_RESERVE_17 InstructionKind = 17 // Reserved for use at runtime
	INSN_RESERVE_18 InstructionKind = 18 // Reserved for use at runtime
	INSN_RESERVE_19 InstructionKind = 19 // Reserved for use at runtime
	INSN_RESERVE_20 InstructionKind = 20 // Reserved for use at runtime
	INSN_RESERVE_21 InstructionKind = 21 // Reserved for use at runtime
	INSN_RESERVE_22 InstructionKind = 22 // Reserved for use at runtime
	INSN_RESERVE_23 InstructionKind = 23 // Reserved for use at runtime
	INSN_RESERVE_24 InstructionKind = 24 // Reserved for use at runtime
	INSN_RESERVE_25 InstructionKind = 25 // Reserved for use at runtime
	INSN_RESERVE_26 InstructionKind = 26 // Reserved for use at runtime
	INSN_RESERVE_27 InstructionKind = 27 // Reserved for use at runtime
	INSN_RESERVE_28 InstructionKind = 28 // Reserved for use at runtime
	INSN_RESERVE_29 InstructionKind = 29 // Reserved for use at runtime
	INSN_RESERVE_30 InstructionKind = 30 // Reserved for use at runtime
	INSN_RESERVE_31 InstructionKind = 31 // Reserved for use at runtime
)

func positionInsnKindBits32(insnKind InstructionKind) uint32 {
	// InstructionKind is in bits 24..20 (5 bits)
	return uint32(insnKind) << 20
}

func positionInsnKindBits64(insnKind InstructionKind) uint64 {
	// InstructionKind is in bits 56..52 (5 bits)
	return uint64(positionInsnKindBits32(insnKind)) << 32
}

// Each instruction is at most 128 bits long.
// The instruction is divided into two halves, each 64 bits long.
// The first half contains the opcode and a possible 32 bit operand,
// and the second half contains an expression.
type Instruction struct {
	firstHalf  uint64
	secondHalf uint64
}

func NewInsnSimpleAssign(lhs EntityId, rhs EntityId) Instruction {
	insn := Instruction{}
	insn.firstHalf |= positionInsnKindBits64(INSN_ASSIGN_SIMPLE) | positionEntityKindBits64(ENTITY_INSTRUCTION)

	insn.firstHalf |= uint64(NewExprValue(lhs)) & 0x00000000FFFFFFFF
	insn.secondHalf |= uint64(NewExprValue(rhs))

	return insn
}

func NewInsnUnaryOpAssign(lhs EntityId, rhs EntityId, unaryExprKind ExpressionKind) Instruction {
	insn := Instruction{}
	insn.firstHalf |= positionInsnKindBits64(INSN_ASSIGN_UNARY_OP) | positionEntityKindBits64(ENTITY_INSTRUCTION)

	insn.firstHalf |= uint64(NewExprValue(lhs)) & 0x00000000FFFFFFFF
	insn.secondHalf |= uint64(NewExprUnaryOp(rhs, unaryExprKind))

	return insn
}

func NewInsnBinOpAssign(lhs EntityId, rhsOpr1 EntityId, rhsOpr2 EntityId,
	binExprKind ExpressionKind) Instruction {
	insn := Instruction{}
	insn.firstHalf |= positionInsnKindBits64(INSN_ASSIGN_BINARY_OP) | positionEntityKindBits64(ENTITY_INSTRUCTION)

	insn.firstHalf |= uint64(NewExprValue(lhs)) & 0x00000000FFFFFFFF
	insn.secondHalf |= uint64(NewExprBinaryOp(rhsOpr1, rhsOpr2, binExprKind))

	return insn
}

// Extra assosicated info with the instruction.
type InsnInfo struct {
	bbId BasicBlockId // The basic block to which the instruction belongs
}

func NewInsnInfo(bbId BasicBlockId) InsnInfo {
	return InsnInfo{
		bbId: bbId,
	}
}

func (i InsnInfo) BBId() BasicBlockId {
	return i.bbId
}

func (i Instruction) Id() InsnId {
	return InsnId((i.firstHalf & InstructionIdPosition64) >> 32)
}

func (i Instruction) InsnKind() InstructionKind {
	return InstructionKind((i.firstHalf >> 52) & 0x1F)
}
