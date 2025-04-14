package spir

// This file defines the types of instructions in the SPAN IR.

// Each instruction is at most 128 bits long.
// The instruction is divided into two halves, each 64 bits long.
// The first half contains the opcode and a possible 32 bit operand,
// and the second half contains an expression.
type Instruction struct {
	firstHalf  uint64
	secondHalf uint64
}
