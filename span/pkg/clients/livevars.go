package clients

// Live Variables Analysis Client

import (
	"github.com/adhuliya/span/pkg/analysis"
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

type LiveVarsClient struct {
	analysis.AnalysisClient
}

func (c *LiveVarsClient) BoundaryFact(graph spir.Graph, context *spir.Context) lattice.Pair {
	// Generate the boundary information for the given graph.
	return lattice.NewPair(&lattice.TopBotLatticeTop, &lattice.TopBotLatticeTop)
}
