package lattice

import "fmt"

type Pair struct {
	lats [2]Lattice
}

func (l *Pair) String() string {
	return fmt.Sprintf("LatticePair(%s, %s)", Stringify(l.lats[0]), Stringify(l.lats[1]))
}

func NewPair(l1, l2 Lattice) Pair {
	pair := Pair{}
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
	return l.lats[0].IsTop() && l.lats[1].IsTop()
}

func (l Pair) IsBot() bool {
	return l.lats[0].IsBot() && l.lats[1].IsBot()
}

func (l *Pair) Equals(other Lattice) bool {
	if oth := other.(*Pair); oth != nil {
		return l.lats[0].Equals(oth.lats[0]) && l.lats[1].Equals(oth.lats[1])
	}
	return false
}

func (l *Pair) Join(other Lattice) (Lattice, bool) {
	if oth := other.(*Pair); oth != nil {
		change1, change2 := false, false
		l.lats[0], change1 = l.lats[0].Join(oth.L1())
		l.lats[1], change2 = l.lats[1].Join(oth.L2())
		return l, change1 || change2
	}
	return l, false
}

func (l *Pair) Meet(other Lattice) (Lattice, bool) {
	if oth := other.(*Pair); oth != nil {
		change1, change2 := false, false
		l.lats[0], change1 = l.lats[0].Meet(oth.L1())
		l.lats[1], change2 = l.lats[1].Meet(oth.L2())
		return l, change1 || change2
	}
	return l, false
}

func (l *Pair) WeakerThan(other Lattice) bool {
	if oth := other.(*Pair); oth != nil {
		return l.lats[0].WeakerThan(oth.lats[0]) && l.lats[1].WeakerThan(oth.lats[1])
	}
	return false
}

func (l *Pair) Widen(other Lattice) (Lattice, bool) {
	if oth := other.(*Pair); oth != nil {
		change1, change2 := false, false
		l.lats[0], change1 = l.lats[0].Widen(oth.L1())
		l.lats[1], change2 = l.lats[1].Widen(oth.L2())
		return l, change1 || change2
	}
	return l, false
}
