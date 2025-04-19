package spir

// This file defines the ID generation structure and functions.

// A pool of free IDs available for allocation which points to the next pool of free IDs.
// Each pool has a range of IDs from `from` to `to`.
// The `next` field points to the next pool of free IDs.
// A pool is empty if from > to.
type IDPool struct {
	from uint32
	to   uint32
	next *IDPool
}

// A 12 bit Pool ID is used to identify the pool of IDs.
type PoolId uint32

func generateEntityId(poolId PoolId, id uint32) EntityId {
	return EntityId((uint32(poolId) << 20) | id)
}

// IDGenerator is a structure that helps generates unique IDs for SPAN IR entities.
// It maintains a linked list of pool ids that are available for allocation.
type IDGenerator struct {
	pools [1024]*IDPool
}

// NewIDGenerator creates a new IDGenerator with an empty pool of IDs.
func NewIDGenerator() *IDGenerator {
	return &IDGenerator{}
}

// NewIDPool creates a new IDPool with an initial pool of IDs.
func NewIDPool(from uint32, to uint32) *IDPool {
	return &IDPool{
		from: from,
		to:   to,
		next: nil,
	}
}

func emptyThePool(pool *IDPool) {
	pool.from = 0
	pool.to = 0
	pool.next = nil
}

// AllocateID allocates a unique ID from the IDGenerator.
// It takes a start value with only the upper 12 bits set and
// returns the next available ID between startValue and startValue+0xFFFFF from the pool,
// excluding the limits.
// It returns 0 if no ID is available in the defined range.
func (gen *IDGenerator) AllocateID(poolId PoolId) EntityId {
	poolId = poolId & 0x3FF // Mask to 10 bits
	pool := gen.pools[poolId]
	if pool == nil {
		// Create a new pool if it doesn't exist
		pool = NewIDPool(1, 0xFFFFF-1)
		gen.pools[poolId] = pool
	}

	if pool.from > pool.to {
		return 0 // No IDs available in the pool
	}

	id := pool.from
	pool.from++

	if pool.from > pool.to {
		// If the pool is empty, remove it from the list
		if pool.next != nil {
			tmp := pool.next
			pool.from = tmp.from
			pool.to = tmp.to
			pool.next = tmp.next
			emptyThePool(tmp)
		} else {
			pool.from = 0xFFFFF
			pool.to = 0xFFFFF - 1
		}
	}

	return generateEntityId(poolId, id)
}

// FreeID puts an EntityId back to the pool.
// It returns true if the ID is successfully freed.
func (gen *IDGenerator) FreeID(entityId EntityId) bool {
	id := uint32(entityId & 0xFFFFF)
	poolId := PoolId((entityId >> 20) & 0x3FF)
	pool := gen.pools[poolId]
	if pool == nil {
		return false // Pool not found
	}

	freed := false
	var prevTo uint32 = 0
	var prev *IDPool = nil
	for pool != nil {
		// COND 1: First, check if the id is already in the pool.
		if id >= pool.from && id <= pool.to {
			return false // ID is already in the pool
		}

		// COND 2: Otherwise, if id is one less than from, or one more than to,
		// free it by decrementing the 'from' or incrementing the 'to'.
		if id == pool.from-1 {
			pool.from, freed = id, true
		} else if id == pool.to+1 {
			pool.to, freed = id, true
		}
		// COND 2.1: Check if the curr and next pools have become consecutive, if so, merge them
		next := pool.next
		if freed {
			if next != nil {
				if pool.to+1 == next.from {
					// Merge the pools and remove the next pool
					pool.to = next.to
					pool.next = next.next
					emptyThePool(next) // GC shall collect this
				}
			}
			return true
		}

		// CONDITION 3: If id is between the current pool and the next pool, create a new pool between them
		if id > prevTo && id < pool.from {
			newPool := NewIDPool(id, id)
			newPool.next = pool
			if prev == nil {
				gen.pools[poolId] = newPool
			} else {
				prev.next = newPool
			}
			return true
		}

		prev, pool = pool, pool.next
		prevTo = prev.to
	}

	return freed
}
