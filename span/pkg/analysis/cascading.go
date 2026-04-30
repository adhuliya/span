package analysis

import (
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines the CascadingATPair interface for cascading analysis.
// Cascading analysis is a type of analysis that uses a transformation pair
// to transform the program analysis CFG (i.e. the control flow graph).
// It is used to analyze the program with a "more precise" (i.e. transformed) CFG.

type CascadingATPair interface {
	Analysis
	Transform(graph spir.Graph, factMap AnalysisFactMap, ctx *spir.Context) spir.Graph
}
