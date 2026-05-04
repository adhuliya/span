package clients

// (Strong) Live Variables Analysis Client

import (
	"fmt"

	"github.com/adhuliya/span/pkg/analysis"
	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

// (Strong) Live Variables lattice type
// The variables marked live at the program point are in gen,
// and the variables marked dead at a program point are in kill.
type LiveVarsLT struct {
	lattice.ScopedLatticeBase
	gen    spir.EidSet
	kill   spir.EidSet
	islive bool
}

func NewLiveVarsLT(parent *LiveVarsLT, factId lattice.FactId, maxEntityCount int) *LiveVarsLT {
	parentFactId := lattice.NIL_FACT_ID
	if parent != nil {
		parentFactId = parent.ParentFactId()
	}

	lvt := &LiveVarsLT{
		islive: false,
	}

	lvt.SetFactId(factId)
	lvt.SetParent(parent)
	lvt.SetParentFactId(parentFactId)
	lvt.SetMaxEntityCount(maxEntityCount)
	return lvt
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

	if lvfs.Parent() != nil {
		return lvfs.Parent().(*LiveVarsLT).IsLive(id)
	}
	return lvfs.islive // unknown (over-approximate) FIXME: panic here?
}

// Gen marks the given variable as live at this program point if not already present.
func (lvfs *LiveVarsLT) Gen(id spir.EntityId) bool {
	if id != spir.NIL_ID {
		return lvfs.gen.Add(id)
	}
	return false
}

func (lvfs *LiveVarsLT) Gen3(id1, id2, id3 spir.EntityId) bool {
	changed := lvfs.Gen(id1)
	changed = lvfs.Gen(id2) || changed
	changed = lvfs.Gen(id3) || changed
	return changed
}

// Kill marks the given variable as dead at this program point if not already present.
func (lvfs *LiveVarsLT) Kill(id spir.EntityId) bool {
	if id != spir.NIL_ID {
		return lvfs.kill.Add(id)
	}
	return false
}

func (lvfs *LiveVarsLT) ResetGenKill() bool {
	changed := lvfs.gen.Clear()
	changed = lvfs.kill.Clear() || changed
	return changed
}

// Implement the lattice.Lattice interface for LiveVarsLT.

// IsTop returns true if this is the top element of the lattice.
// In LiveVars analysis, Top typically means no variables are live.
func (lvfs *LiveVarsLT) IsTop() bool {
	// Convention: islive==false, gen is empty, kill is empty, parent==nil
	return !lvfs.islive && lvfs.gen.IsEmpty() && lvfs.kill.IsEmpty() && lvfs.Parent() == nil
}

// IsBot returns true if this is the bottom element of the lattice.
// In LiveVars analysis, Bot typically means all variables are live.
func (lvfs *LiveVarsLT) IsBot() bool {
	// Convention: islive==true, gen is empty, kill is empty, parent==nil
	return lvfs.islive && lvfs.gen.IsEmpty() && lvfs.kill.IsEmpty() && lvfs.Parent() == nil
}

// WeakerThan returns true if lvfs is less precise (more approximate/greater) than other.
// For sets: A is weaker than B if A contains all live vars in B (A is super set of B).
func (lvfs *LiveVarsLT) WeakerThan(other lattice.Lattice) bool {
	otherLV, ok := other.(*LiveVarsLT)
	if !ok {
		return false
	}

	if (lvfs.Parent() == nil && otherLV.Parent() == nil) || (lvfs.Parent() == otherLV.Parent()) {
		return lvfs.gen.IsSubsetEq(otherLV.gen) && lvfs.kill.IsSubsetEq(otherLV.kill)
	}

	// LiveVars is a powerset lattice, so superset is weaker
	lvSet := spir.NewEidSet(false, false)
	lvfs.LiveSet(lvSet)
	otherSet := spir.NewEidSet(false, false)
	otherLV.LiveSet(otherSet)
	return otherSet.IsSubsetEq(*lvSet)
}

// Meet returns the meet (greatest lower bound) of lvfs and other.
// In LiveVars, meet is set union of the live variables in lvfs and other.
// Both the lattices should be flat (that is no parents), or have the same parent.
func (lvfs *LiveVarsLT) Meet(other lattice.Lattice) (lattice.Lattice, bool) {
	otherLV, ok := other.(*LiveVarsLT)
	if !ok {
		return lvfs, false
	}

	if lvfs.Parent() != otherLV.Parent() {
		panic(fmt.Sprintf("LiveVarsLT.Meet: parent is not the same for %s and %s",
			lattice.String(lvfs), lattice.String(otherLV)))
	}

	genChanged := lvfs.gen.UnionWith(otherLV.gen)
	killChanged := lvfs.kill.IntersectionWith(otherLV.kill)
	changed := genChanged || killChanged
	lvfs.SetFactId(lvfs.FactId().CondIncVersion(changed))
	return lvfs, changed
}

// Join returns the join (least upper bound) of lvfs and other.
// In LiveVars, join is set intersection.
func (lvfs *LiveVarsLT) Join(other lattice.Lattice) (lattice.Lattice, bool) {
	otherLV, ok := other.(*LiveVarsLT)
	if !ok {
		return lvfs, false
	}

	if lvfs.Parent() != otherLV.Parent() {
		panic(fmt.Sprintf("LiveVarsLT.Meet: parent is not the same for %s and %s",
			lattice.String(lvfs), lattice.String(otherLV)))
	}

	genChanged := lvfs.gen.IntersectionWith(otherLV.gen)
	killChanged := lvfs.kill.UnionWith(otherLV.kill)
	changed := genChanged || killChanged
	lvfs.SetFactId(lvfs.FactId().CondIncVersion(changed))
	return lvfs, changed
}

// Widen is just Meet for finite LiveVars lattice (no infinite ascending chains).
func (lvfs *LiveVarsLT) Widen(other lattice.Lattice) (lattice.Lattice, bool) {
	return lattice.Meet(lvfs, other)
}

// Equals returns true if lvfs and other are the same lattice element.
func (lvfs *LiveVarsLT) Equals(other lattice.Lattice) bool {
	otherLV, ok := other.(*LiveVarsLT)
	if !ok {
		panic(fmt.Sprintf("LiveVarsLT.Equals: other is not a LiveVarsLT: %T", other))
	}
	return lvfs.Parent() == otherLV.Parent() && lvfs.gen.Equals(otherLV.gen) && lvfs.kill.Equals(otherLV.kill)
}

// String returns a string representation of the lattice element.
func (lvfs *LiveVarsLT) String() string {
	lvSet := spir.NewEidSet(false, false)
	lvfs.LiveSet(lvSet)
	return fmt.Sprintf("LiveVarsLT{%s}", lvSet.String())
}

// LiveSet returns the set of variables live at this program point, as a spir.EidSet (accumulating from parents).
func (lvfs *LiveVarsLT) LiveSet(lvSet *spir.EidSet) *spir.EidSet {
	if lvfs.Parent() != nil {
		lvfs.Parent().(*LiveVarsLT).LiveSet(lvSet)
	}
	lvSet.SubtractWith(lvfs.kill)
	lvSet.UnionWith(lvfs.gen)
	return lvSet
}

// Flatten removes all the parents and brings all the facts into the current object.
// FIXME
func (lvfs *LiveVarsLT) Flatten(self bool) (lattice.Lattice, bool) {
	if lvfs.Parent() == nil {
		return lvfs, false
	}
	lvSet := spir.NewEidSet(false, false)
	lvfs.LiveSet(lvSet) // Get all the live variables at this program point
	if self {
		genChanged := !lvfs.gen.Equals(*lvSet)
		lvfs.gen = *lvSet
		killChanged := lvfs.kill.Clear()
		changed := genChanged || killChanged
		lvfs.SetFactId(lvfs.FactId().CondIncVersion(changed))
		lvfs.SetParent(nil)
		return lvfs, changed
	}
	newLvfs := NewLiveVarsLT(lvfs.Parent().(*LiveVarsLT), lvfs.FactId().ZeroVersion(), lvfs.MaxEntityCount())
	newLvfs.gen = *lvSet
	newLvfs.islive = lvfs.islive
	return newLvfs, true
}

func (lvfs *LiveVarsLT) SetActiveEids(eids *spir.EidSet) {
	lvfs.SetMaxEntityCount(eids.Len())
}

func (lvfs *LiveVarsLT) MaxEntityCount() int {
	if lvfs.Parent() != nil {
		return lvfs.Parent().(*LiveVarsLT).MaxEntityCount()
	}
	return lvfs.MaxEntityCount()
}

// (Strong) Live Variables analysis
type LiveVarsAn struct {
	analysis.AnalysisClientBase
}

func (c *LiveVarsAn) Name() string {
	return "(Strong) Live Variables Analysis"
}

func (c *LiveVarsAn) VisitingOrder() spir.GraphVisitingOrder {
	return spir.PostOrder // For backward flow analysis.
}

func (c *LiveVarsAn) BoundaryFact(graph spir.Graph, ctx *spir.Context) lattice.Pair {
	// Generate the boundary information for the given graph.
	factId := lattice.NIL_FACT_ID.WithAnalysisId(c.AnalysisId()).
		WithUBEntityId(ctx.CurrentScopeEid())
	var exitFact *LiveVarsLT = nil
	// For any function apart from main, the exit fact contains all the globals.
	if !ctx.IsCurrFuncMain() {
		globals := ctx.TU().GlobalVars()
		exitFact = NewLiveVarsLT(nil /*parent*/, factId.WithFactPoint(lattice.FactIdUB_Point_OUT), globals.Len())
		exitFact.gen = globals
		exitFact.islive = false
	}
	return lattice.NewPair(nil, exitFact, factId.WithFactPoint(lattice.FactIdUB_Point_INOUT))
}

func (c *LiveVarsAn) NewNonNilTopLattice(factId lattice.FactId) lattice.Lattice {
	return NewLiveVarsLT(nil, factId, 0)
}

func (c *LiveVarsAn) AnalyzeInsn(insn spir.Insn, inOut lattice.Pair, ctx *spir.Context) (lattice.Pair, lattice.FactChanged) {
	factChange := lattice.NoChange
	changed := false
	l1 := GetL1(inOut, false)

	// For each instruction kind:
	ik := insn.InsnKind()
	switch ik {
	case spir.K_IK_IUSE, spir.K_IK_IUSE_KILL:
		// Statement with one to three operands that must be marked live.
		eid1, eid2, eid3 := insn.GetOperands()
		l1 = GetL1(inOut, true)
		changed = l1.Gen3(eid1, eid2, eid3)
		if ik == spir.K_IK_IUSE_KILL {
			// Hard kill all the variables at this program point.
			l1.kill.MakeUniversal()
		}
		if changed {
			factChange = lattice.InChanged
		}
		inOut.SetLats(l1, inOut.L2())
	case spir.K_IK_IRETURN, spir.K_IK_ICOND:
		// Statements with single operand that must be marked live.
		eid1, _, _ := insn.GetOperands()
		if !eid1.Kind().IsLiteral() {
			changed := l1.Gen(eid1)
			if changed {
				factChange = lattice.InChanged
			}
			inOut.SetLats(l1, inOut.L2())
		}
	case spir.K_IK_IASGN_RHS_OP, spir.K_IK_IASGN_SIMPLE:
		// LHS has a simple variable use, and rhs has one or two operands.
		lhsVar := insn.LhsX().GetOpr1()
		lhsIsLive := IsLiveAtOut(inOut, lhsVar)
		changed = l1.Kill(lhsVar)
		if lhsIsLive {
			eid1, eid2 := insn.RhsX().GetOperands()
			changed = l1.Gen3(eid1, eid2, spir.NIL_ID) || changed
		}
		if changed {
			factChange = lattice.InChanged
		}
		inOut.SetLats(l1, inOut.L2())
		// TODO: Handle all remining cases.
	} // switch ik ends here

	if changed {
		factChange = lattice.InChanged
	}
	inOut.SetLats(l1, inOut.L2())
	return inOut, factChange
}

func GetL1(inOut lattice.Pair, reset bool) *LiveVarsLT {
	if inOut.L1() != nil {
		l1 := inOut.L1().(*LiveVarsLT)
		if reset {
			l1.ResetGenKill()
		}
		return l1
	}
	// Otherwise, create a new LiveVarsLT and return it.
	return NewLiveVarsLT(inOut.L2().(*LiveVarsLT), inOut.FactId().WithFactPoint(lattice.FactIdUB_Point_IN), 0)
}

func IsLiveAtOut(inOut lattice.Pair, eid spir.EntityId) bool {
	if inOut.L2() == nil {
		return false
	}
	return inOut.L2().(*LiveVarsLT).IsLive(eid)
}
