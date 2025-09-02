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
// The remaining lower 20 bits are used to assign a sequential ID to the entity.
type EntityId uint32
type EId = EntityId

func (e EntityId) String() string {
	return EntityIdString(e, 'x')
}

const NIL_ID EntityId = 0

// The EntityKind (EK) type is used to represent the kind of an entity in the SPAN IR.
// It is an integer type in the range of 0 to 31 (5 bits)
// that can take on various values to indicate different kinds of entities.
type EntityKind = K_EK

const EIdBitLength uint8 = 30
const EIdMask32 EntityId = 0x3FFF_FFFF
const EIdShift32 uint8 = 0
const EIdPosMask64 uint64 = 0x3FFF_FFFF_0000_0000
const EIdShift64 uint8 = 32

// EntityKind (EK) is a 5-bit integer that represents the kind of an entity.
const EKPosMask16 uint16 = 0x3E00
const EKShift16 uint8 = 9
const EKPosMask32 uint32 = 0x3E00_0000
const EKShift32 uint8 = 25
const EKPosMask64 uint64 = 0x3E00_0000_0000_0000
const EKShift64 uint8 = 57

// EntitySubKind (ESK) is a 5-bit integer that represents the sub-kind of an entity.
const ESKPosMask16 uint16 = 0x01F0
const ESKShift16 uint8 = 4
const ESKPosMask32 uint32 = 0x01F0_0000
const ESKShift32 uint8 = 20
const ESKPosMask64 uint64 = 0x01F0_0000_0000_0000
const ESKShift64 uint8 = 52

const ImmConstBitCount uint8 = 20
const ImmConstMask32 uint32 = 0x000F_FFFF
const ImmConstMask64 uint64 = 0x0000_0000_000F_FFFF

// GetTrueEntityId extracts the true entity ID from an EntityId
// by masking the upper 2 bits of the EntityId.
func GetTrueEntityId(id EntityId) EntityId {
	return id & EIdMask32
}

// Info associated with a literal value.
type LiteralInfo struct {
	valueType ValueType
	value     uint64
}

type ValueInfo struct {
	name      string
	fid       EntityId // A function ID is also an EntityId
	eKind     EntityKind
	valueType ValueType
}

// Function represents a function in the SPAN IR.
type Function struct {
	fid        EntityId // The function ID
	fName      string   // The function name
	originTu   *TU      // The TU that the function was originally from
	tu         *TU      // The TU that the function belongs to
	returnType ValueType
	paramIds   []EntityId

	// The sequence of instructions in the function.
	// It should contain a list of instructions with appropriate labels
	// and jumps to allow construction of a CFG graph.
	insns []Insn // This is only populated for debugging purposes
	body  Graph  // The CFG of the function
}

type TU struct {
	// globalInit is a special function with one basic block
	// with all the initialization of global variables.
	tuId   EntityId // The TU ID
	tuName string   // The source file name
	tuDir  string   // The source file directory
	origin string   // The origin of the TU (e.g. Clang AST)

	mergedTUs map[EntityId]*TU // Map of TU IDs to merged TUs

	globalInit     EntityId
	functions      map[EntityId]*Function
	callArgs       map[CallSiteId][]EntityId
	valueTypes     map[EntityId]ValueType // Holds complete value type information
	constants      map[EntityId]LiteralInfo
	labelNames     map[LabelId]string
	namesToId      map[string]EntityId // Necessary for name lookup during linking
	entityInfo     map[EntityId]any    // For scratch use
	insnInfo       map[InsnId]InsnInfo // For information on an instruction
	idGen          *idgen.IDGenerator
	sourceInfo     *SrcLocInfo
	sourceLocation map[EntityId]SrcLoc
}

func NewTU() *TU {
	tu := &TU{
		tuId:           NIL_ID,
		tuName:         "",
		tuDir:          "",
		origin:         "",
		mergedTUs:      make(map[EntityId]*TU),
		globalInit:     NIL_ID,
		entityInfo:     make(map[EntityId]interface{}),
		functions:      make(map[EntityId]*Function),
		constants:      make(map[EntityId]LiteralInfo),
		valueTypes:     make(map[EntityId]ValueType),
		sourceLocation: make(map[EntityId]SrcLoc),
		insnInfo:       make(map[InsnId]InsnInfo),
		callArgs:       make(map[CallSiteId][]EntityId),
		idGen:          idgen.NewIDGenerator(),
		sourceInfo:     NewSrcLocInfo(),
		labelNames:     make(map[LabelId]string),
		namesToId:      make(map[string]EntityId),
	}

	tu.globalInit = tu.NewFunction(K_00_INITS_FUNC_NAME, &VoidVT, nil, nil).id
	return tu
}

func NewValueInfo(name string, eKind EntityKind,
	vType ValueType, fid EntityId) *ValueInfo {
	return &ValueInfo{
		name:      name,
		fid:       fid,
		eKind:     eKind,
		valueType: vType,
	}
}

func (tu *TU) GetUniqueLabelId() LabelId {
	return LabelId(tu.idGen.AllocateID(GenPrefix16(K_EK_LABEL, 0),
		K_EK_LABEL.SeqIdBitLength()))
}

func (tu *TU) AddInsn(bb *BasicBlock, insn Insn, srcLoc *SrcLoc) {
	insnId := InsnId(tu.idGen.AllocateID(insn.GetInsnPrefix16(),
		K_EK_INSN.SeqIdBitLength()))
	tu.entityInfo[EntityId(insnId)] = &InsnInfo{bbId: bb.id, srcLoc: srcLoc}
	bb.insns = append(bb.insns, insn)
}

func (tu *TU) GetUniqueBBId() BasicBlockId {
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
	vType ValueType, fid EntityId) EntityId {
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
	tu.constants[entityId] = LiteralInfo{
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
		return uint16(eKind.place16() | (uint16(eSubKind) << ESKShift16))
	} else {
		return uint16(eKind)
	}
}

func GenPrefix32(eKind EntityKind, eSubKind uint8) uint32 {
	if eKind.HasSubKind() {
		return uint32(eKind.place32() | (uint32(eSubKind) << ESKShift32))
	} else {
		return uint32(eKind)
	}
}

func (tu *TU) NewFunction(name string, returnType ValueType,
	paramIds []EntityId, body Graph) *Function {
	id := EntityId(tu.idGen.AllocateID(GenPrefix16(K_EK_FUNC, uint8(returnType.GetType())),
		K_EK_FUNC.SeqIdBitLength()))

	fun := &Function{
		fid:        id,
		fName:      name,
		returnType: returnType,
		paramIds:   paramIds,
		body:       body,
	}

	tu.functions[id] = fun
	tu.namesToId[name] = EntityId(id)
	tu.entityInfo[EntityId(id)] = fun

	return fun
}

func (fun *Function) SetBody(tu *TU, body Graph) {
	fun.body = createCfgForFunction(fun, body)
}

func (fun *Function) GetId() EntityId {
	return fun.fid
}

func (fun *Function) GetName() string {
	return fun.fName
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

func (tu *TU) GetGlobalInit() EntityId {
	return tu.globalInit
}

func (tu *TU) GetFunction(name string) *Function {
	if id, ok := tu.namesToId[name]; ok {
		if fun, ok := tu.functions[EntityId(id)]; ok {
			return fun
		}
	}
	return nil
}

func (tu *TU) GetFunctionById(id EntityId) *Function {
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
	return entityId & EIdMask32
}

// EKind extracts the EntityKind from an EntityId.
// The EntityKind is encoded in bits 25-29 of the EntityId.
func (entityId EntityId) EKind() EntityKind {
	return EntityKind((entityId & EIdMask32) >> EKShift32)
}

// Does the entity kind have a sub-kind?
// A sub-kind uses another 5 bits to represent the sub type of the entity.
func (eKind EntityKind) HasSubKind() bool {
	if (eKind >= K_EK_BB && eKind <= K_EK_TU) ||
		eKind == K_EK_LABEL {
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
	return uint16(eKind) << EKShift16
}

func (eKind EntityKind) place32() uint32 {
	return uint32(eKind) << EKShift32
}

func (eKind EntityKind) place64() uint64 {
	return uint64(eKind) << EKShift64
}

func (eKind EntityKind) IsVariable() bool {
	if eKind >= K_EK_VAR && eKind <= K_EK_VAR_PSEUDO {
		return true
	}
	return false
}

func (eKind EntityKind) IsLiteral() bool {
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
