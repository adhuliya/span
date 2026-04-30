// idgen_test.go - updated to match the semantics and API of idgen.go
package idgen

import (
	"testing"
)

// Use prefix values that are guaranteed to fit in (32 - seqIdBitLen) bits for all tests.

func TestIDGenerator_AllocateID(t *testing.T) {
	gen := NewIDGenerator()

	// Choose prefix so that for seqIdBitLen=20, prefix fits in (32-20)=12 bits, that is max 0xFFF
	prefix := uint16(0x07A5) // 0x07A5 = 1957, well under 0xFFF
	seqIdBitLen := uint8(20)
	if prefix > ((1 << (32 - seqIdBitLen)) - 1) {
		t.Fatalf("Test misuse: prefix %x too large for seqIdBitLen %d", prefix, seqIdBitLen)
	}

	// Test 1: Allocate a valid ID
	id1 := gen.AllocateID(prefix, seqIdBitLen)
	if id1 == 0 {
		t.Fatalf("AllocateID failed to allocate a valid ID")
	}

	// Test 2: Allocate several more IDs from same pool, ensure all unique
	id2 := gen.AllocateID(prefix, seqIdBitLen)
	id3 := gen.AllocateID(prefix, seqIdBitLen)
	if id2 == 0 || id3 == 0 || id2 == id1 || id3 == id1 || id3 == id2 {
		t.Fatalf("AllocateID generated non-unique IDs or failed")
	}

	// Test 3: Invalid seqIdBitLen (too large)
	defer func() {
		if r := recover(); r == nil {
			t.Errorf("AllocateID should panic for seqIdBitLen >= 32")
		}
	}()
	gen.AllocateID(prefix, 32)
}

func TestIDGenerator_AllocateID_Exhaustion(t *testing.T) {
	gen := NewIDGenerator()

	// For seqIdBitLen=17, prefix must fit into 15 bits (max 0x7FFF)
	prefix := uint16(0x4321) // 0x4321 = 17185, well under 0x7FFF
	seqIdBitLen := uint8(17)
	if prefix > ((1 << (32 - seqIdBitLen)) - 1) {
		t.Fatalf("Test misuse: prefix %x too large for seqIdBitLen %d", prefix, seqIdBitLen)
	}

	maxId := maxSeqIdValue(seqIdBitLen)
	for i := uint32(0); i < maxId; i++ {
		if gen.AllocateID(prefix, seqIdBitLen) == 0 {
			t.Fatalf("Premature exhaustion at i=%v", i)
		}
	}
	id := gen.AllocateID(prefix, seqIdBitLen)
	if id != 0 {
		t.Fatalf("Pool not exhausted as expected")
	}
}

func TestIDGenerator_FreeID_ReuseAndInvalid(t *testing.T) {
	gen := NewIDGenerator()
	// For seqIdBitLen=18, prefix must fit in 14 bits (max 0x3FFF)
	prefix := uint16(0x2EEE) // 0x2EEE = 12014, well under 0x3FFF
	seqIdBitLen := uint8(18)
	if prefix > ((1 << (32 - seqIdBitLen)) - 1) {
		t.Fatalf("Test misuse: prefix %x too large for seqIdBitLen %d", prefix, seqIdBitLen)
	}

	id1 := gen.AllocateID(prefix, seqIdBitLen)
	if ok := gen.FreeID(id1, seqIdBitLen); !ok {
		t.Fatalf("Should be able to free a valid ID")
	}

	id2 := gen.AllocateID(prefix, seqIdBitLen)
	if id2 != id1 {
		t.Errorf("Expected to reuse freed id %v, got %v", id1, id2)
	}

	ok := gen.FreeID(id2, seqIdBitLen)
	if !ok {
		t.Fatalf("Failed to free valid ID on first call")
	}
	if ok2 := gen.FreeID(id2, seqIdBitLen); ok2 {
		t.Errorf("FreeID should return false for already-freed ID")
	}
	if gen.FreeID(0, seqIdBitLen) {
		t.Errorf("FreeID should return false for id 0")
	}

	defer func() {
		if r := recover(); r == nil {
			t.Errorf("FreeID should panic with invalid seqIdBitLen")
		}
	}()
	_ = gen.FreeID(id1, 1)
}

func TestIDGenerator_MergePools(t *testing.T) {
	gen := NewIDGenerator()
	// For seqIdBitLen=19, prefix fits in 13 bits (max 0x1FFF)
	prefix := uint16(0x1111) // 0x1111 = 4369, under 0x1FFF
	seqIdBitLen := uint8(19)
	if prefix > ((1 << (32 - seqIdBitLen)) - 1) {
		t.Fatalf("Test misuse: prefix %x too large for seqIdBitLen %d", prefix, seqIdBitLen)
	}

	idA := gen.AllocateID(prefix, seqIdBitLen)
	idB := gen.AllocateID(prefix, seqIdBitLen)

	if !gen.FreeID(idB, seqIdBitLen) {
		t.Fatalf("expected free to succeed")
	}
	if !gen.FreeID(idA, seqIdBitLen) {
		t.Fatalf("expected free to succeed")
	}

	result := map[uint32]bool{idA: false, idB: false}
	for i := 0; i < 2; i++ {
		id := gen.AllocateID(prefix, seqIdBitLen)
		if _, exists := result[id]; exists {
			result[id] = true
		} else {
			t.Errorf("unexpected id allocated: %v", id)
		}
	}
	for k, v := range result {
		if !v {
			t.Errorf("id %v should have been returned after frees/merge", k)
		}
	}
}

func TestIDGenerator_ValidateAndEncodePoolId(t *testing.T) {
	// For bits = 20, prefix must fit in 12 bits (0xFFF)
	p := uint16(0x05A3) // 0x05A3 = 1443 < 0xFFF
	b := uint8(20)
	pid := validateAndEncodePoolId(p, b)
	if pid == invalidPoolId {
		t.Fatalf("unexpected invalidPoolId for valid args")
	}

	// Out-of-range bitlen (too small): validation panics instead of returning a sentinel.
	func() {
		defer func() {
			if r := recover(); r == nil {
				t.Errorf("validateAndEncodePoolId must panic for bitlen <= 16")
			}
		}()
		validateAndEncodePoolId(p, 16)
	}()

	// Out-of-range bitlen (too large)
	func() {
		defer func() {
			if r := recover(); r == nil {
				t.Errorf("validateAndEncodePoolId must panic on seqIdBitLen >= 32")
			}
		}()
		validateAndEncodePoolId(p, 32)
	}()

	// Bit shift drops prefix (prefix too large for (32 - seqIdBitLen) bits)
	func() {
		defer func() {
			if r := recover(); r == nil {
				t.Errorf("validateAndEncodePoolId should panic when prefix bits are dropped")
			}
		}()
		// Use a prefix that will not fit within (32-19)=13 bits; 0x3FFF is 14 bits, so it will be truncated
		validateAndEncodePoolId(0x3FFF, 19)
	}()
}

func TestIDGenerator_PoolIdHelpers(t *testing.T) {
	// bits = 21 ⇒ prefix must fit in (32-21)=11 bits ⇒ max 0x7FF
	const prefix uint16 = 0x02AD
	const bits uint8 = 21
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("Test misuse: prefix %x too large for bits %d", prefix, bits)
	}
	poolId := encodePoolId(prefix, bits)
	if poolId.Prefix() != prefix {
		t.Errorf("Prefix got %04x, want %04x", poolId.Prefix(), prefix)
	}
	if poolId.SeqIdBitLen() != bits {
		t.Errorf("SeqIdBitLen got %d, want %d", poolId.SeqIdBitLen(), bits)
	}
	if poolId.String() == "" {
		t.Errorf("String() should not return empty string")
	}
}

func TestIDGenerator_GetNextIdMonotonic(t *testing.T) {
	a1, a2, a3 := GetNextIdA(), GetNextIdA(), GetNextIdA()
	if !(a1 < a2 && a2 < a3) {
		t.Errorf("GetNextIdA not strictly increasing: %d, %d, %d", a1, a2, a3)
	}
	b1, b2 := GetNextIdB(), GetNextIdB()
	if !(b1 < b2) {
		t.Errorf("GetNextIdB not increasing: %d, %d", b1, b2)
	}
	c1 := GetNextIdC()
	if c1 == 0 {
		t.Errorf("GetNextIdC returned 0")
	}
}

func TestIDGenerator_GetNextIdOverflowPanics(t *testing.T) {
	var c uint32 = ^uint32(0) - 1
	defer func() {
		if recover() == nil {
			t.Fatal("expected panic when incrementing counter to max uint32")
		}
	}()
	getNextId(&c)
}

func TestIDGenerator_GetNextIdABCIndependent(t *testing.T) {
	a, aa := GetNextIdA(), GetNextIdA()
	b, bb := GetNextIdB(), GetNextIdB()
	if !(a < aa) {
		t.Errorf("GetNextIdA should advance independently: %d then %d", a, aa)
	}
	if !(b < bb) {
		t.Errorf("GetNextIdB should advance independently: %d then %d", b, bb)
	}
	c1, c2 := GetNextIdC(), GetNextIdC()
	if !(c1 < c2) {
		t.Errorf("GetNextIdC not increasing: %d, %d", c1, c2)
	}
}

func TestIDGenerator_ReserveID(t *testing.T) {
	gen := NewIDGenerator()
	prefix := uint16(0x0100)
	bits := uint8(20)
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("Test misuse: prefix %x too large for bits %d", prefix, bits)
	}

	_ = gen.AllocateID(prefix, bits) // consumes sequence id 1; free pool is [2, max]
	poolId := validateAndEncodePoolId(prefix, bits)
	id1 := constructFullId(poolId, 1)
	if gen.ReserveID(id1, bits) {
		t.Errorf("ReserveID should fail: seq 1 was allocated, not in free pool")
	}

	target := uint32(42)
	full := constructFullId(poolId, target)
	if !gen.ReserveID(full, bits) {
		t.Fatalf("ReserveID should remove a free id in the middle of the range")
	}
	if gen.ReserveID(full, bits) {
		t.Errorf("second ReserveID for same id should fail")
	}
}

func TestIDGenerator_AllocateIDMergesWhenHeadSegmentExhaustedWithNext(t *testing.T) {
	gen := NewIDGenerator()
	prefix := uint16(0x0200)
	bits := uint8(20)
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse: prefix %x too large for bits %d", prefix, bits)
	}
	poolId := validateAndEncodePoolId(prefix, bits)

	_ = gen.AllocateID(prefix, bits) // seq 1
	_ = gen.AllocateID(prefix, bits) // seq 2
	_ = gen.AllocateID(prefix, bits) // seq 3, free pool [4, max]

	if !gen.FreeID(constructFullId(poolId, 2), bits) {
		t.Fatal("FreeID(seq 2) should succeed")
	}
	// free list: [2,2] -> [4, max]

	got := gen.AllocateID(prefix, bits)
	want := constructFullId(poolId, 2)
	if got != want {
		t.Fatalf("AllocateID got full id %v, want %v (head singleton [2,2])", got, want)
	}
	// After merging next into head, next allocation should take seq 4
	got2 := gen.AllocateID(prefix, bits)
	want2 := constructFullId(poolId, 4)
	if got2 != want2 {
		t.Fatalf("AllocateID after merge got %v, want %v", got2, want2)
	}
}

func TestIDGenerator_ReserveIDRemovesSingletonFreeBlock(t *testing.T) {
	gen := NewIDGenerator()
	prefix := uint16(0x0201)
	bits := uint8(20)
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse: prefix %x too large for bits %d", prefix, bits)
	}
	poolId := validateAndEncodePoolId(prefix, bits)

	_ = gen.AllocateID(prefix, bits)
	_ = gen.AllocateID(prefix, bits)
	_ = gen.AllocateID(prefix, bits) // pool [4, max]

	if !gen.FreeID(constructFullId(poolId, 2), bits) {
		t.Fatal("FreeID(seq 2) should succeed")
	}
	if !gen.ReserveID(constructFullId(poolId, 2), bits) {
		t.Fatal("ReserveID should consume singleton free block [2,2]")
	}
	if gen.ReserveID(constructFullId(poolId, 2), bits) {
		t.Error("second ReserveID for same seq should fail")
	}
}

func TestIDGenerator_ReserveIDShrinkFromStartAndEnd(t *testing.T) {
	gen := NewIDGenerator()
	prefix := uint16(0x0202)
	bits := uint8(20)
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse: prefix %x too large for bits %d", prefix, bits)
	}
	poolId := validateAndEncodePoolId(prefix, bits)
	maxVal := maxSeqIdValue(bits)

	_ = gen.AllocateID(prefix, bits) // pool [2, maxVal]
	if !gen.ReserveID(constructFullId(poolId, 2), bits) {
		t.Fatal("reserve from start of free range")
	}
	// pool [3, maxVal]
	if !gen.ReserveID(constructFullId(poolId, maxVal), bits) {
		t.Fatal("reserve from end of free range")
	}
}

func TestIDGenerator_FreeIDPoolNotCreated(t *testing.T) {
	gen := NewIDGenerator()
	prefix := uint16(0x0203)
	bits := uint8(20)
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse: prefix %x too large for bits %d", prefix, bits)
	}
	poolId := validateAndEncodePoolId(prefix, bits)
	id := constructFullId(poolId, 10)
	if gen.FreeID(id, bits) {
		t.Error("FreeID should fail when no pool exists for that prefix/bitlen")
	}
}

func TestIDGenerator_ConstructFullId(t *testing.T) {
	// For bits=22, prefix fits in 10 bits (max 0x3FF)
	prefix := uint16(0x01ED) // 0x01ED = 493 < 0x3FF
	bits := uint8(22)
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("Test misuse: prefix %x too large for bits %d", prefix, bits)
	}
	seqId := uint32(123456)
	poolId := encodePoolId(prefix, bits)
	fullId := constructFullId(poolId, seqId)

	// Check prefix from fullId matches
	pfx := getPrefixFromFullId(fullId, bits)
	if pfx != prefix {
		t.Errorf("getPrefixFromFullId got %x, want %x", pfx, prefix)
	}
}

func TestIDGenerator_GetPrefixFromFullIdLargePrefix(t *testing.T) {
	// Prefix uses more than the top 16 bits of the composite id alone; recovery must use >> bits.
	const bits uint8 = 20
	const prefix uint16 = 0x0F00 // 3840, still fits in (32-20)=12 bits
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse: prefix %x too large for bits %d", prefix, bits)
	}
	poolId := encodePoolId(prefix, bits)
	seq := uint32(0xABCDE) // within 20 bits
	full := constructFullId(poolId, seq)
	if got := getPrefixFromFullId(full, bits); got != prefix {
		t.Fatalf("getPrefixFromFullId(%#x, %d) = %#x, want %#x", full, bits, got, prefix)
	}
}

func TestIDGenerator_AllocateIDBitLenBoundaries(t *testing.T) {
	gen := NewIDGenerator()
	// seqIdBitLen 17 and 31 are inclusive bounds; prefix must fit in (32 - bits) bits.
	for _, tc := range []struct {
		prefix uint16
		bits   uint8
	}{
		{prefix: 1, bits: 17},
		{prefix: 1, bits: 31},
	} {
		if tc.prefix > ((1 << (32 - tc.bits)) - 1) {
			t.Fatalf("test misuse: prefix %x for bits %d", tc.prefix, tc.bits)
		}
		id := gen.AllocateID(tc.prefix, tc.bits)
		if id == 0 {
			t.Fatalf("AllocateID(%#x, %d) returned 0", tc.prefix, tc.bits)
		}
	}
}

func TestIDGenerator_FreeIDInvalidSequencePortion(t *testing.T) {
	gen := NewIDGenerator()
	const bits uint8 = 20
	const prefix uint16 = 0x0300
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse")
	}
	poolId := validateAndEncodePoolId(prefix, bits)
	if gen.AllocateID(prefix, bits) == 0 {
		t.Fatal("AllocateID to materialize pool")
	}
	// Sequence id 0 is never valid for FreeID (pool exists so we exercise the seqId check).
	if gen.FreeID(constructFullId(poolId, 0), bits) {
		t.Fatal("FreeID must reject sequence id 0")
	}
}

func TestIDGenerator_FreeIDMergeWhenHighSideTouchesNextBlock(t *testing.T) {
	gen := NewIDGenerator()
	const bits uint8 = 20
	const prefix uint16 = 0x0301
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse")
	}
	poolID := validateAndEncodePoolId(prefix, bits)
	for i := 0; i < 4; i++ {
		if gen.AllocateID(prefix, bits) == 0 {
			t.Fatalf("allocate %d", i)
		}
	}
	// Free pool is [5, max]; insert [2,2] then grow into [5, max] with a merge on the boundary.
	if !gen.FreeID(constructFullId(poolID, 2), bits) {
		t.Fatal("FreeID(2)")
	}
	if !gen.FreeID(constructFullId(poolID, 3), bits) {
		t.Fatal("FreeID(3)")
	}
	if !gen.FreeID(constructFullId(poolID, 4), bits) {
		t.Fatal("FreeID(4) should extend and merge consecutive free blocks")
	}
}

func TestIDGenerator_FreeIDInsertBetweenBlocksWithNonNilPrev(t *testing.T) {
	gen := NewIDGenerator()
	const bits uint8 = 20
	const prefix uint16 = 0x0302
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse")
	}
	poolID := validateAndEncodePoolId(prefix, bits)
	// Consume 1..15 so ids 1..15 are in use and the free pool starts at 16.
	for i := 0; i < 15; i++ {
		if gen.AllocateID(prefix, bits) == 0 {
			t.Fatalf("allocate %d", i)
		}
	}
	// Return a few non-contiguous ids to the free list: [5,5], [7,7], [16, max].
	if !gen.FreeID(constructFullId(poolID, 5), bits) {
		t.Fatal("FreeID(5)")
	}
	if !gen.FreeID(constructFullId(poolID, 7), bits) {
		t.Fatal("FreeID(7)")
	}
	// Id 9 is still in use; inserting 9 as free sits strictly between [7,7] and [16, max].
	if !gen.FreeID(constructFullId(poolID, 9), bits) {
		t.Fatal("FreeID(9) should create a middle singleton with a non-nil predecessor pool")
	}
}

func TestIDGenerator_FreeIDAdjacentLowSideOfTailPool(t *testing.T) {
	gen := NewIDGenerator()
	const bits uint8 = 20
	const prefix uint16 = 0x0303
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse")
	}
	poolID := validateAndEncodePoolId(prefix, bits)
	if gen.AllocateID(prefix, bits) == 0 {
		t.Fatal("allocate 1")
	}
	// Tail free pool is [2, max]; freeing the allocated seq 1 hits the pool.from-1 case.
	if !gen.FreeID(constructFullId(poolID, 1), bits) {
		t.Fatal("FreeID(1)")
	}
}

func TestIDGenerator_ReserveIDNotFreeReturnsFalse(t *testing.T) {
	gen := NewIDGenerator()
	const bits uint8 = 20
	const prefix uint16 = 0x0304
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse")
	}
	poolID := validateAndEncodePoolId(prefix, bits)
	if gen.AllocateID(prefix, bits) == 0 {
		t.Fatal("AllocateID to create pool and consume seq 1")
	}
	// seq 1 is in use; the free pool begins at 2, so reserving seq 1 must fail.
	if gen.ReserveID(constructFullId(poolID, 1), bits) {
		t.Fatal("ReserveID on an allocated id should return false")
	}
}

func TestIDGenerator_ReserveIDRemoveSingletonSecondBlockWithPrev(t *testing.T) {
	gen := NewIDGenerator()
	const bits uint8 = 20
	const prefix uint16 = 0x0305
	if prefix > ((1 << (32 - bits)) - 1) {
		t.Fatalf("test misuse")
	}
	poolID := validateAndEncodePoolId(prefix, bits)
	for i := 0; i < 4; i++ {
		if gen.AllocateID(prefix, bits) == 0 {
			t.Fatalf("allocate %d", i)
		}
	}
	// Free pool [5, max]. Split around 50 then narrow the right segment to a singleton [53,53].
	if !gen.ReserveID(constructFullId(poolID, 50), bits) {
		t.Fatal("ReserveID(50) to split the tail range")
	}
	if !gen.ReserveID(constructFullId(poolID, 51), bits) {
		t.Fatal("ReserveID(51)")
	}
	if !gen.ReserveID(constructFullId(poolID, 52), bits) {
		t.Fatal("ReserveID(52)")
	}
	if !gen.ReserveID(constructFullId(poolID, 54), bits) {
		t.Fatal("ReserveID(54) leaving a singleton free id at 53")
	}
	if !gen.ReserveID(constructFullId(poolID, 53), bits) {
		t.Fatal("ReserveID(53) should remove a singleton block when a previous free block exists")
	}
}
