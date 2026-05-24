package spir

import "fmt"

type BasicBlockId EntityId
type EdgeLabel uint8

const NIL_BB_ID = BasicBlockId(0)

// A scope controls the visibility of the variables.
type ScopeId EntityId
type CFGId EntityId

type Graph interface {
	Scope() ScopeId
	FuncId() EntityId
	BBCount() int
	EntryBlock() *BasicBlock
	ExitBlock() *BasicBlock
	BasicBlock(id BasicBlockId) *BasicBlock
}

const (
	// 2 bit labels.
	SimpleEdge EdgeLabel = 0
	TrueEdge   EdgeLabel = 1
	FalseEdge  EdgeLabel = 2
	BackEdge   EdgeLabel = 3
)

type GraphVisitingOrder uint8

const (
	NoOrder          GraphVisitingOrder = 0 // No order.
	ReversePostOrder GraphVisitingOrder = 1 // For forward flow.
	PostOrder        GraphVisitingOrder = 2 // For backward flow.
)

// A BasicBlock represents a liner code with only one entry and one eixt.
// The first instruction in the sequence is the entry and the last one is the exit.
// A basic block holds at most 64 instructions.
type BasicBlock struct {
	id           BasicBlockId
	scope        ScopeId  // A scope this BB is part of (sub-blocks in a function)
	fid          EntityId // The function this BB is part of.
	labels       []LabelId
	insns        []Insn
	insnBitMap   uint64 // 0/1 bit map of which instructions are valid in insns[]
	predecessors []*BasicBlock
	// First successor is the true edge
	// Second successor is the false edge
	successors []*BasicBlock
}

func NewBasicBlock(id BasicBlockId, scope ScopeId, fid EntityId,
	insnCount uint) *BasicBlock {
	bb := &BasicBlock{
		id:           id,
		scope:        scope,
		fid:          fid,
		insns:        nil,
		predecessors: nil,
		successors:   nil,
	}

	if insnCount > 64 {
		panic("More than 64 instruction count given.")
	}

	if insnCount > 0 {
		bb.insns = make([]Insn, 0, insnCount)
	}
	return bb
}

func (bb *BasicBlock) BBCount() int {
	return 1
}

func (bb *BasicBlock) Scope() ScopeId {
	return bb.scope
}

func (bb *BasicBlock) FuncId() EntityId {
	return bb.fid
}

func (bb *BasicBlock) EntryBlock() *BasicBlock {
	return bb
}

func (bb *BasicBlock) ExitBlock() *BasicBlock {
	return bb
}

func (bb *BasicBlock) BasicBlock(id BasicBlockId) *BasicBlock {
	if bb.id == id {
		return bb
	}
	return nil
}

func (bb *BasicBlock) Id() BasicBlockId {
	return bb.id
}

func (bb *BasicBlock) InsnCount() int {
	return len(bb.insns)
}

func (bb *BasicBlock) Insn(idx int) Insn {
	return bb.insns[idx]
}

func (bb *BasicBlock) EntryInsn() Insn {
	return bb.insns[0]
}

func (bb *BasicBlock) ExitInsn() Insn {
	return bb.insns[bb.InsnCount()-1]
}

func (bb *BasicBlock) EntryInsnId() InsnId {
	return bb.insns[0].Id()
}

func (bb *BasicBlock) ExitInsnId() InsnId {
	return bb.insns[bb.InsnCount()-1].Id()
}

func (bb *BasicBlock) PredCount() int {
	return len(bb.predecessors)
}

func (bb *BasicBlock) Pred(idx int) *BasicBlock {
	return bb.predecessors[idx]
}

func (bb *BasicBlock) SuccCount() int {
	return len(bb.successors)
}

func (bb *BasicBlock) Succ(idx int) *BasicBlock {
	return bb.successors[idx]
}

func (bb *BasicBlock) OnlySucc() *BasicBlock {
	if bb.SuccCount() == 1 {
		return bb.successors[0]
	}
	return nil
}

func (bb *BasicBlock) TrueSucc() *BasicBlock {
	if bb.SuccCount() > 0 {
		return bb.successors[0]
	}
	return nil
}

func (bb *BasicBlock) FalseSucc() *BasicBlock {
	if bb.SuccCount() == 2 {
		return bb.successors[1]
	}
	return nil
}

func (bb *BasicBlock) IsLastIndex(idx int) bool {
	return idx == bb.InsnCount()-1
}

func (bb *BasicBlock) HasOnlyOneSucc() bool {
	return bb.SuccCount() == 1
}

func (bb *BasicBlock) IsTrueSucc(succ *BasicBlock) bool {
	// a simple pointer euqality check should be fine here
	return bb.SuccCount() > 0 && bb.successors[0] == succ
}

func (bb *BasicBlock) IsFalseSucc(succ *BasicBlock) bool {
	// a simple pointer euqality check should be fine here
	return bb.SuccCount() > 1 && bb.successors[1] == succ
}

// Returns the position of the successor BB
func (bb *BasicBlock) SuccPos(succ *BasicBlock) int {
	// a simple pointer euqality check should be fine here
	switch {
	case bb.IsTrueSucc(succ):
		return 0
	case bb.IsFalseSucc(succ):
		return 1
	}
	return -1
}

func (bb *BasicBlock) addSucc(succ *BasicBlock) *BasicBlock {
	bb.successors = append(bb.successors, succ)
	return bb
}

func (bb *BasicBlock) addPred(pred *BasicBlock) *BasicBlock {
	bb.predecessors = append(bb.predecessors, pred)
	return bb
}

type ControlFlowGraph struct {
	id          CFGId
	tu          *TU
	scope       ScopeId
	fid         EntityId
	basicBlocks []*BasicBlock
	entryBlock  *BasicBlock
	exitBlock   *BasicBlock
}
type CFG = ControlFlowGraph

func (tu *TU) GetUniqueCFGId() CFGId {
	return CFGId(tu.idGen.AllocateID(GenKindPrefix16(K_EK_ECFG, 0),
		K_EK_ECFG.SeqIdBitLen()))
}

func NewControlFlowGraph(tu *TU, scope ScopeId, fid EntityId) *ControlFlowGraph {
	cfg := &ControlFlowGraph{
		id:    tu.GetUniqueCFGId(),
		tu:    tu,
		scope: scope,
		fid:   fid,
	}
	return cfg
}

func (cfg *ControlFlowGraph) BBCount() int {
	return len(cfg.basicBlocks)
}

func (cfg *ControlFlowGraph) AddBB(bb *BasicBlock) *ControlFlowGraph {
	cfg.basicBlocks = append(cfg.basicBlocks, bb)
	return cfg
}

func (cfg *ControlFlowGraph) AddBBs(bbs ...*BasicBlock) *ControlFlowGraph {
	cfg.basicBlocks = append(cfg.basicBlocks, bbs...)
	return cfg
}

func (cfg *ControlFlowGraph) SetEntryBB(bb *BasicBlock) *ControlFlowGraph {
	cfg.entryBlock = bb
	return cfg
}

func (cfg *ControlFlowGraph) SetExitBB(bb *BasicBlock) *ControlFlowGraph {
	cfg.exitBlock = bb
	return cfg
}

func (cfg *ControlFlowGraph) Id() CFGId {
	return cfg.id
}

func (cfg *ControlFlowGraph) Scope() ScopeId {
	return cfg.scope
}

func (cfg *ControlFlowGraph) FuncId() EntityId {
	return cfg.fid
}

func (cfg *ControlFlowGraph) EntryBlock() *BasicBlock {
	for i := 0; i < len(cfg.basicBlocks); i++ {
		if cfg.basicBlocks[i] == cfg.entryBlock {
			return cfg.basicBlocks[i]
		}
	}
	return nil
}

func (cfg *ControlFlowGraph) ExitBlock() *BasicBlock {
	return cfg.exitBlock
}

func (cfg *ControlFlowGraph) BasicBlock(id BasicBlockId) *BasicBlock {
	for i := 0; i < len(cfg.basicBlocks); i++ {
		if cfg.basicBlocks[i].id == id {
			return cfg.basicBlocks[i]
		}
	}
	return nil
}

// Validate the CFG
// 1. All basic blocks must have at least one successor. Except the exit block.
// 2. All basic blocks must have at least one predecessor. Except the entry block.
func (cfg *ControlFlowGraph) IsValid() bool {
	if cfg.entryBlock == nil || cfg.exitBlock == nil {
		return false
	}

	for _, bb := range cfg.basicBlocks {
		if bb == cfg.entryBlock || bb == cfg.exitBlock {
			continue
		}
		if bb.SuccCount() == 0 {
			return false
		}
		if bb.PredCount() == 0 {
			return false
		}
	}
	return true
}

// WorkList is a sequence of basic blocks to be analyzed.
// It maintains a sequence of basic blocks to be analyzed in the order of the visiting order.
// It maintains a correponding boolean list to track which basic block to visit next.
type BBWorklistRecord struct {
	bbId        BasicBlockId
	shouldVisit bool // Whether the BB is marked for visiting?
	feasible    bool // Whether the basic block is feasible to visit (like, not a dead code)
}

func (r *BBWorklistRecord) BBId() BasicBlockId {
	return r.bbId
}

func (r *BBWorklistRecord) IsFeasible() bool {
	return r.feasible
}

func (r *BBWorklistRecord) ShouldVisit() bool {
	return r.shouldVisit
}

// Visit a BB only if it is feasible and needs visiting.
func (r *BBWorklistRecord) CanVisit() bool {
	return r.feasible && r.shouldVisit
}

func (r *BBWorklistRecord) SetFeasible(feasible bool) {
	r.feasible = feasible
}

func (r *BBWorklistRecord) SetShouldVisit(shouldVisit bool) {
	r.shouldVisit = shouldVisit
}

type BBWorklist struct {
	graph         Graph
	visitOrder    GraphVisitingOrder
	bbOrderedList []BBWorklistRecord
	nextIndex     int // The index of the next basic block to visit.
}

func NewBBWorklist(graph Graph, visitOrder GraphVisitingOrder) *BBWorklist {
	wl := GetBBWorklist(graph, visitOrder, true)
	bbwl := &BBWorklist{
		graph:         graph,
		visitOrder:    visitOrder,
		bbOrderedList: wl,
		nextIndex:     0,
	}

	for i := range wl {
		bbwl.bbOrderedList[i].SetShouldVisit(true)
	}
	return bbwl
}

func (wl *BBWorklist) IsEmpty() bool {
	return wl.nextIndex == len(wl.bbOrderedList)
}

func (wl *BBWorklist) Pop() BasicBlockId {
	for i := wl.nextIndex; i < len(wl.bbOrderedList); i++ {
		if !wl.bbOrderedList[i].CanVisit() {
			continue
		}
		wl.bbOrderedList[i].SetShouldVisit(false)
		wl.nextIndex = len(wl.bbOrderedList)
		for j := i + 1; j < len(wl.bbOrderedList); j++ {
			if wl.bbOrderedList[j].CanVisit() {
				wl.nextIndex = j
				break
			}
		}
		return wl.bbOrderedList[i].BBId()
	}
	wl.nextIndex = len(wl.bbOrderedList)
	return BasicBlockId(0)
}

// Push a BB into the worklist.
// If the BB is already in the worklist, it will be marked for visiting.
// The feasibility of the BB remains unchanged.
// The return value is true if the worklist is modified.
func (wl *BBWorklist) Push(bbId BasicBlockId) bool {
	for i := range wl.bbOrderedList {
		record := &wl.bbOrderedList[i]
		if record.BBId() == bbId {
			if !record.ShouldVisit() {
				record.SetShouldVisit(true)
				if record.CanVisit() && i < wl.nextIndex {
					wl.nextIndex = i
				}
				return true // BB is marked for visiting
			}
			// Already marked for visiting
			return false
		}
	}
	// bbId not found in the worklist
	return false
}

// PushFeasible marks the given bbId as feasible and recursively marks its successor chain as feasible.
// It stops at a BB with zero or two successors.
// The visit parameter is used to mark only the given bbId for visiting.
// The return value is true if the worklist is modified.
func (wl *BBWorklist) PushFeasible(bbId BasicBlockId, visit bool) bool {
	changed := false
	// Find the index of bbId in the worklist records
	index := -1
	for i, record := range wl.bbOrderedList {
		if record.BBId() == bbId {
			index = i
			break
		}
	}
	if index == -1 {
		// bbId not found
		return false
	}

	record := &wl.bbOrderedList[index]
	// Mark as feasible and set shouldVisit if requested
	if !record.IsFeasible() {
		changed = true
		record.SetFeasible(true)
	}

	if visit && !record.ShouldVisit() {
		changed = true
		record.SetShouldVisit(true)
	}

	if record.CanVisit() && index < wl.nextIndex {
		wl.nextIndex = index
	}

	// Fetch the BasicBlock from the graph
	bb := wl.graph.BasicBlock(bbId)
	if bb == nil {
		panic(fmt.Sprintf("BasicBlock not found for bbId=%v", bbId))
	}
	// Stop recursion if the block has zero or two successors.
	if bb.SuccCount() == 0 || bb.SuccCount() == 2 {
		return changed // No need to push further
	}
	// Recursively push feasible successor BB (should only be 1 successor)
	if succ := bb.OnlySucc(); succ != nil {
		changed = wl.PushFeasible(succ.Id(), false) || changed
	}
	return changed
}

// This function takes a Graph and returns ReversePostOrder of the graph.
// The assumption is that the BBIds at lower indices are visited (or popped) first.
func GetBBWorklist(graph Graph, visitingOrder GraphVisitingOrder, feasible bool) []BBWorklistRecord {
	visited := make(map[BasicBlockId]bool, graph.BBCount())
	orderedBBs := make([]BBWorklistRecord, 0, graph.BBCount())

	// Default to a backward flow traversal (PostOrder)
	var dfs func(blockId BasicBlockId, feasible bool)
	dfs = func(blockId BasicBlockId, feasible bool) {
		if visited[blockId] {
			return
		}
		visited[blockId] = true
		block := graph.BasicBlock(blockId)
		for _, succ := range block.successors {
			dfs(succ.Id(), feasible && block.SuccCount() == 1)
		}
		orderedBBs = append(orderedBBs, BBWorklistRecord{bbId: blockId, shouldVisit: true, feasible: feasible})
	}

	entryBlock := graph.EntryBlock()
	if entryBlock != nil {
		dfs(entryBlock.id, feasible)
	}

	// Reverse the order if visiting order is ReversePostOrder
	if visitingOrder == ReversePostOrder {
		for i, j := 0, len(orderedBBs)-1; i < j; i, j = i+1, j-1 {
			orderedBBs[i], orderedBBs[j] = orderedBBs[j], orderedBBs[i]
		}
	}

	return orderedBBs
}
