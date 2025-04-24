package spir

import "fmt"

// This file defines the TranslationUnit type.
// The TranslationUnit type is used to represent a single SPAN IR translation unit.
// It is a container for all the entities and instructions which make up a program.

// An Entity ID is a 32 bit unsigned integer which is used to identify an entity.
// The upper 12 bits are used to identify the pool of IDs.
//
//	-- The most significant 2 bits are always masked to zero.
//	-- The next 5 bits is the EntityKind.
//	-- The next 5 bits is the possible type of the Entity (value type, instruction type etc.)
//
// The remaining lower bits are used to assign a sequential ID to the entity.
type EntityId uint32
type FunctionId EntityId

const ENTITY_ID_NONE EntityId = 0

const EntityIdMask32 EntityId = 0x3FFF_FFFF
const EntityIdShift32 uint8 = 0
const EntityIdMask64 uint64 = 0x3FFF_FFFF_0000_0000
const EntityIdShift64 uint8 = 32

const EntityKindMask16 uint16 = 0x3E00
const EntityKindShift16 uint8 = 9
const EntityKindMask32 uint32 = 0x3E00_0000
const EntityKindShift32 uint8 = 25
const EntityKindMask64 uint64 = 0x3E00_0000_0000_0000
const EntityKindShift64 uint8 = 57

const EntitySubKindMask16 uint16 = 0x01F0
const EntitySubKindShift16 uint8 = 4
const EntitySubKindMask32 uint32 = 0x01F0_0000
const EntitySubKindShift32 uint8 = 20
const EntitySubKindMask64 uint64 = 0x01F0_0000_0000_0000
const EntitySubKindShift64 uint8 = 52

const ImmConstMask32 uint32 = 0x000F_FFFF
const ImmConstMask64 uint64 = 0x0000_0000_000F_FFFF

func ValidBits(id EntityId) EntityId {
	return id & EntityIdMask32
}

// Info associated with a constant value.
type ConstantInfo struct {
	valueType ValueType
	value     uint64
}

type ValueInfo struct {
	name      string
	fid       FunctionId
	eKind     EntityKind
	valueType ValueType
}

// Function represents a function in the SPAN IR.
type Function struct {
	id         FunctionId
	name       string
	returnType ValueType
	paramIds   []EntityId
	body       Graph
}

type TranslationUnit struct {
	// This is a special function with one basic block
	// with all the initialization of global variables.
	globalInit     FunctionId
	entityInfo     map[EntityId]any
	functions      map[FunctionId]*Function
	constants      map[EntityId]ConstantInfo
	valueTypes     map[EntityId]ValueType
	insnInfo       map[InsnId]InsnInfo
	callExpr       map[CallId][]EntityId
	recordTypes    map[RecordId]RecordValueType
	idGen          *IDGenerator
	sourceInfo     *SourceLocationInfo
	sourceLocation map[EntitySrcId]SourceLocation
	labelNames     map[LabelId]string
	namesToId      map[string]EntityId
}

// The EntityKind type is used to represent the kind of an entity in the SPAN IR.
// It is an integer type in the range of 0 to 31 (5 bits)
// that can take on various values to indicate different kinds of entities.
type EntityKind uint8

const (
	// Entity kinds which can be in an expression (4 bit values)
	ENTITY_VAR           EntityKind = 1 // The function locals, static vars, and parameters.
	ENTITY_VAR_GLOBAL    EntityKind = 2 // A global variable, function etc.
	ENTITY_VAR_TMP       EntityKind = 3
	ENTITY_VAR_SSA       EntityKind = 4
	ENTITY_VAR_PSEUDO    EntityKind = 5 // To give names to memory allocations
	ENTITY_CONST         EntityKind = 6
	ENTITY_CONST_IMM     EntityKind = 7
	ENTITY_VALUE_TYPE    EntityKind = 8 // A type, like int, float, record etc.
	ENTITY_FUNC          EntityKind = 9
	ENTITY_FUNC_VAR_ARGS EntityKind = 10
	ENTITY_FUNC_NO_DEF   EntityKind = 11
	ENTITY_CLASS         EntityKind = 12 // A class type; for future use.
	ENTITY_LABEL         EntityKind = 13 // In if-then-else statements
	ENTITY_EXPR1         EntityKind = 14 // Reserved for future use
	ENTITY_EXPR2         EntityKind = 15 // Reserved for future use

	// Entity kinds which cannot be in an expression (5 bit values)
	ENTITY_BB    EntityKind = 16
	ENTITY_CFG   EntityKind = 17
	ENTITY_SCOPE EntityKind = 18
	ENTITY_TU    EntityKind = 19
	ENTITY_INSN  EntityKind = 20

	// Reserved entity kinds (5 bit values)
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

func NewTranslationUnit() *TranslationUnit {
	tu := &TranslationUnit{
		globalInit:     FunctionId(ENTITY_ID_NONE),
		entityInfo:     make(map[EntityId]interface{}),
		functions:      make(map[FunctionId]*Function),
		constants:      make(map[EntityId]ConstantInfo),
		valueTypes:     make(map[EntityId]ValueType),
		sourceLocation: make(map[EntitySrcId]SourceLocation),
		insnInfo:       make(map[InsnId]InsnInfo),
		callExpr:       make(map[CallId][]EntityId),
		recordTypes:    make(map[RecordId]RecordValueType),
		idGen:          NewIDGenerator(),
		sourceInfo:     NewSourceLocationInfo(),
		labelNames:     make(map[LabelId]string),
		namesToId:      make(map[string]EntityId),
	}

	tu.globalInit = tu.NewFunction("global_init",
		NewBasicValueType(TY_VOID, QUAL_TYPE_NONE), nil, nil).id
	return tu
}

func NewValueInfo(name string, eKind EntityKind,
	vType ValueType, fid FunctionId) *ValueInfo {
	return &ValueInfo{
		name:      name,
		fid:       fid,
		eKind:     eKind,
		valueType: vType,
	}
}

func (tu *TranslationUnit) AddInsn(bb *BasicBlock, insn Instruction) {
	insnId := InsnId(tu.idGen.AllocateID(insn.GetInsnPrefix16(),
		ENTITY_INSN.SeqIdBitLength()))
	tu.entityInfo[EntityId(insnId)] = &InsnInfo{bbId: bb.id}
	bb.insns = append(bb.insns, insn)
}

func (tu *TranslationUnit) NewBBId() BasicBlockId {
	id := BasicBlockId(tu.idGen.AllocateID(GenPrefix16(ENTITY_BB, 0),
		ENTITY_BB.SeqIdBitLength()))
	return id
}

func (tu *TranslationUnit) GetEntityId(name string) EntityId {
	// Check if the name is already in the map
	if id, ok := tu.namesToId[name]; ok {
		return id
	}
	panic(fmt.Sprintf("EntityId for %s not found", name))
}

// NewVar creates a new value in the translation unit.
// Each value is associated with a name, a function ID, an entity kind,
// and a value type. The function ID is used to identify the function
// to which the value belongs. If fid is 0, it means the value is global.
func (tu *TranslationUnit) NewVar(name string, eKind EntityKind,
	vType ValueType, fid FunctionId) EntityId {
	valInfo := NewValueInfo(name, eKind, vType, fid)
	id := tu.idGen.AllocateID(GenPrefix16(eKind, uint8(vType.GetType())),
		eKind.SeqIdBitLength())
	entityId := EntityId(id)
	tu.entityInfo[entityId] = valInfo
	tu.namesToId[name] = entityId
	return entityId
}

func (tu *TranslationUnit) NewConst(val uint64, vType ValueType) EntityId {
	imm, ok := GenImmediate20(val, vType.GetType())
	eKind := ENTITY_CONST
	var id uint32 = 0
	if ok {
		eKind = ENTITY_CONST_IMM
		id = GenPrefix32(eKind, uint8(vType.GetType()))<<eKind.SeqIdBitLength() | uint32(imm)
	} else {
		id = tu.idGen.AllocateID(GenPrefix16(eKind, uint8(vType.GetType())),
			eKind.SeqIdBitLength())
	}

	entityId := EntityId(id)
	tu.constants[entityId] = ConstantInfo{
		valueType: vType,
		value:     val,
	}
	return entityId
}

func GenImmediate20(val uint64, vType ValueTypeKind) (uint32, bool) {
	if vType.IsInteger() && val == val&ImmConstMask64 {
		return uint32(val & ImmConstMask64), true
	}
	return 0, false
}

func GenPrefix16(eKind EntityKind, eSubKind uint8) uint16 {
	if eKind.HasSubKind() {
		return uint16(eKind.place16() | (uint16(eSubKind) << EntitySubKindShift16))
	} else {
		return uint16(eKind)
	}
}

func GenPrefix32(eKind EntityKind, eSubKind uint8) uint32 {
	if eKind.HasSubKind() {
		return uint32(eKind.place32() | (uint32(eSubKind) << EntitySubKindShift32))
	} else {
		return uint32(eKind)
	}
}

func (tu *TranslationUnit) NewFunction(name string, returnType ValueType,
	paramIds []EntityId, body Graph) *Function {
	id := FunctionId(tu.idGen.AllocateID(GenPrefix16(ENTITY_FUNC, uint8(returnType.GetType())),
		ENTITY_FUNC.SeqIdBitLength()))

	fun := &Function{
		id:         id,
		name:       name,
		returnType: returnType,
		paramIds:   paramIds,
		body:       body,
	}

	tu.functions[id] = fun
	tu.namesToId[name] = EntityId(id)
	tu.entityInfo[EntityId(id)] = fun

	return fun
}

func (fun *Function) GetId() FunctionId {
	return fun.id
}

func (fun *Function) GetName() string {
	return fun.name
}

func (fun *Function) GetReturnType() ValueType {
	return fun.returnType
}

func (fun *Function) GetParamIds() []EntityId {
	return fun.paramIds
}

func (fun *Function) GetBody() Graph {
	return fun.body
}

func (tu *TranslationUnit) GetGlobalInit() FunctionId {
	return tu.globalInit
}

func (tu *TranslationUnit) GetFunction(name string) *Function {
	if id, ok := tu.namesToId[name]; ok {
		if fun, ok := tu.functions[FunctionId(id)]; ok {
			return fun
		}
	}
	return nil
}

func (tu *TranslationUnit) GetFunctionById(id FunctionId) *Function {
	if fun, ok := tu.functions[id]; ok {
		return fun
	}
	return nil
}

func (tu *TranslationUnit) GenerateEntityId(eKind EntityKind) EntityId {
	return EntityId(tu.idGen.AllocateID(uint16(eKind), eKind.SeqIdBitLength()))
}

// ValidBits masks the upper 2 bits of EntityId to zero
func (entityId EntityId) ValidBits() EntityId {
	return entityId & EntityIdMask32
}

// EKind extracts the EntityKind from an EntityId.
// The EntityKind is encoded in bits 25-29 of the EntityId.
func (entityId EntityId) EKind() EntityKind {
	return EntityKind((entityId & EntityIdMask32) >> EntityKindShift32)
}

// Does the entity kind have a sub-kind?
// A sub-kind uses another 5 bits to represent the sub type of the entity.
func (eKind EntityKind) HasSubKind() bool {
	if (eKind >= ENTITY_BB && eKind <= ENTITY_TU) ||
		eKind == ENTITY_LABEL || eKind == ENTITY_CLASS {
		return false
	}
	return true
}

func (eKind EntityKind) SeqIdBitLength() uint8 {
	if eKind.HasSubKind() {
		return 20
	}
	return 25
}

func (eKind EntityKind) place16() uint16 {
	return uint16(eKind) << EntityKindShift16
}

func (eKind EntityKind) place32() uint32 {
	return uint32(eKind) << EntityKindShift32
}

func (eKind EntityKind) place64() uint64 {
	return uint64(eKind) << EntityKindShift64
}

func (eKind EntityKind) IsVariable() bool {
	if eKind >= ENTITY_VAR && eKind <= ENTITY_VAR_PSEUDO {
		return true
	}
	return false
}

func (eKind EntityKind) IsConstant() bool {
	if eKind == ENTITY_CONST || eKind == ENTITY_CONST_IMM {
		return true
	}
	return false
}

func (eKind EntityKind) IsFunction() bool {
	if eKind >= ENTITY_FUNC && eKind <= ENTITY_FUNC_NO_DEF {
		return true
	}
	return false
}
