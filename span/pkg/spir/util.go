package spir

// This file defines the utility functions for the SPAN IR.
// Anything that doesn't fit in other files can be put here in a common place.

import (
	"fmt"
	"strings"
)

// IsBitSet returns true if bit at position n is 1 in the given value.
func IsBitSet(value uint64, n uint) bool {
	return value&(1<<n) != 0
}

// SetBit sets the bit at position n to 1 and returns the udated value.
func SetBit(value uint64, n uint) uint64 {
	return value | (1 << n)
}

// ClearBit clears the bit at position n to 0 and returns the updated value.
func ClearBit(value uint64, n uint) uint64 {
	return value & ^(1 << n)
}

// ConstructCFG creates a control flow graph from the given instruction sequence.
// In the given instruction sequence, it checks for the following statements:
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
// The control flow graph is returned which does not belong to any function or translation unit.
func ConstructCFG(insnSeq []Insn) *ControlFlowGraph {
	cfg := NewControlFlowGraph(nil, 0, NIL_ID)
	// Create a map to track label locations and their usage
	labelToBB := make(map[LabelId]*BasicBlock)
	usedLabels := make(map[LabelId]bool)

	// First pass - identify used labels
	for _, insn := range insnSeq {
		if insn.IsIf() {
			trueLabel, falseLabel := insn.GetLabels()
			usedLabels[trueLabel] = true
			usedLabels[falseLabel] = true
		} else if insn.IsGoto() {
			targetLabel, _ := insn.GetLabels()
			usedLabels[targetLabel] = true
		}
	}

	// Second pass - split basic blocks at control flow boundaries
	var newBBs []*BasicBlock
	currBB := NewBasicBlock(BasicBlockId(NIL_ID), 0, NIL_ID, 0)
	newBBs = append(newBBs, currBB)

	for i, insn := range insnSeq {
		// Handle label statements that are jump targets
		if insn.IsLabel() {
			labelId, _ := insn.GetLabels()
			if usedLabels[labelId] && len(currBB.insns) > 0 {
				currBB = NewBasicBlock(BasicBlockId(NIL_ID), 0, NIL_ID, 0)
				newBBs = append(newBBs, currBB)
			}
			labelToBB[labelId] = currBB
		}

		// For call instructions, ensure they get their own basic block
		if insn.IsCall() || (insn.IsAssign() && insn.HasCallExpr()) {
			// If current BB has other instructions, create new BB for the call
			if len(currBB.insns) > 0 {
				currBB = NewBasicBlock(BasicBlockId(NIL_ID), 0, NIL_ID, 0)
				newBBs = append(newBBs, currBB)
			}

			// Add the call instruction to its own BB
			currBB.insns = append(currBB.insns, insn)

			// Create new BB for subsequent instructions if not last instruction
			if i < len(insnSeq)-1 {
				currBB = NewBasicBlock(BasicBlockId(NIL_ID), 0, NIL_ID, 0)
				newBBs = append(newBBs, currBB)
			}
		} else {
			if !SkipInsn(insn) {
				currBB.insns = append(currBB.insns, insn)
			}

			// Split after control flow instructions if not last instruction
			if i < len(insnSeq)-1 && (insn.IsIf() || insn.IsGoto() || insn.IsReturn()) {
				currBB = NewBasicBlock(BasicBlockId(NIL_ID), 0, NIL_ID, 0)
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
		// Find all blocks with no successors
		var exitCandidates []*BasicBlock
		for _, bb := range newBBs {
			if bb.SuccCount() == 0 {
				exitCandidates = append(exitCandidates, bb)
			}
		}

		var exitBlock *BasicBlock
		if len(exitCandidates) == 1 {
			// Single exit candidate - use it as exit block
			exitBlock = exitCandidates[0]
		} else if len(exitCandidates) > 1 {
			// Multiple exit candidates - create new exit block
			exitBlock = NewBasicBlock(BasicBlockId(NIL_ID), 0, NIL_ID, 1)

			// Connect all exit candidates to the new exit block
			for _, candidate := range exitCandidates {
				candidate.addSucc(exitBlock)
				exitBlock.addPred(candidate)
			}

			// Add the new exit block to the CFG
			cfg.AddBB(exitBlock)
		} else {
			// No blocks without successors - connect the last block to a new exit block
			lastBlock := newBBs[len(newBBs)-1]
			exitBlock = NewBasicBlock(BasicBlockId(NIL_ID), 0, NIL_ID, 1)
			lastBlock.addSucc(exitBlock)
			exitBlock.addPred(lastBlock)
		}

		// Ensure exit block has at least one instruction
		if len(exitBlock.insns) == 0 {
			exitBlock.insns = append(exitBlock.insns, NopI())
		}

		cfg.SetExitBB(exitBlock)
	}

	if !cfg.IsValid() {
		panic("Invalid CFG")
	}

	return cfg
}

func GenerateDotGraph(insnSeq []Insn) string {
	var result strings.Builder

	// DOT graph header
	result.WriteString("digraph G {\n")
	result.WriteString("  rankdir=TB;\n")
	result.WriteString("  node [shape=box, style=filled, fillcolor=lightyellow, align=left];\n")
	result.WriteString("  \n")

	// Create a single block with all instructions
	result.WriteString("  block [label=\"")

	// Add each instruction on a new line
	for i, insn := range insnSeq {
		if i > 0 {
			result.WriteString("\\n")
		}
		// Escape any quotes in the instruction string
		insnStr := strings.ReplaceAll(insn.String(), "\"", "\\\"")
		result.WriteString(insnStr)
	}

	result.WriteString("\"];\n")
	result.WriteString("}\n")

	return result.String()

}

// Generates a dot graph for the CFG with the following properties
// 1. Entry and Exit blocks have bold borders.
// 2. Each basic block is a node with its position in the array as its label.
// 3. True edges are green and false edges are red.
// 4. Each basic block contains its list of instructions (each in its own line)
// 5. Edges are labeled with the instruction that caused the jump.
// 6. BBs immediately after the true edge has light green background
// 7. BBs immediately after the false edge has light red background.
func GenerateDotGraphForCFG(cfg *ControlFlowGraph) string {
	var result strings.Builder
	bbIdMap := make(map[*BasicBlock]uint)

	// DOT graph header
	result.WriteString("digraph CFG {\n")
	result.WriteString("  rankdir=TB;\n")
	result.WriteString("  node [shape=box, style=filled, align=left];\n")
	result.WriteString("  \n")

	// Get all basic blocks
	entryBB := cfg.EntryBlock()
	exitBB := cfg.ExitBlock()
	allBBs := cfg.basicBlocks

	// Track BBs that are targets of true/false edges for coloring
	trueBBs := make(map[BasicBlockId]bool)
	falseBBs := make(map[BasicBlockId]bool)

	// First pass: identify true/false targets
	for _, bb := range allBBs {
		if bb.SuccCount() == 2 {
			trueBBs[bb.TrueSucc().id] = true
			falseBBs[bb.FalseSucc().id] = true
		}
	}

	// Generate nodes for each basic block
	for bbIdx, bb := range allBBs {
		bbIdMap[bb] = uint(bbIdx)
		// Determine node styling
		var style, fillcolor string
		if bb == entryBB || bb == exitBB {
			style = "filled,bold"
		} else {
			style = "filled"
		}

		// Set background color based on edge targeting
		if trueBBs[bb.id] && falseBBs[bb.id] {
			fillcolor = "lightgray" // Both true and false target
		} else if trueBBs[bb.id] {
			fillcolor = "lightgreen"
		} else if falseBBs[bb.id] {
			fillcolor = "lightcoral"
		} else {
			fillcolor = "white"
		}

		// Create node label with BB position and instructions
		result.WriteString(fmt.Sprintf("  BB%d [style=\"%s\", fillcolor=\"%s\", label=\"BB %d\\n",
			bbIdx, style, fillcolor, bbIdx))

		// Add instructions to the label
		for i, insn := range bb.insns {
			if i > 0 {
				result.WriteString("\\n")
			}
			// Escape quotes and backslashes in instruction string
			insnStr := strings.ReplaceAll(insn.String(), "\\", "\\\\")
			insnStr = strings.ReplaceAll(insnStr, "\"", "\\\"")
			result.WriteString(insnStr)
		}

		result.WriteString("\"];\n")
	}

	result.WriteString("  \n")

	// Generate edges
	for bbIdx, bb := range allBBs {
		fromNode := bbIdx

		// Handle successors
		for idx, succ := range bb.successors {
			toNode := bbIdMap[succ]

			// Determine edge color and label
			var color, label string

			if idx == 0 && bb.SuccCount() == 1 {
				color = "black"
				label = ""
			} else if idx == 0 && bb.SuccCount() == 2 {
				color = "green"
				label = "True"
			} else if idx == 1 {
				color = "red"
				label = "False"
			}

			// Escape quotes in label
			label = strings.ReplaceAll(label, "\"", "\\\"")

			result.WriteString(fmt.Sprintf("  BB%d -> BB%d [color=%s, label=\"%s\"];\n",
				fromNode, toNode, color, label))
		}
	}

	result.WriteString("}\n")

	return result.String()
}

// Instruction to skip when adding instructions to a basic block.
// These instructions will not be analyzed, hence not represented in the CFG.
func SkipInsn(insn Insn) bool {
	ik := insn.InsnKind()
	return ik == K_IK_ILABEL || ik == K_IK_IGOTO
}
