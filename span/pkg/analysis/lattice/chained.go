package lattice

// An interface for a chained lattice structure with a parent
type ChainedLattice interface {
	Lattice
	Parent() Lattice
}
