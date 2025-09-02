package analysis

import (
	"slices"

	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/logger"
	"github.com/adhuliya/span/pkg/spir"
)

type BBWorklist struct {
	graph spir.Graph
	// The worklist of Basic Blocks to be analyzed.
	worklist []spir.BasicBlockId
	stackTop int
}

func NewWorklistBB(graph spir.Graph,
	visitOrder GraphVisitingOrder) *BBWorklist {
	wl := spir.ReversePostOrder(graph, visitOrder != ReversePostOrder)
	return &BBWorklist{
		graph:    graph,
		worklist: wl,
		stackTop: len(wl) - 1,
	}
}

func (wl *BBWorklist) Pop() spir.BasicBlockId {
	if wl.stackTop < 0 {
		return spir.BasicBlockId(0)
	}
	bbId := wl.worklist[wl.stackTop]
	wl.stackTop--
	return bbId
}

func (wl *BBWorklist) Push(bbId spir.BasicBlockId) bool {
	if wl.stackTop >= len(wl.worklist)-1 || slices.Contains(wl.worklist, bbId) {
		return false
	}
	wl.stackTop++
	wl.worklist[wl.stackTop] = bbId
	return true
}

func (wl *BBWorklist) IsEmpty() bool {
	return wl.stackTop < 0
}

// This file defines the intraprocedural analysis for the SPAN program analysis engine.
// The intraprocedural analysis is used to analyze the program within a single procedure.
// It is used to analyze the program without considering the control flow between procedures.

type IntraPAN struct {
	// Visitation Identifier for the analysis.
	ctxId spir.ContextId
	// The analysis object used to perform the analysis.
	analysis Analysis
	// The graph object to perform the analysis on.
	graph spir.Graph
	// The context object used to store the state of the analysis.
	context *spir.Context
	// The worklist of Basic Blocks to be analyzed.
	wl *BBWorklist
}

func NewIntraProceduralAnalysis(ctxId spir.ContextId, analysis Analysis,
	graph spir.Graph, context *spir.Context) *IntraPAN {
	return &IntraPAN{
		ctxId:    ctxId,
		analysis: analysis,
		graph:    graph,
		context:  context,
		wl:       NewWorklistBB(graph, analysis.VisitingOrder()),
	}
}

func (intraPAN *IntraPAN) AnalyzeGraph() {
	intraPAN.initializeContext()

	if intraPAN.analysis.VisitingOrder() == ReversePostOrder {
		intraPAN.analyzeGraphForward()
	} else {
		intraPAN.analyzeGraphBackward()
	}
}

func (intraPAN *IntraPAN) initializeContext() {
	if _, ok := intraPAN.context.GetInfo(intraPAN.ctxId); ok {
		return
	} else {
		factMap := make(map[spir.InsnId]lattice.Pair)
		//entryBBId, exitBBId := intraPAN.graph.EntryBlock(), intraPAN.graph.ExitBlock()
		boundaryFact := intraPAN.analysis.BoundaryFact(intraPAN.graph, intraPAN.context)
		factMap[intraPAN.graph.EntryBlock().Insn(0).Id()] = lattice.NewPair(boundaryFact.L1(), nil)
		intraPAN.context.SetInfo(intraPAN.ctxId, factMap)
	}
}

func (intraPAN *IntraPAN) analyzeGraphBackward() {
	logger.Get().Info("Analyzing graph in backward direction")
}

func (intraPAN *IntraPAN) analyzeGraphForward() {
	logger.Get().Info("Analyzing graph in forward direction",
		"CtxId", intraPAN.ctxId, "AnalysisName", intraPAN.analysis.Name())
	tmp, _ := intraPAN.context.GetInfo(intraPAN.ctxId)
	factMap := tmp.(map[spir.InsnId]lattice.Pair)

	analyze, context := intraPAN.analysis.Analyze, intraPAN.context

	// Visit each basic block
	for !intraPAN.wl.IsEmpty() {
		bbId := intraPAN.wl.Pop()
		bb := intraPAN.graph.BasicBlock(bbId)
		logger.Get().Debug("Visiting", "BB", bbId)

		// Visit each instruction in the basic block
		for i := range bb.InsnCount() {
			insn := bb.Insn(i)
			logger.Get().Debug("Visiting instruction", "Insn", insn, "InFact", factMap[insn.Id()].L1())
			inout, change := analyze(insn, factMap[insn.Id()], context)
			logger.Get().Debug("After analysis:", "OutFact", lattice.Stringify(inout.L2()), "change", change)

			intraPAN.propagateFactForward(bb, insn.Id(), inout, factMap, i)
		}
	}
}

func (intraPAN *IntraPAN) propagateFactForward(
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
		nextInsnId := intraPAN.graph.BasicBlock(bb.Succ(i).Id()).Insn(0).Id()
		nextInOut := factMap[nextInsnId]
		val, chg := lattice.Meet(nextInOut.L1(), tfFact[i])
		factMap[nextInsnId] = lattice.NewPair(val, nextInOut.L2())
		if chg {
			intraPAN.wl.Push(bb.Succ(i).Id())
		}
	}
}

func (intraPAN *IntraPAN) initializeInsnFact(insnId spir.InsnId,
	factMap map[spir.InsnId]lattice.Pair) lattice.Pair {
	if _, ok := factMap[insnId]; !ok {
		factMap[insnId] = lattice.NewPair(nil, nil)
	}
	return factMap[insnId]
}

func (intraPAN *IntraPAN) GetAnalysis() Analysis {
	return intraPAN.analysis
}

type Analyzer interface {
	analyzeGraph()
}
