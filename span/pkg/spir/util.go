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
//
//  1. Start a new basic block with the first statement of the function.
//  2. In the given instruction sequence, it checks for the following statements:
//     a. If statement.
//     b. Goto statement.
//     c. Return statement.
//
// If such a statement is found, it becomes the last statement of the basic block.
// It starts a new basic block after these statements.
//
//  3. A Label statement starts a new basic block, with consecutive label statements
//     kept together if there is no other instruction in between them. These label
//     statements give name(s) to the basic block which later helps to connect the
//     basic blocks.
//
//  4. Every call or call assignment is kept in its own basic block,
//     with no other instructions (except label statements preceding it).
//
//  5. Connect the basic blocks as follows
//     a. Targets of If and Goto make the target basic block (with the given label) as a successor
//     of the current basic block.
//     b. A basic block without If, Goto or Return as the last statement automatically connects to
//     the basic block containing the next statement in the original sequence.
//     c. A basic block with the last statment as Return connects to the Exit basic block.
//
//  6. Create a special Exit basic block which is successor of all basic blocks without
//     any successors. This is the exit block of the CFG.
func ConstructCFG(insnSeq []Insn) *ControlFlowGraph {
	// Setup
	type LabelToBBMap map[LabelId]*BasicBlock

	var (
		bbs           []*BasicBlock        // All basic blocks, in order of creation
		currBB        *BasicBlock          // The current basic block under construction
		labelToBB     = make(LabelToBBMap) // Mapping labels to basic blocks
		insnsForBlock []Insn               // To collect instructions for the current block
		pendingLabels []LabelId            // Any label statements seen at block start
	)

	// Helper: Create or reuse the current block object
	startNewBlock := func() {
		currBB = &BasicBlock{
			insns:      nil,
			labels:     nil,
			successors: nil,
		}
		bbs = append(bbs, currBB)
	}

	// Helper: Attach pending label(s) to the current block
	attachLabelsToBlock := func() {
		if len(pendingLabels) > 0 {
			currBB.labels = make([]LabelId, len(pendingLabels))
			copy(currBB.labels, pendingLabels)
			for _, lid := range pendingLabels {
				labelToBB[lid] = currBB
			}
			pendingLabels = nil
		}
	}

	// Helper: Commit current block with its collected insns and (pending) labels
	commitCurrBB := func() {
		if currBB == nil {
			startNewBlock()
		}
		currBB.insns = append([]Insn(nil), insnsForBlock...)
		attachLabelsToBlock()
		insnsForBlock = insnsForBlock[:0]
	}

	// Pass 1: Partition instructions into basic blocks as described
	for i := 0; i < len(insnSeq); i++ {
		insn := insnSeq[i]

		// If this is a label, possibly open a new block if needed
		if insn.IsLabel() {
			// If we're at start of a block, collect the label for association
			labelId, _ := insn.GetLabels()
			// Consecutive labels should stay in the pending list
			if len(insnsForBlock) == 0 {
				pendingLabels = append(pendingLabels, labelId)
			} else {
				// Previous block ended with real instruction
				commitCurrBB()
				startNewBlock()
				pendingLabels = pendingLabels[:0]
				pendingLabels = append(pendingLabels, labelId)
			}
			continue
		}

		// Add to current block's insns
		insnsForBlock = append(insnsForBlock, insn)

		// If call/call-assignment, always end the block afterwards (except for leading labels)
		isCall := insn.IsCall()
		if isCall {
			commitCurrBB()
			startNewBlock()
			continue
		}

		// If/Return/Goto means this is a BB terminator
		if insn.IsIf() || insn.IsGoto() || insn.IsReturn() {
			commitCurrBB()
			startNewBlock()
			continue
		}
	}

	// Commit the last basic block (if has instructions)
	if len(insnsForBlock) > 0 || len(pendingLabels) > 0 {
		commitCurrBB()
	}

	// --- Pass 2: Connect basic blocks by successors according to jump/label structure ---

	// This helper function `getFirstLabel` finds the first label in a block, either from
	// the block's `labels` slice or, if none are present, by scanning for a label instruction
	// in the block's instruction list. However, it is currently unused in this function.
	// It might have been left from a previous implementation or for future extension,
	// but right now the label lookup is handled directly elsewhere.
	// Remove or comment out to silence unused variable error.

	// getFirstLabel := func(bb *BasicBlock) (LabelId, bool) {
	// 	if len(bb.labels) > 0 {
	// 		return bb.labels[0], true
	// 	}
	// 	for _, insn := range bb.insns {
	// 		if insn.IsLabel() {
	// 			lid, _ := insn.GetLabels()
	// 			return lid, true
	// 		}
	// 	}
	// 	return NIL_LABEL_ID, false
	// }

	// Build label lookup for fast block jumps if not already done
	for _, bb := range bbs {
		for _, lid := range bb.labels {
			labelToBB[lid] = bb
		}
	}

	// Traverse and connect blocks
	exitBB := &BasicBlock{insns: nil, labels: nil, successors: nil}
	for i, bb := range bbs {
		nInsns := len(bb.insns)
		if nInsns == 0 {
			// Only labels, no real statement - skip
			continue
		}
		last := bb.insns[nInsns-1]
		switch {
		case last.IsGoto():
			labelId, _ := last.GetLabels()
			if succ, ok := labelToBB[labelId]; ok {
				bb.successors = append(bb.successors, succ)
			}
		case last.IsIf():
			trueId, falseId := last.GetLabels()
			if succT, ok := labelToBB[trueId]; ok && succT != nil {
				bb.successors = append(bb.successors, succT)
			}
			if succF, ok := labelToBB[falseId]; ok && succF != nil && (succF != bb) {
				bb.successors = append(bb.successors, succF)
			}
		case last.IsReturn():
			bb.successors = append(bb.successors, exitBB)
		default:
			// Not ending in a terminator: Fallthrough successor
			if i+1 < len(bbs) {
				bb.successors = append(bb.successors, bbs[i+1])
			} else {
				// Last basic block, fallthrough to exit
				bb.successors = append(bb.successors, exitBB)
			}
		}
	}

	// Pass 3: All BBs without any successors go to exit
	for _, bb := range bbs {
		if len(bb.successors) == 0 {
			bb.successors = append(bb.successors, exitBB)
		}
	}
	exitBB.labels = []LabelId{} // No real labels, just for completeness
	bbs = append(bbs, exitBB)

	// Construct CFG struct
	cfg := &ControlFlowGraph{
		entryBlock:  bbs[0],
		exitBlock:   exitBB,
		basicBlocks: bbs,
	}

	return cfg
}

// Generates a dot graph for the CFG with the following properties
// 1. Entry and Exit blocks have bold borders.
// 2. Each basic block is a node with its position in the array as its label.
// 3. True edges are green and false edges are red.
// 4. Each basic block contains its list of instructions (each in its own line)
// 5. BBs immediately after the true edge has light green background
// 6. BBs immediately after the false edge has light red background.
func GenerateDotGraphForCFG(tu *TU, cfg *ControlFlowGraph) string {
	var sb strings.Builder

	sb.WriteString("digraph CFG {\n")
	sb.WriteString("  node [shape=box fontname=\"Consolas,Menlo,Monospace\"];\n")
	sb.WriteString("  rankdir=TB;\n")

	// Helper: map block pointer to index for unique node labels
	bbIndex := make(map[*BasicBlock]int)
	for i, bb := range cfg.basicBlocks {
		bbIndex[bb] = i
	}

	// Helper: determine if a block is entry or exit
	isEntry := func(bb *BasicBlock) bool { return bb == cfg.entryBlock }
	isExit := func(bb *BasicBlock) bool { return bb == cfg.exitBlock }

	// For fast lookup: find which blocks are immediately after a true/false edge
	trueSuccs := make(map[*BasicBlock]bool)
	falseSuccs := make(map[*BasicBlock]bool)
	for _, bb := range cfg.basicBlocks {
		n := len(bb.insns)
		if n == 0 {
			continue
		}
		last := bb.insns[n-1]
		if last.IsIf() {
			if len(bb.successors) > 0 {
				trueSucc := bb.successors[0]
				trueSuccs[trueSucc] = true
			}
			if len(bb.successors) > 1 {
				falseSucc := bb.successors[1]
				falseSuccs[falseSucc] = true
			}
		}
	}

	// Generate node for each basic block
	for i, bb := range cfg.basicBlocks {
		var style string
		var fillcolor string

		// Special style for entry/exit
		if isEntry(bb) || isExit(bb) {
			style = "bold,filled"
			fillcolor = "#FDF6E3"
		} else if trueSuccs[bb] {
			// Light green for true successor
			style = "filled"
			fillcolor = "#ccffcc"
		} else if falseSuccs[bb] {
			// Light red for false successor
			style = "filled"
			fillcolor = "#ffcccc"
		}

		labelSb := strings.Builder{}
		labelSb.WriteString(fmt.Sprintf("BB%d", i))
		if len(bb.labels) > 0 {
			lbls := make([]string, 0, len(bb.labels))
			for _, lid := range bb.labels {
				lbls = append(lbls, tu.NameOfEntityId(EntityId(lid)))
			}
			labelSb.WriteString("\\n[")
			labelSb.WriteString(strings.Join(lbls, ", "))
			labelSb.WriteString("]")
		}
		// Add instructions in block (one per line)
		for _, insn := range bb.insns {
			if SkipInsn(insn) {
				continue
			}
			labelSb.WriteString("\\n")
			labelSb.WriteString(tu.InsnString(insn, true))
		}

		// Apply node attributes
		sb.WriteString(fmt.Sprintf("  n%d [label=\"%s\"", i, labelSb.String()))
		if style != "" {
			sb.WriteString(fmt.Sprintf(" style=\"%s\"", style))
		}
		if fillcolor != "" {
			sb.WriteString(fmt.Sprintf(" fillcolor=\"%s\"", fillcolor))
		}
		sb.WriteString("];\n")
	}

	// Edges for each basic block
	for i, bb := range cfg.basicBlocks {
		for j, succ := range bb.successors {
			from := i
			to := bbIndex[succ]

			// Edge style
			var attrs []string

			// If edge is from an "if" instruction, color based on true/false
			n := len(bb.insns)
			if n > 0 && bb.insns[n-1].IsIf() {
				// By convention: true edge = first succ, false edge = second
				if j == 0 {
					attrs = append(attrs, "color=\"green\"", "penwidth=2", "label=\"T\"")
				} else if j == 1 {
					attrs = append(attrs, "color=\"red\"", "penwidth=2", "label=\"F\"")
				}
			} else if isEntry(bb) || isExit(succ) {
				attrs = append(attrs, "color=\"black\"", "penwidth=2")
			}

			sb.WriteString(fmt.Sprintf("  n%d -> n%d", from, to))
			if len(attrs) > 0 {
				sb.WriteString(fmt.Sprintf(" [%s]", strings.Join(attrs, " ")))
			}
			sb.WriteString(";\n")
		}
	}

	sb.WriteString("}\n")
	return sb.String()
}

// Instruction to skip when adding instructions to a basic block.
// These instructions will not be analyzed, hence not represented in the CFG.
func SkipInsn(insn Insn) bool {
	ik := insn.InsnKind()
	return ik == K_IK_ILABEL || ik == K_IK_IGOTO
}

// SimpleName returns the string after the last ':' character in the given name.
func SimpleName(name string) string {
	if name == "" {
		return "0name"
	}
	parts := strings.Split(name, ":")
	return parts[len(parts)-1]
}
