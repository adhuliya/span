package dsa

import (
	"slices"
	"sort"
)

// This file defines the common data structures used in the SPAN program analysis engine.

type KeySet32 struct {
	keys []uint32
}

func NewKeySet32(size int) *KeySet32 {
	return &KeySet32{
		keys: make([]uint32, 0, size),
	}
}

// AddKey, HasKey, and RemoveKey are used to add, check, and remove keys from the KeySet32.
// The keys are stored in a sorted order and the operations are performed in O(log n) time.

// AddKey adds a key by inserting it into the sorted slice.
func (ks *KeySet32) AddKey(key uint32) {
	if ks.HasKey(key) {
		return
	}
	ks.keys = append(ks.keys, key)
	// Sort the keys in ascending order.
	slices.Sort(ks.keys)
}

// HasKey checks if a key is present in the KeySet32.
func (ks *KeySet32) HasKey(key uint32) bool {
	// Use binary search to find the key in the sorted slice.
	idx := sort.Search(len(ks.keys), func(i int) bool {
		return ks.keys[i] >= key
	})
	return idx < len(ks.keys) && ks.keys[idx] == key
}

// RemoveKey removes a key from the KeySet32.
func (ks *KeySet32) RemoveKey(key uint32) {
	if !ks.HasKey(key) {
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

// RemoveKeys removes multiple keys from the KeySet32.
func (ks *KeySet32) RemoveKeys(keys ...uint32) {
	for _, key := range keys {
		ks.RemoveKey(key)
	}
}

// KeySet64 is a set of 64-bit keys.
type KeySet64 struct {
	keys []uint64
}

func NewKeySet64(size int) *KeySet64 {
	return &KeySet64{
		keys: make([]uint64, 0, size),
	}
}

// AddKey adds a key by inserting it into the sorted slice.
func (ks *KeySet64) AddKey(key uint64) {
	if ks.HasKey(key) {
		return
	}
	ks.keys = append(ks.keys, key)
	// Sort the keys in ascending order.
	slices.Sort(ks.keys)
}

// HasKey checks if a key is present in the KeySet64.
func (ks *KeySet64) HasKey(key uint64) bool {
	// Use binary search to find the key in the sorted slice.
	idx := sort.Search(len(ks.keys), func(i int) bool {
		return ks.keys[i] >= key
	})
	return idx < len(ks.keys) && ks.keys[idx] == key
}

// RemoveKey removes a key from the KeySet64.
func (ks *KeySet64) RemoveKey(key uint64) {
	if !ks.HasKey(key) {
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

// RemoveKeys removes multiple keys from the KeySet64.
func (ks *KeySet64) RemoveKeys(keys ...uint64) {
	for _, key := range keys {
		ks.RemoveKey(key)
	}
}

// Clear clears the KeySet32.
func (ks *KeySet32) Clear() {
	ks.keys = ks.keys[:0]
}

// Clear clears the KeySet64.
func (ks *KeySet64) Clear() {
	ks.keys = ks.keys[:0]
}

// GetKeys returns the keys in the KeySet32.
func (ks *KeySet32) GetKeys() []uint32 {
	result := make([]uint32, len(ks.keys))
	copy(result, ks.keys)
	return result
}

// GetKeys returns the keys in the KeySet64.
func (ks *KeySet64) GetKeys() []uint64 {
	result := make([]uint64, len(ks.keys))
	copy(result, ks.keys)
	return result
}
