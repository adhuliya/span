package lattice

import (
	"github.com/adhuliya/span/internal/util/errs"
	"github.com/adhuliya/span/pkg/spir"
)

// This file defines the following interfaces for Lattices
// 1. Lattice and ConstLattice interfaces.
// 2. LatticeWithFactId interface.
// 3. ChainedLattice interface.
// 4. GraphLattice interface. (any lattice used at IN/OUT of statements in graph)

// Lattice is the base interface for all lattices used in the SPAN program analysis engine.
// It defines the basic operations that any lattice must implement.
// Any operation that may change a lattice value must return a bool indicating if the value changed.
// The **nil** lattice value is treated as **Top** (most precise value).
type Lattice interface {
	// 1. Lattice top and bot values.
	IsTop() bool
	IsBot() bool

	// 2. Lattice ordering operations
	WeakerThan(other Lattice) bool
	Equals(other Lattice) bool // optional operation

	// 3. Lattice value operations.
	// Meet to get a more approximate value (unlike in Abstract Interpretation)
	// bool indicates if the value changed during the meet operation
	Meet(other Lattice) (Lattice, bool)
	// Join to get a more precise value (unlike in Abstract Interpretation)
	// bool indicates if the value changed during the join operation
	Join(other Lattice) (Lattice, bool)
	// Widening operator to allow termination of the analyses with infinite domain.
	// If the domain is finite, the widening is same as Meet().
	Widen(other Lattice) (Lattice, bool)

	// 4. Lattice' string representation.
	String() string
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

func WeakerThan(l1, l2 Lattice) bool {
	l1Top, l2Top := IsTop(l1), IsTop(l2)
	l1Bot, l2Bot := IsBot(l1), IsBot(l2)
	if l1Top || l2Top || l1Bot || l2Bot {
		if (l1Top && l2Top) || (l1Bot && l2Bot) {
			return true // Both are Top or Both are Bot
		}
		if l1Bot && l2Top {
			return true // Bot is weaker than Top
		}
		if l1Top && l2Bot {
			return false // Top is not weaker than Bot
		}
	}
	return l1.WeakerThan(l2)
}

func Equals(l1, l2 Lattice) bool {
	if (IsTop(l1) && IsTop(l2)) || (IsBot(l1) && IsBot(l2)) {
		return true
	}
	return l1.Equals(l2)
}

// Join makes the value more precise (but possibly unsound)
// nil lattice is treated as top (most precise value)
func Join(l1, l2 Lattice) (Lattice, bool) {
	if IsTop(l1) {
		return l1, false
	}
	if IsTop(l2) {
		return l2, true
	}
	return l1.Join(l2)
}

// Meet makes the value more approximate (but possibly imprecise)
// nil lattice is treated as top (most precise value)
func Meet(l1, l2 Lattice) (Lattice, bool) {
	if IsTop(l2) {
		return l1, false
	}
	if IsTop(l1) {
		return l2, true
	}
	return l1.Meet(l2)
}

func Widen(l1, l2 Lattice) (Lattice, bool) {
	if IsTop(l2) {
		return l1, false
	}
	if IsTop(l1) {
		return l2, true
	}
	return l1.Widen(l2)
}

func String(l Lattice) string {
	if l == nil {
		return "nil_Top"
	}
	return l.String()
}

// A ConstLattice is a place holder Lattice interface for constant values.
// Once set, it remains immutable.
// The Meet and Join operations return a new ConstLattice if the value changes.
type ConstLattice interface {
	Lattice
	// An assurance by the implementation that the value is constant
	// and will not change during the meet, join or other operations
	// It is recommended to use ConstMeet, ConstJoin, ConstWiden
	// instead of direct calls to Meet, Join, Widen.
	IsConstLattice() bool
}

func ConstMeet(l1, l2 ConstLattice) (ConstLattice, bool) {
	lat, change := Meet(l1, l2)
	if change && l1 != nil {
		errs.Assert(l1 != lat, "Constant lattice should not change")
	}
	return lat.(ConstLattice), change
}

func ConstJoin(l1, l2 ConstLattice) (ConstLattice, bool) {
	lat, change := Join(l1, l2)
	if change && l1 != nil {
		errs.Assert(l1 != lat, "Constant lattice should not change")
	}
	return lat.(ConstLattice), change
}

func ConstWiden(l1, l2 ConstLattice) (ConstLattice, bool) {
	lat, change := Widen(l1, l2)
	if change && l1 != nil {
		errs.Assert(l1 != lat, "Constant lattice should not change")
	}
	return lat.(ConstLattice), change
}

// A LatticeWithFactId is a lattice that has a fact id.
// The fact id is used to identify the fact in the data flow analysis,
// and to track the history of changes for the fact (versioning).
// The fact id should increment if the lattice is modified through the Join, Meet, Widen operations.
type LatticeWithFactId interface {
	Lattice
	// Get the fact id of the lattice.
	FactId() FactId
}

// An interface for a chained lattice structure with a parent
type ChainedLattice interface {
	LatticeWithFactId
	// Get the parent lattice.
	Parent() LatticeWithFactId
	// The fact id of the parent lattice this lattice is based on.
	// Since, fact id of the parent changes if it is modified, the parent's fact id
	// is used to check if the parent has been modified since the current fact was created.
	ParentFactId() FactId
	// Flatten the lattice by collapsing data from all the parents.
	// A flattened lattice has no parent.
	// If self is true, the lattice is modified in place, otherwise a new lattice is returned.
	// The boolean return value indicates if the lattice changed during the flatten operation.
	Flatten(self bool) (LatticeWithFactId, bool)
}

// ScopedLattice is a lattice that is specific to a scope (function, basic block, or CFG).
// It is used to track the data flow for the entities in the scope.
// The interface is used at call-sites where the data flow fact from the caller,
// is propagated to the callee. During the propagation, the fact can be modified
// by removing caller's variables and adding callee's variables to the lattice.
type ScopedLattice interface {
	ChainedLattice
	// This could be a function or a basic block or a specific scope (CFG).
	GetScopeEid() spir.EntityId
	SetScopeEid(scopeEid spir.EntityId) // FIXME: Remove this method. It may not be needed.
	// Set the active eids, e.g. local variables in the functions to the lattice.
	SetActiveEids(eids *spir.EidSet)
	// Get the maximum number of entities that can be tracked by the lattice.
	MaxEntityCount() int
}

// DefaultValueLattice is a lattice that has a default value.
// Structures implementing this interface can use the default value to optimize the lattice operations.
// For example, if an entity is not present in a map, the default value can be used.
// Generally, the default is a top (nil) or a bottom (some well-defined non-nil value) value.
type DefaultValueLattice interface {
	Lattice
	// A placeholder to indicate if the lattice has a default value.
	// The default value is only used internally by the lattice implementation.
	HasDefaultValue() bool
}
