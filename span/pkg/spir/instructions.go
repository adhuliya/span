package spir

// This file defines the types of instructions in the SPAN IR.

import (
	"fmt"

	util "github.com/adhuliya/span/internal/util/errs"
)

type InsnId EntityId
type LabelId EntityId

const NIL_LABEL_ID LabelId = 0

// A 5 bit opcode is used to identify the instruction type.
// The instruction type decides the encoding used for the instruction.
type InsnKind = K_IK

const IKMask5 uint8 = 0x1F
const IKPosMask32 uint32 = 0x01F0_0000
const IKShift32 uint32 = 20
const IKPosMask64 uint64 = 0x01F0_0000_0000_0000
const IKShift64 uint64 = 52
const InsnIdMask32 uint64 = 0x3FFF_FFFF
const InsnIdShift32 uint32 = 0
const InsnIdPosMask64 uint64 = 0x3FFF_FFFF_0000_0000
const InsnIdShift64 uint64 = 32

// Instruction id prefix is the 10 bit with <5 bit EK> and <5 bit IK>
const InsnIdPrefixPosMask32 uint32 = 0x3FF0_0000           // Mask to get the prefix bits
const InsnIdPrefixShift32 uint8 = 20                       // Shift to get the prefix bits
const InsnIdPrefixPosMask64 uint64 = 0x3FF0_0000_0000_0000 // Mask to get the prefix bits
const InsnIdPrefixShift64 uint8 = 52                       // Shift to get the prefix bits

// Mask to get the expression part from first half of the instruction
// This expression is always a simple Value expression with no operators
const FirstHalfExprMask64 uint64 = 0x0000_0000_1FFF_FFFF
const FirstHalf2BitMask64 uint64 = 0x0000_0000_C000_0000
const FirstHalf2BitShift64 uint64 = 30

const TrueLabelPosMask64 uint64 = 0x0000_0000_1FFF_FFFF // Mask to get the true label
const TrueLabelShift64 uint64 = 0
const FalseLabelPosMask64 uint64 = 0x8FFF_FFFC_0000_0000 // Mask to get the false label
const FalseLabelShift64 uint64 = 32

// InstructionKind is in bits 24..20 (5 bits)
func (kind InsnKind) place32() uint32 {
	return uint32(kind) << IKShift32
}

// InstructionKind is in bits 56..52 (5 bits)
func (kind InsnKind) place64() uint64 {
	return uint64(kind) << IKShift64
}

// Each instruction is at most 128 bits long.
// The instruction is divided into two halves, each 64 bits long.
// The first half contains the instruction id which contains the opcode and a possible 32 bit operand,
// and the second half contains an expression.
type Insn struct {
	firstHalf  uint64
	secondHalf uint64
}

func (i Insn) String() string {
	kind := i.InsnKind()
	switch kind {
	case K_IK_INIL:
		return "Insn: Nil"
	case K_IK_INOP:
		return "no-op"
	case K_IK_IBARRIER:
		return "barrier"
	case K_IK_IRETURN:
		expr := i.GetFirstHalfExpr()
		return fmt.Sprintf("return %s", expr)
	case K_IK_IASGN_SIMPLE:
		lhs := i.GetFirstHalfExpr()
		rhs := Expr(i.secondHalf)
		return fmt.Sprintf("%s = %s", lhs, rhs)
	case K_IK_IASGN_CALL:
		lhs := i.GetFirstHalfExpr()
		rhs := Expr(i.secondHalf)
		return fmt.Sprintf("%s = %s", lhs, rhs)
	case K_IK_IASGN_RHS_OP:
		lhs := i.GetFirstHalfExpr()
		rhs := Expr(i.secondHalf)
		return fmt.Sprintf("%s = %s", lhs, rhs)
	case K_IK_IASGN_LHS_OP:
		rhs := i.GetFirstHalfExpr()
		lhs := Expr(i.secondHalf)
		return fmt.Sprintf("%s = %s", lhs, rhs)
	case K_IK_IASGN_PHI:
		lhs := i.GetFirstHalfExpr()
		rhs := Expr(i.secondHalf)
		return fmt.Sprintf("%s = φ(%s)", lhs, rhs)
	case K_IK_ICALL:
		expr := Expr(i.secondHalf)
		return fmt.Sprintf("%s", expr)
	case K_IK_ICOND:
		cond := i.GetFirstHalfExpr()
		trueLabel := Expr(i.secondHalf).GetOpr1()
		falseLabel := Expr(i.secondHalf).GetOpr2()
		return fmt.Sprintf("if (%s) T:%s F:%s", cond, trueLabel, falseLabel)
	case K_IK_IGOTO:
		label := Expr(i.secondHalf).GetOpr1()
		return fmt.Sprintf("goto %s", label)
	case K_IK_ILABEL:
		label := i.GetFirstHalfExpr()
		return fmt.Sprintf("%s:", label)
	default:
		return fmt.Sprintf("unknown(%s)", kind)
	}
}

// BLOCK START: API to create instructions

func (i *Insn) SetInsnId(id InsnId) {
	i.firstHalf = (uint64(id) & InsnIdMask32) << InsnIdShift64
}

func NilI() Insn {
	insn := Insn{}
	return insn // No instruction -- all zeros
}

func NopI() Insn {
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_INOP.place64()
	return insn
}

func BarrierI() Insn {
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_IBARRIER.place64()
	return insn
}

func UseI(eid1, eid2, eid3 EntityId) Insn {
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_IUSE.place64()
	insn.SetFirstHalfOprnd(eid1)
	insn.SetCompoundExpr(ValX2(eid2, eid3))
	return insn
}

// A return instruction always has a simple value with no operators.
func ReturnI(expr Expr) Insn {
	util.Assert(expr.IsSimple(), fmt.Sprintf("Expr must have no operator: %s", expr))
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_IRETURN.place64()
	insn.firstHalf |= uint64(expr) & FirstHalfExprMask64
	return insn
}

// Creates Assign instruction except Self Assignment and PHI assignment.
func AssignI(lhs Expr, rhs Expr) Insn {
	util.Assert(lhs.IsSimple() || rhs.IsSimple(), "At least one of the expressions must be simple")
	insn, ik := Insn{}, K_IK_IASGN_SIMPLE
	insn.firstHalf |= K_EK_EINSN0.place64()

	lhsSimple, rhsSimple := lhs.IsSimple(), rhs.IsSimple()
	if lhsSimple {
		if rhsSimple {
			ik = K_IK_IASGN_SIMPLE
		} else if rhs.IsCall() {
			ik = K_IK_IASGN_CALL
		} else {
			ik = K_IK_IASGN_RHS_OP
		}
	} else if rhsSimple {
		ik = K_IK_IASGN_LHS_OP
	} else {
		panic("unreachable: both expressions are not simple")
	}

	switch ik {
	case K_IK_IASGN_SIMPLE:
		insn.firstHalf |= uint64(lhs) & FirstHalfExprMask64
		insn.secondHalf = uint64(rhs)
	case K_IK_IASGN_RHS_OP:
		insn.firstHalf |= uint64(lhs) & FirstHalfExprMask64
		insn.secondHalf = uint64(rhs)
	case K_IK_IASGN_LHS_OP:
		insn.firstHalf |= uint64(rhs) & FirstHalfExprMask64
		insn.secondHalf = uint64(lhs)
	case K_IK_IASGN_CALL:
		insn.firstHalf |= uint64(lhs) & FirstHalfExprMask64
		insn.secondHalf = uint64(rhs)
	}

	insn.firstHalf |= ik.place64()

	return insn
}

func SelfAssignI(eids []EntityId) Insn {
	if len(eids) == 0 || len(eids) > 3 {
		panic(fmt.Sprintf("SelfAssignI: invalid number of entities: %d", len(eids)))
	}
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_IASGN_SELF.place64()
	insn.SetFirstHalfOprnd(eids[0])
	insn.secondHalf = uint64(ValX2(eids[1], eids[2]))
	return insn
}

// Create PHI assignment instruction.
// TODO: Add support for multiple PHI assignments in RHS.
func PhiI(lhs Expr) Insn {
	// FIXME: incomplete
	util.Assert(lhs.IsSimple(), "LHS must be simple")
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_IASGN_PHI.place64()
	insn.firstHalf |= uint64(lhs) & FirstHalfExprMask64
	return insn
}

func CallI(expr Expr) Insn {
	util.Assert(expr.IsCall(), "Expression must be a call expression")
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_ICALL.place64()
	insn.secondHalf = uint64(expr)
	return insn
}

func LabelI(expr Expr) Insn {
	util.Assert(expr.GetOpr1().Kind().IsLabel(), "Expr must be a label entity")
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_ILABEL.place64()
	insn.SetFirstHalfOprnd(expr.GetOpr1())
	return insn
}

func GotoI(expr Expr) Insn {
	util.Assert(expr.GetOpr1().Kind().IsLabel(), "Expr must be a label entity")
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_IGOTO.place64()
	insn.SetFirstHalfOprnd(expr.GetOpr1())
	return insn
}

func IfI(cond Expr, trueFalseLabels Expr) Insn {
	insn := Insn{}
	insn.firstHalf |= K_EK_EINSN0.place64() | K_IK_ICOND.place64()
	insn.SetFirstHalfOprnd(cond.GetOpr1())
	insn.secondHalf = uint64(trueFalseLabels)
	return insn
}

// BLOCK END  : API to create instructions

// Extra assosicated info with the instruction.
type InsnInfo struct {
	SrcLoc
	bbId BasicBlockId // The basic block to which the instruction belongs
}

// NewInsnInfo creates a new InsnInfo struct, initializing its fields.
// If srcLoc is not nil, its contents are copied into the SrcLoc field.
func NewInsnInfo(bbId BasicBlockId, srcLoc SrcLoc) InsnInfo {
	info := InsnInfo{
		bbId: bbId,
	}
	info.SrcLoc = srcLoc
	return info
}

func (i InsnInfo) BBId() BasicBlockId {
	return i.bbId
}

func (i Insn) Id() InsnId {
	return InsnId((i.firstHalf & InsnIdPosMask64) >> InsnIdShift64)
}

func (i Insn) InsnKind() InsnKind {
	return InsnKind((i.firstHalf >> IKShift64) & uint64(IKMask5))
}

// HasProperPrefix returns true if the instruction's Id has a valid kind + (if needed) subkind prefix.
// This checks the entity encoding used for InsnId.
func (i Insn) HasProperPrefix() bool {
	return EntityId(i.Id()).HasProperPrefix()
}

// HasProperId returns true if the instruction has a nonzero, valid instruction Id (i.e., was given a proper allocation).
// This means the prefix is proper and the "sequence" part isn't zero.
func (i Insn) HasProperId() bool {
	return EntityId(i.Id()).IsProper()
}

func (i *Insn) IsAssign() bool {
	return i.InsnKind() >= K_IK_IASGN_SELF && i.InsnKind() <= K_IK_IASGN_PHI
}

// Get2Bits returns the value of the 2 bits (bits 30..29) from the instruction's first half.
func (i *Insn) Get2Bits() uint8 {
	return uint8((i.firstHalf & FirstHalf2BitMask64) >> FirstHalf2BitShift64)
}

// Set2Bits sets the value of the 2 bits (bits 30..29) in the instruction's first half.
// Only the lowest 2 bits of 'val' are used.
func (i *Insn) Set2Bits(val uint8) {
	// Clear existing 3 bits
	i.firstHalf &= ^FirstHalf2BitMask64
	// Set the new 3 bits
	i.firstHalf |= (uint64(val) & 0x3) << FirstHalf2BitShift64
}

func (i Insn) GetCallExpr() Expr {
	if i.HasCallExpr() {
		return Expr(i.secondHalf)
	}
	return NIL_X
}

func (i Insn) GetFirstHalfExpr() Expr {
	return ValX(i.GetFirstHalfEntityId())
}

func (i *Insn) SetFirstHalfExpr(expr Expr) {
	i.firstHalf |= uint64(expr) & FirstHalfExprMask64
}

func (i *Insn) SetFirstHalfOprnd(eid EntityId) {
	i.firstHalf |= uint64(eid) & FirstHalfExprMask64
}

func (i *Insn) SetCompoundExpr(expr Expr) {
	i.secondHalf = uint64(expr)
}

func (i Insn) GetCompoundExpr() Expr {
	return Expr(i.secondHalf)
}

func (i Insn) GetSecondHalfExpr() Expr {
	return Expr(i.secondHalf)
}

func (i Insn) GetFirstHalfEntityId() EntityId {
	return EntityId(i.firstHalf & FirstHalfExprMask64)
}

func (i Insn) GetOperands() (EntityId, EntityId, EntityId) {
	eid1 := i.GetFirstHalfEntityId()
	eid2, eid3 := i.GetCompoundExpr().GetOperands()
	return eid1, eid2, eid3
}

func (i *Insn) GetSelfAssignInsnOprnds() []EntityId {
	if i.InsnKind() != K_IK_IASGN_SELF {
		panic(fmt.Sprintf("GetSelfAssignInsnOprnds: invalid instruction kind: %s", i.InsnKind()))
	}
	oprnd1 := i.GetFirstHalfEntityId()
	oprnd2 := Expr(i.secondHalf).GetOpr1()
	oprnd3 := Expr(i.secondHalf).GetOpr2()
	return []EntityId{oprnd1, oprnd2, oprnd3}
}

func (i *Insn) IsGoto() bool {
	return i.InsnKind() == K_IK_IGOTO
}

func (i Insn) GetInsnPrefix16() uint16 {
	return EntityId(i.firstHalf >> InsnIdShift64).KindAndSubKind16()
}

func (i *Insn) IsCall() bool {
	return i.InsnKind() == K_IK_ICALL
}

func (i *Insn) HasCallExpr() bool {
	return i.InsnKind() == K_IK_ICALL || i.InsnKind() == K_IK_IASGN_CALL
}

func (i *Insn) IsIf() bool {
	return i.InsnKind() == K_IK_ICOND
}

func (i *Insn) IsPhi() bool {
	return i.InsnKind() == K_IK_IASGN_PHI
}

func (i *Insn) IsLabel() bool {
	return i.InsnKind() == K_IK_ILABEL
}

func (i *Insn) IsReturn() bool {
	return i.InsnKind() == K_IK_IRETURN
}

func (i *Insn) IsLocalJump() bool {
	return i.IsGoto() || i.IsIf()
}

func (i *Insn) GetTrueFalseLabelsExpr() Expr {
	return i.GetSecondHalfExpr()
}

// LhsX returns the left-hand side expression of an assignment instruction.
// For simple assignments and assignments involving call/LHS ops, the LHS is in the firstHalf.
// For RHS op assignments, the roles are reversed; the first half expression is the LHS.
// For unsupported instructions, returns NIL_X.
func (i *Insn) LhsX() Expr {
	switch i.InsnKind() {
	case K_IK_IASGN_SIMPLE, K_IK_IASGN_CALL, K_IK_IASGN_RHS_OP:
		return i.GetFirstHalfExpr()
	case K_IK_IASGN_LHS_OP:
		return i.GetSecondHalfExpr()
	default:
		return NIL_X
	}
}

// RhsX returns the right-hand side expression of an assignment instruction.
// For simple assignments and assignments involving call/RHS ops, the RHS is in the secondHalf.
// For lhs op assignments, the roles are reversed, the first half expression is the RHS.
// For unsupported instructions, returns NIL_X.
func (i *Insn) RhsX() Expr {
	switch i.InsnKind() {
	case K_IK_IASGN_SIMPLE, K_IK_IASGN_RHS_OP, K_IK_IASGN_CALL:
		return i.GetSecondHalfExpr()
	case K_IK_IASGN_LHS_OP:
		return i.GetFirstHalfExpr()
	default:
		return NIL_X
	}
}

func (i *Insn) GetLabels() (LabelId, LabelId) {
	if i.IsIf() {
		return LabelId(i.GetSecondHalfExpr().GetOpr1()), LabelId(i.GetSecondHalfExpr().GetOpr2())
	} else if i.IsLabel() {
		return LabelId(i.GetFirstHalfExpr().GetOpr1()), NIL_LABEL_ID
	} else if i.IsGoto() {
		return LabelId(i.GetFirstHalfExpr().GetOpr1()), NIL_LABEL_ID
	}

	return NIL_LABEL_ID, NIL_LABEL_ID
}
