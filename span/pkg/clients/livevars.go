package clients

// (Strong) Live Variables Analysis Client

import (
	"fmt"

	"github.com/adhuliya/span/pkg/analysis"
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

// (Strong) Live Variables analysis
type LiveVarsAn struct {
	analysis.AnalysisClient
}

// (Strong) Live Variables lattice type
// The variables marked live at the program point are in gen,
// and the variables marked dead at a program point are in kill.
type LiveVarsLT struct {
	gen    lattice.EidSet
	kill   lattice.EidSet
	parent *LiveVarsLT
	islive bool
}

func NewLiveVarsLT(parent *LiveVarsLT) *LiveVarsLT {
	return &LiveVarsLT{
		parent: parent,
		islive: parent != nil, // false, if parent is nil
	}
}

func (lvfs *LiveVarsLT) Parent() *LiveVarsLT {
	return lvfs.parent
}

func (lvfs *LiveVarsLT) DefaultLiveness() bool {
	return lvfs.islive
}

func (lvfs *LiveVarsLT) SetDefaultLiveness(islive bool) {
	lvfs.islive = islive
}

func (lvfs *LiveVarsLT) IsLive(id spir.EntityId) bool {
	isGen := lvfs.gen.Contains(id)
	if isGen {
		return true // definitely live
	}

	isDead := lvfs.kill.Contains(id)
	if isDead {
		return false // definitely not live
	}

	if lvfs.parent != nil {
		return lvfs.parent.IsLive(id)
	}
	return lvfs.islive // unknown (over-approximate) FIXME: panic here?
}

// Gen marks the given variable as live at this program point if not already present.
func (lvfs *LiveVarsLT) Gen(id spir.EntityId) {
	lvfs.gen.Add(id)
}

// Kill marks the given variable as dead at this program point if not already present.
func (lvfs *LiveVarsLT) Kill(id spir.EntityId) {
	lvfs.kill.Add(id)
}

// Implement the lattice.Lattice interface for LiveVarsLT.

// IsTop returns true if this is the top element of the lattice.
// In LiveVars analysis, Top typically means no variables are live.
func (lvfs *LiveVarsLT) IsTop() bool {
	// Convention: islive==false, gen is empty, kill is empty, parent==nil
	return !lvfs.islive && lvfs.gen.IsEmpty() && lvfs.kill.IsEmpty() && lvfs.parent == nil
}

// IsBot returns true if this is the bottom element of the lattice.
// In LiveVars analysis, Bot typically means all variables are live.
func (lvfs *LiveVarsLT) IsBot() bool {
	// Convention: islive==true, gen is empty, kill is empty, parent==nil
	return lvfs.islive && lvfs.gen.IsEmpty() && lvfs.kill.IsEmpty() && lvfs.parent == nil
}

// WeakerThan returns true if lvfs is less precise (more approximate/greater) than other.
// For sets: A is weaker than B if A contains all live vars in B (A is super set of B).
func (lvfs *LiveVarsLT) WeakerThan(other lattice.Lattice) bool {
	otherLV, ok := other.(*LiveVarsLT)
	if !ok {
		return false
	}

	if lvfs.parent == nil && otherLV.parent == nil {
		return lvfs.gen.IsSubsetEq(otherLV.gen) && lvfs.kill.IsSubsetEq(otherLV.kill)
	}

	// LiveVars is a powerset lattice, so superset is weaker
	lvSet := lattice.NewEidSet()
	lvfs.LiveSet(lvSet)
	otherSet := lattice.NewEidSet()
	otherLV.LiveSet(otherSet)
	return otherSet.IsSubsetEq(*lvSet)
}

// Meet returns the meet (greatest lower bound) of lvfs and other.
// In LiveVars, meet is set union of the live variables in lvfs and other.
// Both the lattices should flat (that is no parents).
func (lvfs *LiveVarsLT) Meet(other lattice.Lattice) (lattice.Lattice, bool) {
	otherLV, ok := other.(*LiveVarsLT)
	if !ok {
		return lvfs, false
	}

	if lvfs.parent != nil || otherLV.parent != nil {
		panic(fmt.Sprintf("LiveVarsLT.Meet: parent is not nil for %s or %s",
			lvfs.String(), otherLV.String()))
	}

	lvSet, otherSet := lattice.NewEidSet(), lattice.NewEidSet()
	joinedSet, _ := lvfs.LiveSet(lvSet).Union(*otherLV.LiveSet(otherSet))
	newLV := NewLiveVarsLT(nil)
	for _, id := range joinedSet.Values() {
		newLV.Gen(id)
	}
	changed := !lvfs.Equals(newLV)
	return newLV, changed
}

// Join returns the join (least upper bound) of lvfs and other.
// In LiveVars, join is set union.
func (lvfs *LiveVarsLT) Join(other lattice.Lattice) (lattice.Lattice, bool) {
	otherLV, ok := other.(*LiveVarsLT)
	if !ok {
		return lvfs, false
	}
	// Compute intersection of live variable sets
	lvSet, otherSet := lattice.NewEidSet(), lattice.NewEidSet()
	meetedSet, _ := lvfs.LiveSet(lvSet).Intersection(*otherLV.LiveSet(otherSet))
	// Make a new LiveVarsLT with this info (for simplicity, ignore parent/islive here)
	newLV := NewLiveVarsLT(nil)
	for _, id := range meetedSet.Values() {
		newLV.Gen(id)
	}
	changed := !lvfs.Equals(newLV)
	return newLV, changed
}

// Widen is just Meet for finite LiveVars lattice (no infinite ascending chains).
func (lvfs *LiveVarsLT) Widen(other lattice.Lattice) (lattice.Lattice, bool) {
	return lvfs.Meet(other)
}

// Equals returns true if lvfs and other are the same lattice element.
func (lvfs *LiveVarsLT) Equals(other lattice.Lattice) bool {
	otherLV, ok := other.(*LiveVarsLT)
	if !ok {
		panic(fmt.Sprintf("LiveVarsLT.Equals: other is not a LiveVarsLT: %T", other))
	}
	eqParents := true
	if lvfs.parent != nil {
		eqParents = lvfs.parent.Equals(otherLV.parent)
	}
	return eqParents && lvfs.gen.Equals(otherLV.gen) && lvfs.kill.Equals(otherLV.kill)
}

// String returns a string representation of the lattice element.
func (lvfs *LiveVarsLT) String() string {
	lvSet := lattice.NewEidSet()
	lvfs.LiveSet(lvSet)
	return fmt.Sprintf("LiveVarsLT{%s}", lvSet.String())
}

// LiveSet returns the set of variables live at this program point, as a lattice.EidSet (accumulating from parents).
func (lvfs *LiveVarsLT) LiveSet(lvSet *lattice.EidSet) *lattice.EidSet {
	if lvfs.parent != nil {
		lvfs.parent.LiveSet(lvSet)
	}
	lvSet.SubtractWith(lvfs.kill)
	lvSet.UnionWith(lvfs.gen)
	return lvSet
}

// Flatten removes all the parents and brings all the facts into the current object.
// FIXME
func (lvfs *LiveVarsLT) Flatten(self bool) (lattice.Lattice, bool) {
	if lvfs.parent == nil {
		return lvfs, false
	}
	lvSet := lattice.NewEidSet()
	lvfs.LiveSet(lvSet) // Get all the live variables at this program point
	if self {
		lvfs.gen = *lvSet
		lvfs.kill.Clear()
		lvfs.parent = nil
		return lvfs, true
	}
	newLvfs := NewLiveVarsLT(lvfs.parent)
	newLvfs.gen = *lvSet
	newLvfs.kill.Clear()
	newLvfs.islive = lvfs.islive
	return newLvfs, true
}

func (c *LiveVarsAn) BoundaryFact(graph spir.Graph, context *spir.Context) lattice.Pair {
	// Generate the boundary information for the given graph.
	return lattice.NewPair(&lattice.TopBotLatticeTop, &lattice.TopBotLatticeTop)
}
