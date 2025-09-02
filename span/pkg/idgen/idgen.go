package idgen

// This file defines the ID generation structure and functions.

// First, the most basic ID generation structure is defined.
// The three counters can be used to generate IDs for different types of entities.
var idCounterA uint32 = 0
var idCounterB uint32 = 0
var idCounterC uint32 = 0

func getNextId(counter *uint32) uint32 {
	*counter++
	if *counter == ^uint32(0) {
		panic("ID counter overflow: reached maximum uint32 value")
	}
	return *counter
}

func GetNextIdA() uint32 {
	return getNextId(&idCounterA)
}

func GetNextIdB() uint32 {
	return getNextId(&idCounterB)
}

func GetNextIdC() uint32 {
	return getNextId(&idCounterC)
}

// Second, a more complex ID generation structure is defined,
// which can generate IDs and also free them.

// IDGenerator is a structure that helps generates unique IDs for SPAN IR entities.
// It maintains a linked list of pool ids that are available for allocation.
type IDGenerator struct {
	idPools map[poolId_t]*idPool // generic pool for arbirary bit IDs
}

// A pool of free IDs available for allocation which points to the next pool of free IDs.
// Each pool has a range of IDs from `from` to `to`.
// The `next` field points to the next pool of free IDs.
// A pool is empty if from > to.
type idPool struct {
	from uint32
	to   uint32
	next *idPool
}

// A 32 bit pool id is used to identify the pool of IDs.
type poolId_t uint32

const prefixPosMask32 uint32 = 0xFFFF0000 // Mask to get the prefix bits
const prefixShift32 uint32 = 16
const seqIdBitLengthMask32 uint32 = 0x1F // Mask to get number of bits in ID
const invalidPoolId poolId_t = 0

// Prefix is the upper 16 bits of the pool id.
// Hence, prefix can at most be 16 bits long.
func (p poolId_t) getPrefix() uint16 {
	return uint16((uint32(p) & prefixPosMask32) >> prefixShift32)
}

// The lower 5 bits are used to store the number of bits in the ID.
func (p poolId_t) getSeqIdBitLength() uint8 {
	return uint8(uint32(p) & seqIdBitLengthMask32)
}

func constructFullId(poolId poolId_t, seqId uint32) uint32 {
	return uint32((uint32(poolId.getPrefix()) << poolId.getSeqIdBitLength()) | seqId)
}

// NewIDGenerator creates a new IDGenerator with an empty pool of IDs.
func NewIDGenerator() *IDGenerator {
	return &IDGenerator{
		idPools: make(map[poolId_t]*idPool),
	}
}

// newIDPool creates a new idPool with an initial pool of contiguous IDs.
func newIDPool(from uint32, to uint32) *idPool {
	return &idPool{
		from: from,
		to:   to,
		next: nil,
	}
}

func emptyIDPool(pool *idPool) {
	pool.from = 0
	pool.to = 0
	pool.next = nil
}

func getPrefixFromFullId(fullId uint32, seqIdBitLength uint8) uint16 {
	return uint16((fullId & prefixPosMask32) >> uint32(seqIdBitLength))
}

func encodePoolId(prefix uint16, seqIdBitLength uint8) poolId_t {
	return poolId_t(uint32(prefix)<<prefixShift32 | uint32(seqIdBitLength))
}

func validateAndEncodePoolId(prefix uint16, seqIdBitLength uint8) poolId_t {
	if seqIdBitLength >= 32 || seqIdBitLength <= 16 {
		return invalidPoolId // There will be no bits left for prefix after shifting
	}
	tmp := uint32(prefix) << seqIdBitLength
	if (tmp >> seqIdBitLength) != uint32(prefix) {
		return invalidPoolId // Prefix bits are getting dropped during the shift
	}
	return encodePoolId(prefix, seqIdBitLength)
}

func createIDPool(seqIdBitLength uint8) *idPool {
	return newIDPool(1, maxSeqIdValue(seqIdBitLength))
}

func maxSeqIdValue(seqIdBitLength uint8) uint32 {
	return (1 << seqIdBitLength) - 1
}

func (gen *IDGenerator) getOrCreatePool(poolId poolId_t) *idPool {
	pool, ok := gen.idPools[poolId]
	if !ok || pool == nil {
		pool = createIDPool(uint8(poolId))
		gen.idPools[poolId] = pool
	}
	return pool
}

// AllocateID allocates a unique ID from the IDGenerator.
// It returns 0 if no ID is available in the defined range, or the arguments are invalid.
// The prefix is the upper 16 bits of the pool id.
// The seqIdBitLength is the number of bits in the sequence ID.
// The seqIdBitLength must be between 1 and 31.
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

	seqId := pool.from
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
			pool.from = maxSeqIdValue(uint8(poolId))
			pool.to = maxSeqIdValue(uint8(poolId)) - 1
		}
	}

	return constructFullId(poolId, seqId)
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

	seqId := fullId & ((1 << seqIdBitLength) - 1)
	if seqId == 0 || seqId > maxSeqIdValue(seqIdBitLength) {
		return false // Invalid ID
	}

	freed := false
	var prevTo uint32 = 0
	var prev *idPool = nil
	for pool != nil {
		// COND 1: First, check if the id is already in the pool.
		if seqId >= pool.from && seqId <= pool.to {
			return false // ID is already in the pool
		}

		// COND 2: Otherwise, if seqId is one less than from, or one more than to,
		// free it by decrementing the 'from' or incrementing the 'to'.
		switch seqId {
		case pool.from - 1:
			pool.from, freed = seqId, true
		case pool.to + 1:
			pool.to, freed = seqId, true
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

		// CONDITION 3: If seqId is between the current pool and the next pool, create a new pool between them
		if seqId > prevTo && seqId < pool.from {
			newPool := newIDPool(seqId, seqId)
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
