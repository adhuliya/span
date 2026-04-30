package spir

import (
	"math/rand/v2"
	"slices"
	"strings"
	"testing"
)

// eids is a helper converting a variadic list of uint32 values
// into a slice of EntityId, as expected by EidSet.
func eids(xs ...uint32) []EntityId {
	out := make([]EntityId, len(xs))
	for i, x := range xs {
		out[i] = EntityId(x)
	}
	return out
}

// TestNewEidSet_sortsDedupesAndCapacity covers basic construction guarantees for EidSet.
func TestNewEidSet_sortsDedupesAndCapacity(t *testing.T) {
	t.Parallel()
	s := NewEidSet(false, eids(3, 1, 2, 1, 3)...)
	if !slices.Equal(s.Values(), eids(1, 2, 3)) {
		t.Fatalf("Values: got %v", s.Values())
	}
	if cap(s.data) < 4 {
		t.Fatalf("expected cap >= 4, got %d", cap(s.data))
	}
}

// TestNewEidSet_empty checks construction of an empty EidSet.
func TestNewEidSet_empty(t *testing.T) {
	t.Parallel()
	s := NewEidSet(false)
	if !s.IsEmpty() {
		t.Fatal("expected empty")
	}
	if s.Values() == nil {
		t.Fatal("empty set should have non-nil slice with len 0 for consistent capacity behavior")
	}
}

// TestEidSet_IsEmpty_Clear checks IsEmpty and Clear.
func TestEidSet_IsEmpty_Clear(t *testing.T) {
	t.Parallel()
	s := NewEidSet(false, eids(1)...)
	if s.IsEmpty() {
		t.Fatal("not empty")
	}
	s.Clear()
	if !s.IsEmpty() {
		t.Fatal("after Clear")
	}
	if s.data != nil {
		t.Fatal("Clear should nil backing slice")
	}
}

// TestEidSet_IsSortedAndUnique checks that the sorted and unique invariant holds.
func TestEidSet_IsSortedAndUnique(t *testing.T) {
	t.Parallel()
	if !NewEidSet(false).IsSortedAndUnique() {
		t.Fatal("empty")
	}
	if !NewEidSet(false, eids(7)...).IsSortedAndUnique() {
		t.Fatal("single")
	}
	s := NewEidSet(false, eids(1, 2, 3)...)
	if !s.IsSortedAndUnique() {
		t.Fatal("valid")
	}
}

// TestEidSet_Contains_Add_Remove covers containership, as well as addition/removal of elements.
func TestEidSet_Contains_Add_Remove(t *testing.T) {
	t.Parallel()
	s := NewEidSet(false, eids(2, 4)...)
	if !s.Contains(2) || s.Contains(3) {
		t.Fatalf("Contains: %+v", s.Values())
	}
	if !s.Add(3) || s.Add(3) {
		t.Fatalf("Add idempotent: %+v", s.Values())
	}
	if !slices.Equal(s.Values(), eids(2, 3, 4)) {
		t.Fatalf("after add: %v", s.Values())
	}
	if !s.Remove(3) || s.Remove(3) {
		t.Fatalf("Remove: %+v", s.Values())
	}
	if !slices.Equal(s.Values(), eids(2, 4)) {
		t.Fatalf("after remove: %v", s.Values())
	}
}

// TestEidSet_Union tests creation of new set via union.
func TestEidSet_Union(t *testing.T) {
	t.Parallel()
	a := *NewEidSet(false, eids(1, 3)...)
	b := *NewEidSet(false, eids(2, 3)...)
	u, ch := a.Union(b)
	if !slices.Equal(u.Values(), eids(1, 2, 3)) {
		t.Fatalf("union values: %v", u.Values())
	}
	if !ch {
		t.Fatal("changed should be true when merged length != len(a)")
	}
	empty := *NewEidSet(false)
	u2, ch2 := empty.Union(empty)
	if !u2.IsEmpty() || ch2 {
		t.Fatalf("two empties: empty=%v ch=%v", u2.IsEmpty(), ch2)
	}
	u3, ch3 := empty.Union(*NewEidSet(false, eids(1)...))
	if !slices.Equal(u3.Values(), eids(1)) || !ch3 {
		t.Fatalf("left empty: %v %v", u3.Values(), ch3)
	}
	u4p, ch4b := NewEidSet(false, eids(1)...).Union(empty)
	if !slices.Equal(u4p.Values(), eids(1)) || ch4b {
		t.Fatalf("right empty: %v ch=%v", u4p.Values(), ch4b)
	}
}

// TestEidSet_UnionWith tests in-place union.
func TestEidSet_UnionWith(t *testing.T) {
	t.Parallel()
	s := NewEidSet(false, eids(1, 5)...)
	if s.UnionWith(*NewEidSet(false)) {
		t.Fatal("union empty should not change")
	}
	if !s.UnionWith(*NewEidSet(false, eids(2, 5, 7)...)) {
		t.Fatal("expected change")
	}
	if !slices.Equal(s.Values(), eids(1, 2, 5, 7)) {
		t.Fatalf("UnionWith: %v", s.Values())
	}
	if !s.IsSortedAndUnique() {
		t.Fatal("invariant")
	}
}

// TestEidSet_Intersection tests creation of intersection set.
func TestEidSet_Intersection(t *testing.T) {
	t.Parallel()
	a := *NewEidSet(false, eids(1, 2, 4)...)
	b := *NewEidSet(false, eids(2, 3, 4)...)
	in, ch := a.Intersection(b)
	if !slices.Equal(in.Values(), eids(2, 4)) {
		t.Fatalf("got %v", in.Values())
	}
	if !ch {
		t.Fatal("intersection shorter than a")
	}
	in2, _ := a.Intersection(*NewEidSet(false))
	if !in2.IsEmpty() {
		t.Fatal("no overlap")
	}
}

// TestEidSet_IntersectionWith tests in-place intersection operation.
func TestEidSet_IntersectionWith(t *testing.T) {
	t.Parallel()
	s := NewEidSet(false, eids(1, 2, 3)...)
	if !s.IntersectionWith(*NewEidSet(false, eids(2, 4)...)) {
		t.Fatal("expected change")
	}
	if !slices.Equal(s.Values(), eids(2)) {
		t.Fatalf("got %v", s.Values())
	}
	s2 := NewEidSet(false, eids(1)...)
	if s2.IntersectionWith(*NewEidSet(false, eids(1)...)) {
		t.Fatal("same set should not report change")
	}
}

// TestEidSet_Subtract tests set subtraction.
func TestEidSet_Subtract(t *testing.T) {
	t.Parallel()
	a := *NewEidSet(false, eids(1, 2, 3)...)
	b := *NewEidSet(false, eids(2, 4)...)
	d, ch := a.Subtract(b)
	if !slices.Equal(d.Values(), eids(1, 3)) || !ch {
		t.Fatalf("Subtract: %v ch=%v", d.Values(), ch)
	}
}

// TestEidSet_SubtractWith tests in-place subtraction.
func TestEidSet_SubtractWith(t *testing.T) {
	t.Parallel()
	s := NewEidSet(false, eids(1, 2, 3)...)
	if !s.SubtractWith(*NewEidSet(false, eids(2)...)) {
		t.Fatal("expected change")
	}
	if !slices.Equal(s.Values(), eids(1, 3)) {
		t.Fatalf("got %v", s.Values())
	}
}

// TestEidSet_IsSubset_IsSubsetEq tests IsSubset and IsSubsetEq behavior.
func TestEidSet_IsSubset_IsSubsetEq(t *testing.T) {
	t.Parallel()
	small := *NewEidSet(false, eids(1, 2)...)
	big := *NewEidSet(false, eids(0, 1, 2, 3)...)
	if !small.IsSubsetEq(big) || !small.IsSubset(big) {
		t.Fatal("small in big")
	}
	if big.IsSubset(small) {
		t.Fatal("big not proper subset of small")
	}
	if !(*NewEidSet(false)).IsSubsetEq(*NewEidSet(false, eids(1)...)) {
		t.Fatal("empty subseteq nonempty")
	}
	if (*NewEidSet(false)).IsSubset(*NewEidSet(false)) {
		t.Fatal("empty not proper subset of empty")
	}
	if !small.IsSubsetEq(small) || small.IsSubset(small) {
		t.Fatal("equal: subseteq yes, proper subset no")
	}
}

// TestEidSet_Equals_Duplicate_String tests equality, duplication, and string representation.
func TestEidSet_Equals_Duplicate_String(t *testing.T) {
	t.Parallel()
	a := *NewEidSet(false, eids(1, 2)...)
	b := *NewEidSet(false, eids(1, 2)...)
	if !a.Equals(b) || a.Equals(*NewEidSet(false, eids(2)...)) {
		t.Fatal("Equals")
	}
	d := a.Duplicate(false)
	d.Add(99)
	if !slices.Equal(a.Values(), eids(1, 2)) {
		t.Fatal("Duplicate must not alias")
	}
	got := a.String()
	if !strings.HasPrefix(got, "{") || !strings.HasSuffix(got, "}") || strings.Count(got, ",") != 1 {
		t.Fatalf("String (two sorted elements): %q", got)
	}
	if NewEidSet(false).String() != "{}" {
		t.Fatalf("empty string: %q", NewEidSet(false).String())
	}
}

// TestEidSet_LargeRandomized performs tests with large sets of random EntityIds.
// This tests efficiency and correctness of large set operations and invariants.
func TestEidSet_LargeRandomized(t *testing.T) {
	t.Parallel()
	const setSize = 1000

	// Seeded randomness for deterministic test outcomes.
	rng := rand.New(rand.NewPCG(42, 55))

	// Helper to generate a random slice of uint32s of given size, with possible duplicates.
	randomSlice := func(size int) []uint32 {
		out := make([]uint32, size)
		for i := range out {
			out[i] = rng.Uint32() % 3000 // Many will be unique, some not.
		}
		return out
	}

	// Generate two large random slices, with overlap.
	sliceA := randomSlice(setSize)
	sliceB := randomSlice(setSize)
	setA := NewEidSet(false, eids(sliceA...)...)
	setB := NewEidSet(false, eids(sliceB...)...)

	// 1. Test invariants.
	if !setA.IsSortedAndUnique() || !setB.IsSortedAndUnique() {
		t.Fatal("EidSet failed to maintain invariants on large random input")
	}

	// 2. Test Union and compare values to Go's set semantics.
	unionGo := map[EntityId]struct{}{}
	for _, x := range setA.Values() {
		unionGo[x] = struct{}{}
	}
	for _, x := range setB.Values() {
		unionGo[x] = struct{}{}
	}

	unionSet, changed := setA.Union(*setB)
	if !changed && len(unionGo) != len(setA.Values()) {
		t.Fatalf("Union should have changed if lengths differ")
	}

	unionList := make([]EntityId, 0, len(unionGo))
	for k := range unionGo {
		unionList = append(unionList, k)
	}
	slices.Sort(unionList)

	if !slices.Equal(unionSet.Values(), unionList) {
		t.Errorf("Union mismatch: got %v want %v", unionSet.Values(), unionList)
	}

	// 3. Test Intersection with Go's set intersection logic.
	interGo := map[EntityId]struct{}{}
	for _, a := range setA.Values() {
		interGo[a] = struct{}{}
	}
	interList := make([]EntityId, 0, len(setA.Values()))
	for _, b := range setB.Values() {
		if _, ok := interGo[b]; ok {
			interList = append(interList, b)
		}
	}
	slices.Sort(interList)
	// interList may contain duplicates due to setB semantics, dedupe for proper intersection
	dedup := make([]EntityId, 0, len(interList))
	for i, v := range interList {
		if i == 0 || v != interList[i-1] {
			dedup = append(dedup, v)
		}
	}
	interList = dedup
	interSet, _ := setA.Intersection(*setB)
	if !slices.Equal(interSet.Values(), interList) {
		t.Errorf("Intersection mismatch: got %v want %v", interSet.Values(), interList)
	}

	// 4. Test Subtract with reference Go implementation: setA - setB
	subGo := map[EntityId]struct{}{}
	for _, a := range setA.Values() {
		subGo[a] = struct{}{}
	}
	for _, b := range setB.Values() {
		delete(subGo, b)
	}
	subList := make([]EntityId, 0, len(subGo))
	for k := range subGo {
		subList = append(subList, k)
	}
	slices.Sort(subList)

	subSet, _ := setA.Subtract(*setB)
	if !slices.Equal(subSet.Values(), subList) {
		t.Errorf("Subtract mismatch: got %v want %v", subSet.Values(), subList)
	}

	// Finally, check that after mutating with UnionWith/IntersectionWith/SubtractWith, the invariants hold.
	setCopy := setA.Duplicate(false)
	setCopy.UnionWith(*setB)
	if !setCopy.IsSortedAndUnique() {
		t.Error("UnionWith violated invariants on large set")
	}
	setCopy = setA.Duplicate(false)
	setCopy.IntersectionWith(*setB)
	if !setCopy.IsSortedAndUnique() {
		t.Error("IntersectionWith violated invariants on large set")
	}
	setCopy = setA.Duplicate(false)
	setCopy.SubtractWith(*setB)
	if !setCopy.IsSortedAndUnique() {
		t.Error("SubtractWith violated invariants on large set")
	}
}
