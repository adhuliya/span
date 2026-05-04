package analysis

/* For an analysis engine, we need the following major components:
1. A worklist of basic blocks to be analyzed.
2. Iterate over the worklist and analyze each basic block.
3. Propagate the facts forward/backward through the control flow graph.
4. Combine the facts at the boundaries of the analysis.
5. Update the worklist with the new basic blocks to be analyzed.
6. Keep analyzing until the worklist is empty.
*/

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

func NewWorklistBB(graph spir.Graph, visitOrder spir.GraphVisitingOrder) *BBWorklist {
	wl := spir.GetBBWorklist(graph, visitOrder)
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
	if wl.stackTop >= wl.graph.BBCount()-1 || slices.Contains(wl.worklist, bbId) {
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
	AnalyzeGraph() lattice.FactChanged

	// Methods to get information about the analysis engine.
	Graph() spir.Graph
	GetAnalysis() Analysis
	GetContextId() spir.ContextId
	Context() *spir.Context
	FactMap() *AnalysisFactMap
	// Set the value of the fact map for the given instruction id.
	// This is used by inter-procedural analyses to set the fact map value for a call site.
	SetFactMapValue(insnId spir.InsnId, fact lattice.Pair)
	// Get the fact map value for the given instruction id.
	// This is used by inter-procedural analyses to get the fact map value for a call site.
	GetFactMapValue(insnId spir.InsnId) lattice.Pair
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
	// Analysis handles basic blocks explicitly.
	analysisHandlesBB bool
	// Skip processing statements with call expression
	// If true, the analysis engine will not propagate facts through call statements.
	// If false, the facts will be over-approximated when propagated through call statements.
	// Default is false; i.e. an intra-procedural analysis.
	skipCallsKnob bool
	// Apply meet operation at basic block boundary
	meetAtBasicBlock bool
}

func NewIntraPAN(ctxId spir.ContextId, analysis Analysis,
	graph spir.Graph, context *spir.Context,
	skipCallsKnob bool, meetAtBasicBlock bool) Analyzer {
	intra := &IntraPAN{
		ctxId:            ctxId,
		context:          context,
		analysis:         analysis,
		graph:            graph,
		wl:               NewWorklistBB(graph, analysis.VisitingOrder()),
		skipCallsKnob:    skipCallsKnob,
		meetAtBasicBlock: meetAtBasicBlock,
	}
	intra.initialize() // Initialize the fact map.
	return Analyzer(intra)
}

func (intra *IntraPAN) initialize() {
	if _, ok := intra.context.GetInfo(uint64(intra.ctxId)); ok {
		return // Already initialized.
	}

	// 1. Initialize the fact map.
	intra.factMap = make(AnalysisFactMap)
	factId := lattice.NIL_FACT_ID.WithFactPoint(lattice.FactIdUB_Point_INOUT).
		WithAnalysisId(intra.analysis.InstanceId().AnalysisId())
	//entryBBId, exitBBId := intra.graph.EntryBlock(), intra.graph.ExitBlock()
	boundaryFact := intra.analysis.BoundaryFact(intra.graph, intra.context)
	entryInsnId := intra.graph.EntryBlock().EntryInsn().Id()
	exitInsnId := intra.graph.ExitBlock().ExitInsn().Id()
	if entryInsnId == exitInsnId {
		intra.factMap[entryInsnId] = lattice.NewPair(boundaryFact.L1(), boundaryFact.L2(),
			factId.WithUBEntityId(spir.EntityId(entryInsnId)))
	} else {
		intra.factMap[entryInsnId] = lattice.NewPair(boundaryFact.L1(), nil,
			factId.WithUBEntityId(spir.EntityId(entryInsnId)))
		intra.factMap[exitInsnId] = lattice.NewPair(nil, boundaryFact.L2(),
			factId.WithUBEntityId(spir.EntityId(exitInsnId)))
	}
	intra.context.SetInfo(uint64(intra.ctxId), intra.factMap)

	// 2. Initialize the analysis handles basic blocks flag.
	_, change := intra.analysis.AnalyzeBB(nil, lattice.NewPair(nil, nil, lattice.NIL_FACT_ID), intra.context)
	if change == lattice.NotImplemented {
		intra.analysisHandlesBB = false
	} else {
		intra.analysisHandlesBB = true
	}
}

func (intra *IntraPAN) Context() *spir.Context {
	return intra.context
}

func (intra *IntraPAN) GetAnalysis() Analysis {
	return intra.analysis
}

func (intra *IntraPAN) GetContextId() spir.ContextId {
	return intra.ctxId
}

func (intra *IntraPAN) FactMap() *AnalysisFactMap {
	return &intra.factMap
}

func (intra *IntraPAN) Graph() spir.Graph {
	return intra.graph
}

func (intra *IntraPAN) SetFactMapValue(insnId spir.InsnId, fact lattice.Pair) {
	intra.factMap[insnId] = fact
}

func (intra *IntraPAN) GetFactMapValue(insnId spir.InsnId) lattice.Pair {
	if _, ok := intra.factMap[insnId]; !ok {
		intra.factMap[insnId] = lattice.NewPair(nil, nil,
			lattice.NIL_FACT_ID.WithFactPoint(lattice.FactIdUB_Point_INOUT).
				WithAnalysisId(intra.analysis.InstanceId().AnalysisId()).
				WithUBEntityId(spir.EntityId(insnId)))
	}
	return intra.factMap[insnId]
}

func (intra *IntraPAN) GetBBFact(bb *spir.BasicBlock) lattice.Pair {
	entryInsnId := bb.EntryInsnId()
	exitInsnId := bb.ExitInsnId()
	entryFact := intra.GetFactMapValue(entryInsnId).L1()
	exitFact := intra.GetFactMapValue(exitInsnId).L2()

	return lattice.NewPair(entryFact, exitFact,
		lattice.NIL_FACT_ID.WithFactPoint(lattice.FactIdUB_Point_INOUT).
			WithAnalysisId(intra.analysis.InstanceId().AnalysisId()).
			WithUBEntityId(spir.EntityId(bb.Id())))
}

// AnalyzeGraph performs intra-procedural analysis on the program.
// It iterates over the worklist of basic blocks, updating analysis facts until a fixed point is reached,
// then stores the result in the context object.
func (intra *IntraPAN) AnalyzeGraph() lattice.FactChanged {
	factChange := lattice.NoChange
	for !intra.wl.IsEmpty() {
		bbId := intra.wl.Pop()
		bb := intra.graph.BasicBlock(bbId)

		logger.Get().Debug("Visiting", "BB", bbId)
		inout, change := intra.AnalyzeBB(bb)
		logger.Get().Debug("After analysis:", "OutFact", lattice.String(inout.L2()), "change", change)

		if change.HasChange() {
			// The fact map changed
			factChange = lattice.Changed
			intra.propagateFacts(change, bb, inout)
		}
	}
	return factChange
}

func (intra *IntraPAN) AnalyzeBB(bb *spir.BasicBlock) (lattice.Pair, lattice.FactChanged) {
	// Visit each instruction in the basic block and propagate the facts.
	// Use the analysis's AnalyzeBB method if it handles basic blocks explicitly.
	if intra.analysisHandlesBB {
		bbInOut := intra.GetBBFact(bb)
		return intra.analysis.AnalyzeBB(bb, bbInOut, intra.context)
	}

	// Otherwise, visit each instruction in the basic block and propagate the facts.
	reverse := intra.analysis.VisitingOrder() == spir.PostOrder
	firstIndx, lastIndx := 0, bb.InsnCount()-1
	bbInChanged, bbOutChanged := false, false
	var inout lattice.Pair
	change := lattice.NoChange

	for i := range bb.InsnCount() {
		i = InsnIndex(i, lastIndx, reverse)
		insn := bb.Insn(i)

		logger.Get().Debug("Before analysis:", "Insn", insn, "InFact", intra.GetFactMapValue(insn.Id()).L1())
		inout, change = intra.analysis.AnalyzeInsn(insn, intra.GetFactMapValue(insn.Id()), intra.context)
		logger.Get().Debug("After  analysis:", "Insn", insn, "OutFact", inout.L2(), "change", change)

		// Record changes at the boundaries of the basic block.
		bbInChanged = bbInChanged || (i == firstIndx && change.HasChangedIn())
		bbOutChanged = bbOutChanged || (i == lastIndx && change.HasChangedOut())

		if !change.HasChange() {
			break // No need to propagate further. This is an optimization.
		}

		// Save and Propagate the facts to the next instruction.
		intra.SetFactMapValue(insn.Id(), inout) // Save
		nextInsnIdx := InsnIndex(i+1, lastIndx, reverse)
		if i != nextInsnIdx {
			nextInsnId := bb.Insn(nextInsnIdx).Id()
			nextInsnInOut := intra.GetFactMapValue(nextInsnId)
			intra.SetFactMapValue(nextInsnId,
				nextInsnInOut.UpdateOther(change, inout.ChangedOne(change))) // Propagate
		}
	}
	return intra.GetBBFact(bb), lattice.GetInOutChanged(bbInChanged, bbOutChanged)
}

// Returns the index of the instruction in the basic block.
// If reverse is true, the index is returned in reverse order (i.e. i = 0 translates to lastIndx).
// The returned index is always in the range [0, lastIndx].
func InsnIndex(i int, lastIndx int, reverse bool) int {
	if reverse {
		if i == lastIndx {
			return lastIndx
		}
		return lastIndx - i
	}

	if i == 0 {
		return 0
	}
	return i
}

func (intra *IntraPAN) propagateFacts(change lattice.FactChanged,
	bb *spir.BasicBlock, inout lattice.Pair) {
	if change.HasChangedIn() {
		intra.propagateFactsBackward(change, bb, inout)
	}
	if change.HasChangedOut() {
		intra.propagateFactsForward(change, bb, inout)
	}
}

// Propagate facts backward to predecessor BBs.
func (intra *IntraPAN) propagateFactsBackward(
	change lattice.FactChanged,
	bb *spir.BasicBlock, inout lattice.Pair) {

	for i := range bb.PredCount() {
		predBB := bb.Pred(i)
		predInsnId := predBB.ExitInsnId()
		thisBBSuccPos := predBB.SuccPos(bb)
		val, chg := GetPredOutFact(predBB, intra.GetFactMapValue(predInsnId), thisBBSuccPos), true

		if intra.meetAtBasicBlock {
			val, chg = lattice.Meet(val, inout.L1())
		}

		intra.SetFactMapValue(predInsnId, SetPredOutFact(predBB, intra.GetFactMapValue(predInsnId), thisBBSuccPos, val))

		if chg {
			intra.wl.Push(predBB.Id())
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
		return lattice.NewPair(inout.L1(), val, inout.FactId())
	} else {
		pair, _ := val.(*lattice.Pair)
		if succIdx == 0 {
			pair.SetLats(val, pair.L2())
		} else if succIdx == 1 {
			pair.SetLats(pair.L1(), val)
		}
		return lattice.NewPair(inout.L1(), pair, inout.FactId())
	}
}

func (intra *IntraPAN) propagateFactsForward(
	change lattice.FactChanged,
	bb *spir.BasicBlock, inout lattice.Pair) {
	trueFact, falseFact := inout.L2(), inout.L2()

	// This condition is taken only if there are two successors.
	if fbb := bb.FalseSucc(); fbb != nil {
		// STEP: Extract the lattice pair
		trueFalseOutFact, ok := trueFact.(*lattice.Pair)
		errs.Assert(ok, "Out fact is not a lattice pair")
		trueFact, falseFact = trueFalseOutFact.L1(), trueFalseOutFact.L2()

		// STEP: Propagete fact
		nextInOut := intra.GetFactMapValue(fbb.EntryInsnId())
		val, chg := falseFact, true
		if intra.meetAtBasicBlock {
			val, chg = lattice.Meet(nextInOut.L1(), falseFact)
		}
		intra.SetFactMapValue(fbb.EntryInsnId(), lattice.NewPair(val, nextInOut.L2(), nextInOut.FactId()))
		if chg {
			intra.wl.Push(fbb.Id())
		}
	}

	// Here, the trueFact is either the OUT or the true part of the OUT lattice pair.
	if tbb := bb.TrueSucc(); tbb != nil {
		// STEP: Propagete fact
		nextInOut := intra.GetFactMapValue(tbb.EntryInsnId())
		val, chg := trueFact, true
		if tbb.PredCount() > 1 || intra.meetAtBasicBlock {
			val, chg = lattice.Meet(nextInOut.L1(), trueFact)
		}
		intra.SetFactMapValue(tbb.EntryInsnId(), lattice.NewPair(val, nextInOut.L2(), nextInOut.FactId()))
		if chg {
			intra.wl.Push(tbb.Id())
		}
	}
}
