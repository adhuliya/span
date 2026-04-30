package lattice

import "fmt"

type Pair struct {
	factId FactId
	lats   [2]Lattice
}

func (l *Pair) String() string {
	return fmt.Sprintf("LatticePair(%s, %s)", String(l.lats[0]), String(l.lats[1]))
}

func NewPair(l1, l2 Lattice) Pair {
	pair := Pair{}
	pair.factId = FactId(0)
	pair.lats[0] = l1
	pair.lats[1] = l2
	return pair
}

func (l *Pair) SetLats(l1, l2 Lattice) {
	l.lats[0] = l1
	l.lats[1] = l2
}

func (l Pair) L1() Lattice {
	return l.lats[0]
}

func (l Pair) L2() Lattice {
	return l.lats[1]
}

func (l Pair) Lats(idx int) Lattice {
	if idx < 2 {
		return l.lats[idx]
	} else {
		panic("idx to the lattice pair must be less than 2")
	}
}

func (l Pair) IsTop() bool {
	return IsTop(l.lats[0]) && IsTop(l.lats[1])
}

func (l Pair) IsBot() bool {
	return IsBot(l.lats[0]) && IsBot(l.lats[1])
}

func (l *Pair) WeakerThan(other Lattice) bool {
	if oth := other.(*Pair); oth != nil {
		return WeakerThan(l.lats[0], oth.lats[0]) && WeakerThan(l.lats[1], oth.lats[1])
	}
	return false
}

func (l *Pair) Equals(other Lattice) bool {
	if oth := other.(*Pair); oth != nil {
		return Equals(l.lats[0], oth.lats[0]) && Equals(l.lats[1], oth.lats[1])
	}
	return false
}

func (l *Pair) Join(other Lattice) (Lattice, bool) {
	changed := false
	if oth := other.(*Pair); oth != nil {
		change1, change2 := false, false
		l.lats[0], change1 = Join(l.lats[0], oth.L1())
		l.lats[1], change2 = Join(l.lats[1], oth.L2())
		changed = change1 || change2
	}
	if changed {
		l.incVersion()
	}
	return l, changed
}

func (l *Pair) Meet(other Lattice) (Lattice, bool) {
	changed := false
	if oth := other.(*Pair); oth != nil {
		change1, change2 := false, false
		l.lats[0], change1 = Meet(l.lats[0], oth.L1())
		l.lats[1], change2 = Meet(l.lats[1], oth.L2())
		changed = change1 || change2
	}
	if changed {
		l.incVersion()
	}
	return l, changed
}

func (l *Pair) Widen(other Lattice) (Lattice, bool) {
	changed := false
	if oth := other.(*Pair); oth != nil {
		change1, change2 := false, false
		l.lats[0], change1 = Widen(l.lats[0], oth.L1())
		l.lats[1], change2 = Widen(l.lats[1], oth.L2())
		changed = change1 || change2
	}
	if changed {
		l.incVersion()
	}
	return l, changed
}

func (l *Pair) FactId() FactId {
	return l.factId
}

func (l *Pair) incVersion() FactId {
	l.factId = l.factId.IncVersion()
	return l.factId
}
