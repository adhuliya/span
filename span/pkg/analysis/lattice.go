package analysis

// This file contains the lattice data structure used in the SPAN program analysis engine.

type Lattice interface {
	isTop() bool
	isBot() bool
	weakerThan(other Lattice) bool
	join(other Lattice) Lattice
	meet(other Lattice) Lattice
	equals(other Lattice) bool
}

func Meet(l1, l2 Lattice) Lattice {
	if l1 == nil {
		return l2
	}
	if l2 == nil {
		return l1
	}
	return l1.meet(l2)
}

func Join(l1, l2 Lattice) Lattice {
	if l1 == nil {
		return l2
	}
	if l2 == nil {
		return l1
	}
	return l1.join(l2)
}

func Equals(l1, l2 Lattice) bool {
	if l1 == nil && l2 == nil {
		return true
	}
	if l1 == nil || l2 == nil {
		return false
	}
	return l1.equals(l2)
}

func IsTop(l Lattice) bool {
	if l == nil {
		return true
	}
	return l.isTop()
}

func IsBot(l Lattice) bool {
	if l == nil {
		return false
	}
	return l.isBot()
}

type TopBotLattice struct {
	top bool // Most precise value
	bot bool // Most approximate value
}

func NewTopBotLattice(top, bot bool) TopBotLattice {
	return TopBotLattice{
		top: top,
		bot: bot,
	}
}

var TopBotLatticeTop TopBotLattice = NewTopBotLattice(true, false)
var TopBotLatticeBot TopBotLattice = NewTopBotLattice(false, true)

func (l *TopBotLattice) isTop() bool {
	return l.top
}

func (l *TopBotLattice) isBot() bool {
	return l.bot
}

func (l *TopBotLattice) equals(other Lattice) bool {
	if other == nil {
		return false
	}
	return l.top == other.isTop() && l.bot == other.isBot()
}

func (l *TopBotLattice) join(other Lattice) Lattice {
	if other == nil {
		return l
	}

	if l.top || other.isTop() {
		return &TopBotLattice{top: true}
	}
	return &TopBotLattice{bot: true}
}

func (l *TopBotLattice) meet(other Lattice) Lattice {
	if other == nil {
		return l
	}

	if l.bot || other.isBot() {
		return &TopBotLattice{bot: true}
	}
	return &TopBotLattice{top: true}
}

func (l *TopBotLattice) weakerThan(other Lattice) bool {
	equal := l.equals(other)
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

type LatticePair struct {
	l1 Lattice
	l2 Lattice
}

func NewLatticePair(in, out Lattice) *LatticePair {
	return &LatticePair{
		l1: in,
		l2: out,
	}
}

func (l *LatticePair) SetL1(in Lattice) {
	l.l1 = in
}

func (l *LatticePair) SetL2(out Lattice) {
	l.l2 = out
}

func (l *LatticePair) L1() Lattice {
	return l.l1
}

func (l *LatticePair) L2() Lattice {
	return l.l2
}

func (l *LatticePair) isTop() bool {
	return l.l1.isTop() && l.l2.isTop()
}

func (l *LatticePair) isBot() bool {
	return l.l1.isBot() && l.l2.isBot()
}

func (l *LatticePair) equals(other Lattice) bool {
	if oth := other.(*LatticePair); oth != nil {
		return l.l1.equals(oth.l1) && l.l2.equals(oth.l2)
	}
	return false
}

func (l *LatticePair) join(other Lattice) Lattice {
	if oth := other.(*LatticePair); oth != nil {
		return &LatticePair{l1: l.l1.join(oth.l1), l2: l.l2.join(oth.l2)}
	}
	return l
}

func (l *LatticePair) meet(other Lattice) Lattice {
	if oth := other.(*LatticePair); oth != nil {
		return &LatticePair{l1: l.l1.meet(oth.l1), l2: l.l2.meet(oth.l2)}
	}
	return l
}

func (l *LatticePair) weakerThan(other Lattice) bool {
	if oth := other.(*LatticePair); oth != nil {
		return l.l1.weakerThan(oth.l1) && l.l2.weakerThan(oth.l2)
	}
	return false
}
