package spir

// This file defines the different types of expressions in the SPAN IR.

import "fmt"

// Each expression is 64 bits long.
// Some simple expression maybe stripped to only 32 bits, like ones with EXPR_VALUE kind.
type Expression uint64

type ExpressionKind int

//go:generate stringer -type=ExpressionKind
const (
	// Expression kinds that can be used in expressions
	EXPR_VALUE ExpressionKind = 0 // A single value type: a constant, variable or function

	EXPR_BINARY_ADD ExpressionKind = 1 // A binary addition expression
	EXPR_BINARY_SUB ExpressionKind = 2 // A binary subtraction expression
	EXPR_BINARY_MUL ExpressionKind = 3 // A binary multiplication expression
	EXPR_BINARY_DIV ExpressionKind = 4 // A binary division expression
	EXPR_BINARY_MOD ExpressionKind = 5 // A binary modulo expression

	EXPR_BINARY_AND  ExpressionKind = 6  // A binary AND expression
	EXPR_BINARY_OR   ExpressionKind = 7  // A binary OR expression
	EXPR_BINARY_XOR  ExpressionKind = 8  // A binary XOR expression
	EXPR_BINARY_SHL  ExpressionKind = 9  // A binary shift left expression
	EXPR_BINARY_SHR  ExpressionKind = 10 // A binary shift right expression
	EXPR_BINARY_SHRL ExpressionKind = 11 // A binary shift right logical expression

	EXPR_UNARY_BIT_NOT ExpressionKind = 12 // A unary bitwise NOT expression
	EXPR_UNARY_SUB     ExpressionKind = 13 // A unary subtraction expression
	EXPR_UNARY_NOT     ExpressionKind = 14 // A unary NOT expression

	EXPR_DEREF  ExpressionKind = 15 // A dereference expression
	EXPR_ADDROF ExpressionKind = 16 // An address expression

	EXPR_ARRAY_SUBSCRIPT   ExpressionKind = 17 // An array subscript expression
	EXPR_MEMBER_ACCESS     ExpressionKind = 18 // A member access expression
	EXPR_MEMBER_PTR_ACCESS ExpressionKind = 19 // A member pointer access expression

	EXPR_CALL          ExpressionKind = 20 // A function call expression (more than 1 arguments are stored seprately)
	EXPR_CALL_COMPLETE ExpressionKind = 21 // Call expression with zero or one argument
	EXPR_CAST          ExpressionKind = 22 // A cast expression
	EXPR_COMMA         ExpressionKind = 23 // A comma expression
	EXPR_SIZEOF        ExpressionKind = 24 // A sizeof expression
	EXPR_ALIGNOF       ExpressionKind = 25 // An alignof expression

	EXPR_GOTO  ExpressionKind = 26 // A goto expression
	EXPR_LABEL ExpressionKind = 27 // A label expression

	EXPR_APPLE     ExpressionKind = 28 // An apple expression
	EXPR_BANANA    ExpressionKind = 29 // A banana expression
	EXPR_PINEAPPLE ExpressionKind = 30 // A pineapple expression

	EXPR_OTHER ExpressionKind = 31 // An other expression
)

func positionExpressionKindBits64(exprKind ExpressionKind) uint64 {
	// ExpressionKind in bits 62..58 (5 bits)
	return uint64(exprKind) << 58
}

func positionBinExprOperand1(operand EntityId) uint64 {
	opr := uint32(operand) & 0x1FFFFFFF // zero out most significant 3 bits
	return uint64(opr) << (32 - 6 + 3)  // 1 + 5 bits reserved for ExpressionKind
}

func positionBinExprOperand2(operand EntityId) uint64 {
	opr := uint32(operand) & 0x1FFFFFFF // zero out most significant 3 bits
	return uint64(opr)
}

func NewExprValue(value EntityId) Expression {
	var expr uint64 = positionExpressionKindBits64(EXPR_VALUE)
	expr |= uint64(value) // EntityId in the lower 32 bits
	return Expression(expr)
}

func NewExprUnaryOp(value EntityId, unaryExprKind ExpressionKind) Expression {
	var expr uint64
	switch unaryExprKind {
	case EXPR_UNARY_SUB, EXPR_UNARY_BIT_NOT, EXPR_UNARY_NOT:
		expr = positionExpressionKindBits64(unaryExprKind)
	default:
		panic(fmt.Sprintf("Invalid unary expression kind: %s", unaryExprKind))
	}
	expr |= uint64(value) // EntityId in the lower 32 bits
	return Expression(expr)
}

func NewExprBinaryOp(opr1 EntityId, opr2 EntityId, binExprKind ExpressionKind) Expression {
	var expr uint64
	switch binExprKind {
	case EXPR_BINARY_ADD, EXPR_BINARY_SUB, EXPR_BINARY_MUL, EXPR_BINARY_DIV, EXPR_BINARY_MOD:
		expr = positionExpressionKindBits64(binExprKind)
	default:
		panic(fmt.Sprintf("Invalid binary expression kind: %s", binExprKind))
	}
	expr |= positionBinExprOperand1(opr1)
	expr |= positionBinExprOperand2(opr2)
	return Expression(expr)
}
