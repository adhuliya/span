package spir

// This file defines the different types of expressions in the SPAN IR.

// Each expression is at most 64 bits long.
// Some expression maybe only 32 bits long, stored in the lower 32 bits.
type Expression uint64

type ExpressionKind int

const (
	// Expression kinds that can be used in expressions
	EXPR_VALUE ExpressionKind = 0 // A single value type: a constant, variable or function

	EXPR_BINARY_ADD ExpressionKind = 1 // A binary addition expression
	EXPR_BINARY_SUB ExpressionKind = 2 // A binary subtraction expression
	EXPR_BINARY_MUL ExpressionKind = 3 // A binary multiplication expression
	EXPR_BINARY_DIV ExpressionKind = 4 // A binary division expression
	EXPR_BINARY_MOD ExpressionKind = 5 // A binary modulo expression

	EXPR_BINARY_AND ExpressionKind = 6  // A binary AND expression
	EXPR_BINARY_OR  ExpressionKind = 7  // A binary OR expression
	EXPR_BINARY_XOR ExpressionKind = 8  // A binary XOR expression
	EXPR_BINARY_SHL ExpressionKind = 9  // A binary shift left expression
	EXPR_BINARY_SHR ExpressionKind = 10 // A binary shift right expression

	EXPR_UNARY_ADD ExpressionKind = 11 // A unary addition expression
	EXPR_UNARY_SUB ExpressionKind = 12 // A unary subtraction expression
	EXPR_UNARY_NOT ExpressionKind = 13 // A unary NOT expression

	EXPR_DEREF  ExpressionKind = 14 // A dereference expression
	EXPR_ADDROF ExpressionKind = 15 // An address expression

	EXPR_ARRAY_SUBSCRIPT   ExpressionKind = 16 // An array subscript expression
	EXPR_MEMBER_ACCESS     ExpressionKind = 17 // A member access expression
	EXPR_MEMBER_PTR_ACCESS ExpressionKind = 18 // A member pointer access expression

	EXPR_CALL    ExpressionKind = 19 // A function call expression
	EXPR_CAST    ExpressionKind = 20 // A cast expression
	EXPR_COMMA   ExpressionKind = 21 // A comma expression
	EXPR_SIZEOF  ExpressionKind = 22 // A sizeof expression
	EXPR_ALIGNOF ExpressionKind = 23 // An alignof expression

	EXPR_GOTO  ExpressionKind = 24 // A goto expression
	EXPR_LABEL ExpressionKind = 25 // A label expression

	EXPR_OTHER ExpressionKind = 26 // An other expression
)
