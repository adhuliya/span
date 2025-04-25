package analysis

import (
	"slices"

	"github.com/adhuliya/span/pkg/logger"
	"github.com/adhuliya/span/pkg/spir"
)

type VisitId uint32

type WorklistBB struct {
	graph spir.Graph
	// The worklist of Basic Blocks to be analyzed.
	worklist []spir.BasicBlockId
	stackTop int
}

func NewWorklistBB(graph spir.Graph,
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
	bbId := wl.worklist[wl.stackTop]
	wl.stackTop--
	return bbId
}

func (wl *WorklistBB) Push(bbId spir.BasicBlockId) bool {
	if wl.stackTop >= len(wl.worklist)-1 || slices.Contains(wl.worklist, bbId) {
		return false
	}
	wl.stackTop++
	wl.worklist[wl.stackTop] = bbId
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
	// The graph object to perform the analysis on.
	graph spir.Graph
	// The context object used to store the state of the analysis.
	context *spir.Context
	// The worklist of Basic Blocks to be analyzed.
	wl *WorklistBB
}

func NewIntraProceduralAnalysis(visitId VisitId, analysis Analysis,
	graph spir.Graph, context *spir.Context) *IntraProceduralAnalysis {
	return &IntraProceduralAnalysis{
		visitId:  visitId,
		analysis: analysis,
		graph:    graph,
		context:  context,
		wl:       NewWorklistBB(graph, analysis.VisitingOrder()),
	}
}

func (ipa *IntraProceduralAnalysis) AnalyzeGraph() {
	ipa.initializeContext()

	if ipa.analysis.VisitingOrder() == ReversePostOrder {
		ipa.analyzeGraphForward()
	} else {
		ipa.analyzeGraphBackward()
	}
}

func (ipa *IntraProceduralAnalysis) initializeContext() {
	if _, ok := ipa.context.GetInfo(uint32(ipa.visitId)); ok {
		return
	} else {
		factMap := make(map[spir.InsnId]LatticePair)
		//entryBBId, exitBBId := ipa.graph.EntryBlock(), ipa.graph.ExitBlock()
		boundaryFact := ipa.analysis.BoundaryFact(ipa.graph, ipa.context)
		factMap[ipa.graph.EntryBlock().Insn(0).Id()] = LatticePair{l1: boundaryFact.l1, l2: nil}
		ipa.context.SetInfo(uint32(ipa.visitId), factMap)
	}
}

func (ipa *IntraProceduralAnalysis) analyzeGraphBackward() {
	logger.Get().Info("Analyzing graph in forward direction")
}

func (ipa *IntraProceduralAnalysis) analyzeGraphForward() {
	logger.Get().Info("Analyzing graph in forward direction")
	tmp, _ := ipa.context.GetInfo(uint32(ipa.visitId))
	factMap := tmp.(map[spir.InsnId]LatticePair)

	analyze, context := ipa.analysis.Analyze, ipa.context

	// Visit each basic block
	for !ipa.wl.IsEmpty() {
		bbId := ipa.wl.Pop()
		bb := ipa.graph.BasicBlock(bbId)
		logger.Get().Debug("Visiting ", "BB", bbId)

		// Visit each instruction in the basic block
		for i := 0; i < bb.InsnCount(); i++ {
			insn := bb.Insn(i)
			logger.Get().Debug("Visiting instruction ", "Insn", insn)
			inout, change := analyze(insn, factMap[insn.Id()], context)
			logger.Get().Debug("After analysis:", "InoutFact", Stringify(&inout), "change", change)

			if change == NoChange {
				break
			}

			if change != NoChange {
				// If here, then the out fact changed from its previous value
				ipa.propagateFactForward(bb, insn, inout, factMap, i, bb.InsnCount())
			}
		}
	}
}

func (ipa *IntraProceduralAnalysis) propagateFactForward(
	bb *spir.BasicBlock, insn spir.Instruction,
	inout LatticePair, factMap map[spir.InsnId]LatticePair,
	insnIdx int, insnCount int) {
	// STEP 1: Save the computed fact for the current instruction
	factMap[insn.Id()] = inout

	// STEP 2: Propagate the fact to the successors
	if insnIdx != insnCount-1 {
		// CASE 2.1: Successor is within the basic block
		nextInsnId := bb.Insn(insnIdx + 1).Id()
		nextInOut := ipa.initializeInsnFact(nextInsnId, factMap)
		factMap[nextInsnId] = NewLatticePair(inout.L2(), nextInOut.L2())
		return
	}

	// CASE 2.2: Next insn is in the successor basic block
	outFact := inout.L2()
	trueOut, falseOut := outFact, outFact
	if bb.SuccCount() == 2 {
		if trueFalseOutFact, ok := outFact.(*LatticePair); ok {
			// If the outFact is a LatticePair, set it as the incoming fact
			trueOut, falseOut = trueFalseOutFact.L1(), trueFalseOutFact.L2()
		}
	}

	for i := range bb.SuccCount() {
		succBB := ipa.graph.BasicBlock(bb.Succ(i))
		nextInsnId := succBB.Insn(0).Id()
		nextInOut := ipa.initializeInsnFact(nextInsnId, factMap)
		// Check and add the successor basic block to the worklist
		if bb.SuccCount() == 1 {
			nextInOut = NewLatticePair(outFact, nextInOut.L2())
			ipa.wl.Push(bb.Succ(i))
		} else {
			if i == 0 && !IsTop(trueOut) && !Equals(nextInOut.L1(), trueOut) { // True edge successor
				nextInOut = NewLatticePair(Meet(nextInOut.L1(), trueOut), nextInOut.L2())
				ipa.wl.Push(bb.Succ(i))
			} else if i == 1 && !IsTop(falseOut) && !Equals(nextInOut.L2(), falseOut) { // False edge successor
				nextInOut = NewLatticePair(Meet(nextInOut.L2(), falseOut), nextInOut.L2())
				ipa.wl.Push(bb.Succ(i))
			}
		}
		factMap[nextInsnId] = nextInOut
	}
}

func (ipa *IntraProceduralAnalysis) initializeInsnFact(insnId spir.InsnId,
	factMap map[spir.InsnId]LatticePair) LatticePair {
	if _, ok := factMap[insnId]; !ok {
		factMap[insnId] = NewLatticePair(nil, nil)
	}
	return factMap[insnId]
}

func (ipa *IntraProceduralAnalysis) GetAnalysis() Analysis {
	return ipa.analysis
}

type Analyzer interface {
	analyzeGraph()
}
