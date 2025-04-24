package test

import (
	"os"
	"testing"

	"github.com/adhuliya/span/pkg/analysis"
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

	intraAnalysis := analysis.NewIntraProceduralAnalysis(
		1,
		botbotAn,
		tu.GetFunction("main").GetBody(),
		ctx,
	)

	intraAnalysis.AnalyzeGraph()

	// Get the expected and actual results
	expected := analysis.TopBotLatticeBot
	result, ok := ctx.GetInfo(1)
	if !ok {
		t.Fatalf("Expected info with key 1 not found in context")
	}

	res := result.(map[spir.InsnId]analysis.LatticePair)
	res2 := res[spir.InsnId(tu.GetFunction("main").GetBody().EntryBlock().Insn(0).Id())]
	actual, ok := res2.L1().(*analysis.TopBotLattice)
	if !ok {
		t.Fatalf("Expected L1 to be of type *TopBotLattice, but got %T", res2.L1())
	}

	// Perform test
	if !analysis.Equals(&expected, actual) {
		t.Errorf("Expected %v, but got %v", expected, actual)
	}
}
