package analysis

import (
	"slices"

	"github.com/adhuliya/span/pkg/spir"
)

type VisitId uint32

type WorklistBB struct {
	graph *spir.ControlFlowGraph
	// The worklist of Basic Blocks to be analyzed.
	worklist []spir.BasicBlockId
	stackTop int
}

func NewWorklistBB(graph *spir.ControlFlowGraph,
	visitOrder GraphVisitingOrder) *WorklistBB {
	wl := spir.ReversePostOrder(graph, visitOrder != ReversePostOrder)
	return &WorklistBB{
		graph:    graph,
		worklist: wl,
		stackTop: len(wl) - 1,
	}
}

func (wl *WorklistBB) Pop() spir.BasicBlockId {
	if wl.stackTop < 0 {
		return spir.BasicBlockId(0)
	}
	blockId := wl.worklist[wl.stackTop]
	wl.stackTop--
	return blockId
}

func (wl *WorklistBB) Push(blockId spir.BasicBlockId) bool {
	if wl.stackTop >= len(wl.worklist)-1 || slices.Contains(wl.worklist, blockId) {
		return false
	}
	wl.stackTop++
	wl.worklist[wl.stackTop] = blockId
	return true
}

func (wl *WorklistBB) IsEmpty() bool {
	return wl.stackTop < 0
}

// This file defines the intraprocedural analysis for the SPAN program analysis engine.
// The intraprocedural analysis is used to analyze the program within a single procedure.
// It is used to analyze the program without considering the control flow between procedures.

type IntraProceduralAnalysis struct {
	// Visitation Identifier for the analysis.
	visitId VisitId
	// The analysis object used to perform the analysis.
	analysis Analysis
	// The grpah object to perform the analysis on.
	graph *spir.ControlFlowGraph
	// The context object used to store the state of the analysis.
	context *spir.Context
	// The worklist of Basic Blocks to be analyzed.
	wl *WorklistBB
}

func NewIntraProceduralAnalysis(visitId VisitId, analysis Analysis,
	graph *spir.ControlFlowGraph, context *spir.Context) *IntraProceduralAnalysis {
	return &IntraProceduralAnalysis{
		visitId:  visitId,
		analysis: analysis,
		graph:    graph,
		context:  context,
		wl:       NewWorklistBB(graph, analysis.VisitingOrder()),
	}
}

func (ipa *IntraProceduralAnalysis) analyzeGraph() {
	ipa.initializeContext()

	if ipa.analysis.VisitingOrder() == ReversePostOrder {
		ipa.analyzeGraphBackward()
	} else {
		ipa.analyzeGraphForward()
	}
}

func (ipa *IntraProceduralAnalysis) initializeContext() {
	ipa.context.GetInfo(uint32(ipa.visitId))
	if _, ok := ipa.context.GetInfo(uint32(ipa.visitId)); ok {
		return
	} else {
		factMap := make(map[spir.InsnId]LatticePair)
		//entryBBId, exitBBId := ipa.graph.EntryBlock(), ipa.graph.ExitBlock()
		//boundaryFact := ipa.analysis.BoundaryFact(ipa.graph, ipa.context)
		ipa.context.SetInfo(uint32(ipa.visitId), factMap)
	}
}

func (ipa *IntraProceduralAnalysis) analyzeGraphBackward() {
}

func (ipa *IntraProceduralAnalysis) analyzeGraphForward() {
	tmp, _ := ipa.context.GetInfo(uint32(ipa.visitId))
	factMap := tmp.(map[spir.InsnId]LatticePair)

	analyze, context := ipa.analysis.Analyze, ipa.context

	// Visit each basic block
	for !ipa.wl.IsEmpty() {
		blockId := ipa.wl.Pop()
		block := ipa.graph.BasicBlock(blockId)
		insnCount := len(block.Insns())

		// Visit each instruction in the basic block
		for i := 0; i < insnCount; i++ {
			insn := block.Insns()[i]
			inout, change := analyze(insn, factMap[insn.Id()], context)

			if change == NoChange {
				break
			}

			if change != NoChange {
				// If here, then the out fact did not change from its previous value
				ipa.propagateFactForward(block, insn, inout, factMap, i, insnCount)
			}
		}
	}
}

func (ipa *IntraProceduralAnalysis) propagateFactForward(
	block *spir.BasicBlock, insn spir.Instruction,
	inout LatticePair, factMap map[spir.InsnId]LatticePair,
	insnIdx int, insnCount int) {
	// STEP 1: Save the computed fact for the current instruction
	factMap[insn.Id()] = inout

	// STEP 2: Propagate the fact to the successors
	if insnIdx != insnCount-1 {
		// CASE 2.1: Successor is within the basic block
		nextInsnId := block.Insns()[insnIdx+1].Id()
		nextInOut := ipa.initializeInsnFact(nextInsnId, factMap)
		nextInOut.SetL1(inout.L2())
		return
	}

	// CASE 2.2: Next insn is in the successor basic block
	succs, count := block.Successors(), len(block.Successors())
	outFact := inout.L2()
	trueOut, falseOut := outFact, outFact
	if count == 2 {
		if trueFalseOutFact, ok := outFact.(*LatticePair); ok {
			// If the outFact is a LatticePair, set it as the incoming fact
			trueOut, falseOut = trueFalseOutFact.L1(), trueFalseOutFact.L2()
		}
	}

	for i := 0; i < len(succs); i++ {
		succBB := ipa.graph.BasicBlock(succs[i])
		nextInsnId := succBB.Insns()[0].Id()
		nextInOut := ipa.initializeInsnFact(nextInsnId, factMap)
		// Check and add the successor basic block to the worklist
		if count == 1 {
			nextInOut.SetL1(outFact)
			ipa.wl.Push(succs[i])
		} else {
			if i == 0 && !IsTop(trueOut) && !Equals(nextInOut.L1(), trueOut) { // True edge successor
				nextInOut.SetL1(Meet(nextInOut.L1(), trueOut))
				ipa.wl.Push(succs[i])
			} else if i == 1 && !IsTop(falseOut) && !Equals(nextInOut.L2(), falseOut) { // False edge successor
				nextInOut.SetL1(Meet(nextInOut.L2(), falseOut))
				ipa.wl.Push(succs[i])
			}
		}
	}
}

func (ipa *IntraProceduralAnalysis) initializeInsnFact(insnId spir.InsnId,
	factMap map[spir.InsnId]LatticePair) LatticePair {
	if _, ok := factMap[insnId]; !ok {
		factMap[insnId] = *NewLatticePair(nil, nil)
	}
	return factMap[insnId]
}

func (ipa *IntraProceduralAnalysis) GetAnalysis() Analysis {
	return ipa.analysis
}

type Analyzer interface {
	analyzeGraph()
}
