package lattice

type KVLattice interface {
	ChainedLattice
	Get(uint64) ConstLattice
	Set(uint64, ConstLattice, bool) bool
}

type UInt64MapKVLattice struct {
	parent KVLattice
	kv     map[uint64]ConstLattice
}

func NewKVLatticeImpl(parent KVLattice) *UInt64MapKVLattice {
	return &UInt64MapKVLattice{
		parent: parent,
		kv:     make(map[uint64]ConstLattice),
	}
}

func (kv *UInt64MapKVLattice) Parent() Lattice {
	return kv.parent
}

func (kv *UInt64MapKVLattice) Get(key uint64) ConstLattice {
	if val, ok := kv.kv[key]; ok {
		return val
	}
	if kv.parent != nil {
		return kv.parent.Get(key)
	}
	return nil
}

func (kv *UInt64MapKVLattice) Set(key uint64, value ConstLattice, must bool) bool {
	oldValue := kv.Get(key)
	if must && !Equals(oldValue, value) {
		kv.kv[key] = value
		return true
	} else { /* may information */
		oldValue = nil
		if kv.parent != nil {
			oldValue = kv.parent.Get(key)
		}
		newValue, change := ConstMeet(oldValue, value)
		if change {
			kv.kv[key] = newValue
		}
		return change
	}
}
