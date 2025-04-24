package spir

// This file defines the types of instructions in the SPAN IR.

import "fmt"

type InsnId EntityId
type LabelId EntityId

// A 5 bit opcode is used to identify the instruction type.
// The instruction type decides the encoding used for the instruction.
type InsnKind uint8

const InsnKindMask5 uint8 = 0x1F
const InsnKindMask32 uint32 = 0x1F0_0000
const InsnKindShift32 uint32 = 20
const InsnKindMask64 uint64 = 0x1F0_0000_0000_0000
const InsnKindShift64 uint64 = 52
const InsnIdMask32 uint64 = 0x3FFF_FFFF
const InsnIdShift32 uint32 = 0
const InsnIdMask64 uint64 = 0x3FFF_FFFF_0000_0000
const InsnIdShift64 uint64 = 32

const InsnIdPrefixMask32 uint32 = 0x3FF0_0000           // Mask to get the prefix bits
const InsnIdPrefixMask64 uint64 = 0x3FF0_0000_0000_0000 // Mask to get the prefix bits
const InsnIdPrefixShift32 uint8 = 20                    // Shift to get the prefix bits
const InsnIdPrefixShift64 uint8 = 52                    // Shift to get the prefix bits

const FirstHalfExprMask64 uint64 = 0x0000_0000_FFFF_FFFF // Mask to get the expression part from first half of the instruction

//go:generate stringer -type=InsnKind
const (
	INSN_ASSIGN_SIMPLE         InsnKind = 1 // var = simple_value; simple_value is variable or a constant
	INSN_ASSIGN_BINARY_OP      InsnKind = 2 // var = simple_value BOP simple_value; Except array dereference.
	INSN_ASSIGN_UNARY_OP       InsnKind = 3 // var = UOP simple_value; Except dereference.
	INSN_ASSIGN_RHS_DEREF      InsnKind = 4 // var = *simple_value;
	INSN_ASSIGN_LHS_DEREF      InsnKind = 5 // *var = simple_value;
	INSN_ASSIGN_RHS_ARRAY_EXPR InsnKind = 6 // var = var[simple_value];
	INSN_ASSIGN_LHS_ARRAY_EXPR InsnKind = 7 // var[simple_value] = simple_value;
	INSN_ASSIGN_CALL           InsnKind = 8 // var = call_target(simple_value,...); A call_target is a function or a pointer to it
	INSN_ASSING_PHI            InsnKind = 9 // var = phi(simple_value,...); A phi instruction is used to select a value from a set of values

	INSN_CALL         InsnKind = 10 // call_target(simple_value,...);
	INSN_GOTO         InsnKind = 11 // goto label;
	INSN_IF_THEN_ELSE InsnKind = 12 // if (simple_value) goto labelTrue else goto labelFalse;
	INSN_LABEL        InsnKind = 13 // A label is a target for a goto or if instruction
	INSN_RETURN       InsnKind = 14 // A return instruction is used to return from a function

	INSN_RESERVE_15 InsnKind = 15 // Reserved for use at runtime
	INSN_RESERVE_16 InsnKind = 16 // Reserved for use at runtime
	INSN_RESERVE_17 InsnKind = 17 // Reserved for use at runtime
	INSN_RESERVE_18 InsnKind = 18 // Reserved for use at runtime
	INSN_RESERVE_19 InsnKind = 19 // Reserved for use at runtime
	INSN_RESERVE_20 InsnKind = 20 // Reserved for use at runtime
	INSN_RESERVE_21 InsnKind = 21 // Reserved for use at runtime
	INSN_RESERVE_22 InsnKind = 22 // Reserved for use at runtime
	INSN_RESERVE_23 InsnKind = 23 // Reserved for use at runtime
	INSN_RESERVE_24 InsnKind = 24 // Reserved for use at runtime
	INSN_RESERVE_25 InsnKind = 25 // Reserved for use at runtime
	INSN_RESERVE_26 InsnKind = 26 // Reserved for use at runtime
	INSN_RESERVE_27 InsnKind = 27 // Reserved for use at runtime
	INSN_RESERVE_28 InsnKind = 28 // Reserved for use at runtime
	INSN_RESERVE_29 InsnKind = 29 // Reserved for use at runtime
	INSN_RESERVE_30 InsnKind = 30 // Reserved for use at runtime
	INSN_RESERVE_31 InsnKind = 31 // Reserved for use at runtime
)

func (kind InsnKind) place32() uint32 {
	// InstructionKind is in bits 24..20 (5 bits)
	return uint32(kind) << InsnKindShift32
}

func (kind InsnKind) place64() uint64 {
	// InstructionKind is in bits 56..52 (5 bits)
	return uint64(kind.place32()) << 32
}

// Each instruction is at most 128 bits long.
// The instruction is divided into two halves, each 64 bits long.
// The first half contains the opcode and a possible 32 bit operand,
// and the second half contains an expression.
type Instruction struct {
	firstHalf  uint64
	secondHalf uint64
}

func (i Instruction) String() string {
	if i.firstHalf == 0 {
		return "Insn: Nop"
	} else {
		return fmt.Sprintf("Insn: %s", i.InsnKind())
	}
}

func NewInsnNop() Instruction {
	return Instruction{}
}

func NewInsnReturn(value EntityId) Instruction {
	insn := Instruction{}
	insn.firstHalf |= INSN_RETURN.place64() | ENTITY_INSN.place64()
	insn.secondHalf = uint64(NewValueExpr(value))
	return insn
}

func NewInsnSimpleAssign(lhs EntityId, rhs EntityId) Instruction {
	insn := Instruction{}
	insn.firstHalf |= INSN_ASSIGN_SIMPLE.place64() | ENTITY_INSN.place64()
	insn.firstHalf |= uint64(NewValueExpr(lhs)) & FirstHalfExprMask64
	insn.secondHalf = uint64(NewValueExpr(rhs))
	return insn
}

func NewInsnUnaryOpAssign(lhs EntityId, rhs EntityId, unaryExprKind ExpressionKind) Instruction {
	insn := Instruction{}
	insn.firstHalf |= INSN_ASSIGN_UNARY_OP.place64() | ENTITY_INSN.place64()
	insn.firstHalf |= uint64(NewValueExpr(lhs)) & FirstHalfExprMask64
	insn.secondHalf = uint64(NewExpr(rhs, 0, unaryExprKind))
	return insn
}

func NewInsnBinOpAssign(lhs EntityId, rhsOpr1 EntityId, rhsOpr2 EntityId,
	binExprKind ExpressionKind) Instruction {
	insn := Instruction{}
	insn.firstHalf |= INSN_ASSIGN_BINARY_OP.place64() | ENTITY_INSN.place64()
	insn.firstHalf |= uint64(NewValueExpr(lhs)) & FirstHalfExprMask64
	insn.secondHalf = uint64(NewExpr(rhsOpr1, rhsOpr2, binExprKind))
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
	return InsnId((i.firstHalf & InsnIdMask64) >> InsnIdShift64)
}

func (i Instruction) InsnKind() InsnKind {
	return InsnKind((i.firstHalf >> InsnKindShift64) & uint64(InsnKindMask5))
}

func (i Instruction) GetInsnPrefix16() uint16 {
	return uint16(EntityId(i.firstHalf>>InsnIdShift64).ValidBits() >> ENTITY_INSN.SeqIdBitLength())
}
