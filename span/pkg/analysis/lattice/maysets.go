package lattice

import "github.com/adhuliya/span/pkg/spir"

// MaySetLattice is a ConstLattice for may-sets of spir.EntityId values.
// Smaller sets are more precise: top is the empty set, meet is union,
// and join is intersection.
type MaySetLattice struct {
	isBot  bool
	maySet spir.EidSet
}

var _ ConstLattice = (*MaySetLattice)(nil)

// NewMaySetLattice creates a MaySetLattice containing the given EntityIds.
func NewMaySetLattice(eids spir.EidSet, isBot bool) *MaySetLattice {
	eidSet := *spir.NewEidSet(false)
	for _, id := range eids.Iterator {
		eidSet.Add(id)
	}
	eidSet.MakeFixed() // Make the set fixed to avoid modifications after creation
	return &MaySetLattice{
		isBot:  isBot,
		maySet: eidSet,
	}
}

func (l *MaySetLattice) IsConstLattice() bool {
	return true
}

func (l *MaySetLattice) IsTop() bool {
	return l.maySet.IsEmpty()
}

// IsBot is false because this lattice does not carry a universe of all EntityIds.
func (l *MaySetLattice) IsBot() bool {
	return false
}

func (l *MaySetLattice) WeakerThan(other Lattice) bool {
	oth, ok := other.(*MaySetLattice)
	if !ok {
		return false
	}
	return oth.maySet.IsSubsetEq(l.maySet)
}

func (l *MaySetLattice) Equals(other Lattice) bool {
	oth, ok := other.(*MaySetLattice)
	if !ok {
		return false
	}
	return l.maySet.Equals(oth.maySet)
}

func (l *MaySetLattice) Meet(other Lattice) (Lattice, bool) {
	oth, ok := other.(*MaySetLattice)
	if !ok {
		return l, false
	}

	meetSet, changed := l.maySet.Union(oth.maySet)
	if !changed {
		return l, false
	}
	return &MaySetLattice{maySet: *meetSet}, true
}

func (l *MaySetLattice) Join(other Lattice) (Lattice, bool) {
	oth, ok := other.(*MaySetLattice)
	if !ok {
		return l, false
	}

	joinSet, changed := l.maySet.Intersection(oth.maySet)
	if !changed {
		return l, false
	}
	return &MaySetLattice{maySet: *joinSet}, true
}

func (l *MaySetLattice) Widen(other Lattice) (Lattice, bool) {
	return l.Meet(other)
}

func (l *MaySetLattice) String() string {
	return "MaySetLattice" + l.maySet.String()
}
