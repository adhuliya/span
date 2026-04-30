package lattice

import (
	"fmt"
	"sort"
	"strings"

	"github.com/adhuliya/span/pkg/spir"
)

// KVLattice is a lattice that is specialized for spir.EntityId keys.
// It is used to track the data flow for the entities in the program.
// Entities not present in the map are assumed to be mapped to Top (most precise value).
type KVLattice interface {
	ScopedLattice
	// Get retrieves the ConstLattice associated with the given EntityId key.
	// bool indicates if the value was found in the lattice chain (true) or not (false).
	Get(spir.EntityId) (ConstLattice, bool)
	// Set sets the ConstLattice for the given EntityId key.
	// The boolean 'must' indicates if the value must be assigned (strong update)
	// or should be merged (weak update).
	// The boolean return value indicates if the value was changed (true) or not (false).
	Set(spir.EntityId, ConstLattice, bool) bool
}

// EntityIdMapKVLattice is a default implementation of KVLattice using a map[EntityId]ConstLattice.
type EntityIdMapKVLattice struct {
	factId         FactId
	parent         KVLattice
	parentFactId   FactId
	scopeEid       spir.EntityId
	maxEntityCount int
	kv             map[spir.EntityId]ConstLattice
}

// NewKVLatticeImpl creates a new KVLattice with the specified parent lattice.
func NewKVLatticeImpl(parent KVLattice, maxEntityCount int) *EntityIdMapKVLattice {
	if maxEntityCount <= 0 {
		panic("maxEntityCount must be greater than 0")
	}
	return &EntityIdMapKVLattice{
		parent:         parent,
		maxEntityCount: maxEntityCount,
		kv:             make(map[spir.EntityId]ConstLattice),
	}
}

// Parent returns the parent lattice.
func (kv *EntityIdMapKVLattice) Parent() LatticeWithFactId {
	return kv.parent
}

func (kv *EntityIdMapKVLattice) isFlat() bool {
	return kv.parent == nil
}

func (kv *EntityIdMapKVLattice) requireFlat(op string) {
	if !kv.isFlat() {
		panic(fmt.Sprintf("KVLattice.%s requires the current lattice to be flat", op))
	}
}

func (kv *EntityIdMapKVLattice) GetFactId() FactId {
	return kv.factId
}

func (kv *EntityIdMapKVLattice) ParentFactId() FactId {
	return kv.parentFactId
}

func (kv *EntityIdMapKVLattice) GetScopeEid() spir.EntityId {
	return kv.scopeEid
}

func (kv *EntityIdMapKVLattice) SetScopeEid(scopeEid spir.EntityId) {
	kv.scopeEid = scopeEid
}

func (kv *EntityIdMapKVLattice) SetActiveEids(eids *spir.EidSet) {
	//FIXME: Implement this.
}

func (kv *EntityIdMapKVLattice) MaxEntityCount() int {
	return kv.maxEntityCount
}

// Get retrieves the ConstLattice value associated with the key, or
// recursively queries the parent if not found.
func (kv *EntityIdMapKVLattice) Get(key spir.EntityId) (ConstLattice, bool) {
	if val, ok := kv.kv[key]; ok {
		return val, true
	}
	if kv.parent != nil {
		return kv.parent.Get(key)
	}
	return nil, false
}

// Set assigns or merges the value with the existing lattice for the key.
// If 'must' is true, set unconditionally if the value changed (strong update).
// Otherwise, merges with the parent's value (weak update).
func (kv *EntityIdMapKVLattice) Set(key spir.EntityId, value ConstLattice, must bool) bool {
	oldValue, ok := kv.Get(key)
	// A new entity, not present in the map.
	if !ok {
		if IsTop(value) {
			return false
		}
		kv.kv[key] = value // regardless of may/must, set the value to the new value.
		return true
	}

	// An existing entity, present in the map.
	if must { // Strong update.
		if Equals(oldValue, value) {
			return false
		}
		kv.kv[key] = value
		return true
	}

	// Weak update. Merge the existing value with the new value.
	newValue, change := ConstMeet(oldValue, value)
	if change {
		kv.kv[key] = newValue
	}
	return change
}

// Flatten the lattice by collapsing data from all the parents.
// If self is true, the lattice is modified in place, otherwise a new lattice is returned.
// bool indicates if the lattice changed during the flatten operation.
func (kv *EntityIdMapKVLattice) Flatten(self bool) (LatticeWithFactId, bool) {
	var changed bool

	var out *EntityIdMapKVLattice
	out = kv // Use the original object if self is true
	if !self {
		// Make a new object and copy the kv map, but use same parent
		out = &EntityIdMapKVLattice{
			parent: kv.parent,
			kv:     make(map[spir.EntityId]ConstLattice, len(kv.kv)),
		}
		for id, v := range kv.kv {
			out.kv[id] = v
		}
	}

	// Build a list of parent lattices, from closest to farthest ancestor
	var parents []KVLattice
	for p := kv.parent; p != nil; {
		parents = append(parents, p)
		// Walk up
		parent := p.Parent()
		switch t := parent.(type) {
		case KVLattice:
			p = t
		case *EntityIdMapKVLattice:
			p = t
		default:
			p = nil
		}
	}

	// Traverse parents from closest to farthest, filling missing keys
	for i := 0; i < len(parents); i++ {
		parentKv := parents[i]
		// Try to type assert to *EntityIdMapKVLattice for the map
		parentMap, ok := parentKv.(*EntityIdMapKVLattice)
		if !ok {
			continue
		}
		for id, v := range parentMap.kv {
			if _, present := out.kv[id]; !present {
				out.kv[id] = v
				changed = true
			}
		}
	}

	out.parent = nil // Remove the parent, since the lattice is now flattened.
	return out, changed
}

func (kv *EntityIdMapKVLattice) IsTop() bool {
	kv.requireFlat("IsTop")
	for _, v := range kv.kv {
		if !IsTop(v) {
			return false
		}
	}
	return true
}

// Fixme: add an entity count to check all entities are bot.
func (kv *EntityIdMapKVLattice) IsBot() bool {
	kv.requireFlat("IsBot")
	for _, v := range kv.kv {
		if !IsBot(v) {
			return false
		}
	}
	return true
}

func (kv *EntityIdMapKVLattice) WeakerThan(other Lattice) bool {
	kv.requireFlat("WeakerThan")
	oth, ok := flatKVLattice(other)
	if !ok {
		return false
	}

	for id, value := range kv.kv {
		if !WeakerThan(value, oth.kv[id]) {
			return false
		}
	}
	for id, value := range oth.kv {
		if _, present := kv.kv[id]; present {
			continue
		}
		if !WeakerThan(nil, value) {
			return false
		}
	}
	return true
}

func (kv *EntityIdMapKVLattice) Equals(other Lattice) bool {
	kv.requireFlat("Equals")
	oth, ok := flatKVLattice(other)
	if !ok {
		return other == nil && kv.IsTop()
	}

	for id, value := range kv.kv {
		if !Equals(value, oth.kv[id]) {
			return false
		}
	}
	for id, value := range oth.kv {
		if _, present := kv.kv[id]; present {
			continue
		}
		if !Equals(nil, value) {
			return false
		}
	}
	return true
}

func (kv *EntityIdMapKVLattice) Meet(other Lattice) (Lattice, bool) {
	kv.requireFlat("Meet")
	oth, ok := flatKVLattice(other)
	if !ok {
		return kv, false
	}

	changed := false
	for id, otherValue := range oth.kv {
		newValue, change := ConstMeet(kv.kv[id], otherValue)
		if change {
			kv.setOrDeleteTop(id, newValue)
			changed = true
		}
	}
	return kv, changed
}

func (kv *EntityIdMapKVLattice) Join(other Lattice) (Lattice, bool) {
	kv.requireFlat("Join")
	oth, ok := flatKVLattice(other)
	if !ok {
		return kv, false
	}

	changed := false
	for id, value := range kv.kv {
		newValue, change := ConstJoin(value, oth.kv[id])
		if change {
			kv.setOrDeleteTop(id, newValue)
			changed = true
		}
	}
	return kv, changed
}

func (kv *EntityIdMapKVLattice) Widen(other Lattice) (Lattice, bool) {
	kv.requireFlat("Widen")
	oth, ok := flatKVLattice(other)
	if !ok {
		return kv, false
	}

	changed := false
	for id, otherValue := range oth.kv {
		newValue, change := ConstWiden(kv.kv[id], otherValue)
		if change {
			kv.setOrDeleteTop(id, newValue)
			changed = true
		}
	}
	return kv, changed
}

func (kv *EntityIdMapKVLattice) String() string {
	kv.requireFlat("String")
	keys := make([]spir.EntityId, 0, len(kv.kv))
	for id := range kv.kv {
		keys = append(keys, id)
	}
	sort.Slice(keys, func(i, j int) bool {
		return uint32(keys[i]) < uint32(keys[j])
	})

	parts := make([]string, 0, len(keys))
	for _, id := range keys {
		parts = append(parts, fmt.Sprintf("%s: %s", id, Stringify(kv.kv[id])))
	}
	return fmt.Sprintf("KVLattice{%s}", strings.Join(parts, ", "))
}

func flatKVLattice(l Lattice) (*EntityIdMapKVLattice, bool) {
	if l == nil {
		return nil, false
	}

	kv, ok := l.(*EntityIdMapKVLattice)
	if !ok {
		return nil, false
	}
	if kv.isFlat() {
		return kv, true
	}

	flat, _ := kv.Flatten(false)
	flatKV, ok := flat.(*EntityIdMapKVLattice)
	return flatKV, ok
}

func (kv *EntityIdMapKVLattice) setOrDeleteTop(id spir.EntityId, value Lattice) {
	if IsTop(value) {
		delete(kv.kv, id)
		return
	}
	kv.kv[id] = value.(ConstLattice)
}
