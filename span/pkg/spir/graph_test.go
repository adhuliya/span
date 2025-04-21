// graph_test.go
package spir

import (
	"reflect"
	"testing"
)

// --- Mock Graph Implementation for Testing ---

type mockBasicBlock struct {
	mockId           BasicBlockId
	mockSuccessors   []BasicBlockId
	mockPredecessors []BasicBlockId // Not strictly needed for RPO, but good practice
}

func (m *mockBasicBlock) Id() BasicBlockId          { return m.mockId }
func (m *mockBasicBlock) InsnCount() int            { return 0 }             // Not needed for RPO
func (m *mockBasicBlock) Insn(idx int) Instruction  { return Instruction{} } // Not needed for RPO
func (m *mockBasicBlock) PredCount() int            { return len(m.mockPredecessors) }
func (m *mockBasicBlock) Pred(idx int) BasicBlockId { return m.mockPredecessors[idx] }
func (m *mockBasicBlock) SuccCount() int            { return len(m.mockSuccessors) }
func (m *mockBasicBlock) Succ(idx int) BasicBlockId { return m.mockSuccessors[idx] }

// Implement the BasicBlock methods needed by the Graph interface adapter below
func (m *mockBasicBlock) basicBlockAdapter() *BasicBlock {
	// This adapter is needed because the Graph interface returns *BasicBlock,
	// but our mock uses mockBasicBlock. We create a temporary BasicBlock
	// wrapper when needed by the Graph interface methods.
	return &BasicBlock{
		id:           m.mockId,
		insns:        nil, // Not needed
		predecessors: m.mockPredecessors,
		successors:   m.mockSuccessors,
	}
}

type mockGraph struct {
	mockScope      ScopeId
	mockFunc       *Function // Can be nil for these tests
	mockEntryBlock BasicBlockId
	mockExitBlock  BasicBlockId // Not directly used by RPO, but part of the interface
	mockBlocks     map[BasicBlockId]*mockBasicBlock
}

func newMockGraph(entry, exit BasicBlockId) *mockGraph {
	return &mockGraph{
		mockEntryBlock: entry,
		mockExitBlock:  exit,
		mockBlocks:     make(map[BasicBlockId]*mockBasicBlock),
	}
}

func (mg *mockGraph) addBlock(id BasicBlockId, successors ...BasicBlockId) {
	// Basic predecessor tracking (optional for RPO but useful)
	preds := []BasicBlockId{}
	for _, b := range mg.mockBlocks {
		for _, succ := range b.mockSuccessors {
			if succ == id {
				preds = append(preds, b.mockId)
				break // Add only once per predecessor block
			}
		}
	}

	mg.mockBlocks[id] = &mockBasicBlock{
		mockId:           id,
		mockSuccessors:   successors,
		mockPredecessors: preds, // Store calculated predecessors
	}

	// Update predecessors of successor blocks
	for _, succId := range successors {
		if succBlock, exists := mg.mockBlocks[succId]; exists {
			// Avoid duplicate entries
			found := false
			for _, predId := range succBlock.mockPredecessors {
				if predId == id {
					found = true
					break
				}
			}
			if !found {
				succBlock.mockPredecessors = append(succBlock.mockPredecessors, id)
			}
		}
	}
}

func (mg *mockGraph) Scope() ScopeId      { return mg.mockScope }
func (mg *mockGraph) Function() *Function { return mg.mockFunc }
func (mg *mockGraph) EntryBlock() *BasicBlock {
	if bb, ok := mg.mockBlocks[mg.mockEntryBlock]; ok {
		return bb.basicBlockAdapter()
	}
	return nil
}
func (mg *mockGraph) ExitBlock() *BasicBlock {
	if bb, ok := mg.mockBlocks[mg.mockExitBlock]; ok {
		return bb.basicBlockAdapter()
	}
	return nil
}
func (mg *mockGraph) BasicBlock(id BasicBlockId) *BasicBlock {
	if bb, ok := mg.mockBlocks[id]; ok {
		// Use the adapter here
		return bb.basicBlockAdapter()
	}
	return nil
}

// --- Test Cases ---

func TestReversePostOrder(t *testing.T) {
	// Define some block IDs for clarity
	b1 := BasicBlockId(1)
	b2 := BasicBlockId(2)
	b3 := BasicBlockId(3)
	b4 := BasicBlockId(4)
	b5 := BasicBlockId(5)
	b6 := BasicBlockId(6)

	testCases := []struct {
		name            string
		graphSetup      func() Graph
		expectedPost    []BasicBlockId // reverse = false
		expectedReverse []BasicBlockId // reverse = true
	}{
		{
			name: "Linear Graph",
			// A -> B -> C (Exit)
			graphSetup: func() Graph {
				graph := newMockGraph(b1, b3)
				graph.addBlock(b1, b2)
				graph.addBlock(b2, b3)
				graph.addBlock(b3) // Exit block
				return graph
			},
			expectedPost:    []BasicBlockId{b3, b2, b1},
			expectedReverse: []BasicBlockId{b1, b2, b3},
		},
		{
			name: "Simple Branch",
			//    A
			//   / \
			//  B   C
			//   \ /
			//    D (Exit)
			graphSetup: func() Graph {
				graph := newMockGraph(b1, b4)
				graph.addBlock(b1, b2, b3)
				graph.addBlock(b2, b4)
				graph.addBlock(b3, b4)
				graph.addBlock(b4) // Exit block
				return graph
			},
			// DFS might visit B then C, or C then B. Both lead to valid PostOrders.
			// Option 1 (A->B->D, then A->C->D): PostOrder: D, B, C, A | RPO: A, C, B, D
			// Option 2 (A->C->D, then A->B->D): PostOrder: D, C, B, A | RPO: A, B, C, D
			// We'll test against one possibility (Option 2 here). The core idea is D is first in Post, A is last.
			expectedPost:    []BasicBlockId{b4, b2, b3, b1}, // Assumes C visited before B in DFS from A
			expectedReverse: []BasicBlockId{b1, b3, b2, b4}, // Assumes B visited before C in RPO construction
		},
		{
			name: "Graph with Loop",
			// A -> B -> C -> D (Exit)
			//      ^----|
			graphSetup: func() Graph {
				graph := newMockGraph(b1, b4)
				graph.addBlock(b1, b2)
				graph.addBlock(b2, b3)
				graph.addBlock(b3, b2, b4) // Loop back to B, also exit path to D
				graph.addBlock(b4)         // Exit block
				return graph
			},
			// DFS: A -> B -> C -> (B visited) -> D.
			expectedPost:    []BasicBlockId{b4, b3, b2, b1},
			expectedReverse: []BasicBlockId{b1, b2, b3, b4},
		},
		{
			name: "Single Block Graph",
			// A (Entry & Exit)
			graphSetup: func() Graph {
				graph := newMockGraph(b1, b1)
				graph.addBlock(b1)
				return graph
			},
			expectedPost:    []BasicBlockId{b1},
			expectedReverse: []BasicBlockId{b1},
		},
		{
			name: "Disconnected Component (ignored)",
			// A -> B (Exit)
			// C -> D
			graphSetup: func() Graph {
				graph := newMockGraph(b1, b2) // Entry is A, Exit is B
				graph.addBlock(b1, b2)
				graph.addBlock(b2)
				graph.addBlock(b3, b4) // C, D are disconnected from entry A
				graph.addBlock(b4)
				return graph
			},
			expectedPost:    []BasicBlockId{b2, b1}, // Only A, B should be visited
			expectedReverse: []BasicBlockId{b1, b2},
		},
		{
			name: "More Complex Graph",
			//      A
			//     / \
			//    B   C
			//    |   | \
			//    D   E  F
			//     \ /  /
			//      G (Exit)
			graphSetup: func() Graph {
				graph := newMockGraph(b1, BasicBlockId(7)) // A is entry, G is exit
				g := BasicBlockId(7)
				graph.addBlock(b1, b2, b3) // A -> B, C
				graph.addBlock(b2, b4)     // B -> D
				graph.addBlock(b3, b5, b6) // C -> E, F
				graph.addBlock(b4, g)      // D -> G
				graph.addBlock(b5, g)      // E -> G
				graph.addBlock(b6, g)      // F -> G
				graph.addBlock(g)          // G (Exit)
				return graph
			},
			// Possible DFS paths and resulting PostOrder (depends on successor order):
			// Path: A->B->D->G, A->C->E->G, A->C->F->G
			// PostOrder: G, D, B, E, F, C, A (if B branch first, then C->E, then C->F)
			expectedPost: []BasicBlockId{BasicBlockId(7), b4, b2, b5, b6, b3, b1},
			// RPO: A, C, F, E, B, D, G (Reverse of the above)
			expectedReverse: []BasicBlockId{b1, b3, b6, b5, b2, b4, BasicBlockId(7)},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			graph := tc.graphSetup()

			// Test PostOrder (reverse = false)
			postOrder := ReversePostOrder(graph, false)
			// Note: Due to map iteration non-determinism in DFS successor processing,
			// multiple valid PostOrders might exist. We compare against one possibility.
			// A more robust test might check properties (e.g., exit node first, entry node last)
			// but direct comparison is simpler if successor order is predictable or fixed.
			// For these tests, we assume a consistent (though arbitrary) DFS traversal order.
			if !reflect.DeepEqual(postOrder, tc.expectedPost) {
				t.Errorf("PostOrder mismatch:\ngot:  %v\nwant: %v", postOrder, tc.expectedPost)
			}

			// Test Reverse PostOrder (reverse = true)
			reverseOrder := ReversePostOrder(graph, true)
			if !reflect.DeepEqual(reverseOrder, tc.expectedReverse) {
				t.Errorf("ReversePostOrder mismatch:\ngot:  %v\nwant: %v", reverseOrder, tc.expectedReverse)
			}
		})
	}

	t.Run("Nil Entry Block", func(t *testing.T) {
		graph := newMockGraph(BasicBlockId(99), BasicBlockId(1)) // Entry 99 doesn't exist
		graph.addBlock(b1)                                       // Add some block so graph isn't totally empty

		postOrder := ReversePostOrder(graph, false)
		if len(postOrder) != 0 {
			t.Errorf("Expected empty order when entry block is nil, got %v", postOrder)
		}
		reverseOrder := ReversePostOrder(graph, true)
		if len(reverseOrder) != 0 {
			t.Errorf("Expected empty order when entry block is nil, got %v", reverseOrder)
		}
	})
}
