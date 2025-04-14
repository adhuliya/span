package spir

// This file defines the types of entities in the SPAN IR.

// The EntityKind type is used to represent the kind of an entity in the SPAN IR.
// It is an integer type in the range of 0 to 31 (5 bits)
// that can take on various values to indicate different kinds of entities.
type EntityKind int

const (
	// Entity kinds that can be used in expressions
	ENTITY_VARIABLE           EntityKind = 0
	ENTITY_TMP_VARIABLE       EntityKind = 1
	ENTITY_PSEUDO_VARIABLE    EntityKind = 2
	ENTITY_CONSTANT           EntityKind = 3
	ENTITY_IMMEDIATE_CONSTANT EntityKind = 4
	ENTITY_NAMED_CONSTANT     EntityKind = 5
	ENTITY_FUNCTION           EntityKind = 6
	ENTITY_OTHER              EntityKind = 7

	// Other entity kinds
	ENTITY_INSTRUCTION EntityKind = 8
	ENTITY_BASIC_BLOCK EntityKind = 9
	ENTITY_SCOPE_BLOCK EntityKind = 10
	ENTITY_EXPRESSION  EntityKind = 11
)
