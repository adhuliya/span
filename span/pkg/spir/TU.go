package spir

import (
	"fmt"
	"path/filepath"

	"github.com/adhuliya/span/pkg/idgen"
)

// This file defines the TranslationUnit type.
// The TranslationUnit type is used to represent a single SPAN IR translation unit.
// It is a container for all the entities and instructions which make up a program.

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
// A special global initialization function is used to initialize global variables.
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
	// 1. Basic information about the TU
	tuId      EntityId // The TU ID
	tuName    string   // The TU name
	tuAbspath string   // The source file path
	origin    string   // The origin of the TU (e.g. Clang AST)

	// 2. Information about the TU's parent and merged TUs (when linking TUs together)
	mergedTUs map[EntityId]*TU // Map of TU IDs if this is a merged TU
	parentTU  *TU              // The parent TU, if this TU has been merged into another TU

	// 3. The minimal complete TU program
	valueTypes map[EntityId]ValueType // Holds complete value type information
	constants  map[EntityId]LiteralInfo
	functions  map[EntityId]*Function
	callArgs   map[CallSiteId][]EntityId // Arguments for a call site
	labelNames map[LabelId]string
	globalInit EntityId // A special function with one basic block with all the initialization of global variables.

	// 4. Meta information about the TU
	namesToId    map[string]EntityId // Necessary for name lookup during linking
	entityInfo   map[EntityId]any    // For scratch use
	insnInfo     map[InsnId]InsnInfo // For information on an instruction
	idGen        *idgen.IDGenerator
	srcFilesInfo *SrcFilesInfo
	srcLocations map[EntityId]SrcLoc
}

func NewTU() *TU {
	tu := &TU{
		tuId:         NIL_ID,
		tuName:       "",
		tuAbspath:    "",
		origin:       "",
		mergedTUs:    make(map[EntityId]*TU),
		parentTU:     nil,
		globalInit:   NIL_ID,
		entityInfo:   make(map[EntityId]any),
		functions:    make(map[EntityId]*Function),
		constants:    make(map[EntityId]LiteralInfo),
		valueTypes:   make(map[EntityId]ValueType),
		insnInfo:     make(map[InsnId]InsnInfo),
		callArgs:     make(map[CallSiteId][]EntityId),
		idGen:        idgen.NewIDGenerator(),
		srcLocations: make(map[EntityId]SrcLoc),
		srcFilesInfo: NewSrcFilesInfo(),
		labelNames:   make(map[LabelId]string),
		namesToId:    make(map[string]EntityId),
	}

	tu.globalInit = tu.NewFunction(K_00_GLBL_INIT_FUNC_NAME, &VoidVT, nil, nil).fid
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
	return LabelId(tu.idGen.AllocateID(GenKindPrefix16(K_EK_ELABEL, 0),
		K_EK_ELABEL.SeqIdBitLen()))
}

func (tu *TU) AddInsn(bb *BasicBlock, insn Insn, srcLoc *SrcLoc) {
	insnId := InsnId(tu.idGen.AllocateID(insn.GetInsnPrefix16(),
		K_EK_EINSN.SeqIdBitLen()))
	tu.entityInfo[EntityId(insnId)] = &InsnInfo{bbId: bb.id, srcLoc: srcLoc}
	bb.insns = append(bb.insns, insn)
}

func (tu *TU) GetUniqueBBId() BasicBlockId {
	id := BasicBlockId(tu.idGen.AllocateID(GenKindPrefix16(K_EK_EBB, 0),
		K_EK_EBB.SeqIdBitLen()))
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
	id := tu.idGen.AllocateID(GenKindPrefix16(eKind, uint8(vType.GetType())),
		eKind.SeqIdBitLen())
	entityId := EntityId(id)
	tu.entityInfo[entityId] = valInfo
	tu.namesToId[name] = entityId
	return entityId
}

func (tu *TU) NewConst(val uint64, vType ValueType) EntityId {
	imm, ok := GenImmediate20(val, vType.GetType())
	eKind := K_EK_ELIT_NUM
	var id uint32 = 0
	if ok {
		eKind = K_EK_ELIT_NUM_IMM
		id = GenKindPrefix32(eKind, uint8(vType.GetType()))<<eKind.SeqIdBitLen() | uint32(imm)
	} else {
		id = tu.idGen.AllocateID(GenKindPrefix16(eKind, uint8(vType.GetType())),
			eKind.SeqIdBitLen())
	}

	entityId := EntityId(id)
	tu.constants[entityId] = LiteralInfo{
		valueType: vType,
		value:     val,
	}
	return entityId
}

func (tu *TU) NewFunction(name string, returnType ValueType,
	paramIds []EntityId, body Graph) *Function {
	id := EntityId(tu.idGen.AllocateID(GenKindPrefix16(K_EK_EFUNC, uint8(returnType.GetType())),
		K_EK_EFUNC.SeqIdBitLen()))

	fun := &Function{
		fid:        id,
		fName:      name,
		returnType: returnType,
		paramIds:   paramIds,
		body:       body,
		insns:      nil,
	}

	tu.functions[id] = fun
	tu.namesToId[name] = EntityId(id)
	tu.entityInfo[EntityId(id)] = fun

	return fun
}

func (fun *Function) SetBody(tu *TU, insnSeq []Insn) {
	fun.body = ConstructCFG(insnSeq)
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

func (tu *TU) AddSrcFile(fullPath string) FileId {
	// if the source file is already in the map, return the existing ID
	if id := tu.GetSrcFileId(fullPath); id != FileId(NIL_ID) {
		return id
	}

	// else, create a new source file entry
	fileId := FileId(tu.idGen.AllocateID(GenKindPrefix16(K_EK_ESRC_FILE, 0),
		K_EK_ESRC_FILE.SeqIdBitLen()))

	directory, fileName := filepath.Split(fullPath)

	tu.srcFilesInfo.files[fileId] = SrcFile{
		id:        fileId,
		name:      fileName,
		directory: directory,
	}

	tu.srcFilesInfo.fileIdMap[fullPath] = fileId
	return fileId
}

func (tu *TU) GetSrcFileId(fullPath string) FileId {
	if id, ok := tu.srcFilesInfo.fileIdMap[fullPath]; ok {
		return id
	}
	return FileId(NIL_ID)
}

func (tu *TU) GetFunctionById(id EntityId) *Function {
	if fun, ok := tu.functions[id]; ok {
		return fun
	}
	return nil
}

func (tu *TU) GenerateEntityId(eKind EntityKind) EntityId {
	return EntityId(tu.idGen.AllocateID(uint16(eKind), eKind.SeqIdBitLen()))
}
