package spir

/* Defines a set and its operations
1. EidSet
*/

import (
	"fmt"
	"slices"
	"strings"
)

// EidSet is a set of uint32 values that always maintains its slice sorted.
// All operations are performed assuming the sorted invariant.
type EidSet struct {
	fixed bool
	data  []EntityId
}

// Iterator allows external code to "yield" each EntityId, emulating generator semantics.
// The yield callback should return true to continue, false to stop iteration early.
// Usage example:
//
//	set.Iterator(func(index int, id EntityId) bool {
//	    fmt.Println(index, id)
//	    return true // return false to stop early
//	})
func (s *EidSet) Iterator(yield func(index int, id EntityId) bool) {
	for i := 0; i < len(s.data); i++ {
		if !yield(i, s.data[i]) {
			return
		}
	}
}

// IsEmpty returns true if the set has no elements.
func (s *EidSet) IsEmpty() bool {
	return len(s.data) == 0
}

// IsFixed returns true if the set is fixed.
// A fixed set is one that cannot be modified after creation.
// This is useful for creating sets that are used as constants.
func (s *EidSet) IsFixed() bool {
	return s.fixed
}

func (s *EidSet) MakeFixed() {
	s.sortAndUnique() // ensure the set is sorted and unique
	s.fixed = true
}

// Len returns the number of elements in the set.
func (s *EidSet) Len() int {
	return len(s.data)
}

// NewEidSet creates a new EidSet from the given elements.
// It allocates a minimum size of 4 elements.
func NewEidSet(fixed bool, elems ...EntityId) *EidSet {
	set := &EidSet{fixed: fixed}
	capSize := max(4, len(elems))
	// Keep the logical length equal to provided elements to avoid
	// introducing zero-valued EntityIds.
	set.data = make([]EntityId, len(elems), capSize)
	copy(set.data, elems)
	// Remove duplicates and sort
	set.sortAndUnique()
	return set
}

// Clear removes all elements from the set, making it empty.
func (s *EidSet) Clear() {
	if s.fixed {
		panic("cannot clear a fixed EidSet")
	}
	// Release the underlying array memory as well.
	s.data = nil
}

// sortAndUnique sorts the data and removes duplicates in-place.
func (s *EidSet) sortAndUnique() {
	if len(s.data) == 0 {
		return
	}
	slices.Sort(s.data)
	uni := s.data[:1]
	for _, v := range s.data[1:] {
		if v != uni[len(uni)-1] {
			uni = append(uni, v)
		}
	}
	s.data = uni
}

// IsSortedAndUnique returns true if the elements in the set are sorted in strictly
// increasing order and are unique.
// An empty or single-element set is trivially sorted and unique.
func (s *EidSet) IsSortedAndUnique() bool {
	n := len(s.data)
	if n == 0 || n == 1 {
		return true
	}
	for i := 1; i < n; i++ {
		if s.data[i] <= s.data[i-1] {
			return false
		}
	}
	return true
}

// Contains returns true if x is in the set.
func (s *EidSet) Contains(x EntityId) bool {
	_, found := slices.BinarySearch(s.data, x)
	return found
}

// Add inserts x into the set (if not already present).
func (s *EidSet) Add(x EntityId) bool {
	if s.fixed {
		panic("cannot add to a fixed EidSet")
	}
	i, found := slices.BinarySearch(s.data, x)
	if found {
		return false // no change
	}
	// Insert x at index i
	s.data = append(s.data, 0)
	copy(s.data[i+1:], s.data[i:])
	s.data[i] = x
	return true // element added
}

// Remove deletes x from the set if it exists.
func (s *EidSet) Remove(x EntityId) bool {
	if s.fixed {
		panic("cannot remove from a fixed EidSet")
	}
	i, found := slices.BinarySearch(s.data, x)
	if !found {
		return false // no change
	}
	// Remove the element at index i
	s.data = append(s.data[:i], s.data[i+1:]...)
	return true // element removed
}

// UnionWith unions this set with another set b (in place).
func (s *EidSet) UnionWith(b EidSet) bool {
	if s.fixed {
		panic("cannot union with a fixed EidSet. Use Union instead.")
	}
	if len(b.data) == 0 {
		return false // no change
	}
	// Optimization: prepare capacity before merging
	// In-place union without allocating a merged slice
	changed := false
	i, j := 0, 0
	aLen, bLen := len(s.data), len(b.data)
	// We'll walk through both sorted arrays, inserting from b into s.data where needed.
	for j < bLen {
		// Advance i such that s.data[i] >= b.data[j] or i == aLen
		for i < aLen && s.data[i] < b.data[j] {
			i++
		}
		if i == aLen {
			// Append the remainder of b.data[j:] to s.data
			s.data = append(s.data, b.data[j:]...)
			changed = true
			break
		}
		if s.data[i] == b.data[j] {
			// Already present, move both pointers
			j++
			i++
		} else if s.data[i] > b.data[j] {
			// Insert b.data[j] at index i
			s.data = append(s.data, 0)     // make room
			copy(s.data[i+1:], s.data[i:]) // shift to the right
			aLen++
			s.data[i] = b.data[j]
			changed = true
			i++
			j++
		}
	}
	return changed
}

// Union returns a new EidSet that is the union of this set and another set b.
// The original sets are not modified.
func (s EidSet) Union(b EidSet) (*EidSet, bool) {
	// Handle empty set cases.
	if len(s.data) == 0 && len(b.data) == 0 {
		return &EidSet{data: []EntityId{}}, false
	}
	if len(s.data) == 0 {
		return &EidSet{data: append([]EntityId(nil), b.data...)}, true
	}
	if len(b.data) == 0 {
		return &EidSet{data: append([]EntityId(nil), s.data...)}, false
	}

	// Merge the two sets, but do not mutate sources.
	merged := make([]EntityId, 0, len(s.data)+len(b.data))
	i, j := 0, 0
	for i < len(s.data) && j < len(b.data) {
		aVal, bVal := s.data[i], b.data[j]
		switch {
		case aVal < bVal:
			merged = append(merged, aVal)
			i++
		case bVal < aVal:
			merged = append(merged, bVal)
			j++
		default:
			merged = append(merged, aVal)
			i++
			j++
		}
	}
	merged = append(merged, s.data[i:]...)
	merged = append(merged, b.data[j:]...)

	// changed is true iff merged length differs from s.data length
	changed := len(merged) != len(s.data)
	eidSet := &EidSet{data: merged}
	return eidSet, changed
}

// Intersection returns a new EidSet that is the intersection of this set and b.
func (s EidSet) Intersection(b EidSet) (*EidSet, bool) {
	intersection := make([]EntityId, 0, min(len(s.data), len(b.data)))
	i, j := 0, 0
	for i < len(s.data) && j < len(b.data) {
		aVal, bVal := s.data[i], b.data[j]
		switch {
		case aVal < bVal:
			i++
		case bVal < aVal:
			j++
		default:
			intersection = append(intersection, aVal)
			i++
			j++
		}
	}
	changed := len(intersection) != len(s.data)
	return &EidSet{data: intersection}, changed
}

// IntersectionWith modifies s in-place, keeping only the elements also in b.
// Returns true if s.data changed, false otherwise.
// Calls the Intersection method internally.
func (s *EidSet) IntersectionWith(b EidSet) bool {
	if s.fixed {
		panic("cannot modify a fixed EidSet with IntersectionWith. Use Intersection instead.")
	}
	result, changed := s.Intersection(b)
	if changed {
		s.data = result.data
	}
	return changed
}

// Subtract returns a new EidSet containing elements in s that are not in b.
// Also returns a bool indicating if the result differs from s.data.
func (s EidSet) Subtract(b EidSet) (*EidSet, bool) {
	diff := make([]EntityId, 0, len(s.data))
	i, j := 0, 0
	for i < len(s.data) && j < len(b.data) {
		aVal, bVal := s.data[i], b.data[j]
		switch {
		case aVal < bVal:
			diff = append(diff, aVal)
			i++
		case aVal > bVal:
			j++
		default:
			// Element present in both, skip
			i++
			j++
		}
	}
	// Append the rest of s's elements (since b is exhausted)
	diff = append(diff, s.data[i:]...)
	changed := len(diff) != len(s.data)
	return &EidSet{data: diff}, changed
}

// SubtractWith removes from s all elements that are present in b, mutating s in-place.
// Returns true if s.data changed, false otherwise.
func (s *EidSet) SubtractWith(b EidSet) bool {
	if s.fixed {
		panic("cannot modify a fixed EidSet with SubtractWith. Use Subtract instead.")
	}
	out := make([]EntityId, 0, len(s.data))
	i, j := 0, 0
	for i < len(s.data) && j < len(b.data) {
		aVal, bVal := s.data[i], b.data[j]
		switch {
		case aVal < bVal:
			out = append(out, aVal)
			i++
		case aVal > bVal:
			j++
		default:
			// Element present in both, skip
			i++
			j++
		}
	}
	// Append the rest of s's elements (since b is exhausted)
	out = append(out, s.data[i:]...)
	changed := len(out) != len(s.data)
	s.data = out
	return changed
}

// IsSubset checks if the set s is a (proper) subset of set b.
// Proper subset: all elements in s are in b, and s != b.
func (s EidSet) IsSubset(b EidSet) bool {
	if len(s.data) == 0 {
		return len(b.data) > 0 // empty set is proper subset of any non-empty set
	}
	if len(s.data) >= len(b.data) {
		return false
	}
	i, j := 0, 0
	for i < len(s.data) && j < len(b.data) {
		if s.data[i] < b.data[j] {
			return false // element in s that's not in b
		} else if s.data[i] > b.data[j] {
			j++
		} else {
			i++
			j++
		}
	}
	return i == len(s.data)
}

// IsSubsetEq checks if the set s is a subset (possibly equal) of set b.
// Returns true if every element of s is in b (s may equal b).
func (s EidSet) IsSubsetEq(b EidSet) bool {
	if len(s.data) == 0 {
		return true // empty set is subset of any set
	}
	if len(s.data) > len(b.data) {
		return false
	}
	i, j := 0, 0
	for i < len(s.data) && j < len(b.data) {
		if s.data[i] < b.data[j] {
			return false // element in s that's not in b
		} else if s.data[i] > b.data[j] {
			j++
		} else {
			i++
			j++
		}
	}
	return i == len(s.data)
}

// Equals checks if the set s is equal to set b.
func (s EidSet) Equals(b EidSet) bool {
	if len(s.data) != len(b.data) {
		return false
	}
	for i, v := range s.data {
		if v != b.data[i] {
			return false
		}
	}
	return true
}

// Duplicate returns a new copy of the set.
func (s EidSet) Duplicate(fixed bool) *EidSet {
	dup := make([]EntityId, len(s.data))
	copy(dup, s.data)
	return &EidSet{data: dup, fixed: fixed}
}

// Values returns the backing slice (sorted, do not mutate).
func (s EidSet) Values() []EntityId {
	if s.fixed {
		panic("cannot get values from a fixed EidSet")
	}
	return s.data
}

// String returns a string representation of the EidSet.
// Example output: "{1,2,3}" for a set containing EntityIds 1,2,3.
func (s EidSet) String() string {
	if len(s.data) == 0 {
		return "{}"
	}
	var builder strings.Builder
	builder.WriteByte('{')
	for i, v := range s.data {
		if i > 0 {
			builder.WriteByte(',')
		}
		fmt.Fprintf(&builder, "%v", v)
	}
	builder.WriteByte('}')
	return builder.String()
}
