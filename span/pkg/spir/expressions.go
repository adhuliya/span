package spir

// This file defines the different types of expressions in the SPAN IR.

import "fmt"

// Each expression is 64 bits long.
// An expression can be a value, unary or binary operation, or a call expression.
// A binary operand format:      <one bit>-<29 bits Opr2  >-<5 bits XK       >-<29 bits Opr1>
// A unary operand expr format:  <one bit>-<29 bits unused>-<5 bits XK       >-<29 bits Opr>
// A value expr format: 		 <one bit>-<29 bits unused>-<5 bits K_XK_VAL >-<29 bits Opr> (for constants, variables, etc.)
// A call expression format: 	 <one bit>-<29 bits callee>-<5 bits XK_CALL  >-<29 bits SiteId> (for functions with non-zero arguments)
// For non-zero arguments, the arguments are stored in a map in the Translation Unit separately.
// Hence the CallSiteId is required to uniquely identify the call site with its arguments.
type Expr uint64

type ExprKind = K_XK

const NIL_X Expr = 0

const XKMask uint8 = 0x1F                           // Mask to get the expression kind (5 bits)
const XKPosMask64 uint64 = 0x0000_0003_E000_0000    // Mask to get the expression kind (5 bits)
const XKShift64 uint8 = 29                          // Shift to get the expression kind
const XOprIdMask32 uint32 = 0x1FFF_FFFF             // Mask to get the relevant operand bits (zeros out most significant 3 bits)
const UnaryOprMask64 uint64 = 0x0000_0000_1FFF_FFFF // Mask to get the operand in a simple expression
const BinXOpr1Mask64 uint64 = 0x0000_0000_1FFF_FFFF // Mask to get the first operand in a binary expression
const BinXOpr1Shift64 uint8 = 0                     // Shift to get the first operand in a binary expression
const BinXOpr2Mask64 uint64 = 0x7FFF_FFFC_0000_0000 // Mask to get the second operand in a binary expression
const BinXOpr2Shift64 uint8 = 29 + 5                // Shift to get the second operand in a binary expression

type CallSiteId uint32 // A 29 bit unsigned integer, uniquely identifying a call site

const TopBitMask64 uint64 = 0x8000_0000_0000_0000 // Mask to get/set the top bit
const TopBitShift64 uint8 = 63                    // Shift to get/set the top bit

func (xk ExprKind) IsCall() bool {
	return xk == K_XK_XCALL
}

// IsSingleOpr returns true if the expression kind is a single operand expression.
// Except a CALL_0 call expression, which is a special case.
func (xk ExprKind) IsSingleOprnd() bool {
	return xk == K_XK_XVAL ||
		(xk >= K_XK_XBIT_NOT && xk <= K_XK_XALLOC)
}

func (xk ExprKind) IsTwoOprnd() bool {
	return !xk.IsSingleOprnd() && !xk.IsCall()
}

func (xk ExprKind) IsRelational() bool {
	return xk == K_XK_XEQ || xk == K_XK_XNE || xk == K_XK_XLT || xk == K_XK_XGE
}

func (xk ExprKind) IsCommutative() bool {
	return (xk == K_XK_XADD || xk == K_XK_XMUL ||
		xk == K_XK_XAND || xk == K_XK_XOR || xk == K_XK_XXOR)
}

func placeExprOpr1(operand EntityId) uint64 {
	opr := uint32(operand) & XOprIdMask32
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
	return placeExprOpr1(EntityId(siteId))
}

func placeCallee(callee EntityId) uint64 {
	return placeExprOpr2(callee)
}

// BLOCK START: API to create expressions

// Simple value without any operator.
func ValX(value EntityId) Expr {
	return UnaryX(K_XK_XVAL, value)
}

func UnaryX(xk ExprKind, opr EntityId) Expr {
	return Expr(placeXK(xk) | placeExprOpr1(opr))
}

func CallX(callee EntityId, callSiteId CallSiteId) Expr {
	return Expr(placeXK(K_XK_XCALL) | placeExprOpr2(callee) | placeCallSiteId(callSiteId))
}

// Creates a 64 bit expression from two operands and an expression kind.
func BinX(exprKind ExprKind, opr1 EntityId, opr2 EntityId) Expr {
	expr := placeXK(exprKind)
	if opr1 != NIL_ID { // if exprKind.IsSingleOprnd() {
		expr = expr | placeExprOpr1(opr1)
	}
	if opr2 != NIL_ID {
		expr = expr | placeExprOpr2(opr2)
	}
	return Expr(expr)
}

// BLOCK END: API to create expressions

// Creates a 64 bit expression from an operand and an expression kind.
func (expr Expr) GetXK() ExprKind {
	return ExprKind((uint64(expr) & XKPosMask64) >> XKShift64)
}

func (expr Expr) GetCallSiteId() CallSiteId {
	return CallSiteId(expr.GetOpr1())
}

func (expr Expr) GetCallee() EntityId {
	return expr.GetOpr2()
}

// A simple expression has no operator (including nil expressions).
func (expr Expr) IsSimple() bool {
	return expr.GetXK() == K_XK_XVAL || expr.GetXK() == K_XK_XNIL
}

func (expr Expr) IsCall() bool {
	return expr.GetXK() == K_XK_XCALL
}

// Returns one or two operands.
// For expression with only one operand, the second operand is a NULL_ID.
func (expr Expr) GetOperands() (EntityId, EntityId) {
	return expr.GetOpr1(), expr.GetOpr2()
}

func (expr Expr) GetOpr1() EntityId {
	exprKind := expr.GetXK()
	if exprKind.IsSingleOprnd() {
		return EntityId(uint64(expr) & UnaryOprMask64)
	} else if exprKind.IsTwoOprnd() || exprKind.IsCall() {
		return EntityId((uint64(expr) & BinXOpr1Mask64) >> BinXOpr1Shift64)
	}
	panic(fmt.Sprintf("Invalid expression kind: %s", exprKind))
}

func (expr Expr) GetOpr2() EntityId {
	return EntityId((uint64(expr) & BinXOpr2Mask64) >> BinXOpr2Shift64)
}

func (expr *Expr) SetTopBit() {
	*expr |= Expr(TopBitMask64)
}

func (expr *Expr) ClearTopBit() {
	*expr &= Expr(^TopBitMask64)
}

// Converts expressions kind to the operator symbol string
func (xk K_XK) OperatorString() string {
	switch xk {
	case K_XK_XADD:
		return "+"
	case K_XK_XMUL:
		return "*"
	case K_XK_XSUB:
		return "-"
	case K_XK_XDIV:
		return "/"
	case K_XK_XMOD:
		return "%"
	case K_XK_XAND:
		return "&"
	case K_XK_XOR:
		return "^"
	case K_XK_XXOR:
		return "^"
	case K_XK_XSHL:
		return "<<"
	case K_XK_XSHR:
		return ">>"
	case K_XK_XSHRA:
		return ">>>"
	case K_XK_XEQ:
		return "=="
	case K_XK_XNE:
		return "!="
	case K_XK_XLT:
		return "<"
	case K_XK_XGE:
		return ">="
	case K_XK_XARR_INDX:
		return "[]"
	case K_XK_XMEMBER_ACCESS:
		return "->"
	case K_XK_XMEMBER_ADDROF:
		return "&"
	case K_XK_XCALL:
		return "()"
	case K_XK_XCAST:
		return "("
	case K_XK_XBIT_NOT:
		return "~"
	case K_XK_XNEGATE:
		return "-"
	case K_XK_XNOT:
		return "!"
	case K_XK_XDEREF:
		return "*"
	case K_XK_XADDROF:
		return "&"
	case K_XK_XSIZEOF:
		return "sizeof"
	case K_XK_XALIGNOF:
		return "alignof"
	case K_XK_XALLOC:
		return "alloc"
	case K_XK_XOTHER:
		return "xother"
	}
	return ""
}

func (expr Expr) String() string {
	xk := expr.GetXK()
	if xk.IsSingleOprnd() {
		opStr := xk.OperatorString()
		if opStr == "" {
			opStr = fmt.Sprintf("%s", xk)
		}
		return fmt.Sprintf("((X) %s%s)", opStr, expr.GetOpr1())
	} else if xk.IsTwoOprnd() {
		opStr := xk.OperatorString()
		if opStr == "" {
			opStr = fmt.Sprintf("%s", xk)
		}
		return fmt.Sprintf("((X) %s %s %s)", opStr, expr.GetOpr1(), expr.GetOpr2())
	}
	return ""
}
