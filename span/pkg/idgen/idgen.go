package idgen

import "fmt"

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
	idPools map[poolId_t]*freeIdPool // generic pool for arbirary bit IDs
}

// A pool of free IDs available for allocation which points to the next pool of free IDs.
// Each pool has a range of IDs from `from` to `to`.
// The `next` field points to the next pool of free IDs.
// A pool is empty if from > to.
type freeIdPool struct {
	from uint32
	to   uint32
	next *freeIdPool
}

// A 32 bit pool id is used to identify the pool of IDs.
// The upper 16 bits are the prefix, and the lower 5 bits are the number of bits in the sequence ID.
// Representation: <prefix:16 bits>-<zeros(unused):11 bits>-<seqIdBitLen:5 bits>
type poolId_t uint32

// Convert the pool to a hex string for printing/debugging.
func (p poolId_t) String() string {
	return fmt.Sprintf("poolId_t(0x%X)", uint32(p))
}

const prefixPosMask32 uint32 = 0xFFFF0000 // Mask to get the prefix bits
const prefixShift32 uint32 = 16
const seqIdBitLengthMask32 uint32 = 0x1F // Mask to get number of bits in ID
const invalidPoolId poolId_t = 0

// Prefix returns the upper 16 bits of the 32 bit pool id.
func (p poolId_t) Prefix() uint16 {
	return uint16((uint32(p) & prefixPosMask32) >> prefixShift32)
}

// SeqIdBitLen returns the number of bits in the sequence ID.
func (p poolId_t) SeqIdBitLen() uint8 {
	return uint8(uint32(p) & seqIdBitLengthMask32)
}

func constructFullId(poolId poolId_t, seqId uint32) uint32 {
	return uint32((uint32(poolId.Prefix()) << poolId.SeqIdBitLen()) | seqId)
}

// NewIDGenerator creates a new IDGenerator with an empty pool of IDs.
func NewIDGenerator() *IDGenerator {
	return &IDGenerator{
		idPools: make(map[poolId_t]*freeIdPool),
	}
}

// newIDPool creates a new freeIdPool with an initial pool of contiguous IDs.
func newIDPool(from uint32, to uint32) *freeIdPool {
	return &freeIdPool{
		from: from,
		to:   to,
		next: nil,
	}
}

func emptyIDPool(pool *freeIdPool) {
	pool.from = 0
	pool.to = 0
	pool.next = nil
}

func getPrefixFromFullId(fullId uint32, seqIdBitLen uint8) uint16 {
	return uint16((fullId & prefixPosMask32) >> uint32(seqIdBitLen))
}

func encodePoolId(prefix uint16, seqIdBitLen uint8) poolId_t {
	return poolId_t(uint32(prefix)<<prefixShift32 | uint32(seqIdBitLen))
}

func validateAndEncodePoolId(prefix uint16, seqIdBitLen uint8) poolId_t {
	if seqIdBitLen >= 32 || seqIdBitLen <= 16 {
		return invalidPoolId // There will be no bits left for prefix after shifting
	}
	tmp := uint32(prefix) << seqIdBitLen
	if (tmp >> seqIdBitLen) != uint32(prefix) {
		return invalidPoolId // Prefix bits are getting dropped during the shift
	}
	return encodePoolId(prefix, seqIdBitLen)
}

func createIDPool(seqIdBitLen uint8) *freeIdPool {
	return newIDPool(1, maxSeqIdValue(seqIdBitLen))
}

func maxSeqIdValue(seqIdBitLen uint8) uint32 {
	return (1 << seqIdBitLen) - 1
}

func (gen *IDGenerator) getOrCreatePool(poolId poolId_t) *freeIdPool {
	pool, ok := gen.idPools[poolId]
	if !ok || pool == nil {
		pool = createIDPool(poolId.SeqIdBitLen())
		gen.idPools[poolId] = pool
	}
	return pool
}

// AllocateID allocates a unique 32 bit ID from the IDGenerator.
// It returns 0 if no ID is available in the defined range, or the arguments are invalid.
// The prefix is the upper 16 bits of the pool id.
// The seqIdBitLen is the number of bits in the sequence ID.
// The seqIdBitLen must be between 1 and 31.
func (gen *IDGenerator) AllocateID(prefix uint16, seqIdBitLen uint8) uint32 {
	poolId := validateAndEncodePoolId(prefix, seqIdBitLen)
	if poolId == invalidPoolId {
		return 0 // zero is always an invalid full ID
	}
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
			// The pool is exhausted, reset it to the maximum value for the sequence ID length.
			pool.from = maxSeqIdValue(poolId.SeqIdBitLen())
			pool.to = maxSeqIdValue(poolId.SeqIdBitLen()) - 1
		}
	}

	return constructFullId(poolId, seqId)
}

// FreeID puts an id back to the pool.
// It returns true if the ID is successfully freed.
func (gen *IDGenerator) FreeID(fullId uint32, seqIdBitLen uint8) bool {
	poolId := validateAndEncodePoolId(getPrefixFromFullId(fullId, seqIdBitLen), seqIdBitLen)
	if poolId == invalidPoolId {
		return false // Invalid pool ID
	}
	pool := gen.idPools[poolId]
	if pool == nil {
		return false // Pool not found
	}

	seqId := fullId & ((1 << seqIdBitLen) - 1)
	if seqId == 0 || seqId > maxSeqIdValue(seqIdBitLen) {
		return false // Invalid ID
	}

	freed := false
	var prevTo uint32 = 0
	var prev *freeIdPool = nil
	for pool != nil {
		// COND 1: First, check if the id is already in the free pool.
		if seqId >= pool.from && seqId <= pool.to {
			return false // ID is already in the free pool
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

// ReserveID reserves an id from the pool (removes it from the free pool).
// It returns true if the ID was free and is now reserved (i.e., successfully removed from the free pool).
// When using this function for multiple IDs in succession,
// the caller must invoke
func (gen *IDGenerator) ReserveID(fullId uint32, seqIdBitLen uint8) bool {
	poolId := validateAndEncodePoolId(getPrefixFromFullId(fullId, seqIdBitLen), seqIdBitLen)
	if poolId == invalidPoolId {
		return false // Invalid pool ID
	}

	pool := gen.getOrCreatePool(poolId)
	seqId := fullId & ((1 << seqIdBitLen) - 1) // the sequence ID

	var prev *freeIdPool = nil
	curr := pool
	for curr != nil {
		// COND 1: If id is inside the current free pool, reserve it (remove from free pool)
		if seqId >= curr.from && seqId <= curr.to {
			// Found the correct free pool block
			if curr.from == curr.to {
				// Only one id in this pool, remove the pool
				if prev == nil {
					gen.idPools[poolId] = curr.next
				} else {
					prev.next = curr.next
				}
				emptyIDPool(curr)
			} else if seqId == curr.from {
				// Shrink the pool from start
				curr.from++
			} else if seqId == curr.to {
				// Shrink the pool from end
				curr.to--
			} else {
				// Split the pool into two, around the given sequence ID
				newPool := newIDPool(seqId+1, curr.to)
				newPool.next = curr.next
				curr.to = seqId - 1
				curr.next = newPool
			}
			return true // Successfully reserved the given sequence ID
		}
		if seqId < curr.from {
			// Pools are sorted, so if seqId is less than current from, it is not in any pool
			return false // ID was not free
		}
		prev, curr = curr, curr.next
	}
	return false // Not found in any pool
}
