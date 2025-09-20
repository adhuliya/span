package analysis

// This file defines the analysis interface used in the SPAN program analysis engine.

import (
	"fmt"

	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

type GraphVisitingOrder uint8
type StmtViewType uint32

const (
	// A view from x = RHS to x = Top
	DeadAssignmentView StmtViewType = 0
	// A view from *x = RHS to {a = RHS, b = RHS, ...}
	// or 			x = *y  to {x = a, x = b, ...}
	DereferencedView StmtViewType = 1
	// A view from x = y to {x = 10, x = 11, ...}
	ConstantView StmtViewType = 2
	// A view from if(x) to {if(true)} or {if(false)}
	ConditionView StmtViewType = 3
)

const (
	ReversePostOrder GraphVisitingOrder = 0 // For forward flow.
	PostOrder        GraphVisitingOrder = 1 // For backward flow.
)

// A pair of facts associated with each instruction (in a graph).
type AnalysisFactMap map[spir.InsnId]lattice.Pair

// High 32 bits are the function entity id.
// Low 32 bits are the analysis' instance id (on the function)
type InstanceId uint64

const Low32BitsMask32 = 0xFFFFFFFF
const High32BitsMask64 = 0xFFFFFFFF00000000
const Shift32Bits = 32

func (id InstanceId) Low32() uint32 {
	return uint32(id & Low32BitsMask32)
}

func (id *InstanceId) SetLow32(low32 uint32) {
	*id = InstanceId(uint64(low32) | (High32BitsMask64 & uint64(*id)))
}

func (id InstanceId) High32() uint32 {
	return uint32(id & High32BitsMask64)
}

func (id *InstanceId) SetHigh32(high32 uint32) {
	*id = InstanceId((uint64(high32) << Shift32Bits) | (High32BitsMask64 & uint64(*id)))
}

func (id InstanceId) String() string {
	return fmt.Sprintf("%d", id)
}

type Analysis interface {
	InstanceId() InstanceId
	SetId(instanceId InstanceId)
	Name() string
	VisitingOrder() GraphVisitingOrder
	BoundaryFact(graph spir.Graph, context *spir.Context) lattice.Pair
	AnalyzeInsn(insn spir.Insn, inOut lattice.Pair,
		context *spir.Context) (lattice.Pair, lattice.FactChanged)
}

type SpanAnalysis interface {
	Analysis
	StmtView(insn spir.Insn, inOut lattice.Pair,
		viewType StmtViewType, context *spir.Context) []spir.Insn
	Policy(insn spir.Insn, viewType StmtViewType, view []spir.Insn,
		context *spir.Context) []spir.Insn
}

type LernersAnalysis interface {
	Analysis
	StmtGraph(insn spir.Insn, inOut lattice.Pair,
		context *spir.Context) spir.Graph
}

type AnalysisClient struct {
	instanceId InstanceId
}

func (ac *AnalysisClient) InstanceId() InstanceId {
	return ac.instanceId
}

func (ac *AnalysisClient) SetId(instanceId InstanceId) {
	ac.instanceId = instanceId
}

func (ac *AnalysisClient) Name() string {
	return "AnalysisClient"
}

// By default, assumes a forward flow analysis.
func (ac *AnalysisClient) VisitingOrder() GraphVisitingOrder {
	return ReversePostOrder
}

// A default (Bot, Top) initialization at entry and exit boundaries.
func (ac *AnalysisClient) BoundaryFact(graph spir.Graph, context *spir.Context) lattice.Pair {
	return lattice.NewPair(&lattice.TopBotLatticeBot, &lattice.TopBotLatticeTop)
}

// Just propagate the IN data flow value to the OUT fact.
func (ac *AnalysisClient) AnalyzeInsn(instruction spir.Insn,
	inOut lattice.Pair, context *spir.Context) (lattice.Pair, lattice.FactChanged) {
	factChange := lattice.NoChange
	if !lattice.Equals(inOut.L1(), inOut.L2()) {
		factChange = lattice.OnlyOutChanged
	}
	inOut = lattice.NewPair(inOut.L1(), inOut.L1())
	return inOut, factChange
}
