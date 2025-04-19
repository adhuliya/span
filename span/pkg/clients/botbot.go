package clients

import (
	"github.com/adhuliya/span/pkg/analysis"
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines a simple BotBot analysis client.
// The BotBot is a forward analysis which simply propagates
// bot values from Entry to Exit of a given CFGraph.

type ForwardTopBotClient struct {
	name       string
	visitOrder analysis.GraphVisitingOrder
}

func NewForwardTopBotClient() *ForwardTopBotClient {
	return &ForwardTopBotClient{
		name:       "ForwardTopBotClient",
		visitOrder: analysis.ReversePostOrder,
	}
}

func (c *ForwardTopBotClient) Name() string {
	return c.name
}

func (c *ForwardTopBotClient) VisitingOrder() analysis.GraphVisitingOrder {
	return c.visitOrder
}

func (c *ForwardTopBotClient) BoundaryFact(graph spir.Graph, context *spir.Context) analysis.LatticePair {
	return *analysis.NewLatticePair(
		&analysis.TopBotLatticeBot,
		&analysis.TopBotLatticeTop,
	)
}

// Just propagate the bot to the out fact.
func (c *ForwardTopBotClient) Analyze(instruction spir.Instruction,
	inOut analysis.LatticePair, context *spir.Context) (analysis.LatticePair, analysis.FactChanged) {
	factChange := analysis.NoChange
	if analysis.IsTop(inOut.L2()) {
		factChange = analysis.OnlyOutChanged
	}
	inOut.SetL2(&analysis.TopBotLatticeBot)
	return inOut, factChange
}

func (c *ForwardTopBotClient) StmtView(instruction spir.Instruction,
	inOut analysis.LatticePair, view analysis.StmtViewType,
	context *spir.Context) []spir.Instruction {
	// No views for this client.
	return nil
}
