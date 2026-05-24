package spir

import "testing"

func recordsToIDs(records []BBWorklistRecord) []BasicBlockId {
	out := make([]BasicBlockId, len(records))
	for i, record := range records {
		out[i] = record.BBId()
	}
	return out
}

func reverseCopy(ids []BasicBlockId) []BasicBlockId {
	out := append([]BasicBlockId(nil), ids...)
	for i, j := 0, len(out)-1; i < j; i, j = i+1, j-1 {
		out[i], out[j] = out[j], out[i]
	}
	return out
}

func reachableFromEntry(graph Graph) map[BasicBlockId]bool {
	reachable := map[BasicBlockId]bool{}
	entry := graph.EntryBlock()
	if entry == nil {
		return reachable
	}

	stack := []*BasicBlock{entry}
	for len(stack) > 0 {
		bb := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if reachable[bb.Id()] {
			continue
		}
		reachable[bb.Id()] = true
		for i := 0; i < bb.SuccCount(); i++ {
			stack = append(stack, bb.Succ(i))
		}
	}
	return reachable
}

func assertUniqueAndReachable(t *testing.T, got []BasicBlockId, reachable map[BasicBlockId]bool) {
	t.Helper()

	seen := make(map[BasicBlockId]bool, len(got))
	for _, id := range got {
		if !reachable[id] {
			t.Fatalf("worklist contains unreachable block id %v", id)
		}
		if seen[id] {
			t.Fatalf("worklist contains duplicate block id %v", id)
		}
		seen[id] = true
	}

	if len(seen) != len(reachable) {
		t.Fatalf("reachable/worklist size mismatch: reachable=%d worklist=%d", len(reachable), len(seen))
	}
}

func TestGetBBWorklistOrderingAndCoverage(t *testing.T) {
	// Deterministic graph:
	//   10 -> 20, 30
	//   20 -> 40
	//   30 -> 40
	//   40 -> (exit)
	//
	// DFS postorder from entry 10 is: [40, 20, 30, 10].
	// Reverse postorder is: [10, 30, 20, 40].
	b10 := NewBasicBlock(10, 0, 0, 0)
	b20 := NewBasicBlock(20, 0, 0, 0)
	b30 := NewBasicBlock(30, 0, 0, 0)
	b40 := NewBasicBlock(40, 0, 0, 0)
	b10.successors = []*BasicBlock{b20, b30}
	b20.successors = []*BasicBlock{b40}
	b30.successors = []*BasicBlock{b40}

	graph := &getBBTestGraph{
		entry: b10,
		exit:  b40,
		blocks: map[BasicBlockId]*BasicBlock{
			b10.Id(): b10,
			b20.Id(): b20,
			b30.Id(): b30,
			b40.Id(): b40,
		},
	}
	entry := graph.EntryBlock()
	if entry == nil {
		t.Fatal("expected non-nil entry block")
	}

	postRecords := GetBBWorklist(graph, PostOrder, true)
	rpoRecords := GetBBWorklist(graph, ReversePostOrder, true)
	post := recordsToIDs(postRecords)
	rpo := recordsToIDs(rpoRecords)

	if len(postRecords) == 0 || len(rpoRecords) == 0 {
		t.Fatalf("expected non-empty worklists, post=%v rpo=%v", postRecords, rpoRecords)
	}
	if len(postRecords) != len(rpoRecords) {
		t.Fatalf("post/rpo length mismatch: %d vs %d", len(postRecords), len(rpoRecords))
	}

	reachable := reachableFromEntry(graph)
	assertUniqueAndReachable(t, post, reachable)
	assertUniqueAndReachable(t, rpo, reachable)

	revPost := reverseCopy(post)
	for i := range rpo {
		if rpo[i] != revPost[i] {
			t.Fatalf("reverse(post) mismatch at index %d: got %v, want %v", i, rpo[i], revPost[i])
		}
	}

	if rpo[0] != entry.Id() {
		t.Fatalf("reverse postorder should start with entry block %v, got %v", entry.Id(), rpo[0])
	}
	if post[len(post)-1] != entry.Id() {
		t.Fatalf("postorder should end with entry block %v, got %v", entry.Id(), post[len(post)-1])
	}
	wantPost := []BasicBlockId{40, 20, 30, 10}
	wantRPO := []BasicBlockId{10, 30, 20, 40}
	for i := range wantPost {
		if post[i] != wantPost[i] {
			t.Fatalf("unexpected postorder at index %d: got %v, want %v", i, post[i], wantPost[i])
		}
	}
	for i := range wantRPO {
		if rpo[i] != wantRPO[i] {
			t.Fatalf("unexpected reverse postorder at index %d: got %v, want %v", i, rpo[i], wantRPO[i])
		}
	}

	// Feasibility propagation starts from true at entry, then
	// becomes false after traversing a BB with 2 successors.
	wantFeasible := map[BasicBlockId]bool{
		10: true,
		20: false,
		30: false,
		40: false,
	}
	for _, record := range postRecords {
		if got, want := record.IsFeasible(), wantFeasible[record.BBId()]; got != want {
			t.Fatalf("unexpected feasible flag for bb=%v: got %v, want %v", record.BBId(), got, want)
		}
	}
}

type nilEntryGraph struct{}

func (nilEntryGraph) Scope() ScopeId                      { return 0 }
func (nilEntryGraph) FuncId() EntityId                    { return 0 }
func (nilEntryGraph) BBCount() int                        { return 0 }
func (nilEntryGraph) EntryBlock() *BasicBlock             { return nil }
func (nilEntryGraph) ExitBlock() *BasicBlock              { return nil }
func (nilEntryGraph) BasicBlock(BasicBlockId) *BasicBlock { return nil }

type getBBTestGraph struct {
	entry  *BasicBlock
	exit   *BasicBlock
	blocks map[BasicBlockId]*BasicBlock
}

func (g *getBBTestGraph) Scope() ScopeId { return 0 }

func (g *getBBTestGraph) FuncId() EntityId { return 0 }

func (g *getBBTestGraph) BBCount() int { return len(g.blocks) }

func (g *getBBTestGraph) EntryBlock() *BasicBlock { return g.entry }

func (g *getBBTestGraph) ExitBlock() *BasicBlock { return g.exit }

func (g *getBBTestGraph) BasicBlock(id BasicBlockId) *BasicBlock { return g.blocks[id] }

func TestGetBBWorklistNilEntry(t *testing.T) {
	graph := nilEntryGraph{}
	if got := GetBBWorklist(graph, PostOrder, true); len(got) != 0 {
		t.Fatalf("expected empty postorder for nil-entry graph, got %v", got)
	}
	if got := GetBBWorklist(graph, ReversePostOrder, false); len(got) != 0 {
		t.Fatalf("expected empty reverse postorder for nil-entry graph, got %v", got)
	}
}
