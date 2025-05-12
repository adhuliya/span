package spir

// This file defines the types of instructions in the SPAN IR.

import "fmt"

type InsnId EntityId
type LabelId EntityId

// A 5 bit opcode is used to identify the instruction type.
// The instruction type decides the encoding used for the instruction.
type InsnKind = K_IK

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
	insn.firstHalf |= K_IK_IRETURN.place64() | K_EK_INSN.place64()
	insn.secondHalf = uint64(NewValueExpr(value))
	return insn
}

func NewInsnSimpleAssign(lhs EntityId, rhs EntityId) Instruction {
	insn := Instruction{}
	insn.firstHalf |= K_IK_IASGN_SIMPLE.place64() | K_EK_INSN.place64()
	insn.firstHalf |= uint64(NewValueExpr(lhs)) & FirstHalfExprMask64
	insn.secondHalf = uint64(NewValueExpr(rhs))
	return insn
}

func NewInsnUnaryOpAssign(lhs EntityId, rhs EntityId, unaryExprKind ExprKind) Instruction {
	insn := Instruction{}
	insn.firstHalf |= K_IK_IASGN_UOP.place64() | K_EK_INSN.place64()
	insn.firstHalf |= uint64(NewValueExpr(lhs)) & FirstHalfExprMask64
	insn.secondHalf = uint64(NewExpr(rhs, 0, unaryExprKind))
	return insn
}

func NewInsnBinOpAssign(lhs EntityId, rhsOpr1 EntityId, rhsOpr2 EntityId,
	binExprKind ExprKind) Instruction {
	insn := Instruction{}
	insn.firstHalf |= K_IK_IASGN_BOP.place64() | K_EK_INSN.place64()
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
	return uint16(EntityId(i.firstHalf>>InsnIdShift64).ValidBits() >> K_EK_INSN.SeqIdBitLength())
}
