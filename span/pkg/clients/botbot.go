package clients

import (
	"github.com/adhuliya/span/pkg/analysis"
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines a simple BotBot analysis client.
// The BotBot is a forward analysis which simply propagates
// bot values from Entry to Exit of a given CFGraph.

type ForwardBotBotClient struct {
	id         analysis.AnalysisId
	name       string
	visitOrder analysis.GraphVisitingOrder
}

func NewForwardTopBotClient() *ForwardBotBotClient {
	return &ForwardBotBotClient{
		id:         0,
		name:       "ForwardBotBotClient",
		visitOrder: analysis.ReversePostOrder,
	}
}

func (c *ForwardBotBotClient) Id() analysis.AnalysisId {
	return c.id
}

func (c *ForwardBotBotClient) Name() string {
	return c.name
}

func (c *ForwardBotBotClient) VisitingOrder() analysis.GraphVisitingOrder {
	return c.visitOrder
}

func (c *ForwardBotBotClient) BoundaryFact(graph spir.Graph, context *spir.Context) lattice.Pair {
	return lattice.NewPair(&lattice.TopBotLatticeBot, &lattice.TopBotLatticeTop)
}

// Just propagate the bot to the out fact.
func (c *ForwardBotBotClient) Analyze(instruction spir.Instruction,
	inOut lattice.Pair, context *spir.Context) (lattice.Pair, lattice.FactChanged) {
	factChange := lattice.NoChange
	if lattice.IsTop(inOut.L2()) {
		factChange = lattice.OnlyOutChanged
	}
	inOut = lattice.NewPair(inOut.L1(), &lattice.TopBotLatticeBot)
	return inOut, factChange
}
