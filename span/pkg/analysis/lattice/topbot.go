package lattice

import "github.com/adhuliya/span/internal/util"

type TopBotLattice struct {
	top bool // Most precise value
	bot bool // Most approximate value
}

func (l *TopBotLattice) String() string {
	if l.top && l.bot {
		return "TopAndBot"
	}
	if l.top {
		return "Top"
	}
	if l.bot {
		return "Bot"
	}
	return "Unknown"
}

func NewTopBotLattice(top, bot bool) TopBotLattice {
	return TopBotLattice{
		top: top,
		bot: bot,
	}
}

var TopBotLatticeTop TopBotLattice = NewTopBotLattice(true, false)
var TopBotLatticeBot TopBotLattice = NewTopBotLattice(false, true)

func (l *TopBotLattice) IsConstLattice() bool {
	return true
}

func (l *TopBotLattice) IsTop() bool {
	return l.top
}

func (l *TopBotLattice) IsBot() bool {
	return l.bot
}

func (l *TopBotLattice) Equals(other Lattice) bool {
	if other == nil {
		return false
	}
	return l.top == other.IsTop() && l.bot == other.IsBot()
}

func (l *TopBotLattice) Join(other Lattice) (Lattice, bool) {
	if other == nil || l.top {
		return l, false
	}

	if other.IsTop() {
		return other, true
	}
	return l, false
}

func (l *TopBotLattice) ConstJoin(other ConstLattice) (ConstLattice, bool) {
	j, change := l.Join(other)
	if change {
		util.Assert(l != j, "Constant lattice should not change")
	}
	return j.(ConstLattice), change
}

func (l *TopBotLattice) Meet(other Lattice) (Lattice, bool) {
	if other == nil || l.bot {
		return l, false
	}

	if other.IsBot() {
		return other, true
	}
	return l, false
}

func (l *TopBotLattice) ConstMeet(other ConstLattice) (ConstLattice, bool) {
	j, change := l.Meet(other)
	if change {
		util.Assert(l != j, "Constant lattice should not change")
	}
	return j.(ConstLattice), change
}

func (l *TopBotLattice) WeakerThan(other Lattice) bool {
	equal := l.Equals(other)
	if equal {
		return true
	}

	if l.top {
		return false
	}
	if l.bot {
		return true
	}
	return false
}
