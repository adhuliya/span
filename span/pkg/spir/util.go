package spir

// This file defines the utility functions for the SPAN IR.

import "fmt"

// PrintEntityId prints the different parts of a 32-bit entity ID separated by hyphens.
// The format is: <top-2-bits>-<entity-kind>-<sub-kind>-<seq-id>
// base can be 'd' for decimal, 'o' for octal, or 'x' for hexadecimal
func EntityIdString(id EntityId, base byte) string {
	// Extract the parts
	topBits := uint32(id) >> EIdBitLength
	eKind := EntityKind((uint32(id) & uint32(EKPosMask32)) >> EKShift32)
	subKind := uint8((uint32(id) & uint32(ESKPosMask32)) >> ESKShift32)
	seqId := uint32(id) & uint32(ImmConstMask32)

	switch base {
	case 'o':
		return fmt.Sprintf("0o%o-0o%o-0o%o-0o%o", topBits, eKind, subKind, seqId)
	case 'd':
		return fmt.Sprintf("%d-%d-%d-%d", topBits, eKind, subKind, seqId)
	default: // hexadecimal
		return fmt.Sprintf("0x%x-0x%x-0x%x-0x%x", topBits, eKind, subKind, seqId)
	}
}

// createCfgForFunction creates a control flow graph for a function.
// It checks each basic block in the body and check for the follwoing statements
//  1. If statement.
//  2. Goto statement.
//  3. Label statement.
//  4. Return statement.
//  5. Call statement.
//  6. Assign statement with a Call.
//
// If such a statement is found, and is not the last statement in the basic block,
// the statements after it are moved to a new basic block.
// The new basic block is added to the control flow graph.
// As a special case, each call or call assignment is kept in its own basic block,
// with no other instructions.
// If a label in a label statement is the target of an if or a goto statement,
// it marks the label as used and creates a new basic block.
//
// The control flow graph is returned.
func createCfgForFunction(fun *Function, body Graph) *ControlFlowGraph {
	cfg := NewControlFlowGraph(fun.tu, 0, fun.id)
	// Create a map to track label locations and their usage
	labelToBB := make(map[LabelId]*BasicBlock)
	usedLabels := make(map[LabelId]bool)

	// First pass - identify used labels
	for _, bb := range body.(*ControlFlowGraph).basicBlocks {
		for i := 0; i < bb.InsnCount(); i++ {
			insn := bb.Insn(i)
			if insn.IsIf() {
				trueLabel, falseLabel := insn.GetLabels()
				usedLabels[trueLabel] = true
				usedLabels[falseLabel] = true
			} else if insn.IsGoto() {
				targetLabel, _ := insn.GetLabels()
				usedLabels[targetLabel] = true
			}
		}
	}

	// Second pass - split basic blocks at control flow boundaries
	var newBBs []*BasicBlock
	for _, bb := range body.(*ControlFlowGraph).basicBlocks {
		currBB := NewBasicBlock(BasicBlockId(fun.tu.GenerateEntityId(K_EK_BB)), bb.scope, fun.id, 0)
		newBBs = append(newBBs, currBB)

		for i := 0; i < bb.InsnCount(); i++ {
			insn := bb.Insn(i)

			// Handle label statements that are jump targets
			if insn.IsLabel() {
				labelId, _ := insn.GetLabels()
				if usedLabels[labelId] && len(currBB.insns) > 0 {
					currBB = NewBasicBlock(BasicBlockId(fun.tu.GenerateEntityId(K_EK_BB)), bb.scope, fun.id, 0)
					newBBs = append(newBBs, currBB)
				}
				labelToBB[labelId] = currBB
			}

			currBB.insns = append(currBB.insns, insn)

			// Split after control flow instructions if not last instruction
			if i < bb.InsnCount()-1 && (insn.IsIf() || insn.IsGoto() || insn.IsReturn() ||
				insn.IsCall() || (insn.IsAssign() && insn.HasCallExpr())) {
				currBB = NewBasicBlock(BasicBlockId(fun.tu.GenerateEntityId(K_EK_BB)), bb.scope, fun.id, 0)
				newBBs = append(newBBs, currBB)
			}
		}
	}

	// Third pass - connect basic blocks based on control flow
	for i, bb := range newBBs {
		if len(bb.insns) == 0 {
			continue
		}

		lastInsn := bb.insns[len(bb.insns)-1]

		// Handle if statements
		if lastInsn.IsIf() {
			trueLabel, falseLabel := lastInsn.GetLabels()
			if trueBB, ok := labelToBB[trueLabel]; ok {
				bb.addSucc(trueBB)
				trueBB.addPred(bb)
			}
			if falseBB, ok := labelToBB[falseLabel]; ok {
				bb.addSucc(falseBB)
				falseBB.addPred(bb)
			}
			continue
		}

		// Handle goto statements
		if lastInsn.IsGoto() {
			targetLabel, _ := lastInsn.GetLabels()
			if targetBB, ok := labelToBB[targetLabel]; ok {
				bb.addSucc(targetBB)
				targetBB.addPred(bb)
			}
			continue
		}

		// Handle return statements
		if lastInsn.IsReturn() {
			continue
		}

		// Fall through to next block if no control flow instruction
		if i < len(newBBs)-1 {
			bb.addSucc(newBBs[i+1])
			newBBs[i+1].addPred(bb)
		}
	}

	// Add all basic blocks to CFG
	cfg.AddBBs(newBBs...)

	// Set entry and exit blocks
	if len(newBBs) > 0 {
		cfg.SetEntryBB(newBBs[0])
		// Find exit block - one with return statement or last block
		for i := len(newBBs) - 1; i >= 0; i-- {
			bb := newBBs[i]
			if len(bb.insns) > 0 && bb.insns[len(bb.insns)-1].IsReturn() {
				cfg.SetExitBB(bb)
				break
			}
		}
		if cfg.ExitBlock() == nil {
			cfg.SetExitBB(newBBs[len(newBBs)-1])
		}
	}
	return cfg
}
