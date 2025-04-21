package spir

type BasicBlockId EntityId
type EdgeLabel uint8

// A scope controls the visibility of the variables.
type ScopeId EntityId
type CFGId EntityId

type Graph interface {
	Scope() ScopeId
	Function() *Function
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
	insns        []Instruction
	predecessors []BasicBlockId
	// First successor is the true edge
	// Second successor is the false edge
	successors []BasicBlockId
}

type ControlFlowGraph struct {
	id          CFGId
	scope       ScopeId
	function    *Function
	basicBlocks []BasicBlock
	entryBlock  BasicBlockId
	exitBlock   BasicBlockId
}

func (cfg *ControlFlowGraph) Id() CFGId {
	return cfg.id
}

func (cfg *ControlFlowGraph) Scope() ScopeId {
	return cfg.scope
}

func (cfg *ControlFlowGraph) Function() *Function {
	return cfg.function
}

func (cfg *ControlFlowGraph) EntryBlock() *BasicBlock {
	for i := 0; i < len(cfg.basicBlocks); i++ {
		if cfg.basicBlocks[i].id == cfg.entryBlock {
			return &cfg.basicBlocks[i]
		}
	}
	return nil
}

func (cfg *ControlFlowGraph) ExitBlock() *BasicBlock {
	for i := 0; i < len(cfg.basicBlocks); i++ {
		if cfg.basicBlocks[i].id == cfg.exitBlock {
			return &cfg.basicBlocks[i]
		}
	}
	return nil
}

func (cfg *ControlFlowGraph) BasicBlock(id BasicBlockId) *BasicBlock {
	for i := 0; i < len(cfg.basicBlocks); i++ {
		if cfg.basicBlocks[i].id == id {
			return &cfg.basicBlocks[i]
		}
	}
	return nil
}

func (bb *BasicBlock) Id() BasicBlockId {
	return bb.id
}

func (bb *BasicBlock) InsnCount() int {
	return len(bb.insns)
}

func (bb *BasicBlock) Insn(idx int) Instruction {
	return bb.insns[idx]
}

func (bb *BasicBlock) PredCount() int {
	return len(bb.predecessors)
}

func (bb *BasicBlock) Pred(idx int) BasicBlockId {
	return bb.predecessors[idx]
}

func (bb *BasicBlock) SuccCount() int {
	return len(bb.successors)
}

func (bb *BasicBlock) Succ(idx int) BasicBlockId {
	return bb.successors[idx]
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
			dfs(succ)
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
