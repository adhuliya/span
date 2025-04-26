package lattice

import "fmt"

type Pair struct {
	l1 Lattice
	l2 Lattice
}

func (l *Pair) String() string {
	return fmt.Sprintf("LatticePair(%s, %s)", Stringify(l.l1), Stringify(l.l2))
}

func NewPair(in, out Lattice) Pair {
	return Pair{
		l1: in,
		l2: out,
	}
}

func (l Pair) L1() Lattice {
	return l.l1
}

func (l Pair) L2() Lattice {
	return l.l2
}

func (l Pair) IsTop() bool {
	return l.l1.IsTop() && l.l2.IsTop()
}

func (l Pair) IsBot() bool {
	return l.l1.IsBot() && l.l2.IsBot()
}

func (l *Pair) Equals(other Lattice) bool {
	if oth := other.(*Pair); oth != nil {
		return l.l1.Equals(oth.l1) && l.l2.Equals(oth.l2)
	}
	return false
}

func (l *Pair) Join(other Lattice) (Lattice, bool) {
	if oth := other.(*Pair); oth != nil {
		change1, change2 := false, false
		l.l1, change1 = l.l1.Join(oth.L1())
		l.l2, change2 = l.l2.Join(oth.L2())
		return l, change1 || change2
	}
	return l, false
}

func (l *Pair) Meet(other Lattice) (Lattice, bool) {
	if oth := other.(*Pair); oth != nil {
		change1, change2 := false, false
		l.l1, change1 = l.l1.Meet(oth.L1())
		l.l2, change2 = l.l2.Meet(oth.L2())
		return l, change1 || change2
	}
	return l, false
}

func (l *Pair) WeakerThan(other Lattice) bool {
	if oth := other.(*Pair); oth != nil {
		return l.l1.WeakerThan(oth.l1) && l.l2.WeakerThan(oth.l2)
	}
	return false
}
