package analysis

import (
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines the inter-procedural analysis for the SPAN program analysis engine.

type IpaContext interface {
	Equals(other IpaContext) bool
	GetBoundaryFact() lattice.Pair
	GetNewContext(callSite spir.Instruction, lp lattice.Pair) IpaContext
	GetAnalyzer() *IntraProceduralAnalysis
}

type IPA interface {
	Analysis
	// Get the first context for the analysis
	GetInitialContext() IpaContext
	// Get the context for the analysis of a call site
	GetContext(callSite spir.Instruction, lp lattice.Pair, ipaCtx IpaContext) IpaContext
}
