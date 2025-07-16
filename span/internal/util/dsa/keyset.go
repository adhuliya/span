package dsa

import (
	"slices"
	"sort"
)

// This file defines some common data structures used in the SPAN program analysis engine.

// Data structures defined in this file are:
// Key stores (with MAX32/64 as an invalid key):
//  * KeySeqUint32
//  * KeySetUint64

type KeySeqUint32 struct {
	keys []uint32
}

// KeySeqUint64 is a set of 64-bit keys.
type KeySeqUint64 struct {
	keys []uint64
}

func NewKeySetUint32(size int) *KeySeqUint32 {
	return &KeySeqUint32{
		keys: make([]uint32, 0, size),
	}
}

func NewKeySeqUint64(size int) *KeySeqUint64 {
	return &KeySeqUint64{
		keys: make([]uint64, 0, size),
	}
}

// AddKey, GetKeyIndex, and RemoveKey are used to add, check, and remove keys from the KeySeqUint32.
// The keys are stored in a sorted order and the operations are performed in O(log n) time.

// AddKey adds a key by inserting it into the sorted slice.
// It returns false if the key is already present.
func (ks *KeySeqUint32) AddKey(key uint32) bool {
	if ks.GetKeyIndex(key) != -1 {
		return false
	}
	// Append the key and sort.
	ks.keys = append(ks.keys, key)
	slices.Sort(ks.keys)
	return true
}

// GetKeyIndex checks if a key is present in the KeySeqUint32.
// Returns -1 if the key is not present
func (ks *KeySeqUint32) GetKeyIndex(key uint32) int {
	// Use binary search to find the key in the sorted slice.
	idx := sort.Search(len(ks.keys), func(i int) bool {
		return ks.keys[i] >= key
	})

	if idx > len(ks.keys) || ks.keys[idx] != key {
		idx = -1
	}
	return idx
}

// RemoveKey removes a key from the KeySeqUint32.
func (ks *KeySeqUint32) RemoveKey(key uint32) {
	if ks.GetKeyIndex(key) == -1 {
		return
	}
	// Remove the key from the sorted slice.
	for i, k := range ks.keys {
		if k == key {
			// Shift all elements after i one position to the left
			copy(ks.keys[i:], ks.keys[i+1:])
			// Set the last element to 0
			// to avoid keeping a reference to the old value.
			ks.keys[len(ks.keys)-1] = 0
			break
		}
	}
}

// RemoveKeys removes multiple keys from the KeySeqUint32.
func (ks *KeySeqUint32) RemoveKeys(keys ...uint32) {
	for _, key := range keys {
		ks.RemoveKey(key)
	}
}
