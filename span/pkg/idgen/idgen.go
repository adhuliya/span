package idgen

// This file defines the ID generation structure and functions.

// First, the most basic ID generation structure is defined.
var idCounter uint32 = 0

func GetNextId() uint32 {
	idCounter++
	return idCounter
}

// Second, a more complex ID generation structure is defined,
// which can generate IDs and also free them.

// IDGenerator is a structure that helps generates unique IDs for SPAN IR entities.
// It maintains a linked list of pool ids that are available for allocation.
type IDGenerator struct {
	idPools map[PoolId]*IDPool // generic pool for arbirary bit IDs
}

// A pool of free IDs available for allocation which points to the next pool of free IDs.
// Each pool has a range of IDs from `from` to `to`.
// The `next` field points to the next pool of free IDs.
// A pool is empty if from > to.
type IDPool struct {
	from uint32
	to   uint32
	next *IDPool
}

// A 32 bit pool id is used to identify the pool of IDs.
type PoolId uint32

const prefixMask uint32 = 0xFFFF0000 // Mask to get the prefix bits
const shiftBitsMask uint32 = 0x1F    // Mask to get number of bits in ID
const invalidPoolId PoolId = 0

// Prefix is the upper 16 bits of the pool id.
// Hence, prefix can at most be 16 bits long.
func (p PoolId) getPrefix() uint16 {
	return uint16((uint32(p) & prefixMask) >> 16)
}

// The lower 16 bits are used to store the number of bits in the ID.
func (p PoolId) getSeqIdBitLength() uint8 {
	return uint8(uint32(p) & shiftBitsMask)
}

func constructFullId(poolId PoolId, id uint32) uint32 {
	return uint32((uint32(poolId.getPrefix()) << poolId.getSeqIdBitLength()) | id)
}

// NewIDGenerator creates a new IDGenerator with an empty pool of IDs.
func NewIDGenerator() *IDGenerator {
	return &IDGenerator{
		idPools: make(map[PoolId]*IDPool),
	}
}

// newIDPool creates a new IDPool with an initial pool of contiguous IDs.
func newIDPool(from uint32, to uint32) *IDPool {
	return &IDPool{
		from: from,
		to:   to,
		next: nil,
	}
}

func emptyIDPool(pool *IDPool) {
	pool.from = 0
	pool.to = 0
	pool.next = nil
}

func getPrefixFromFullId(fullId uint32, seqIdBitLength uint8) uint16 {
	return uint16((fullId & prefixMask) >> uint32(seqIdBitLength))
}

func encodePoolId(prefix uint16, seqIdBitLength uint8) PoolId {
	return PoolId(uint32(prefix)<<16 | uint32(seqIdBitLength))
}

func validateAndEncodePoolId(prefix uint16, seqIdBitLength uint8) PoolId {
	if seqIdBitLength >= 32 || seqIdBitLength <= 16 {
		return invalidPoolId // There will be no bits left for prefix after shifting
	}
	tmp := uint32(prefix) << seqIdBitLength
	if (tmp >> seqIdBitLength) != uint32(prefix) {
		return invalidPoolId // Prefix bits are getting dropped during the shift
	}
	return encodePoolId(prefix, seqIdBitLength)
}

func createIDPool(seqIdBitLength uint8) *IDPool {
	return newIDPool(1, maxIdValue(seqIdBitLength))
}

func maxIdValue(seqIdBitLength uint8) uint32 {
	return (1 << seqIdBitLength) - 1
}

func (gen *IDGenerator) getOrCreatePool(poolId PoolId) *IDPool {
	pool, ok := gen.idPools[poolId]
	if !ok || pool == nil {
		pool = createIDPool(uint8(poolId))
		gen.idPools[poolId] = pool
	}
	return pool
}

// AllocateID allocates a unique ID from the IDGenerator.
// It returns 0 if no ID is available in the defined range, or the arguments are invalid.
func (gen *IDGenerator) AllocateID(prefix uint16, seqIdBitLength uint8) uint32 {
	poolId := validateAndEncodePoolId(prefix, seqIdBitLength)
	if poolId == invalidPoolId {
		return 0 // zero is always an invalid full ID
	}
	poolId = poolId & 0x3FF // Mask to 10 bits
	pool := gen.getOrCreatePool(poolId)

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
			emptyIDPool(tmp)
		} else {
			pool.from = maxIdValue(uint8(poolId))
			pool.to = maxIdValue(uint8(poolId)) - 1
		}
	}

	return constructFullId(poolId, id)
}

// FreeID puts an id back to the pool.
// It returns true if the ID is successfully freed.
func (gen *IDGenerator) FreeID(fullId uint32, seqIdBitLength uint8) bool {
	poolId := validateAndEncodePoolId(getPrefixFromFullId(fullId, seqIdBitLength), seqIdBitLength)
	if poolId == invalidPoolId {
		return false // Invalid pool ID
	}
	pool := gen.idPools[poolId]
	if pool == nil {
		return false // Pool not found
	}

	id := fullId & ((1 << seqIdBitLength) - 1)
	if id == 0 || id > maxIdValue(seqIdBitLength) {
		return false // Invalid ID
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
					emptyIDPool(next) // GC shall collect this
				}
			}
			return true
		}

		// CONDITION 3: If id is between the current pool and the next pool, create a new pool between them
		if id > prevTo && id < pool.from {
			newPool := newIDPool(id, id)
			newPool.next = pool
			if prev == nil {
				gen.idPools[poolId] = newPool
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
