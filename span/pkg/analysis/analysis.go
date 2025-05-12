package analysis

import (
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir" // This file defined the analysis interface used in the SPAN program analysis engine.
)

type AnalysisId uint32
type GraphVisitingOrder uint8
type StmtViewType uint32

const (
	// A view from x = RHS to x = Top
	DeadAssignmentView StmtViewType = 0
	// A view from *x = RHS to [a = RHS, b = RHS, ...]
	// or 			x = *y  to [x = a, x = b, ...]
	DereferencedView StmtViewType = 1
	// A view from x = y to [x = 10, x = 11, ...]
	ConstantView StmtViewType = 2
)

const (
	ReversePostOrder GraphVisitingOrder = 0 // For forward flow.
	PostOrder        GraphVisitingOrder = 1 // For backward flow.
)

type Analysis interface {
	Id() AnalysisId
	Name() string
	VisitingOrder() GraphVisitingOrder
	BoundaryFact(graph spir.Graph, context *spir.Context) lattice.Pair
	Analyze(insn spir.Instruction, inOut lattice.Pair,
		context *spir.Context) (lattice.Pair, lattice.FactChanged)
}

type SpanAnalysis interface {
	Analysis
	StmtView(insn spir.Instruction, inOut lattice.Pair,
		view StmtViewType, context *spir.Context) []spir.Instruction
}

type LernersAnalysis interface {
	Analysis
	StmtGraph(insn spir.Instruction, inOut lattice.Pair,
		context *spir.Context) spir.Graph
}
