package analysis

import (
	"slices"

	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/logger"
	"github.com/adhuliya/span/pkg/spir"

	"github.com/adhuliya/span/internal/util/errs"
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

type Analyzer interface {
	InitializeAnalyzer(ctxId spir.ContextId, analysis Analysis,
		graph spir.Graph, context *spir.Context, visitOrder GraphVisitingOrder,
		factMap AnalysisFactMap) Analyzer
	AnalyzeGraph()
	Graph() spir.Graph
	GetAnalysis() Analysis
	GetContextId() spir.ContextId
	Context() *spir.Context
	FactMap() *AnalysisFactMap
	SetFactMapValue(insnId spir.InsnId, fact lattice.Pair)
	InitializeWorklist(visitOrder GraphVisitingOrder)
}

// This file defines the intra-procedural analysis for the SPAN program analysis engine.
// The intra-procedural analysis is used to analyze the program within a single procedure.
// It is used to analyze the program without considering the control-flow between procedures.

type IntraPAN struct {
	// Visitation Identifier for the analysis.
	ctxId spir.ContextId
	// The context object used to store the state of the analysis.
	context *spir.Context
	// The analysis object used to perform the analysis.
	analysis Analysis
	// The graph object to perform the analysis on.
	graph spir.Graph
	// The worklist of Basic Blocks to be analyzed.
	wl *BBWorklist
	// The fact map of the analysis.
	factMap AnalysisFactMap
	// Skip processing statements with call expression
	skipCallsKnob bool
	// Skip processing statements with call expression
	meetAtBasicBlock bool
}

func (intraPAN *IntraPAN) InitializeAnalyzer(ctxId spir.ContextId, analysis Analysis,
	graph spir.Graph, context *spir.Context, visitOrder GraphVisitingOrder,
	skipCallsKnob bool, meetAtBasicBlock bool) Analyzer {
	intraPAN.ctxId = ctxId
	intraPAN.context = context
	intraPAN.analysis = analysis
	intraPAN.graph = graph
	intraPAN.wl = NewWorklistBB(graph, visitOrder)
	intraPAN.factMap = make(AnalysisFactMap)
	intraPAN.skipCallsKnob = skipCallsKnob
	intraPAN.meetAtBasicBlock = meetAtBasicBlock
	return intraPAN
}

func (intraPAN *IntraPAN) AnalyzeGraph() {
	intraPAN.initializeContext()

	logger.Get().Info("Analyzing graph in any direction",
		"CtxId", intraPAN.ctxId, "AnalysisName", intraPAN.analysis.Name())
	tmp, _ := intraPAN.context.GetInfo(intraPAN.ctxId)
	factMap := tmp.(AnalysisFactMap)

	AnalyzeInsn, context := intraPAN.analysis.AnalyzeInsn, intraPAN.context

	// Visit each basic block
	for !intraPAN.wl.IsEmpty() {
		bbId := intraPAN.wl.Pop()
		bb := intraPAN.graph.BasicBlock(bbId)
		logger.Get().Debug("Visiting", "BB", bbId)

		// Visit each instruction in the basic block
		for i := range bb.InsnCount() {
			insn := bb.Insn(i)
			logger.Get().Debug("Visiting instruction", "Insn", insn, "InFact", factMap[insn.Id()].L1())
			inout, change := AnalyzeInsn(insn, factMap[insn.Id()], context)
			logger.Get().Debug("After analysis:", "OutFact", lattice.Stringify(inout.L2()), "change", change)

			intraPAN.propagateFacts(change, bb, insn.Id(), inout, factMap, i)
		}
	}
}

func (intraPAN *IntraPAN) initializeContext() {
	if _, ok := intraPAN.context.GetInfo(intraPAN.ctxId); ok {
		return
	} else {
		factMap := make(AnalysisFactMap)
		//entryBBId, exitBBId := intraPAN.graph.EntryBlock(), intraPAN.graph.ExitBlock()
		boundaryFact := intraPAN.analysis.BoundaryFact(intraPAN.graph, intraPAN.context)
		factMap[intraPAN.graph.EntryBlock().EntryInsn().Id()] = lattice.NewPair(boundaryFact.L1(), nil)
		factMap[intraPAN.graph.ExitBlock().ExitInsn().Id()] = lattice.NewPair(nil, boundaryFact.L2())
		intraPAN.context.SetInfo(intraPAN.ctxId, factMap)
	}
}

func (intraPAN *IntraPAN) propagateFacts(
	change lattice.FactChanged,
	bb *spir.BasicBlock, insnId spir.InsnId,
	inout lattice.Pair, factMap AnalysisFactMap,
	insnIdx int) {
	// STEP 1: Save the computed fact for the current instruction
	factMap[insnId] = inout

	if change.HasChangedIn() {
		intraPAN.propagateFactsBackward(change, bb, insnId, insnIdx, inout, factMap)
	} else if change.HasChangedOut() {
		intraPAN.propagateFactsForward(change, bb, insnId, insnIdx, inout, factMap)
	}
}

func (intraPAN *IntraPAN) propagateFactsBackward(
	change lattice.FactChanged,
	bb *spir.BasicBlock, insnId spir.InsnId, insnIdx int,
	inout lattice.Pair, factMap AnalysisFactMap) {

	// CASE 1: Propagate within the same BB
	if insnIdx != 0 {
		prevInsnId := bb.Insn(insnIdx - 1).Id()
		factMap[prevInsnId] = lattice.NewPair(factMap[prevInsnId].L1(), inout.L2())
		return
	}

	// CASE 2: Propagate to predecessor BBs
	for i := range bb.PredCount() {
		predBB := bb.Pred(i)
		predInsnId := predBB.ExitInsnId()
		thisBBSuccPos := predBB.SuccPos(bb)
		val, chg := GetPredOutFact(predBB, factMap[predInsnId], thisBBSuccPos), true

		if intraPAN.meetAtBasicBlock {
			val, chg = lattice.Meet(val, inout.L1())
		}

		factMap[predInsnId] = SetPredOutFact(predBB, factMap[predInsnId], thisBBSuccPos, val)

		if chg {
			intraPAN.wl.Push(predBB.Id())
		}
	}
}

func GetPredOutFact(predBB *spir.BasicBlock, inout lattice.Pair,
	succIdx int) lattice.Lattice {
	val := inout.L2()
	if predBB.SuccCount() > 1 {
		pair, ok := val.(*lattice.Pair)
		if !ok {
			panic("val is not a lattice pair")
		}
		return pair.Lats(succIdx)
	}
	return val
}

func SetPredOutFact(predBB *spir.BasicBlock, inout lattice.Pair,
	succIdx int, val lattice.Lattice) lattice.Pair {
	if predBB.SuccCount() == 1 {
		return lattice.NewPair(inout.L1(), val)
	} else {
		pair, _ := val.(*lattice.Pair)
		if succIdx == 0 {
			pair.SetLats(val, pair.L2())
		} else if succIdx == 1 {
			pair.SetLats(pair.L1(), val)
		}
		return lattice.NewPair(inout.L1(), pair)
	}
}

func (intraPAN *IntraPAN) propagateFactsForward(
	change lattice.FactChanged,
	bb *spir.BasicBlock, insnId spir.InsnId, insnIdx int,
	inout lattice.Pair, factMap AnalysisFactMap) {
	// CASE 1: Propagate within the same BB
	if !bb.IsLastIndex(insnIdx) {
		nextInsnId := bb.Insn(insnIdx + 1).Id()
		factMap[nextInsnId] = lattice.NewPair(inout.L2(), factMap[nextInsnId].L2())
		return
	}

	// CASE 2: Propagate to successor BBs
	trueFact, falseFact := inout.L2(), inout.L2()
	if fbb := bb.FalseSucc(); fbb != nil {
		// STEP: Extract the lattice pair
		trueFalseOutFact, ok := trueFact.(*lattice.Pair)
		errs.Assert(ok, "Out fact is not a lattice pair")
		trueFact, falseFact = trueFalseOutFact.L1(), trueFalseOutFact.L2()

		// STEP: Propagete fact
		nextInOut := factMap[fbb.EntryInsnId()]
		val, chg := falseFact, true
		if intraPAN.meetAtBasicBlock {
			val, chg = lattice.Meet(nextInOut.L1(), falseFact)
		}
		factMap[fbb.EntryInsnId()] = lattice.NewPair(val, nextInOut.L2())
		if chg {
			intraPAN.wl.Push(fbb.Id())
		}
	}

	if tbb := bb.TrueSucc(); tbb != nil {
		// STEP: Propagete fact
		nextInOut := factMap[tbb.EntryInsnId()]
		val, chg := trueFact, true
		if tbb.PredCount() > 1 || intraPAN.meetAtBasicBlock {
			val, chg = lattice.Meet(nextInOut.L1(), trueFact)
		}
		factMap[tbb.EntryInsnId()] = lattice.NewPair(val, nextInOut.L2())
		if chg {
			intraPAN.wl.Push(tbb.Id())
		}
	}
}

func (intraPAN *IntraPAN) initializeInsnFact(insnId spir.InsnId,
	factMap AnalysisFactMap) lattice.Pair {
	if _, ok := factMap[insnId]; !ok {
		factMap[insnId] = lattice.NewPair(nil, nil)
	}
	return factMap[insnId]
}

func (intraPAN *IntraPAN) GetAnalysis() Analysis {
	return intraPAN.analysis
}
