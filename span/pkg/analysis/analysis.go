package analysis

// This file defines the analysis interface used in the SPAN program analysis engine.

import (
	"fmt"

	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

// A pair of facts associated with each instruction (in a graph).
type AnalysisFactMap map[spir.InsnId]lattice.Pair

// High 32 bits are the function entity id.
// Low 32 bits are the analysis' instance id (on the function)
type InstanceId uint64

const AnalysisIdBits = 12
const AnalysisIdMask = (1 << AnalysisIdBits) - 1
const AnalysisIdShift = 0
const FuncIdBits = 32
const FuncIdMask = (1 << FuncIdBits) - 1
const FuncIdShift = AnalysisIdBits + 0

func (id InstanceId) AnalysisId() lattice.AnalysisId {
	return lattice.AnalysisId((id >> AnalysisIdShift) & AnalysisIdMask)
}

func (id InstanceId) WithAnalysisId(analysisId lattice.AnalysisId) InstanceId {
	return InstanceId((uint64(analysisId) << AnalysisIdShift) | (uint64(id) & ^(uint64(AnalysisIdMask) << AnalysisIdShift)))
}

func (id InstanceId) FuncId() spir.EntityId {
	return spir.EntityId((id >> FuncIdShift) & FuncIdMask)
}

func (id InstanceId) WithFuncId(funcId spir.EntityId) InstanceId {
	return InstanceId((uint64(funcId) << FuncIdShift) | (uint64(id) & ^(uint64(FuncIdMask) << FuncIdShift)))
}

func (id InstanceId) String() string {
	return fmt.Sprintf("AnalysisId: %d, FuncId: %s", id.AnalysisId(), id.FuncId())
}

type Analysis interface {
	InstanceId() InstanceId
	SetInstanceId(instanceId InstanceId)
	Name() string

	VisitingOrder() spir.GraphVisitingOrder
	BoundaryFact(graph spir.Graph, ctx *spir.Context) lattice.Pair
	NewNonNilTopLattice(factId lattice.FactId) lattice.Lattice

	AnalyzeInsn(insn spir.Insn, inOut lattice.Pair,
		ctx *spir.Context) (lattice.Pair, lattice.FactChanged)
	AnalyzeBB(bb *spir.BasicBlock, inOut lattice.Pair,
		ctx *spir.Context) (lattice.Pair, lattice.FactChanged)
}

type AnalysisClientBase struct {
	instanceId    InstanceId
	name          string
	visitingOrder spir.GraphVisitingOrder
}

func (ac *AnalysisClientBase) Name() string {
	return ac.name
}

func (ac *AnalysisClientBase) SetName(name string) {
	ac.name = name
}

func (ac *AnalysisClientBase) InstanceId() InstanceId {
	return ac.instanceId
}

func (ac *AnalysisClientBase) SetInstanceId(instanceId InstanceId) {
	ac.instanceId = instanceId
}

func (ac *AnalysisClientBase) AnalysisId() lattice.AnalysisId {
	return ac.instanceId.AnalysisId()
}

func (ac *AnalysisClientBase) FuncId() spir.EntityId {
	return ac.instanceId.FuncId()
}

// By default, assumes a forward flow analysis.
func (ac *AnalysisClientBase) VisitingOrder() spir.GraphVisitingOrder {
	if ac.visitingOrder == 0 {
		return spir.ReversePostOrder
	}
	return ac.visitingOrder
}

func (ac *AnalysisClientBase) SetVisitingOrder(visitingOrder spir.GraphVisitingOrder) {
	ac.visitingOrder = visitingOrder
}

// A default (Bot, Top) initialization at entry and exit boundaries.
func (ac *AnalysisClientBase) BoundaryFact(graph spir.Graph, ctx *spir.Context) lattice.Pair {
	return lattice.NewPair(&lattice.TopBotLatticeBot, &lattice.TopBotLatticeTop,
		lattice.NIL_FACT_ID.WithAnalysisId(ac.AnalysisId()).
			WithUBEntityId(ctx.CurrentScopeEid()).
			WithFactPoint(lattice.FactIdUB_Point_INOUT))
}

// (Default) Just propagate the IN data flow value to the OUT fact.
func (ac *AnalysisClientBase) AnalyzeInsn(instruction spir.Insn,
	inOut lattice.Pair, ctx *spir.Context) (lattice.Pair, lattice.FactChanged) {
	factChange := lattice.NoChange
	if !lattice.Equals(inOut.L1(), inOut.L2()) {
		factChange = lattice.OutChanged
	}
	inOut = lattice.NewPair(inOut.L1(), inOut.L1(), inOut.FactId())
	return inOut, factChange
}

// (Default) Not implemented.
func (ac *AnalysisClientBase) AnalyzeBB(bb *spir.BasicBlock,
	inOut lattice.Pair, ctx *spir.Context) (lattice.Pair, lattice.FactChanged) {
	return inOut, lattice.NotImplemented
}
