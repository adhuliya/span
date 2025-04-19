package spir

// This file defines the TranslationUnit type.
// The TranslationUnit type is used to represent a single SPAN IR translation unit.
// It is a container for all the entities and instructions which make up a program.

// An Entity ID is a 32 bit unsigned integer which is used to identify an entity.
// The upper 12 bits are used to identify the pool of IDs.
//
//	-- The most significant 2 bits are always masked to zero.
//	-- The next 5 bits is the EntityKind.
//	-- The next 5 bits is the type of the Entity.
//
// The lower 20 bits are used to identify the ID within the pool.
type EntityId uint32

type FunctionId EntityId

type Function struct {
	id         FunctionId
	returnType ValueType
	paramIds   []EntityId
	body       Graph
}

type TranslationUnit struct {
	// This is a special function with one basic block
	// with all the initialization of global variables.
	globalInitialization Function
	functions            map[FunctionId]Function
	valueTypes           map[EntityId]ValueType
	sourceLocation       map[EntityId]SourceLocation
	insnInfo             map[InsnId]InsnInfo
	recordTypes          map[RecordId]RecordValueType
	idGen                IDGenerator
	sourceInfo           SourceLocationInfo
	labelNames           map[EntityId]string
}

// The EntityKind type is used to represent the kind of an entity in the SPAN IR.
// It is an integer type in the range of 0 to 31 (5 bits)
// that can take on various values to indicate different kinds of entities.
type EntityKind uint8

const EntityKindPosition uint32 = 0x3C000000

const (
	// Entity kinds which can be in an expression (4 bit values)
	ENTITY_VARIABLE                  EntityKind = 0 // The function locals, static vars, and parameters.
	ENTITY_GLOBAL_VARIABLE           EntityKind = 1 // A global variable, function etc.
	ENTITY_TMP_VARIABLE              EntityKind = 2
	ENTITY_SSA_VARIABLE              EntityKind = ENTITY_TMP_VARIABLE
	ENTITY_PSEUDO_VARIABLE           EntityKind = 3 // To give names to memory allocations
	ENTITY_CONSTANT                  EntityKind = 4
	ENTITY_IMMEDIATE_CONSTANT        EntityKind = 5
	ENTITY_LABEL                     EntityKind = 6 // In if-then-else statements
	ENTITY_VALUE_TYPE                EntityKind = 8 // A type, like int, float, record etc.
	ENTITY_FUNC                      EntityKind = 9
	ENTITY_FUNC_WITH_DEF             EntityKind = 10
	ENTITY_FUNC_WITH_DEF_VAR_ARGS    EntityKind = 11
	ENTITY_FUNC_WITHOUT_DEF          EntityKind = 12
	ENTITY_FUNC_WITHOUT_DEF_VAR_ARGS EntityKind = 13
	ENTITY_CLASS                     EntityKind = 14 // A class type; for future use.
	ENTITY_OTHER                     EntityKind = 15

	// Entity kinds which cannot be in an expression (5 bit values)
	ENTITY_INSTRUCTION      EntityKind = 16
	ENTITY_BASIC_BLOCK      EntityKind = 17
	ENTITY_CFG              EntityKind = 18
	ENTITY_SCOPE_BLOCK      EntityKind = 19
	ENTITY_TRANSLATION_UNIT EntityKind = 20

	// Reserved entity kinds (5 bit values)
	ENTITY_RESERVED_21 EntityKind = 21 // Reserved for use at runtime
	ENTITY_RESERVED_22 EntityKind = 22 // Reserved for use at runtime
	ENTITY_RESERVED_23 EntityKind = 23 // Reserved for use at runtime
	ENTITY_RESERVED_24 EntityKind = 24 // Reserved for use at runtime
	ENTITY_RESERVED_25 EntityKind = 25 // Reserved for use at runtime
	ENTITY_RESERVED_26 EntityKind = 26 // Reserved for use at runtime
	ENTITY_RESERVED_27 EntityKind = 27 // Reserved for use at runtime
	ENTITY_RESERVED_28 EntityKind = 28 // Reserved for use at runtime
	ENTITY_RESERVED_29 EntityKind = 29 // Reserved for use at runtime
	ENTITY_RESERVED_30 EntityKind = 30 // Reserved for use at runtime
	ENTITY_RESERVED_31 EntityKind = 31 // Reserved for use at runtime
)

func GetEntityKind(entityId EntityId) EntityKind {
	return EntityKind((uint32(entityId) >> 25) & 0x1F)
}

func positionEntityKindBits32(entityKind EntityKind) uint32 {
	// EntityKind is in bits 29..25 (5 bits)
	return uint32(entityKind) << 25
}

func positionEntityKindBits64(entityKind EntityKind) uint64 {
	// EntityKind is in bits 61..57 (5 bits)
	return uint64(positionEntityKindBits32(entityKind)) << 32
}

func IsVariable(entitId EntityId) bool {
	eKind := GetEntityKind(entitId)
	if eKind >= ENTITY_VARIABLE && eKind <= ENTITY_PSEUDO_VARIABLE {
		return true
	}
	return false
}

func IsConstant(entitId EntityId) bool {
	eKind := GetEntityKind(entitId)
	if eKind == ENTITY_CONSTANT || eKind == ENTITY_IMMEDIATE_CONSTANT {
		return true
	}
	return false
}

func IsFunction(entitId EntityId) bool {
	eKind := GetEntityKind(entitId)
	if eKind >= ENTITY_FUNC && eKind <= ENTITY_FUNC_WITHOUT_DEF_VAR_ARGS {
		return true
	}
	return false
}
