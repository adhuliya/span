package spir

type BasicBlockId EntityId
type EdgeLabel uint8

// A scope controls the visibility of the variables.
type ScopeId EntityId
type CFGId EntityId

type Graph interface {
	Scope() ScopeId
	FuncId() EntityId
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

type BasicBlock struct {
	id           BasicBlockId
	scope        ScopeId
	fid          EntityId
	insns        []Insn
	predecessors []*BasicBlock
	// First successor is the true edge
	// Second successor is the false edge
	successors []*BasicBlock
}

func NewBasicBlock(id BasicBlockId, scope ScopeId, fid EntityId,
	insnCount int) *BasicBlock {
	bb := &BasicBlock{
		id:           id,
		scope:        scope,
		fid:          fid,
		insns:        nil,
		predecessors: nil,
		successors:   nil,
	}

	if insnCount > 0 {
		bb.insns = make([]Insn, 0, insnCount)
	}
	return bb
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
	if succ == bb.successors[0] {
		return 0
	} else if succ == bb.successors[1] {
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
	return CFGId(tu.idGen.AllocateID(GenPrefix16(K_EK_CFG, 0),
		K_EK_CFG.SeqIdBitLength()))
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

// This function takes a Graph and returns ReversePostOrder of the graph.
func ReversePostOrder(graph Graph, reverse bool) []BasicBlockId {
	visited := make(map[BasicBlockId]bool)
	var order []BasicBlockId

	var dfs func(blockId BasicBlockId)
	dfs = func(blockId BasicBlockId) {
		if visited[blockId] {
			return
		}
		visited[blockId] = true
		block := graph.BasicBlock(blockId)
		for _, succ := range block.successors {
			dfs(succ.Id())
		}
		order = append(order, blockId)
	}

	entryBlock := graph.EntryBlock()
	if entryBlock != nil {
		dfs(entryBlock.id)
	}

	// Reverse the order if needed
	if reverse {
		for i, j := 0, len(order)-1; i < j; i, j = i+1, j-1 {
			order[i], order[j] = order[j], order[i]
		}
	}

	return order
}
