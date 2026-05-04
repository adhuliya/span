package lattice

type FactChanged uint8

//go:generate stringer -type=FactChanged
const (
	NoChange        FactChanged = 0
	Changed         FactChanged = 1 // changes without any specific change information
	InChanged       FactChanged = 2 // changes only in the IN fact
	OutChanged      FactChanged = 3 // changes only in the OUT fact
	InOutChanged    FactChanged = 4 // changes both IN and OUT facts
	TrueOutChanged  FactChanged = 5 // changes only in the TRUE OUT fact
	FalseOutChanged FactChanged = 6 // changes only in the FALSE OUT fact

	// The special Nop__Changed values tell SPAN not only that the information changed or not;
	// but also if the analysis is treating the current insn like a No-op instruction.
	// If the analysis returns these values, SPAN can optimize the analysis
	// by simply propagating the values across the instruction in the next visit.
	NopNoChange     FactChanged = 7 // No change and Insn is treated as as no-op
	NopInChanged    FactChanged = 8
	NopOutChanged   FactChanged = 9
	NopInOutChanged FactChanged = 10

	// Analyses may not provide any change information (at the cost of efficiency)
	NoChangeInfo FactChanged = 11

	// The transfer function is not implemented for this analysis
	NotImplemented FactChanged = 12
)

func (fc FactChanged) HasNop() bool {
	return fc == NopNoChange || fc == NopInChanged || fc == NopOutChanged || fc == NopInOutChanged
}

func (fc FactChanged) HasChange() bool {
	return (fc >= Changed && fc <= NopInOutChanged)
}

func (fc FactChanged) HasChangedIn() bool {
	if fc.HasChange() {
		return fc == InChanged || fc == InOutChanged || fc == NopInChanged || fc == NopInOutChanged
	}
	return false
}

func (fc FactChanged) HasChangedOut() bool {
	if fc.HasChange() {
		return fc == OutChanged || fc == InOutChanged || fc == TrueOutChanged || fc == FalseOutChanged || fc == NopOutChanged || fc == NopInOutChanged
	}
	return false
}

func GetInOutChanged(inChanged, outChanged bool) FactChanged {
	if inChanged && outChanged {
		return InOutChanged
	} else if inChanged {
		return InChanged
	} else if outChanged {
		return OutChanged
	}
	return NoChange
}

func (fc FactChanged) String() string {
	switch fc {
	case NoChange:
		return "NoChange"
	case Changed:
		return "Changed"
	case InChanged:
		return "InChanged"
	case OutChanged:
		return "OutChanged"
	case InOutChanged:
		return "InOutChanged"
	case TrueOutChanged:
		return "TrueOutChanged"
	case FalseOutChanged:
		return "FalseOutChanged"
	case NopNoChange:
		return "NopNoChange"
	case NopInChanged:
		return "NopInChanged"
	case NopOutChanged:
		return "NopOutChanged"
	case NopInOutChanged:
		return "NopInOutChanged"
	case NoChangeInfo:
		return "NoChangeInfo"
	case NotImplemented:
		return "NotImplemented"
	}
	return "UnknownFactChange"
}
