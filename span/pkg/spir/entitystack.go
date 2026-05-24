package spir

import "slices"

// EntityStack is a stack structure that can be of fixed-size or dynamic size.
// If capacity > 0, the stack is fixed-size: when pushing past capacity, the oldest element is dropped.
type EntityStack struct {
	capacity int
	entities []EntityId
}

// NewEntityStack creates a new EntityStack.
// If capacity > 0, the stack is fixed-size; if capacity == 0, the stack is unbounded.
func NewEntityStack(capacity int) *EntityStack {
	initialCap := max(capacity, 0)
	return &EntityStack{
		capacity: capacity,
		entities: make([]EntityId, 0, initialCap),
	}
}

// Push adds an EntityId to the stack. If fixed-size and capacity exceeded, evicts oldest.
func (es *EntityStack) Push(eid EntityId) {
	if es.capacity > 0 && len(es.entities) >= es.capacity {
		copy(es.entities[0:], es.entities[1:])
		// Remove the last element (now duplicated)
		es.entities = es.entities[:len(es.entities)-1]
	}
	es.entities = append(es.entities, eid)
}

// Pop removes and returns the latest EntityId; returns false if empty.
func (es *EntityStack) Pop() (EntityId, bool) {
	if len(es.entities) == 0 {
		var zero EntityId
		return zero, false
	}
	last := es.entities[len(es.entities)-1]
	es.entities = es.entities[:len(es.entities)-1]
	return last, true
}

// Peek returns the latest EntityId without removing; returns false if empty.
func (es *EntityStack) Peek() (EntityId, bool) {
	if len(es.entities) == 0 {
		return NIL_ID, false
	}
	return es.entities[len(es.entities)-1], true
}

// Peek4 returns the top 4 EntityIds on the stack as a fixed size array.
// If there are fewer than 4 entities, the returned array will have zero values (NIL_ID) at the start for missing elements.
// The newest entities are at the end of the array.
// Example: Stack = [a, b], Peek4() => [0, 0, a, b].
func (es *EntityStack) Peek4() [4]EntityId {
	var result [4]EntityId
	stackLen := len(es.entities)
	if stackLen == 0 {
		return result
	}
	start := 0
	if stackLen >= 4 {
		start = stackLen - 4
	}
	for i := 0; i < 4 && start+i < stackLen; i++ {
		result[i] = es.entities[start+i]
	}
	return result
}

// Count returns the number of times eid appears in the stack.
func (es *EntityStack) Count(eid EntityId) int {
	count := 0
	for _, v := range es.entities {
		if v == eid {
			count++
		}
	}
	return count
}

// Size returns the current size of the stack.
func (es *EntityStack) Size() int {
	return len(es.entities)
}

// IsEmpty returns true if the stack is empty.
func (es *EntityStack) IsEmpty() bool {
	return len(es.entities) == 0
}

// Equals returns true if the two stacks are equal.
func (es *EntityStack) Equals(other *EntityStack) bool {
	return slices.Equal(es.entities, other.entities)
}
