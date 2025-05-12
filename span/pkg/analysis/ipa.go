package analysis

import (
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines the inter-procedural analysis interface.

type InterPACtx interface {
	Equals(other InterPACtx) bool
	GetFact() lattice.Pair
	NewContext(callSite spir.Instruction, lp lattice.Pair, ipaCtx InterPACtx) InterPACtx
	GetCallSite() spir.Instruction
	GetParentCtx() InterPACtx
}

type InterPA interface {
	Analysis
	// Get the context for the analysis of a call site
	// Use GetContext(nil, nil, nil) to get the context for the main (entry) function.
	GetContext(callSite *spir.Instruction, lp lattice.Pair, ipaCtx InterPACtx) InterPACtx
}
