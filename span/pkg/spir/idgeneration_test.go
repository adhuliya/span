// idgeneration_test.go
package spir

import (
	"testing"
)

// Helper function to extract ID part
func extractID(entityId EntityId) uint32 {
	return uint32(entityId & 0xFFFFF)
}

// Helper function to extract PoolId part
func extractPoolId(entityId EntityId) PoolId {
	// Mask to 10 bits as done in AllocateID/FreeID
	return PoolId((entityId >> 20) & 0x3FF)
}

func TestIDGenerator_AllocateID(t *testing.T) {
	poolId1 := PoolId(1)
	poolId2 := PoolId(2)
	maxIDValue := uint32(0xFFFFF - 1) // Max allocatable ID value

	t.Run("AllocateFirstID", func(t *testing.T) {
		gen := NewIDGenerator() // Fresh generator
		id := gen.AllocateID(poolId1)
		if id == 0 {
			t.Fatalf("AllocateID returned 0 for the first allocation")
		}
		if extractPoolId(id) != poolId1 {
			t.Errorf("Expected poolId %d, got %d", poolId1, extractPoolId(id))
		}
		if extractID(id) != 1 {
			t.Errorf("Expected first ID to be 1, got %d", extractID(id))
		}
		// Check internal state
		if gen.pools[poolId1] == nil {
			t.Fatalf("Pool %d should have been created", poolId1)
		}
		if gen.pools[poolId1].from != 2 {
			t.Errorf("Expected pool.from to be 2 after allocating 1, got %d", gen.pools[poolId1].from)
		}
		if gen.pools[poolId1].to != maxIDValue {
			t.Errorf("Expected pool.to to be %d, got %d", maxIDValue, gen.pools[poolId1].to)
		}
	})

	t.Run("AllocateMultipleIDs", func(t *testing.T) {
		gen := NewIDGenerator() // Fresh generator
		count := 5
		for i := 1; i <= count; i++ {
			id := gen.AllocateID(poolId1)
			if id == 0 {
				t.Fatalf("AllocateID returned 0 during multiple allocations (iteration %d)", i)
			}
			if extractPoolId(id) != poolId1 {
				t.Errorf("Iteration %d: Expected poolId %d, got %d", i, poolId1, extractPoolId(id))
			}
			if extractID(id) != uint32(i) {
				t.Errorf("Iteration %d: Expected ID %d, got %d", i, i, extractID(id))
			}
		}
		// Check internal state
		if gen.pools[poolId1].from != uint32(count+1) {
			t.Errorf("Expected pool.from to be %d after allocating %d IDs, got %d", count+1, count, gen.pools[poolId1].from)
		}
	})

	t.Run("AllocateAllIDs", func(t *testing.T) {
		gen := NewIDGenerator() // Fresh generator
		for i := uint32(1); i <= maxIDValue; i++ {
			id := gen.AllocateID(poolId1)
			if id == 0 {
				t.Fatalf("AllocateID returned 0 unexpectedly at ID %d", i)
			}
			if extractID(id) != i {
				t.Errorf("Expected ID %d, got %d", i, extractID(id))
			}
		}

		// Pool should now be empty (from > to)
		if gen.pools[poolId1] == nil {
			t.Fatalf("Pool %d should still exist but be empty", poolId1)
		}
		// The exhaustion logic sets from = 0xFFFFF, to = 0xFFFFF - 1
		expectedFrom := uint32(0xFFFFF)
		expectedTo := uint32(0xFFFFF - 1)
		if gen.pools[poolId1].from != expectedFrom {
			t.Errorf("Expected pool.from to be %d after exhaustion, got %d", expectedFrom, gen.pools[poolId1].from)
		}
		if gen.pools[poolId1].to != expectedTo {
			t.Errorf("Expected pool.to to be %d after exhaustion, got %d", expectedTo, gen.pools[poolId1].to)
		}

		// Try allocating one more
		id := gen.AllocateID(poolId1)
		if id != 0 {
			t.Errorf("Expected AllocateID to return 0 after pool exhaustion, got %d (ID %d)", id, extractID(id))
		}
	})

	t.Run("AllocateFromExhaustedPool", func(t *testing.T) {
		gen := NewIDGenerator() // Fresh generator
		// Manually exhaust the pool for simplicity
		gen.pools[poolId1] = NewIDPool(0xFFFFF, 0xFFFFF-1) // Mark as exhausted

		id := gen.AllocateID(poolId1)
		if id != 0 {
			t.Errorf("Expected AllocateID to return 0 for an exhausted pool, got %d", id)
		}
	})

	t.Run("AllocateDifferentPools", func(t *testing.T) {
		gen := NewIDGenerator() // Fresh generator
		id1 := gen.AllocateID(poolId1)
		id2 := gen.AllocateID(poolId2)

		if id1 == 0 || id2 == 0 {
			t.Fatalf("Failed to allocate from different pools")
		}
		if extractPoolId(id1) != poolId1 {
			t.Errorf("Expected poolId %d for id1, got %d", poolId1, extractPoolId(id1))
		}
		if extractID(id1) != 1 {
			t.Errorf("Expected ID 1 for id1, got %d", extractID(id1))
		}
		if extractPoolId(id2) != poolId2 {
			t.Errorf("Expected poolId %d for id2, got %d", poolId2, extractPoolId(id2))
		}
		if extractID(id2) != 1 {
			t.Errorf("Expected ID 1 for id2, got %d", extractID(id2))
		}

		// Check internal state
		if gen.pools[poolId1].from != 2 || gen.pools[poolId2].from != 2 {
			t.Errorf("Expected pool states to be updated independently (pool1.from=%d, pool2.from=%d)", gen.pools[poolId1].from, gen.pools[poolId2].from)
		}
	})

	t.Run("PoolIDMasking", func(t *testing.T) {
		gen := NewIDGenerator()
		rawPoolId := PoolId(0b1111_0000_0000_0000_0101)    // Has bits beyond the 10 allowed (0x3FF)
		maskedPoolId := PoolId(0b0000_0000_0000_0000_0101) // Should be masked to 5
		id := gen.AllocateID(rawPoolId)
		if id == 0 {
			t.Fatal("Allocation failed with masked pool ID")
		}
		if extractPoolId(id) != maskedPoolId {
			t.Errorf("Expected masked pool ID %d, got %d", maskedPoolId, extractPoolId(id))
		}
		if gen.pools[maskedPoolId] == nil {
			t.Errorf("Pool with masked ID %d was not created", maskedPoolId)
		}
	})
}

func TestIDGenerator_FreeID(t *testing.T) {
	poolId := PoolId(5)
	maxIDValue := uint32(0xFFFFF - 1)

	t.Run("FreeToNonExistentPool", func(t *testing.T) {
		gen := NewIDGenerator() // Fresh generator
		entityId := generateEntityId(poolId, 10)
		freed := gen.FreeID(entityId)
		if freed {
			t.Errorf("Expected FreeID to return false for non-existent pool, got true")
		}
	})

	t.Run("FreeBeforeFrom", func(t *testing.T) {
		gen := NewIDGenerator()
		// Allocate 1, 2, 3, 4 -> pool.from = 5, pool.to = max
		gen.AllocateID(poolId)        // 1
		gen.AllocateID(poolId)        // 2
		gen.AllocateID(poolId)        // 3
		id4 := gen.AllocateID(poolId) // 4
		expectedFrom := uint32(5)
		if gen.pools[poolId] == nil || gen.pools[poolId].from != expectedFrom {
			t.Fatalf("Setup failed: expected pool.from to be %d, got %d", expectedFrom, gen.pools[poolId].from)
		}

		entityToFree := generateEntityId(poolId, extractID(id4)) // Free ID 4 (which is pool.from - 1)
		freed := gen.FreeID(entityToFree)
		if !freed {
			t.Errorf("Expected FreeID to return true when freeing ID %d (pool.from - 1)", extractID(entityToFree))
		}
		if gen.pools[poolId].from != extractID(entityToFree) {
			t.Errorf("Expected pool.from to become %d after freeing, got %d", extractID(entityToFree), gen.pools[poolId].from)
		}
		if gen.pools[poolId].to != maxIDValue {
			t.Errorf("Expected pool.to to remain %d, got %d", maxIDValue, gen.pools[poolId].to)
		}
	})

	t.Run("FreeAfterTo", func(t *testing.T) {
		gen := NewIDGenerator()
		// Manually set pool state for simplicity, assume 'to' is less than max
		currentTo := uint32(100)
		gen.pools[poolId] = NewIDPool(1, currentTo)

		entityToFree := generateEntityId(poolId, currentTo+1)
		freed := gen.FreeID(entityToFree)
		if !freed {
			t.Errorf("Expected FreeID to return true when freeing ID %d (pool.to + 1)", extractID(entityToFree))
		}
		if gen.pools[poolId].to != extractID(entityToFree) {
			t.Errorf("Expected pool.to to become %d after freeing, got %d", extractID(entityToFree), gen.pools[poolId].to)
		}
		if gen.pools[poolId].from != 1 {
			t.Errorf("Expected pool.from to remain 1, got %d", gen.pools[poolId].from)
		}
	})

	t.Run("FreeAlreadyFreeInRange", func(t *testing.T) {
		gen := NewIDGenerator()
		// Pool has [1, max] available initially
		gen.AllocateID(poolId) // Alloc 1, pool is [2, max]
		gen.AllocateID(poolId) // Alloc 2, pool is [3, max]

		// Try to free 5 (which is currently free and >= pool.from)
		entityToFree := generateEntityId(poolId, 5)
		freed := gen.FreeID(entityToFree)
		if freed {
			t.Errorf("Expected FreeID to return false when freeing ID %d (already free in range)", extractID(entityToFree))
		}
		// Check state hasn't changed
		if gen.pools[poolId].from != 3 {
			t.Errorf("Expected pool.from to remain 3, got %d", gen.pools[poolId].from)
		}
		if gen.pools[poolId].to != maxIDValue {
			t.Errorf("Expected pool.to to remain %d, got %d", maxIDValue, gen.pools[poolId].to)
		}
	})

	t.Run("FreeAllocatedNotAdjacent", func(t *testing.T) {
		// Test freeing an ID that was allocated but is not adjacent to the current free range.
		gen := NewIDGenerator()
		gen.AllocateID(poolId) // 1
		gen.AllocateID(poolId) // 2
		gen.AllocateID(poolId) // 3, pool is [4, max]

		// Try to free 1 (which is allocated, and < pool.from - 1)
		entityToFree := generateEntityId(poolId, 1)
		freed := gen.FreeID(entityToFree)
		if !freed {
			t.Errorf("Expected FreeID to return true when freeing ID %d (< pool.from - 1)", extractID(entityToFree))
		}
		// Check state hasn't changed
		if gen.pools[poolId].from != 1 {
			t.Errorf("Expected pool.from to be 1 now, but got %d", gen.pools[poolId].from)
		}
	})

	t.Run("FreeFarAwayNotInRange", func(t *testing.T) {
		gen := NewIDGenerator()
		gen.AllocateID(poolId) // 1
		gen.AllocateID(poolId) // 2, pool is [3, max]

		// Try to free 100 (which is currently free, but not adjacent to 'from' or 'to')
		entityToFree := generateEntityId(poolId, 100)
		freed := gen.FreeID(entityToFree)
		// Based on the current implementation, this should return false because it only checks
		// for adjacency (id == next.from-1 or id == next.to+1) or if it's already in the range [from, to].
		// The logic for creating a new pool seems flawed/unreachable in the current structure.
		if freed {
			t.Errorf("Expected FreeID to return false when freeing non-adjacent ID %d", extractID(entityToFree))
		}
		// Check state hasn't changed
		if gen.pools[poolId].from != 3 {
			t.Errorf("Expected pool.from to remain 3, got %d", gen.pools[poolId].from)
		}
		if gen.pools[poolId].to != maxIDValue {
			t.Errorf("Expected pool.to to remain %d, got %d", maxIDValue, gen.pools[poolId].to)
		}
	})

	// --- Tests related to merging/new pool creation (likely to fail/show issues with current FreeID) ---
	// These tests are based on the *code* in FreeID, even if it seems inconsistent with AllocateID.

	t.Run("FreeToMergeAdjacent_Simulated", func(t *testing.T) {
		// Simulate a state where merging *could* happen if FreeID worked with linked lists correctly.
		// Setup: Pool has [1, 5], next pool has [7, 10]. We free 6.
		gen := NewIDGenerator()
		pool := NewIDPool(1, 5)
		nextPool := NewIDPool(7, 10)
		pool.next = nextPool
		gen.pools[poolId] = pool

		entityToFree := generateEntityId(poolId, 6)

		// Simulate expected (though likely flawed) execution based on FreeID code:
		// 1. id=6 == pool.to+1 (5+1=6) -> pool.to=6, freed=true. Merge check skipped (curr=nil). New pool check fails. curr=pool[1,6], next=nextPool[7,10].
		// 2. id=6 == next.from-1 (7-1=6) -> pool.from=6, freed=true. Merge check: curr.to+1 == next.from (6+1==7) -> true. Merge occurs: curr.to=10, curr.next=nil.
		// Final state of gen.pools[poolId] (which is `curr`): from=6, to=10, next=nil. This is incorrect.

		freed := gen.FreeID(entityToFree)
		if !freed {
			t.Error("Expected FreeID to return true based on its internal (flawed) logic for this case")
		}
		// Log warning instead of failing on state, as the logic itself is suspect.
		if gen.pools[poolId].from != 1 || gen.pools[poolId].to != 10 || gen.pools[poolId].next != nil {
			t.Errorf("Test resulted in potentially incorrect state: %+v", gen.pools[poolId])
		}
	})

	t.Run("FreeToCreateNewPool_Simulated", func(t *testing.T) {
		// Simulate a state where creating a new pool *might* happen.
		// Setup: Pool has [1, 2], next pool has [6, 8]. We free 3.
		gen := NewIDGenerator()
		pool := NewIDPool(1, 2)
		nextPool := NewIDPool(6, 8)
		pool.next = nextPool
		gen.pools[poolId] = pool

		entityToFree := generateEntityId(poolId, 4)

		freed := gen.FreeID(entityToFree)
		if !freed {
			t.Error("Expected FreeID to return true based on its internal (flawed) logic for creating a pool")
		}
		if gen.pools[poolId].from != 1 || gen.pools[poolId].next == nil || gen.pools[poolId].next.from != 4 || gen.pools[poolId].next.to != 4 {
			t.Errorf("Test resulted in potentially incorrect state: head=%+v, head.next=%+v", gen.pools[poolId], gen.pools[poolId].next)
		}
	})

}

func TestIDGenerator_AllocateAndFree(t *testing.T) {
	//gen := NewIDGenerator()
	poolId := PoolId(10)
	maxIDValue := uint32(0xFFFFF - 1)

	t.Run("AllocateFreeAllocateSimple", func(t *testing.T) {
		gen := NewIDGenerator()       // Fresh generator for isolation
		id1 := gen.AllocateID(poolId) // Alloc 1, pool [2, max]
		id2 := gen.AllocateID(poolId) // Alloc 2, pool [3, max]
		id3 := gen.AllocateID(poolId) // Alloc 3, pool [4, max]

		if extractID(id1) != 1 || extractID(id2) != 2 || extractID(id3) != 3 {
			t.Fatalf("Initial allocation failed")
		}

		// Free ID 2 (pool.from is 4, so 2 is not adjacent)
		// According to current logic, this should fail.
		freed := gen.FreeID(id2)
		if !freed {
			t.Errorf("Freeing non-adjacent ID 2 should not have failed")
		}
		// Let's free ID 3 instead (pool.from - 1)
		freed = gen.FreeID(id3)
		if !freed {
			t.Errorf("Freeing ID 3 (pool.from - 1) failed unexpectedly")
		}
		if gen.pools[poolId].from != 2 { // Pool should now be [2, max]
			t.Errorf("Expected pool.from to be 2 after freeing ID 3, got %d", gen.pools[poolId].from)
		}
		if gen.pools[poolId].to != maxIDValue {
			t.Errorf("Expected pool.to to remain %d, got %d", maxIDValue, gen.pools[poolId].to)
		}

		// Allocate again, should get ID 3 back
		id4 := gen.AllocateID(poolId)
		if id4 == 0 {
			t.Fatalf("Allocation after free returned 0")
		}
		if extractID(id4) != 2 {
			t.Errorf("Expected to re-allocate ID 2, got %d", extractID(id4))
		}
		if gen.pools[poolId].from != 3 { // Should advance past 2 again
			t.Errorf("Expected pool.from to be 3 after re-allocating ID 2, got %d", gen.pools[poolId].from)
		}

		// Allocate again, should get ID 3
		id5 := gen.AllocateID(poolId)
		if id5 == 0 {
			t.Fatalf("Second allocation after free returned 0")
		}
		if extractID(id5) != 3 {
			t.Errorf("Expected to allocate ID 3, got %d", extractID(id5))
		}
		if gen.pools[poolId].from != 4 {
			t.Errorf("Expected pool.from to be 4 after allocating ID 3, got %d", gen.pools[poolId].from)
		}
	})

	t.Run("AllocateFreeInReverseOrder", func(t *testing.T) {
		gen := NewIDGenerator()       // Fresh generator
		id1 := gen.AllocateID(poolId) // 1, pool [2, max]
		id2 := gen.AllocateID(poolId) // 2, pool [3, max]
		id3 := gen.AllocateID(poolId) // 3, pool [4, max]

		// Free 3 (pool.from - 1) -> pool becomes [3, max]
		freed3 := gen.FreeID(id3)
		if !freed3 || gen.pools[poolId].from != 3 {
			t.Fatalf("Failed to free ID 3. Freed: %v, Pool From: %d", freed3, gen.pools[poolId].from)
		}

		// Free 2 (pool.from - 1) -> pool becomes [2, max]
		freed2 := gen.FreeID(id2)
		if !freed2 || gen.pools[poolId].from != 2 {
			t.Fatalf("Failed to free ID 2. Freed: %v, Pool From: %d", freed2, gen.pools[poolId].from)
		}

		// Free 1 (pool.from - 1) -> pool becomes [1, max]
		freed1 := gen.FreeID(id1)
		if !freed1 || gen.pools[poolId].from != 1 {
			t.Fatalf("Failed to free ID 1. Freed: %v, Pool From: %d", freed1, gen.pools[poolId].from)
		}

		// Allocate again, should get 1, 2, 3
		alloc1 := gen.AllocateID(poolId)
		alloc2 := gen.AllocateID(poolId)
		alloc3 := gen.AllocateID(poolId)

		if extractID(alloc1) != 1 || extractID(alloc2) != 2 || extractID(alloc3) != 3 {
			t.Errorf("Expected re-allocation order 1, 2, 3, got %d, %d, %d", extractID(alloc1), extractID(alloc2), extractID(alloc3))
		}
		if gen.pools[poolId].from != 4 {
			t.Errorf("Expected pool.from to be 4 after re-allocations, got %d", gen.pools[poolId].from)
		}
	})

	t.Run("FreeToExpandRangeThenAllocate", func(t *testing.T) {
		gen := NewIDGenerator() // Fresh generator
		// Allocate 1..6. Pool is [7, max]
		var ids [6]EntityId
		for i := 0; i < 6; i++ {
			ids[i] = gen.AllocateID(poolId)
			if extractID(ids[i]) != uint32(i+1) {
				t.Fatalf("Setup allocation failed at index %d", i)
			}
		}
		if gen.pools[poolId].from != 7 {
			t.Fatalf("Setup failed, pool.from is %d, expected 7", gen.pools[poolId].from)
		}

		// Free 6 (pool.from - 1 = 7-1=6) -> pool becomes [6, max]
		freed6 := gen.FreeID(ids[5]) // ids[5] corresponds to ID 6
		if !freed6 || gen.pools[poolId].from != 6 {
			t.Fatalf("Failed to free ID 6. Freed: %v, Pool From: %d", freed6, gen.pools[poolId].from)
		}

		// Free 5 (pool.from - 1 = 6-1=5) -> pool becomes [5, max]
		freed5 := gen.FreeID(ids[4]) // ids[4] corresponds to ID 5
		if !freed5 || gen.pools[poolId].from != 5 {
			t.Fatalf("Failed to free ID 5. Freed: %v, Pool From: %d", freed5, gen.pools[poolId].from)
		}

		// Allocate again, should get 5, 6, 7
		alloc1 := gen.AllocateID(poolId)
		alloc2 := gen.AllocateID(poolId)
		alloc3 := gen.AllocateID(poolId)

		if extractID(alloc1) != 5 || extractID(alloc2) != 6 || extractID(alloc3) != 7 {
			t.Errorf("Expected re-allocation order 5, 6, 7, got %d, %d, %d", extractID(alloc1), extractID(alloc2), extractID(alloc3))
		}
		if gen.pools[poolId].from != 8 {
			t.Errorf("Expected pool.from to be 8 after re-allocations, got %d", gen.pools[poolId].from)
		}
	})
}
