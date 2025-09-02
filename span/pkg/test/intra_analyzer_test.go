//go:build integration

package test

import (
	"os"
	"testing"

	"github.com/adhuliya/span/pkg/analysis"
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/clients"
	"github.com/adhuliya/span/pkg/logger"
	"github.com/adhuliya/span/pkg/spir"
)

func TestMain(m *testing.M) {
	// setup code here
	logger.Initialize(logger.NewLogConfig("debug"))

	code := m.Run() // runs the tests

	// teardown code here
	os.Exit(code)
}

func TestBotBotAnalysis(t *testing.T) {
	// Setup test data
	tu := spir.NewExampleTU_A()
	ctx := spir.NewContext(tu)
	botbotAn := clients.NewForwardTopBotClient()
	ctxId := spir.GetNextContextId()

	intraAnalysis := analysis.NewIntraProceduralAnalysis(
		ctxId,
		botbotAn,
		tu.GetFunction("main").GetBody(),
		ctx,
	)

	intraAnalysis.AnalyzeGraph()

	// Get the expected and actual results
	expected := lattice.TopBotLatticeBot
	result, ok := ctx.GetInfo(ctxId)
	if !ok {
		t.Fatalf("Expected info with key %d not found in context", ctxId)
	}

	res := result.(map[spir.InsnId]lattice.Pair)
	entryBB := tu.GetFunction("main").GetBody().EntryBlock()
	res2 := res[entryBB.Insn(entryBB.InsnCount()-1).Id()]
	actual, ok := res2.L2().(*lattice.TopBotLattice)
	if !ok {
		t.Fatalf("Expected L2 to be of type *TopBotLattice, but got %T", res2.L2())
	}

	// Perform test
	if !lattice.Equals(&expected, actual) {
		t.Errorf("Expected %v, but got %v", expected, actual)
	}
}
