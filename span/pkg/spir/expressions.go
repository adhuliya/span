package spir

// This file defines the different types of expressions in the SPAN IR.

import "fmt"

// Each expression is 64 bits long.
// An expression can be call, binary op, unary op or no operator.
// A binary operand format:      <one bit>-<29 bits Opr2  >-<5 bits XK       >-<29 bits Opr1>
// A unary operand expr format:  <one bit>-<29 bits unused>-<5 bits XK       >-<29 bits Opr>
// A value expr format: 		 <one bit>-<29 bits unused>-<5 bits K_XK_VAL >-<29 bits Opr> (for constants, variables, etc.)
// A call expression format: 	 <one bit>-<29 bits SiteId>-<5 bits XK_CALL_0>-<29 bits callee> (for functions with zero arguments)
// A call expression format: 	 <one bit>-<29 bits SiteId>-<5 bits XK_CALL  >-<29 bits callee> (for functions with non-zero arguments)
// For non-zero arguments the arguments are stored in a map in the Translation Unit separately.
// Hence the CallSiteId is required to uniquely identify the call site with its arguments.
type Expr uint64

type ExprKind = K_XK

const NIL_X Expr = 0

const XKMask uint8 = 0x1F                           // Mask to get the expression kind (5 bits)
const XKMask64 uint64 = 0x0000_0003_E000_0000       // Mask to get the expression kind (5 bits)
const XKShift64 uint8 = 29                          // Shift to get the expression kind
const XOprIdMask32 uint32 = 0x1FFF_FFFF             // Mask to get the relevant operand bits
const UnaryOprMask64 uint64 = 0x0000_0000_1FFF_FFFF // Mask to get the operand in a simple expression
const BinXOpr1Mask64 uint64 = 0x0000_0000_1FFF_FFFF // Mask to get the first operand in a binary expression
const BinXOpr1Shift64 uint8 = 0                     // Shift to get the first operand in a binary expression
const BinXOpr2Mask64 uint64 = 0x7FFF_FFFC_0000_0000 // Mask to get the second operand in a binary expression
const BinXOpr2Shift64 uint8 = 5 + 29                // Shift to get the second operand in a binary expression

type CallSiteId uint32 // A 29 bit unsigned integer, uniquely identifying a call site

const CalleeIdMask64 uint64 = 0x0000_0000_1FFF_FFFF // Mask to get the callee in a call expression
const CalleeIdShift64 uint8 = 0
const CallSiteIdMask32 uint32 = 0x1FFF_FFFF // Mask to get the call site id in a call expression
const CallSiteIdShift32 uint8 = 0
const CallSiteIdPosMask64 uint64 = 0x7FFF_FFFC_0000_0000 // Mask to get the call site id in a call expression
const CallSiteIdShift64 uint8 = 5 + 29

const TopBitMask64 uint64 = 0x8000_0000_0000_0000 // Mask to get/set the top bit
const TopBitShift64 uint8 = 63                    // Shift to get/set the top bit

func (xk ExprKind) IsCall() bool {
	return xk == K_XK_CALL || xk == K_XK_CALL_0
}

// IsSingleOpr returns true if the expression kind is a single operand expression.
// Except a CALL_0 call expression, which is a special case.
func (xk ExprKind) IsSingleOprnd() bool {
	return xk == K_XK_VAL ||
		(xk >= K_XK_BIT_NOT && xk <= K_XK_ALIGNOF)
}

func (xk ExprKind) IsTwoOprnd() bool {
	return !xk.IsSingleOprnd() && !xk.IsCall()
}

func placeExprOpr1(operand EntityId) uint64 {
	opr := uint32(operand) & XOprIdMask32 // zero out most significant 3 bits
	return uint64(opr) << BinXOpr1Shift64
}

func placeExprOpr2(operand EntityId) uint64 {
	opr := uint32(operand) & XOprIdMask32 // zero out most significant 3 bits
	return uint64(opr) << BinXOpr2Shift64
}

func placeXK(exprKind ExprKind) uint64 {
	return uint64(exprKind) << XKShift64
}

func placeCallSiteId(siteId CallSiteId) uint64 {
	sid := uint32(siteId) & CallSiteIdMask32 // zero out most significant 3 bits
	return uint64(sid) << CallSiteIdShift64
}

// Simple value without any operator.
func ValX(value EntityId) Expr {
	return UnaryX(K_XK_VAL, value)
}

func UnaryX(xk ExprKind, opr EntityId) Expr {
	return Expr(placeXK(xk) | placeExprOpr1(opr))
}

func CallX(zeroArgs bool, callSiteId CallSiteId, callee EntityId) Expr {
	var expr uint64
	if zeroArgs {
		expr = placeXK(K_XK_CALL_0)
	} else {
		expr = placeXK(K_XK_CALL)
	}
	return Expr(expr | placeCallSiteId(callSiteId) | placeExprOpr1(callee))
}

// Creates a 64 bit expression from two operands and an expression kind.
func BinX(exprKind ExprKind, opr1 EntityId, opr2 EntityId) Expr {
	expr := placeXK(exprKind)
	if exprKind.IsSingleOprnd() {
		return Expr(expr | placeExprOpr1(opr1))
	}
	if exprKind.IsTwoOprnd() {
		return Expr(expr | placeExprOpr1(opr1) | placeExprOpr2(opr2))
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

// Creates a 64 bit expression from an operand and an expression kind.
func (expr Expr) GetXK() ExprKind {
	return ExprKind((uint64(expr) & XKMask64) >> XKShift64)
}

func (expr Expr) GetCallSiteId() CallSiteId {
	return CallSiteId((uint64(expr) & CallSiteIdPosMask64) >> CallSiteIdShift64)
}

func (expr Expr) GetCallee() EntityId {
	return EntityId((uint64(expr) & CalleeIdMask64) >> CalleeIdShift64)
}

// A simple expression has no operator.
func (expr Expr) IsSimple() bool {
	return expr.GetXK() == K_XK_VAL
}

func (expr Expr) IsCall() bool {
	return expr.GetXK() == K_XK_CALL || expr.GetXK() == K_XK_CALL_0
}

func (expr Expr) IsCall0() bool {
	return expr.GetXK() == K_XK_CALL_0
}

// Returns one or two operands.
// For expression with only one operand, the second operand is a NULL_ID.
func (expr Expr) GetOperands() (EntityId, EntityId) {
	exprKind := expr.GetXK()
	if exprKind.IsSingleOprnd() {
		return expr.GetOpr1(), NIL_ID
	} else if exprKind.IsTwoOprnd() {
		return expr.GetOpr1(), expr.GetOpr2()
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func (expr Expr) GetOpr1() EntityId {
	exprKind := expr.GetXK()
	if exprKind.IsSingleOprnd() {
		return EntityId(uint64(expr) & UnaryOprMask64)
	} else if exprKind.IsTwoOprnd() {
		return EntityId((uint64(expr) & BinXOpr1Mask64) >> BinXOpr1Shift64)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func (expr Expr) GetOpr2() EntityId {
	exprKind := expr.GetXK()
	if exprKind.IsSingleOprnd() {
		return NIL_ID
	} else if exprKind.IsTwoOprnd() {
		return EntityId((uint64(expr) & BinXOpr2Mask64) >> BinXOpr2Shift64)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func (expr *Expr) SetTopBit() {
	*expr |= Expr(TopBitMask64)
}

func (expr *Expr) ClearTopBit() {
	*expr &= Expr(^TopBitMask64)
}
