package dsa

import "sort"

// Key-Value pairs using slices

type KVSlice32_32x4 struct {
	// keys is a slice of uint32 keys.
	keys []uint32
	// values is a slice of 4 uint32 values.
	values [][4]uint32
}

func NewKVSlice32_32x4(size int) *KVSlice32_32x4 {
	return &KVSlice32_32x4{
		keys:   make([]uint32, 0, size),
		values: make([][4]uint32, 0, size),
	}
}

// AddKey adds a key and its corresponding value to the KVSlice32_32x4.
// If the key already exists, it updates the value.
func (kv *KVSlice32_32x4) AddKey(key uint32, value [4]uint32) {
	if kv.HasKey(key) {
		// Update the value if the key already exists.
		for i, k := range kv.keys {
			if k == key {
				kv.values[i] = value
				return
			}
		}
	} else {
		// Add the new key and value in sorted order
		insertIdx := 0
		for i, k := range kv.keys {
			if key < k {
				insertIdx = i
				break
			}
			insertIdx = i + 1
		}

		// Insert the key and value at the correct position
		kv.keys = append(kv.keys, 0) // Make space for the new element
		copy(kv.keys[insertIdx+1:], kv.keys[insertIdx:])
		kv.keys[insertIdx] = key

		kv.values = append(kv.values, [4]uint32{})
		copy(kv.values[insertIdx+1:], kv.values[insertIdx:])
		kv.values[insertIdx] = value
	}
}

// HasKey checks if a key is present in the KVSlice32_32x4.
func (kv *KVSlice32_32x4) HasKey(key uint32) bool {
	// Use binary search to find the key in the sorted slice.
	idx := sort.Search(len(kv.keys), func(i int) bool {
		return kv.keys[i] >= key
	})
	return idx < len(kv.keys) && kv.keys[idx] == key
}

// RemoveKey removes a key from the KVSlice32_32x4.
func (kv *KVSlice32_32x4) RemoveKey(key uint32) {
	if !kv.HasKey(key) {
		return
	}
	// Remove the key and value from the sorted slice.
	for i, k := range kv.keys {
		if k == key {
			// Shift all elements after i one position to the left
			copy(kv.keys[i:], kv.keys[i+1:])
			copy(kv.values[i:], kv.values[i+1:])

			// Set the last element to 0
			// to avoid keeping a reference to the old value.
			kv.keys[len(kv.keys)-1] = 0
			kv.values[len(kv.values)-1] = [4]uint32{}

			// // Reduce the length of the slices
			// kv.keys = kv.keys[:len(kv.keys)-1]
			// kv.values = kv.values[:len(kv.values)-1]
			break
		}
	}
}

func (kv *KVSlice32_32x4) GetKey(key uint32) ([4]uint32, bool) {
	if !kv.HasKey(key) {
		return [4]uint32{}, false
	}
	for i, k := range kv.keys {
		if k == key {
			return kv.values[i], true
		}
	}
	return [4]uint32{}, false
}
