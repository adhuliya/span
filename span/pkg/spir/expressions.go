package spir

// This file defines the different types of expressions in the SPAN IR.

import "fmt"

// Each expression is 64 bits long.
// Some simple expression maybe stripped to only 32 bits, like ones with EXPR_VALUE kind.
type Expr uint64

type ExprKind = K_XK

const ExprKindMask uint64 = 0x7C00_0000_0000_0000       // Mask to get the expression kind
const ExprKindShift uint8 = 58                          // Shift to get the expression kind
const TwoOprExprOpr1Mask uint64 = 0x02FF_FFFF_E000_0000 // Mask to get the first operand
const TwoOprExprOpr1Shift uint8 = 29                    // Shift to get the first operand
const TwoOprExprOpr2Mask uint64 = 0x0000_0000_1FFF_FFFF // Mask to get the second operand
const TwoOprExprOpr2Shift uint8 = 0                     // Shift to get the second operand
const TwoOprExprOprIdMask uint32 = 0x1FFF_FFFF          // Mask to get the relevant operand bits
const OneOprExprOprMask uint64 = 0x0000_0000_FFFF_FFFF  // Mask to get the operand in a single operand expression

type CallId uint32 // Its not the same as EntityId, but still a 32 bit value

const CallExprSeqIdLength uint8 = 26                     // The number of bits used to store the sequence ID in a call expression
const CallExprSeqIdMask32 uint32 = 0x03FF_FFFF           // Mask to get the sequence ID in a call expression
const CallExprSeqIdMask64 uint64 = 0x03FF_FFFF_0000_0000 // Mask to get the sequence ID in a call expression
const CallExprIdShift64 uint8 = 32                       // Shift to get the sequence ID in a call expression

func IsCallExprKind(exprKind ExprKind) bool {
	return exprKind == K_XK_CALL || exprKind == K_XK_CALL_0
}

func IsOneOprExprKind(exprKind ExprKind) bool {
	return exprKind == K_XK_VAL ||
		(exprKind >= K_XK_BIT_NOT && exprKind <= K_XK_ALIGNOF)
}

func IsTwoOprExprKind(exprKind ExprKind) bool {
	return !IsOneOprExprKind(exprKind) && !IsCallExprKind(exprKind)
}

func placeExpressionKindBits64(exprKind ExprKind) uint64 {
	return uint64(exprKind) << ExprKindShift
}

func placeOperand1InTwoOperandExpr(operand EntityId) uint64 {
	opr := uint32(operand) & TwoOprExprOprIdMask // zero out most significant 3 bits
	return uint64(opr) << TwoOprExprOpr1Shift
}

func placeOperand2InTwoOperandExpr(operand EntityId) uint64 {
	opr := uint32(operand) & TwoOprExprOprIdMask // zero out most significant 3 bits
	return uint64(opr)
}

func placeOperandInOneOperandExpr(operand EntityId) uint64 {
	return uint64(operand)
}

func NewValueExpr(value EntityId) Expr {
	return NewExpr(value, 0, K_XK_VAL)
}

func NewExpr(opr1 EntityId, opr2 EntityId, exprKind ExprKind) Expr {
	expr := (uint64(exprKind) & ExprKindMask) >> ExprKindShift
	if IsOneOprExprKind(exprKind) {
		return Expr(expr | placeOperandInOneOperandExpr(opr1))
	} else if IsTwoOprExprKind(exprKind) {
		return Expr(expr | placeOperand1InTwoOperandExpr(opr1) | placeOperand2InTwoOperandExpr(opr2))
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func GetExprKind(expr Expr) ExprKind {
	return ExprKind((uint64(expr) & ExprKindMask) >> ExprKindShift)
}

// Returns one or two operands.
// For expression with only one operand, the second operand is invalid.
func GetOperands(expr Expr) (EntityId, EntityId) {
	exprKind := GetExprKind(expr)
	if IsOneOprExprKind(exprKind) {
		return EntityId(expr & Expr(OneOprExprOprMask)), EntityId(ID_NONE)
	} else if IsTwoOprExprKind(exprKind) {
		return GetOpr1(expr), GetOpr2(expr)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func NewOneOprExpr(opr EntityId, oneOprExprKind ExprKind) Expr {
	var expr uint64
	if IsOneOprExprKind(oneOprExprKind) {
		expr = placeExpressionKindBits64(oneOprExprKind)
	} else {
		panic(fmt.Sprintf("Invalid single operand expression kind: %s", oneOprExprKind))
	}
	expr |= placeOperandInOneOperandExpr(opr)
	return Expr(expr)
}

func NewTwoOprExpr(opr1 EntityId, opr2 EntityId, twoOprExprKind ExprKind) Expr {
	var expr uint64
	if IsTwoOprExprKind(twoOprExprKind) {
		expr = placeExpressionKindBits64(twoOprExprKind)
	} else {
		panic(fmt.Sprintf("Invalid two operand expression kind: %s", twoOprExprKind))
	}
	expr |= placeOperand1InTwoOperandExpr(opr1) | placeOperand2InTwoOperandExpr(opr2)
	return Expr(expr)
}

func GetOpr1(expr Expr) EntityId {
	exprKind := ExprKind((uint64(expr) & ExprKindMask) >> ExprKindShift)
	if IsOneOprExprKind(exprKind) {
		return EntityId(expr & Expr(OneOprExprOprMask))
	} else if IsTwoOprExprKind(exprKind) {
		return EntityId((uint64(expr) & TwoOprExprOpr1Mask) >> TwoOprExprOpr1Shift)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func GetOpr2(expr Expr) EntityId {
	exprKind := ExprKind((uint64(expr) & ExprKindMask) >> ExprKindShift)
	if IsOneOprExprKind(exprKind) {
		return EntityId(ID_NONE)
	} else if IsTwoOprExprKind(exprKind) {
		return EntityId(uint64(expr) & TwoOprExprOpr2Mask)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func GetExpressionKind(expr Expr) ExprKind {
	return ExprKind((uint64(expr) & ExprKindMask) >> ExprKindShift)
}
