package lattice

import (
	"github.com/adhuliya/span/internal/util/errs"
)

// This file contains the base lattice interface used in the SPAN program analysis engine.

type Lattice interface {
	IsTop() bool
	IsBot() bool
	WeakerThan(other Lattice) bool

	// Meet to get a more approximate value (unlike in Abstract Interpretation)
	// bool indicates if the value changed during the meet operation
	Meet(other Lattice) (Lattice, bool)

	// Join to get a more precise value (unlike in Abstract Interpretation)
	// bool indicates if the value changed during the join operation
	Join(other Lattice) (Lattice, bool)

	// Widening operator to allow termination of the analysis
	Widen(other Lattice) (Lattice, bool)

	Equals(other Lattice) bool
	String() string
}

// A ConstLattice is a place holder Lattice interface for constant values.
// Once set, it remains immutable.
// The Meet and Join operations return a new ConstLattice if the value changes.
type ConstLattice interface {
	Lattice
	// An assurance by the implementation that the value is constant
	// and will not change during the meet, join or other operations
	IsConstLattice() bool
}

type FactChanged uint8

//go:generate stringer -type=FactChanged
const (
	NoChange            FactChanged = 0
	Changed             FactChanged = 1
	OnlyInChanged       FactChanged = 2
	OnlyOutChanged      FactChanged = 3
	InOutChanged        FactChanged = 4
	OnlyTrueOutChanged  FactChanged = 5
	OnlyFalseOutChanged FactChanged = 6
)

// Join makes the value more precise (but possibly unsound)
func Join(l1, l2 Lattice) (Lattice, bool) {
	if l1 == nil {
		return l1, false
	}
	if l2 == nil {
		return l2, true
	}
	return l1.Join(l2)
}

// Meet makes the value more approximate (but possibly imprecise)
func Meet(l1, l2 Lattice) (Lattice, bool) {
	if l2 == nil {
		return l1, false
	}
	if l1 == nil {
		return l2, true
	}
	return l1.Meet(l2)
}

func Widen(l1, l2 Lattice) (Lattice, bool) {
	if l2 == nil {
		return l1, false
	}
	if l1 == nil {
		return l2, true
	}
	return l1.Widen(l2)
}

func ConstMeet(l1, l2 ConstLattice) (ConstLattice, bool) {
	lat, change := l1.Meet(l2)
	if change {
		errs.Assert(l1 != lat, "Constant lattice should not change")
	}
	return lat.(ConstLattice), change
}

func ConstJoin(l1, l2 ConstLattice) (ConstLattice, bool) {
	lat, change := l1.Join(l2)
	if change {
		errs.Assert(l1 != lat, "Constant lattice should not change")
	}
	return lat.(ConstLattice), change
}

func ConstWiden(l1, l2 ConstLattice) (ConstLattice, bool) {
	lat, change := l1.Widen(l2)
	if change {
		errs.Assert(l1 != lat, "Constant lattice should not change")
	}
	return lat.(ConstLattice), change
}

func WeakerThan(l1, l2 Lattice) bool {
	if l2 == nil {
		return true
	}
	if l1 == nil {
		return false
	}
	return l1.WeakerThan(l2)
}

func Equals(l1, l2 Lattice) bool {
	if IsTop(l1) && IsTop(l2) || IsBot(l1) && IsBot(l2) {
		return true
	}
	return l1.Equals(l2)
}

func IsTop(l Lattice) bool {
	if l == nil {
		return true
	}
	return l.IsTop()
}

func IsBot(l Lattice) bool {
	if l == nil {
		return false
	}
	return l.IsBot()
}

func Stringify(l Lattice) string {
	if l == nil {
		return "nil"
	}
	return l.String()
}
