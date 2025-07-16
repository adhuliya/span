package spir

import (
	"fmt"

	"github.com/adhuliya/span/pkg/idgen"
)

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

const ID_NONE uint32 = 0

// The EntityKind type is used to represent the kind of an entity in the SPAN IR.
// It is an integer type in the range of 0 to 31 (5 bits)
// that can take on various values to indicate different kinds of entities.
type EntityKind = K_EK

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

type TU struct {
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
	idGen          *idgen.IDGenerator
	sourceInfo     *SourceLocationInfo
	sourceLocation map[EntitySrcId]SourceLocation
	labelNames     map[LabelId]string
	namesToId      map[string]EntityId
}

func NewTU() *TU {
	tu := &TU{
		globalInit:     FunctionId(ID_NONE),
		entityInfo:     make(map[EntityId]interface{}),
		functions:      make(map[FunctionId]*Function),
		constants:      make(map[EntityId]ConstantInfo),
		valueTypes:     make(map[EntityId]ValueType),
		sourceLocation: make(map[EntitySrcId]SourceLocation),
		insnInfo:       make(map[InsnId]InsnInfo),
		callExpr:       make(map[CallId][]EntityId),
		recordTypes:    make(map[RecordId]RecordValueType),
		idGen:          idgen.NewIDGenerator(),
		sourceInfo:     NewSourceLocationInfo(),
		labelNames:     make(map[LabelId]string),
		namesToId:      make(map[string]EntityId),
	}

	tu.globalInit = tu.NewFunction(K_FUNC_GLOBAL_INIT,
		NewBasicValueType(K_VK_VOID, K_QK_QNONE), nil, nil).id
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

func (tu *TU) AddInsn(bb *BasicBlock, insn Instruction) {
	insnId := InsnId(tu.idGen.AllocateID(insn.GetInsnPrefix16(),
		K_EK_INSN.SeqIdBitLength()))
	tu.entityInfo[EntityId(insnId)] = &InsnInfo{bbId: bb.id}
	bb.insns = append(bb.insns, insn)
}

func (tu *TU) NewBBId() BasicBlockId {
	id := BasicBlockId(tu.idGen.AllocateID(GenPrefix16(K_EK_BB, 0),
		K_EK_BB.SeqIdBitLength()))
	return id
}

func (tu *TU) GetEntityId(name string) EntityId {
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
func (tu *TU) NewVar(name string, eKind EntityKind,
	vType ValueType, fid FunctionId) EntityId {
	valInfo := NewValueInfo(name, eKind, vType, fid)
	id := tu.idGen.AllocateID(GenPrefix16(eKind, uint8(vType.GetType())),
		eKind.SeqIdBitLength())
	entityId := EntityId(id)
	tu.entityInfo[entityId] = valInfo
	tu.namesToId[name] = entityId
	return entityId
}

func (tu *TU) NewConst(val uint64, vType ValueType) EntityId {
	imm, ok := GenImmediate20(val, vType.GetType())
	eKind := K_EK_LIT_NUM
	var id uint32 = 0
	if ok {
		eKind = K_EK_LIT_NUM_IMM
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

func GenImmediate20(val uint64, vType ValKind) (uint32, bool) {
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

func (tu *TU) NewFunction(name string, returnType ValueType,
	paramIds []EntityId, body Graph) *Function {
	id := FunctionId(tu.idGen.AllocateID(GenPrefix16(K_EK_FUNC, uint8(returnType.GetType())),
		K_EK_FUNC.SeqIdBitLength()))

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

func (tu *TU) GetGlobalInit() FunctionId {
	return tu.globalInit
}

func (tu *TU) GetFunction(name string) *Function {
	if id, ok := tu.namesToId[name]; ok {
		if fun, ok := tu.functions[FunctionId(id)]; ok {
			return fun
		}
	}
	return nil
}

func (tu *TU) GetFunctionById(id FunctionId) *Function {
	if fun, ok := tu.functions[id]; ok {
		return fun
	}
	return nil
}

func (tu *TU) GenerateEntityId(eKind EntityKind) EntityId {
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
	if (eKind >= K_EK_BB && eKind <= K_EK_TU) ||
		eKind == K_EK_LABEL || eKind == K_EK_CLASS {
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
	if eKind >= K_EK_VAR && eKind <= K_EK_VAR_PSEUDO {
		return true
	}
	return false
}

func (eKind EntityKind) IsConstant() bool {
	if eKind == K_EK_LIT_NUM || eKind == K_EK_LIT_STR {
		return true
	}
	return false
}

func (eKind EntityKind) IsFunction() bool {
	if eKind == K_EK_FUNC || eKind == K_EK_FUNC_VARGS {
		return true
	}
	return false
}
