package clients

import (
	"github.com/adhuliya/span/pkg/analysis"
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines a simple BotBot analysis client.
// The BotBot is a forward analysis which simply propagates
// bot values from Entry to Exit of a given CFGraph.

type ForwardBotBotClient struct {
	name       string
	visitOrder analysis.GraphVisitingOrder
}

func NewForwardTopBotClient() *ForwardBotBotClient {
	return &ForwardBotBotClient{
		name:       "ForwardBotBotClient",
		visitOrder: analysis.ReversePostOrder,
	}
}

func (c *ForwardBotBotClient) Name() string {
	return c.name
}

func (c *ForwardBotBotClient) VisitingOrder() analysis.GraphVisitingOrder {
	return c.visitOrder
}

func (c *ForwardBotBotClient) BoundaryFact(graph spir.Graph, context *spir.Context) analysis.LatticePair {
	return analysis.NewLatticePair(
		&analysis.TopBotLatticeBot,
		&analysis.TopBotLatticeTop,
	)
}

// Just propagate the bot to the out fact.
func (c *ForwardBotBotClient) Analyze(instruction spir.Instruction,
	inOut analysis.LatticePair, context *spir.Context) (analysis.LatticePair, analysis.FactChanged) {
	factChange := analysis.NoChange
	if analysis.IsTop(inOut.L2()) {
		factChange = analysis.OnlyOutChanged
	}
	inOut = analysis.NewLatticePair(inOut.L1(), &analysis.TopBotLatticeBot)
	return inOut, factChange
}

func (c *ForwardBotBotClient) StmtView(instruction spir.Instruction,
	inOut analysis.LatticePair, view analysis.StmtViewType,
	context *spir.Context) []spir.Instruction {
	// No views for this client.
	return nil
}
