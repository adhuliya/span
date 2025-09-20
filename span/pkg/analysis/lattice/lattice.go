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
	NoChange    FactChanged = 0
	NopNoChange FactChanged = 1 // No change and Insn is treated as as no-op

	Changed             FactChanged = 2 // changed without any specific change information
	OnlyInChanged       FactChanged = 3 // changed only in the IN fact
	OnlyOutChanged      FactChanged = 4 // changed only in the OUT fact
	InOutChanged        FactChanged = 5 // changed both IN and OUT facts
	OnlyTrueOutChanged  FactChanged = 6 // changed only in the TRUE OUT fact
	OnlyFalseOutChanged FactChanged = 7 // changed only in the FALSE OUT fact

	// The special Nop__Changed values tell SPAN not only that the information changed or not;
	// but also if the analysis is treating the current insn like a No-op instruction.
	// If the analysis returns these values, SPAN can optimize the analysis
	// by simply propagating the values across the instruction in the next visit.
	NopInChanged    FactChanged = 9
	NopOutChanged   FactChanged = 10
	NopInOutChanged FactChanged = 11

	// Analyses may not provide any change information (at the cost of efficiency)
	NoChangeInfo FactChanged = 12
)

func (fc FactChanged) HasNop() bool {
	return fc == NopNoChange || fc == NopInChanged || fc == NopOutChanged || fc == NopInOutChanged
}

func (fc FactChanged) HasChange() bool {
	return (fc >= Changed && fc <= NopInOutChanged)
}

func (fc FactChanged) HasChangedIn() bool {
	return fc == OnlyInChanged || fc == InOutChanged
}

func (fc FactChanged) HasChangedOut() bool {
	return fc == OnlyInChanged || fc == InOutChanged
}

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
