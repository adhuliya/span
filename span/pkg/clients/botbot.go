package clients

import (
	"github.com/adhuliya/span/pkg/analysis"
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines a simple BotBot analysis client.
// It defines both the forward and backward BotBot analysis clients
// which simply propagates the bot value from IN to OUT and OUT to IN respectively.

type ForwardBotBotClient struct {
	analysis.AnalysisClient
}

// Explicitly overrides (though not necessary -- good for demo)
func (c *ForwardBotBotClient) BoundaryFact(graph spir.Graph, context *spir.Context) lattice.Pair {
	return lattice.NewPair(&lattice.TopBotLatticeBot, &lattice.TopBotLatticeTop)
}

// Just propagate the IN data flow value to the OUT fact.
func (c *ForwardBotBotClient) Analyze(instruction spir.Insn,
	inOut lattice.Pair, context *spir.Context) (lattice.Pair, lattice.FactChanged) {
	factChange := lattice.NoChange
	if !lattice.Equals(inOut.L1(), inOut.L2()) {
		factChange = lattice.NopOutChanged // can also be OutChanged
	}
	inOut = lattice.NewPair(inOut.L1(), inOut.L1())
	return inOut, factChange
}

type BackwardBotBotClient struct {
	analysis.AnalysisClient
}

// Explicitly overrides (though not necessary -- good for demo)
func (c *BackwardBotBotClient) BoundaryFact(graph spir.Graph, context *spir.Context) lattice.Pair {
	return lattice.NewPair(&lattice.TopBotLatticeTop, &lattice.TopBotLatticeBot)
}

// Just propagate the OUT data flow value to the IN fact.
func (c *BackwardBotBotClient) Analyze(instruction spir.Insn,
	inOut lattice.Pair, context *spir.Context) (lattice.Pair, lattice.FactChanged) {
	factChange := lattice.NoChange
	if !lattice.Equals(inOut.L1(), inOut.L2()) {
		factChange = lattice.OnlyInChanged // could also be NopInChanged
	}
	inOut = lattice.NewPair(inOut.L2(), inOut.L2())
	return inOut, factChange
}
