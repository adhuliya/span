package analysis

import (
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines the Lerners analysis interface.
// Lerners analysis is a lock-step uni-flow (either all forward or all backward) analysis.

type LernersAnalysis interface {
	Analysis
	StmtGraph(insn spir.Insn, inOut lattice.Pair, ctx *spir.Context) (spir.Graph, []spir.Insn)
}

type LernersAnalysisClient struct {
	AnalysisClientBase
}
