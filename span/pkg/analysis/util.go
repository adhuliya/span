package analysis

import (
	"fmt"

	"github.com/adhuliya/span/pkg/spir"
)

// StmtView creates a new sequence of instructions representing different "views" over an instruction
// using the provided sequence of EntityIds (such as value constants, pointer members, or deref targets).
// The first instruction in the non-nil result is the original instruction (insn) itself.
// Returns nil if entityIds is nil or empty.
// - insn:         The base instruction to view/transform.
// - entityIds:    The EntityIds with which to instantiate the new instructions (can be expansions, values, etc.)
// - viewType:     The type of view to generate (see StmtViewType in analysis.go).
// Returns:        A slice of new Insn objects according to viewType and entityIds, or nil.
func StmtView(insn spir.Insn, entityIds []spir.EntityId, viewType StmtViewType) []spir.Insn {
	if len(entityIds) == 0 {
		return nil
	}

	result := make([]spir.Insn, 0, len(entityIds)+1)
	result = append(result, insn) // Always include the original instruction in the result.

	switch viewType {
	case RhsLiteralView:
		// For LiteralView, replace the RHS only if it's a simple XVAL (i.e., a constant or entity).
		// We interpret "RHS" as the second half entity of the instruction.
		// Only generate a new instruction when the RHS of insn is a simple XVAL;
		// otherwise, do not generate any views.
		for _, eid := range entityIds {
			newInsn := spir.AssignI(insn.LhsX(), spir.ValX(eid))
			result = append(result, newInsn)
		}
	case ArrIdxLiteralView:
		// Must be an assignment instruction. Get the array index expression and replace the index with the entityIds.
		lhsX, rhsX := insn.LhsX(), insn.RhsX()
		arrIdxX, isLhsArrX := lhsX, true
		if rhsX.HasArrIdx() {
			arrIdxX, isLhsArrX = rhsX, false
		}
		newInsn := insn // just to initialize the newInsn variable
		for _, eid := range entityIds {
			arrIdxXNew := spir.BinX(spir.K_XK_XARR_INDX, arrIdxX.GetOpr1(), eid)
			if isLhsArrX {
				newInsn = spir.AssignI(arrIdxXNew, rhsX)
			} else {
				newInsn = spir.AssignI(lhsX, arrIdxXNew)
			}
			result = append(result, newInsn)
		}
	case ConditionView:
		if len(entityIds) <= 2 {
			panic(fmt.Sprintf("ConditionView should have at least two entityIds. entityIds: %v", entityIds))
		}
		// entityIds should be boolean values. Create new condition instructions for each one.
		if len(entityIds) > 1 {
			result = append(result, insn)
		} else {
			result = append(result, spir.IfI(spir.ValX(entityIds[0]), insn.GetTrueFalseLabelsExpr()))
		}
	case DerefView, DerefViewLhs, DerefViewRhs:
		if insn.IsAssign() {
			lhsX, rhsX := insn.LhsX(), insn.RhsX()
			derefX, isLhsDerefX := lhsX, true
			if rhsX.HasDeref() {
				derefX, isLhsDerefX = rhsX, false
			}
			newInsn := insn // just to initialize the newInsn variable
			for _, eid := range entityIds {
				pointeeX := derefX.ReplaceWithPointee(eid)
				if isLhsDerefX {
					newInsn = spir.AssignI(pointeeX, rhsX)
				} else {
					newInsn = spir.AssignI(lhsX, pointeeX)
				}
				result = append(result, newInsn)
			}
		} else if insn.IsCall() {
			callExpr := insn.GetCallExpr()
			for _, eid := range entityIds {
				pointeeX := callExpr.ReplaceWithPointee(eid)
				newInsn := spir.CallI(pointeeX)
				result = append(result, newInsn)
			}
		} else {
			panic(fmt.Sprintf("Invalid instruction: %v", insn))
		}
	case DeadAssignView:
		if !insn.IsAssign() {
			panic(fmt.Sprintf("Invalid instruction: %v", insn))
		}
		if insn.InsnKind() == spir.K_IK_IASGN_SELF {
			// FIXME: todo
			insn.GetSelfAssignInsnOprnds()
		}
	default:
		// For NoView, NilView, or any unhandled view types, do nothing (return nil).
		result = nil
	}

	return result
}
