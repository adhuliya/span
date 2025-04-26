package analysis

import (
	"slices"

	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/logger"
	"github.com/adhuliya/span/pkg/spir"
)

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
	ctxId spir.ContextId
	// The analysis object used to perform the analysis.
	analysis Analysis
	// The graph object to perform the analysis on.
	graph spir.Graph
	// The context object used to store the state of the analysis.
	context *spir.Context
	// The worklist of Basic Blocks to be analyzed.
	wl *WorklistBB
}

func NewIntraProceduralAnalysis(ctxId spir.ContextId, analysis Analysis,
	graph spir.Graph, context *spir.Context) *IntraProceduralAnalysis {
	return &IntraProceduralAnalysis{
		ctxId:    ctxId,
		analysis: analysis,
		graph:    graph,
		context:  context,
		wl:       NewWorklistBB(graph, analysis.VisitingOrder()),
	}
}

func (intraPA *IntraProceduralAnalysis) AnalyzeGraph() {
	intraPA.initializeContext()

	if intraPA.analysis.VisitingOrder() == ReversePostOrder {
		intraPA.analyzeGraphForward()
	} else {
		intraPA.analyzeGraphBackward()
	}
}

func (intraPA *IntraProceduralAnalysis) initializeContext() {
	if _, ok := intraPA.context.GetInfo(intraPA.ctxId); ok {
		return
	} else {
		factMap := make(map[spir.InsnId]lattice.Pair)
		//entryBBId, exitBBId := intraPA.graph.EntryBlock(), intraPA.graph.ExitBlock()
		boundaryFact := intraPA.analysis.BoundaryFact(intraPA.graph, intraPA.context)
		factMap[intraPA.graph.EntryBlock().Insn(0).Id()] = lattice.NewPair(boundaryFact.L1(), nil)
		intraPA.context.SetInfo(intraPA.ctxId, factMap)
	}
}

func (intraPA *IntraProceduralAnalysis) analyzeGraphBackward() {
	logger.Get().Info("Analyzing graph in backward direction")
}

func (intraPA *IntraProceduralAnalysis) analyzeGraphForward() {
	logger.Get().Info("Analyzing graph in forward direction",
		"CtxId", intraPA.ctxId, "AnalysisName", intraPA.analysis.Name())
	tmp, _ := intraPA.context.GetInfo(intraPA.ctxId)
	factMap := tmp.(map[spir.InsnId]lattice.Pair)

	analyze, context := intraPA.analysis.Analyze, intraPA.context

	// Visit each basic block
	for !intraPA.wl.IsEmpty() {
		bbId := intraPA.wl.Pop()
		bb := intraPA.graph.BasicBlock(bbId)
		logger.Get().Debug("Visiting", "BB", bbId)

		// Visit each instruction in the basic block
		for i := range bb.InsnCount() {
			insn := bb.Insn(i)
			logger.Get().Debug("Visiting instruction", "Insn", insn, "InFact", factMap[insn.Id()].L1())
			inout, change := analyze(insn, factMap[insn.Id()], context)
			logger.Get().Debug("After analysis:", "OutFact", lattice.Stringify(inout.L2()), "change", change)

			intraPA.propagateFactForward(bb, insn.Id(), inout, factMap, i)
		}
	}
}

func (intraPA *IntraProceduralAnalysis) propagateFactForward(
	bb *spir.BasicBlock, insnId spir.InsnId,
	inout lattice.Pair, factMap map[spir.InsnId]lattice.Pair,
	insnIdx int) {
	// STEP 1: Save the computed fact for the current instruction
	factMap[insnId] = inout

	// STEP 2: Propagate the fact to the successors
	// CASE 2.1: Next instruction is within the basic block
	if insnIdx != bb.InsnCount()-1 {
		nextInsnId := bb.Insn(insnIdx + 1).Id()
		factMap[nextInsnId] = lattice.NewPair(inout.L2(), factMap[nextInsnId].L2())
		return
	}

	// CASE 2.2: Next instruction is in the successor basic block
	outFact := inout.L2()
	var tfFact = [2]lattice.Lattice{outFact, outFact}
	if bb.SuccCount() == 2 {
		// If the outFact is a LatticePair, set it as the incoming fact
		if trueFalseOutFact, ok := outFact.(*lattice.Pair); ok {
			tfFact[0], tfFact[1] = trueFalseOutFact.L1(), trueFalseOutFact.L2()
		}
	}

	for i := range bb.SuccCount() {
		nextInsnId := intraPA.graph.BasicBlock(bb.Succ(i)).Insn(0).Id()
		nextInOut := factMap[nextInsnId]
		val, chg := lattice.Meet(nextInOut.L1(), tfFact[i])
		factMap[nextInsnId] = lattice.NewPair(val, nextInOut.L2())
		if chg {
			intraPA.wl.Push(bb.Succ(i))
		}
	}
}

func (intraPA *IntraProceduralAnalysis) initializeInsnFact(insnId spir.InsnId,
	factMap map[spir.InsnId]lattice.Pair) lattice.Pair {
	if _, ok := factMap[insnId]; !ok {
		factMap[insnId] = lattice.NewPair(nil, nil)
	}
	return factMap[insnId]
}

func (intraPA *IntraProceduralAnalysis) GetAnalysis() Analysis {
	return intraPA.analysis
}

type Analyzer interface {
	analyzeGraph()
}
