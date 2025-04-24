package spir

// This file defines the different types of expressions in the SPAN IR.

import "fmt"

// Each expression is 64 bits long.
// Some simple expression maybe stripped to only 32 bits, like ones with EXPR_VALUE kind.
type Expression uint64

type ExpressionKind int

const ExpressionKindMask uint64 = 0x7C00_0000_0000_0000       // Mask to get the expression kind
const ExpressionKindShift uint8 = 58                          // Shift to get the expression kind
const TwoOperandExprOpr1Mask uint64 = 0x02FF_FFFF_E000_0000   // Mask to get the first operand
const TwoOperandExprOpr1Shift uint8 = 29                      // Shift to get the first operand
const TwoOperandExprOpr2Mask uint64 = 0x0000_0000_1FFF_FFFF   // Mask to get the second operand
const TwoOperandExprOpr2Shift uint8 = 0                       // Shift to get the second operand
const TwoOperandExprOprIdMask uint32 = 0x1FFF_FFFF            // Mask to get the relevant operand bits
const SingleOperandExprOprMask uint64 = 0x0000_0000_FFFF_FFFF // Mask to get the operand in a single operand expression

type CallId uint32 // Its not the same as EntityId, but still a 32 bit value

const CallExprSeqIdLength uint8 = 26                     // The number of bits used to store the sequence ID in a call expression
const CallExprSeqIdMask32 uint32 = 0x03FF_FFFF           // Mask to get the sequence ID in a call expression
const CallExprSeqIdMask64 uint64 = 0x03FF_FFFF_0000_0000 // Mask to get the sequence ID in a call expression
const CallExprIdShift64 uint8 = 32                       // Shift to get the sequence ID in a call expression

//go:generate stringer -type=ExpressionKind
const (
	// Expression kinds that can be used in expressions
	EXPR_VALUE ExpressionKind = 1 // A single value type: a constant, variable or function

	EXPR_BINARY_ADD ExpressionKind = 2 // A binary addition expression
	EXPR_BINARY_SUB ExpressionKind = 3 // A binary subtraction expression
	EXPR_BINARY_MUL ExpressionKind = 4 // A binary multiplication expression
	EXPR_BINARY_DIV ExpressionKind = 5 // A binary division expression
	EXPR_BINARY_MOD ExpressionKind = 6 // A binary modulo expression

	EXPR_BINARY_AND  ExpressionKind = 7  // A binary AND expression
	EXPR_BINARY_OR   ExpressionKind = 8  // A binary OR expression
	EXPR_BINARY_XOR  ExpressionKind = 9  // A binary XOR expression
	EXPR_BINARY_SHL  ExpressionKind = 10 // A binary shift left expression
	EXPR_BINARY_SHR  ExpressionKind = 11 // A binary shift right expression
	EXPR_BINARY_SHRL ExpressionKind = 12 // A binary shift right logical expression

	EXPR_UNARY_BIT_NOT ExpressionKind = 13 // A unary bitwise NOT expression
	EXPR_UNARY_SUB     ExpressionKind = 14 // A unary subtraction expression
	EXPR_UNARY_NOT     ExpressionKind = 15 // A unary NOT expression

	EXPR_DEREF  ExpressionKind = 16 // A dereference expression
	EXPR_ADDROF ExpressionKind = 17 // An address expression

	EXPR_SIZEOF  ExpressionKind = 18 // A sizeof expression
	EXPR_ALIGNOF ExpressionKind = 19 // An alignof expression

	EXPR_ARRAY_SUBSCRIPT   ExpressionKind = 20 // An array subscript expression
	EXPR_MEMBER_ACCESS     ExpressionKind = 21 // A member access expression
	EXPR_MEMBER_PTR_ACCESS ExpressionKind = 22 // A member pointer access expression

	EXPR_CALL          ExpressionKind = 23 // A function call expression (all arguments are stored seprately)
	EXPR_CALL_COMPLETE ExpressionKind = 24 // Call expression with zero arguments
	EXPR_CAST          ExpressionKind = 25 // A cast expression
	EXPR_COMMA         ExpressionKind = 26 // A comma expression

	EXPR_OTHER_1 ExpressionKind = 27 // Reserved for use at runtime
	EXPR_OTHER_2 ExpressionKind = 28 // Reserved for use at runtime
	EXPR_OTHER_3 ExpressionKind = 29 // Reserved for use at runtime
	EXPR_OTHER_4 ExpressionKind = 30 // Reserved for use at runtime
	EXPR_OTHER_5 ExpressionKind = 31 // Reserved for use at runtime
)

func IsCallExprKind(exprKind ExpressionKind) bool {
	return exprKind == EXPR_CALL || exprKind == EXPR_CALL_COMPLETE
}

func IsOneOperandExprKind(exprKind ExpressionKind) bool {
	return exprKind == EXPR_VALUE ||
		(exprKind >= EXPR_UNARY_BIT_NOT && exprKind <= EXPR_ALIGNOF)
}

func IsTwoOperandExprKind(exprKind ExpressionKind) bool {
	return !IsOneOperandExprKind(exprKind)
}

func placeExpressionKindBits64(exprKind ExpressionKind) uint64 {
	return uint64(exprKind) << ExpressionKindShift
}

func placeOperand1InTwoOperandExpr(operand EntityId) uint64 {
	opr := uint32(operand) & TwoOperandExprOprIdMask // zero out most significant 3 bits
	return uint64(opr) << TwoOperandExprOpr1Shift
}

func placeOperand2InTwoOperandExpr(operand EntityId) uint64 {
	opr := uint32(operand) & TwoOperandExprOprIdMask // zero out most significant 3 bits
	return uint64(opr)
}

func placeOperandInOneOperandExpr(operand EntityId) uint64 {
	return uint64(operand)
}

func NewValueExpr(value EntityId) Expression {
	return NewExpr(value, 0, EXPR_VALUE)
}

func NewExpr(opr1 EntityId, opr2 EntityId, exprKind ExpressionKind) Expression {
	expr := (uint64(exprKind) & ExpressionKindMask) >> ExpressionKindShift
	if IsOneOperandExprKind(exprKind) {
		return Expression(expr | placeOperandInOneOperandExpr(opr1))
	} else if IsTwoOperandExprKind(exprKind) {
		return Expression(expr | placeOperand1InTwoOperandExpr(opr1) | placeOperand2InTwoOperandExpr(opr2))
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

// Returns both the operands. For expression with only one operand,
// the second operand is returned as 0.
func GetOperands(expr Expression) (EntityId, EntityId) {
	exprKind := ExpressionKind((uint64(expr) & ExpressionKindMask) >> ExpressionKindShift)
	if IsOneOperandExprKind(exprKind) {
		return EntityId(expr & Expression(SingleOperandExprOprMask)), 0
	} else if IsTwoOperandExprKind(exprKind) {
		return GetOperand1(expr), GetOperand2(expr)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func NewOneOperandExpr(opr EntityId, oneOprExprKind ExpressionKind) Expression {
	var expr uint64
	if IsOneOperandExprKind(oneOprExprKind) {
		expr = placeExpressionKindBits64(oneOprExprKind)
	} else {
		panic(fmt.Sprintf("Invalid single operand expression kind: %s", oneOprExprKind))
	}
	expr |= placeOperandInOneOperandExpr(opr)
	return Expression(expr)
}

func NewTwoOperandExpr(opr1 EntityId, opr2 EntityId, twoOprExprKind ExpressionKind) Expression {
	var expr uint64
	if IsTwoOperandExprKind(twoOprExprKind) {
		expr = placeExpressionKindBits64(twoOprExprKind)
	} else {
		panic(fmt.Sprintf("Invalid two operand expression kind: %s", twoOprExprKind))
	}
	expr |= placeOperand1InTwoOperandExpr(opr1) | placeOperand2InTwoOperandExpr(opr2)
	return Expression(expr)
}

func GetOperand1(expr Expression) EntityId {
	exprKind := ExpressionKind((uint64(expr) & ExpressionKindMask) >> ExpressionKindShift)
	if IsOneOperandExprKind(exprKind) {
		return EntityId(expr & Expression(SingleOperandExprOprMask))
	} else if IsTwoOperandExprKind(exprKind) {
		return EntityId((uint64(expr) & TwoOperandExprOpr1Mask) >> TwoOperandExprOpr1Shift)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func GetOperand2(expr Expression) EntityId {
	exprKind := ExpressionKind((uint64(expr) & ExpressionKindMask) >> ExpressionKindShift)
	if IsOneOperandExprKind(exprKind) {
		return 0
	} else if IsTwoOperandExprKind(exprKind) {
		return EntityId(uint64(expr) & TwoOperandExprOpr2Mask)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func GetExpressionKind(expr Expression) ExpressionKind {
	return ExpressionKind((uint64(expr) & ExpressionKindMask) >> ExpressionKindShift)
}
