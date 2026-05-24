package spir

import "testing"

type bbWorklistGraph struct {
	entry  *BasicBlock
	exit   *BasicBlock
	blocks map[BasicBlockId]*BasicBlock
}

func (g *bbWorklistGraph) Scope() ScopeId                         { return 0 }
func (g *bbWorklistGraph) FuncId() EntityId                       { return 0 }
func (g *bbWorklistGraph) BBCount() int                           { return len(g.blocks) }
func (g *bbWorklistGraph) EntryBlock() *BasicBlock                { return g.entry }
func (g *bbWorklistGraph) ExitBlock() *BasicBlock                 { return g.exit }
func (g *bbWorklistGraph) BasicBlock(id BasicBlockId) *BasicBlock { return g.blocks[id] }

func lookupRecord(records []BBWorklistRecord, bbId BasicBlockId) *BBWorklistRecord {
	for i := range records {
		if records[i].BBId() == bbId {
			return &records[i]
		}
	}
	return nil
}

func TestBBWorklistPushRequeuesConsumedBlock(t *testing.T) {
	b1 := NewBasicBlock(1, 0, 0, 0)
	b2 := NewBasicBlock(2, 0, 0, 0)
	b3 := NewBasicBlock(3, 0, 0, 0)
	b1.successors = []*BasicBlock{b2}
	b2.successors = []*BasicBlock{b3}

	graph := &bbWorklistGraph{
		entry: b1,
		exit:  b3,
		blocks: map[BasicBlockId]*BasicBlock{
			1: b1,
			2: b2,
			3: b3,
		},
	}

	wl := NewBBWorklist(graph, ReversePostOrder)
	if got := wl.Pop(); got != 1 {
		t.Fatalf("expected first pop to return 1, got %v", got)
	}

	if changed := wl.Push(1); !changed {
		t.Fatal("expected push to re-queue consumed BB 1")
	}
	if got := wl.Pop(); got != 1 {
		t.Fatalf("expected re-queued pop to return 1, got %v", got)
	}
	if changed := wl.Push(99); changed {
		t.Fatal("expected push of unknown BB id to be ignored")
	}
}

func TestPushFeasibleMarksLinearChainAndSetsNextIndex(t *testing.T) {
	b1 := NewBasicBlock(1, 0, 0, 0)
	b2 := NewBasicBlock(2, 0, 0, 0)
	b3 := NewBasicBlock(3, 0, 0, 0)
	b4 := NewBasicBlock(4, 0, 0, 0)
	b5 := NewBasicBlock(5, 0, 0, 0)

	b1.successors = []*BasicBlock{b2}
	b2.successors = []*BasicBlock{b3}
	b3.successors = []*BasicBlock{b4, b5}

	graph := &bbWorklistGraph{
		entry: b1,
		exit:  b5,
		blocks: map[BasicBlockId]*BasicBlock{
			1: b1,
			2: b2,
			3: b3,
			4: b4,
			5: b5,
		},
	}

	records := GetBBWorklist(graph, ReversePostOrder, false)
	for i := range records {
		records[i].SetShouldVisit(false)
	}

	wl := &BBWorklist{
		graph:         graph,
		visitOrder:    ReversePostOrder,
		bbOrderedList: records,
		nextIndex:     len(records),
	}
	if !wl.IsEmpty() {
		t.Fatal("expected empty worklist before pushing feasible BBs")
	}

	if changed := wl.PushFeasible(1, true); !changed {
		t.Fatal("expected PushFeasible to modify worklist")
	}

	expectRecord := func(bbId BasicBlockId, feasible, shouldVisit bool) {
		t.Helper()
		record := lookupRecord(wl.bbOrderedList, bbId)
		if record == nil {
			t.Fatalf("missing record for BB %v", bbId)
		}
		if record.IsFeasible() != feasible || record.ShouldVisit() != shouldVisit {
			t.Fatalf("record mismatch for BB %v: got feasible=%v shouldVisit=%v, want feasible=%v shouldVisit=%v",
				bbId, record.IsFeasible(), record.ShouldVisit(), feasible, shouldVisit)
		}
	}

	expectRecord(1, true, true)
	expectRecord(2, true, false)
	expectRecord(3, true, false)
	expectRecord(4, false, false)
	expectRecord(5, false, false)

	if wl.IsEmpty() {
		t.Fatal("expected non-empty worklist after visiting BB 1")
	}
	if got := wl.Pop(); got != 1 {
		t.Fatalf("expected pop to return BB 1, got %v", got)
	}

	if changed := wl.PushFeasible(2, false); changed {
		t.Fatal("expected no-op when pushing already feasible BB with visit=false")
	}
	if changed := wl.PushFeasible(2, true); !changed {
		t.Fatal("expected pushing BB 2 with visit=true to modify worklist")
	}
	if got := wl.Pop(); got != 2 {
		t.Fatalf("expected pop to return BB 2, got %v", got)
	}
}

func TestControlFlowGraphIsValid(t *testing.T) {
	b1 := NewBasicBlock(1, 0, 0, 0)
	b2 := NewBasicBlock(2, 0, 0, 0)
	b3 := NewBasicBlock(3, 0, 0, 0)

	b1.successors = []*BasicBlock{b2}
	b2.predecessors = []*BasicBlock{b1}
	b2.successors = []*BasicBlock{b3}
	b3.predecessors = []*BasicBlock{b2}

	cfg := &ControlFlowGraph{
		basicBlocks: []*BasicBlock{b1, b2, b3},
		entryBlock:  b1,
		exitBlock:   b3,
	}
	if !cfg.IsValid() {
		t.Fatal("expected CFG to be valid")
	}

	b2.successors = nil
	if cfg.IsValid() {
		t.Fatal("expected CFG to be invalid when middle BB has no successor")
	}
}
