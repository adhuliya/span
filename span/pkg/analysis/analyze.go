package analysis

/* For an analysis engine, we need the following major components:
1. A worklist of basic blocks to be analyzed.
2. Iterate over the worklist and analyze each basic block.
3. Propagate the facts forward/backward through the control flow graph.
4. Merge the facts at merge points in the control flow graph.
5. Update the worklist with the new basic blocks to be analyzed.
6. Keep analyzing until the worklist is empty.
*/

import (
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/logger"
	"github.com/adhuliya/span/pkg/spir"

	"github.com/adhuliya/span/internal/util/errs"
)

type Analyzer interface {
	AnalyzeGraph() lattice.FactChanged

	// Methods to get information about the analysis engine.
	Graph() spir.Graph
	GetAnalysis() Analysis
	GetContextId() spir.ContextId
	Context() *spir.Context
	// Set the value of the fact map for the given instruction id.
	SetFactMapValue(insnId spir.InsnId, fact lattice.Pair)
	// Get the fact map value for the given instruction id.
	GetFactMapValue(insnId spir.InsnId) lattice.Pair
	// Set/Get the value of the fact map for the given basic block id.
	SetBBFactMapValue(bbId spir.BasicBlockId, fact lattice.Pair)
	GetBBFactMapValue(bbId spir.BasicBlockId) lattice.Pair
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
	// The fact map of the analysis.
	factMap   InsnFactMap
	bbFactMap BBFactMap
	// The fact map of the call sites (co-updated by Intra and Inter-procedural analyses)
	// Holds instruction id of the call instruction to the pair fact map.
	callSiteFactMap InsnFactMap
	// Analysis handles basic blocks explicitly.
	analysisHandlesBB bool
	// Skip processing statements with call expression
	// If true, the analysis engine will not propagate facts through call statements.
	// If false, the facts will be over-approximated when propagated through call statements.
	// Default is false; i.e. an intra-procedural analysis.
	skipCallsKnob bool
	// Apply meet operation at basic block boundary
	meetAtBB bool
	// Use instruction fact map along with basic block fact map.
	useInstFactMap bool
}

func NewIntraPAN(ctxId spir.ContextId, analysis Analysis,
	graph spir.Graph, context *spir.Context,
	skipCallsKnob bool, meetAtBasicBlock bool, useInstFactMap bool) Analyzer {
	intra := &IntraPAN{
		ctxId:          ctxId,
		context:        context,
		analysis:       analysis,
		graph:          graph,
		skipCallsKnob:  skipCallsKnob,
		meetAtBB:       meetAtBasicBlock,
		useInstFactMap: useInstFactMap,
	}
	intra.initialize() // Initialize the fact map.
	return Analyzer(intra)
}

func (intra *IntraPAN) initialize() {
	if _, ok := intra.context.GetInfo(uint64(intra.ctxId)); ok {
		return // Already initialized.
	}

	// 1. Initialize the fact map.
	intra.factMap = make(InsnFactMap)
	intra.bbFactMap = make(BBFactMap)
	factId := lattice.NIL_FACT_ID.WithFactPoint(lattice.FactIdUB_Point_INOUT).
		WithAnalysisId(intra.analysis.InstanceId().AnalysisId())
	//entryBBId, exitBBId := intra.graph.EntryBlock(), intra.graph.ExitBlock()
	boundaryFact := intra.analysis.BoundaryFact(intra.graph, intra.context)
	entryInsnId := intra.graph.EntryBlock().EntryInsn().Id()
	exitInsnId := intra.graph.ExitBlock().ExitInsn().Id()
	if intra.graph.EntryBlock() == intra.graph.ExitBlock() {
		if intra.useInstFactMap {
			intra.factMap[entryInsnId] = lattice.NewPair(boundaryFact.L1(), boundaryFact.L2(),
				factId.WithUBEntityId(spir.EntityId(entryInsnId)))
		}
		intra.bbFactMap[intra.graph.EntryBlock().Id()] = lattice.NewPair(boundaryFact.L1(), boundaryFact.L2(),
			factId.WithUBEntityId(spir.EntityId(intra.graph.EntryBlock().Id())))
	} else {
		if intra.useInstFactMap {
			intra.factMap[entryInsnId] = lattice.NewPair(boundaryFact.L1(), nil,
				factId.WithUBEntityId(spir.EntityId(entryInsnId)))
			intra.factMap[exitInsnId] = lattice.NewPair(nil, boundaryFact.L2(),
				factId.WithUBEntityId(spir.EntityId(exitInsnId)))
		}
		intra.bbFactMap[intra.graph.EntryBlock().Id()] = lattice.NewPair(boundaryFact.L1(), nil,
			factId.WithUBEntityId(spir.EntityId(intra.graph.EntryBlock().Id())))
		intra.bbFactMap[intra.graph.ExitBlock().Id()] = lattice.NewPair(nil, boundaryFact.L2(),
			factId.WithUBEntityId(spir.EntityId(intra.graph.ExitBlock().Id())))
	}
	intra.context.SetInfo(uint64(intra.ctxId), intra.factMap)

	// 2. Check if the analysis handles basic blocks explicitly, and set the flag accordingly.
	intra.analysisHandlesBB = CanAnalysisHandleBBs(intra.analysis, intra.context)
}

func CanAnalysisHandleBBs(analysis Analysis, context *spir.Context) bool {
	_, change := analysis.AnalyzeBB(nil, lattice.NewPair(nil, nil, lattice.NIL_FACT_ID), context)
	return change != lattice.NotImplemented
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

func (intra *IntraPAN) FactMap() *InsnFactMap {
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

func (intra *IntraPAN) SetBBFactMapValue(bbId spir.BasicBlockId, fact lattice.Pair) {
	intra.bbFactMap[bbId] = fact
}

func (intra *IntraPAN) GetBBFactMapValue(bbId spir.BasicBlockId) lattice.Pair {
	if _, ok := intra.bbFactMap[bbId]; !ok {
		intra.bbFactMap[bbId] = lattice.NewPair(nil, nil,
			lattice.NIL_FACT_ID.WithFactPoint(lattice.FactIdUB_Point_INOUT).
				WithAnalysisId(intra.analysis.InstanceId().AnalysisId()).
				WithUBEntityId(spir.EntityId(bbId)))
	}
	return intra.bbFactMap[bbId]
}

func (intra *IntraPAN) SetCallSiteFactMapValue(callSiteId spir.InsnId, fact lattice.Pair) {
	intra.callSiteFactMap[callSiteId] = fact
}

func (intra *IntraPAN) GetCallSiteFactMapValue(callSiteId spir.InsnId) lattice.Pair {
	if _, ok := intra.callSiteFactMap[callSiteId]; !ok {
		intra.callSiteFactMap[callSiteId] = lattice.NewPair(nil, nil,
			lattice.NIL_FACT_ID.WithFactPoint(lattice.FactIdUB_Point_INOUT).
				WithAnalysisId(intra.analysis.InstanceId().AnalysisId()).
				WithUBEntityId(spir.EntityId(callSiteId)))
	}
	return intra.callSiteFactMap[callSiteId]
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
// It returns the fact change status of the analysis.
func (intra *IntraPAN) AnalyzeGraph() lattice.FactChanged {
	factChange := lattice.NoChange
	wl := intra.analysis.WorkList()
	for bbId := wl.Pop(); bbId != spir.NIL_BB_ID; bbId = wl.Pop() {
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
	bbInOut := intra.GetBBFactMapValue(bb.Id())
	if intra.analysisHandlesBB {
		return intra.analysis.AnalyzeBB(bb, bbInOut, intra.context)
	}

	// Otherwise, visit each instruction in the basic block and propagate the facts.
	reverse := intra.analysis.VisitingOrder() == spir.PostOrder
	prevInOut := bbInOut
	firstIndx, lastIndx := 0, bb.InsnCount()-1
	bbInChanged, bbOutChanged := false, false
	var inout lattice.Pair
	change := lattice.NoChange

	for i := range bb.InsnCount() {
		i = InsnIndex(i, lastIndx, reverse)
		insn := bb.Insn(i)

		logger.Get().Debug("Before analysis:", "Insn", insn, "InFact", intra.GetFactMapValue(insn.Id()).L1())
		oldInOut := intra.GetCurrentFactMapValue(insn.Id(), i, bb.InsnCount(), bbInOut, prevInOut, reverse)
		inout, change = intra.analysis.AnalyzeInsn(insn, oldInOut, intra.context)
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
		prevInOut = inout
	}
	return intra.GetBBFact(bb), lattice.GetInOutChanged(bbInChanged, bbOutChanged)
}

func (intra *IntraPAN) GetCurrentFactMapValue(insnId spir.InsnId, index int, insnCount int,
	bbInOut, prevInsnInOut lattice.Pair, reverse bool) lattice.Pair {
	first, last := index == 0, index == insnCount-1
	var oldInOut lattice.Pair

	// Fact for each instruction is stored in the instruction fact map.
	// Fetch the fact from the instruction fact map, and modify it based on the flow direction.
	if intra.useInstFactMap {
		oldInOut = intra.GetFactMapValue(insnId)
		if first && !reverse /*forward flow*/ {
			oldInOut.SetLats(bbInOut.L1(), oldInOut.L2())
		} else if last && reverse /*backward flow*/ {
			oldInOut.SetLats(oldInOut.L1(), bbInOut.L2())
		} else if !reverse /*forward flow*/ {
			oldInOut.SetLats(prevInsnInOut.L2(), oldInOut.L2())
		} else /*if reverse; i.e. backward flow*/ {
			oldInOut.SetLats(oldInOut.L1(), prevInsnInOut.L1())
		}
		return oldInOut
	}

	// Facts for instructions are not stored in the instruction fact map.
	// Generate the lattice pair for the instructions.
	factId := lattice.NIL_FACT_ID.WithFactPoint(lattice.FactIdUB_Point_INOUT).
		WithAnalysisId(intra.analysis.InstanceId().AnalysisId()).
		WithUBEntityId(spir.EntityId(insnId))
	if first && !reverse /*forward flow*/ {
		oldInOut = lattice.NewPair(bbInOut.L1(), nil, factId)
	} else if last && reverse /*backward flow*/ {
		oldInOut = lattice.NewPair(nil, bbInOut.L2(), factId)
	} else if !reverse /*forward flow*/ {
		oldInOut = lattice.NewPair(prevInsnInOut.L2(), nil, factId)
	} else /*if reverse; i.e. backward flow*/ {
		oldInOut = lattice.NewPair(nil, prevInsnInOut.L1(), factId)
	}

	return oldInOut
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
		// If the L1 lattice is a Chained lattice, flatten it before propagating.
		if chained, ok := inout.L1().(lattice.ChainedLattice); ok {
			_, changed := chained.Flatten(true)
			inout.FactId().CondIncVersion(changed)
		}
		intra.propagateFactsBackward(bb, inout)
	}
	if change.HasChangedOut() {
		// If the L2 lattice is a Chained lattice, flatten it before propagating.
		if chained, ok := inout.L2().(lattice.ChainedLattice); ok {
			_, changed := chained.Flatten(true)
			inout.FactId().CondIncVersion(changed)
		}
		intra.propagateFactsForward(bb, inout)
	}
}

// Propagate facts backward to predecessor BBs.
func (intra *IntraPAN) propagateFactsBackward(bb *spir.BasicBlock, inout lattice.Pair) {

	for i := range bb.PredCount() {
		predBB := bb.Pred(i)
		thisBBSuccPos := predBB.SuccPos(bb)
		val, chg := GetPredBBOutFact(predBB, intra.GetBBFactMapValue(predBB.Id()), thisBBSuccPos), true

		if intra.meetAtBB {
			val, chg = lattice.Meet(val, inout.L1())
		}

		intra.SetBBFactMapValue(predBB.Id(),
			SetPredBBOutFact(predBB, intra.GetBBFactMapValue(predBB.Id()), thisBBSuccPos, val))

		if chg {
			intra.analysis.WorkList().Push(predBB.Id())
		}
	}
}

func GetPredBBOutFact(predBB *spir.BasicBlock, inout lattice.Pair,
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

func SetPredBBOutFact(predBB *spir.BasicBlock, inout lattice.Pair,
	succIdx int, val lattice.Lattice) lattice.Pair {
	if predBB.SuccCount() == 1 {
		return lattice.NewPair(inout.L1(), val, inout.FactId())
	} else {
		pair, _ := val.(*lattice.Pair)
		switch succIdx {
		case 0:
			pair.SetLats(val, pair.L2())
		case 1:
			pair.SetLats(pair.L1(), val)
		}
		return lattice.NewPair(inout.L1(), pair, inout.FactId())
	}
}

func (intra *IntraPAN) propagateFactsForward(
	bb *spir.BasicBlock, inout lattice.Pair) {
	trueFact, falseFact := inout.L2(), inout.L2()

	// This condition is taken only if there are two successors.
	if fbb := bb.FalseSucc(); fbb != nil {
		// Extract the lattice pair, then propagate the fact.
		trueFalseOutFact, ok := trueFact.(*lattice.Pair)
		errs.Assert(ok, "Out fact is not a lattice pair")
		trueFact, falseFact = trueFalseOutFact.L1(), trueFalseOutFact.L2()

		nextInOut := intra.GetBBFactMapValue(fbb.Id())
		val, chg := falseFact, true
		if intra.meetAtBB {
			val, chg = lattice.Meet(nextInOut.L1(), falseFact)
		}
		intra.SetBBFactMapValue(fbb.Id(), lattice.NewPair(val, nextInOut.L2(), nextInOut.FactId()))
		if chg {
			intra.analysis.WorkList().PushFeasible(fbb.Id(), true)
		}
	}

	// Here, the trueFact is either the OUT or the true part of the lattice pair in OUT.
	if tbb := bb.TrueSucc(); tbb != nil {
		nextInOut := intra.GetBBFactMapValue(tbb.Id())
		val, chg := trueFact, true
		if tbb.PredCount() > 1 || intra.meetAtBB {
			val, chg = lattice.Meet(nextInOut.L1(), trueFact)
		}
		intra.SetBBFactMapValue(tbb.Id(), lattice.NewPair(val, nextInOut.L2(), nextInOut.FactId()))
		if chg {
			intra.analysis.WorkList().PushFeasible(tbb.Id(), true)
		}
	}
}
