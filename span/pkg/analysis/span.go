package analysis

import (
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

type StmtViewType uint32

const (
	// No view generated -- i.e. analysis does not generate a view for the given instruction
	NoView StmtViewType = 0

	// Nil view (a barrier) -- represents a disconnection in graph
	NilView StmtViewType = 1

	// A view from x = RHS to x = Top
	DeadAssignView StmtViewType = 2

	// A view from *x = RHS to {a = RHS, b = RHS, ...}
	// or 			x = *y  to {x = a, x = b, ...}
	DerefView    StmtViewType = 3
	DerefViewLhs StmtViewType = 4
	DerefViewRhs StmtViewType = 5

	// A view from x = y to {x = 10, x = 11, ...} -- a literal value
	RhsLiteralView    StmtViewType = 6
	ArrIdxLiteralView StmtViewType = 7

	// A view from if(x) to {if(1)} or {if(0)} -- a boolean value
	ConditionView StmtViewType = 8
)

type SpanAnalysis interface {
	Analysis
	StmtView(insn spir.Insn, inOut lattice.Pair,
		viewTypeRequested StmtViewType, ctx *spir.Context) (StmtViewType, []spir.Insn)
	Policy(insn spir.Insn, viewType StmtViewType, view []spir.Insn,
		ctx *spir.Context) []spir.Insn
}
