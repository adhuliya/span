package lattice

import "github.com/adhuliya/span/internal/util/errs"

type TopBotLT struct {
	top bool // Most precise value
	bot bool // Most approximate value
}

func (l *TopBotLT) String() string {
	if l.top && l.bot {
		return "TopAndBot"
	}
	if l.top {
		return "Top"
	}
	if l.bot {
		return "Bot"
	}
	return "NotTopNotBot"
}

func NewTopBotLT(top, bot bool) TopBotLT {
	return TopBotLT{
		top: top,
		bot: bot,
	}
}

var TopBotLatticeTop TopBotLT = NewTopBotLT(true, false)
var TopBotLatticeBot TopBotLT = NewTopBotLT(false, true)

func (l *TopBotLT) IsConstLattice() bool {
	return true
}

func (l *TopBotLT) IsTop() bool {
	return l.top
}

func (l *TopBotLT) IsBot() bool {
	return l.bot
}

func (l *TopBotLT) Equals(other Lattice) bool {
	if other == nil {
		return false
	}
	return l.top == other.IsTop() && l.bot == other.IsBot()
}

func (l *TopBotLT) Join(other Lattice) (Lattice, bool) {
	if other == nil || l.top {
		return l, false
	}

	if other.IsTop() {
		return other, true
	}
	return l, false
}

func (l *TopBotLT) ConstJoin(other ConstLattice) (ConstLattice, bool) {
	j, change := l.Join(other)
	if change {
		errs.Assert(l != j, "Constant lattice should not change")
	}
	return j.(ConstLattice), change
}

func (l *TopBotLT) Meet(other Lattice) (Lattice, bool) {
	if other == nil || l.bot {
		return l, false
	}

	if other.IsBot() {
		return other, true
	}
	return l, false
}

func (l *TopBotLT) Widen(other Lattice) (Lattice, bool) {
	if other == nil || l.bot {
		return l, false
	}
	return l, false
}

func (l *TopBotLT) ConstMeet(other ConstLattice) (ConstLattice, bool) {
	j, change := l.Meet(other)
	if change {
		errs.Assert(l != j, "Constant lattice should not change")
	}
	return j.(ConstLattice), change
}

func (l *TopBotLT) WeakerThan(other Lattice) bool {
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
