package lattice

// An interface for a chained lattice structure with a parent
type ChainedLattice interface {
	Lattice
	Parent() Lattice
	// Flatten the lattice by collapsing data from all the parents.
	// If self is true, the lattice is modified in place, otherwise a new lattice is returned.
	// bool indicates if the lattice changed during the flatten operation.
	Flatten(self bool) (Lattice, bool)
}

// The lattice with FactId, which increments (version part only) per update.
type FactIdLattice interface {
	Lattice
	FactId() FactId
}
