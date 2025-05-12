// idgeneration_test.go
package spir

import (
	"testing"
)

func TestIDGenerator_AllocateID(t *testing.T) {
	gen := NewIDGenerator()
	gen.idPools = make(map[PoolId]*IDPool) // Initialize the map

	// Test case 1: Allocate a valid ID
	id1 := gen.AllocateID(1, 20)
	if id1 == 0 {
		t.Errorf("AllocateID failed to allocate a valid ID")
	}

	// Test case 2: Allocate another ID from the same pool
	id2 := gen.AllocateID(1, 20)
	if id2 == 0 || id2 == id1 {
		t.Errorf("AllocateID failed to allocate a unique ID")
	}

	// Test case 3: Allocate an ID with invalid prefix
	id3 := gen.AllocateID(0xFFFF, 20)
	if id3 != 0 {
		t.Errorf("AllocateID should return 0 for invalid prefix")
	}

	// Test case 4: Allocate an ID with invalid seqIdBitLength
	id4 := gen.AllocateID(1, 32)
	if id4 != 0 {
		t.Errorf("AllocateID should return 0 for invalid seqIdBitLength")
	}

	// Test case 5: Exhaust the pool and check for 0 return
	prefix := uint16(1)
	seqIdBitLength := uint8(20)
	poolId := validateAndEncodePoolId(prefix, seqIdBitLength)
	if poolId == invalidPoolId {
		t.Fatalf("Invalid pool ID for valid prefix and seqIdBitLength")
	}
	pool := createIDPool(seqIdBitLength)
	gen.idPools[poolId] = pool

	maxId := maxIdValue(seqIdBitLength)
	for i := uint32(0); i < maxId; i++ {
		gen.AllocateID(prefix, seqIdBitLength)
	}
	idExhausted := gen.AllocateID(prefix, seqIdBitLength)
	if idExhausted != 0 {
		t.Errorf("AllocateID should return 0 when pool is exhausted")
	}
}

func TestIDGenerator_FreeID(t *testing.T) {
	gen := NewIDGenerator()
	gen.idPools = make(map[PoolId]*IDPool) // Initialize the map

	// Allocate an ID to free
	prefix := uint16(1)
	seqIdBitLength := uint8(20)
	idToFree := gen.AllocateID(prefix, seqIdBitLength)

	// Test case 1: Free a valid ID
	freed := gen.FreeID(idToFree, seqIdBitLength)
	if !freed {
		t.Errorf("FreeID failed to free a valid ID")
	}

	// Test case 2: Free an invalid ID (0)
	freed2 := gen.FreeID(0, seqIdBitLength)
	if freed2 {
		t.Errorf("FreeID should return false for invalid ID (0)")
	}

	// Test case 3: Free an ID with invalid seqIdBitLength
	freed3 := gen.FreeID(1, 32)
	if freed3 {
		t.Errorf("FreeID should return false for invalid seqIdBitLength")
	}

	// Test case 4: Free an ID that was already freed
	freed4 := gen.FreeID(idToFree, seqIdBitLength)
	if freed4 {
		t.Errorf("FreeID should return false for already freed ID")
	}

	// Test case 5: Free an ID to a non-existent pool
	prefix2 := uint16(2)
	idToFree2 := constructFullId(validateAndEncodePoolId(prefix2, seqIdBitLength), 1)
	freed5 := gen.FreeID(idToFree2, seqIdBitLength)
	if freed5 {
		t.Errorf("FreeID should return false for non-existent pool")
	}
}

func TestIDGenerator_AllocateAndFree(t *testing.T) {
	gen := NewIDGenerator()
	gen.idPools = make(map[PoolId]*IDPool) // Initialize the map
	prefix := uint16(1)
	seqIdBitLength := uint8(20)

	// Allocate an ID
	id1 := gen.AllocateID(prefix, seqIdBitLength)
	if id1 == 0 {
		t.Fatalf("Failed to allocate initial ID")
	}

	// Free the ID
	freed := gen.FreeID(id1, seqIdBitLength)
	if !freed {
		t.Errorf("Failed to free ID")
	}

	// Allocate a new ID, should be the same as the freed ID
	id2 := gen.AllocateID(prefix, seqIdBitLength)
	if id2 == 0 {
		t.Fatalf("Failed to allocate second ID")
	}

	// Check if the allocated ID is the same as the freed ID
	if id2 != id1 {
		t.Errorf("Allocated ID is not the same as the freed ID")
	}
}

func TestIDGenerator_MergePools(t *testing.T) {
	gen := NewIDGenerator()
	gen.idPools = make(map[PoolId]*IDPool) // Initialize the map
	prefix := uint16(1)
	seqIdBitLength := uint8(20)

	// Allocate two IDs
	id1 := gen.AllocateID(prefix, seqIdBitLength)
	id2 := gen.AllocateID(prefix, seqIdBitLength)

	// Free the IDs in reverse order to create consecutive free pools
	freed2 := gen.FreeID(id2, seqIdBitLength)
	freed1 := gen.FreeID(id1, seqIdBitLength)

	if !freed1 || !freed2 {
		t.Fatalf("Failed to free IDs")
	}

	// Allocate a new ID, which should trigger the merge of the pools
	id3 := gen.AllocateID(prefix, seqIdBitLength)
	if id3 == 0 {
		t.Fatalf("Failed to allocate third ID")
	}

	// Allocate another ID, which should be the next available ID
	id4 := gen.AllocateID(prefix, seqIdBitLength)
	if id4 == 0 {
		t.Fatalf("Failed to allocate fourth ID")
	}

	if id3 == id1 {
		if id4 != id2 {
			t.Errorf("Pools were not merged correctly")
		}
	} else if id3 == id2 {
		if id4 != id1 {
			t.Errorf("Pools were not merged correctly")
		}
	} else {
		t.Errorf("Pools were not merged correctly")
	}
}

func TestValidateAndEncodePoolId(t *testing.T) {
	// Test case 1: Valid prefix and seqIdBitLength
	poolId := validateAndEncodePoolId(1, 20)
	if poolId == invalidPoolId {
		t.Errorf("validateAndEncodePoolId failed for valid prefix and seqIdBitLength")
	}

	// Test case 2: Invalid seqIdBitLength (>= 32)
	poolId2 := validateAndEncodePoolId(1, 32)
	if poolId2 != invalidPoolId {
		t.Errorf("validateAndEncodePoolId should return invalidPoolId for seqIdBitLength >= 32")
	}

	// Test case 3: Invalid seqIdBitLength (<= 16)
	poolId3 := validateAndEncodePoolId(1, 16)
	if poolId3 != invalidPoolId {
		t.Errorf("validateAndEncodePoolId should return invalidPoolId for seqIdBitLength <= 16")
	}

	// Test case 4: Prefix bits are getting dropped during the shift
	poolId4 := validateAndEncodePoolId(0xFFFF, 17)
	if poolId4 != invalidPoolId {
		t.Errorf("validateAndEncodePoolId should return invalidPoolId when prefix bits are dropped")
	}
}
