package analysis

import "github.com/adhuliya/span/pkg/spir"

// This file defined the analysis interface used in the SPAN program analysis engine.

type GraphVisitingOrder uint8
type StmtViewType uint32
type FactChanged uint8

const (
	OnlyInChanged  FactChanged = 0
	OnlyOutChanged FactChanged = 1
	InOutChanged   FactChanged = 2
	NoChange       FactChanged = 3
)

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
	Name() string
	VisitingOrder() GraphVisitingOrder
	BoundaryFact(graph spir.Graph, context *spir.Context) LatticePair
	Analyze(instruction spir.Instruction,
		inOut LatticePair, context *spir.Context) (LatticePair, FactChanged)
	StmtView(instruction spir.Instruction,
		inOut LatticePair, view StmtViewType,
		context *spir.Context) []spir.Instruction
}
