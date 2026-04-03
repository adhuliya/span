package spir

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/adhuliya/span/pkg/idgen"
)

// This file defines the TranslationUnit type.
// The TranslationUnit type is used to represent a single SPAN IR translation unit.
// It is a container for all the entities and instructions which make up a program.

// Info associated with a literal value.
type LiteralInfo struct {
	qualType QualType
	lowVal   uint64
	highVal  uint64
	strVal   string
}

func (li *LiteralInfo) String() string {
	return fmt.Sprintf("LiteralInfo(lowVal=%v, highVal=%v, strVal=%v, qualType=%v)",
		li.lowVal, li.highVal, li.strVal, li.qualType)
}

func (li *LiteralInfo) ValueString() string {
	if li.strVal != "" {
		return li.strVal
	}
	if li.highVal != 0 {
		return fmt.Sprintf("%d %d", li.highVal, li.lowVal)
	}
	return fmt.Sprintf("%d", li.lowVal)
}

// IsImmediateInt20 returns the immediate value as int32 if it fits in 20 bits (signed), else returns false.
//
// This checks if 'lowVal' can be precisely represented as a signed 20-bit value:
// Range: -2^19..2^19-1, i.e., [-524288, 524287]
func (li *LiteralInfo) IsImmediateInt20() (int32, bool) {
	// Consider only LowVal, as per the context for immediates
	val := int64(li.lowVal)
	// If strVal is set, treat as not immediate (string-based literal)
	if li.strVal != "" || li.highVal != 0 {
		return 0, false
	}

	nbits := 20
	vkind := li.qualType.GetVT().GetKind()
	if vkind.IsSingedInteger() {
		tmp := int64((val << (64 - nbits)) >> (64 - nbits))
		if tmp != val {
			return 0, false
		}
		return int32(tmp), true
	} else {
		if vkind.IsBasic() {
			tmp := li.lowVal & ImmConstMask64
			if tmp != li.lowVal {
				return 0, false
			}
			return int32(tmp), true
		}
		return 0, false
	}
}

type ValueInfo struct {
	name     string
	eid      EntityId
	parentId EntityId // Id of the parent (a function or a record)
	qualType QualType
}

func (vi *ValueInfo) String() string {
	return fmt.Sprintf("ValueInfo(name=%v, eid=%v, parentId=%v, qualType=%v)",
		vi.name, vi.eid, vi.parentId, vi.qualType)
}

// Function represents a function in the SPAN IR.
// A special global initialization function is used to initialize global variables.
type Function struct {
	fid      EntityId // The function ID
	fName    string   // The function name
	originTU *TU      // The TU that the function was originally from
	owningTU *TU      // The TU that the function belongs to
	funcType QualType
	paramIds []EntityId

	// The sequence of instructions in the function.
	// It should contain a list of instructions with appropriate labels
	// and jumps to allow construction of a CFG graph.
	insns []Insn // This is only populated for debugging purposes
	body  Graph  // The CFG of the function
}

func (fun *Function) String() string {
	// String returns a nicely formatted string with function info and its instructions.
	funcInfo := fmt.Sprintf(
		"Function Info:\n"+
			"    %-12s: %v\n"+
			"    %-12s: %v\n"+
			"    %-12s: %v\n"+
			"    %-12s: %v\n"+
			"    %-12s: %v",
		"fid", fun.fid,
		"name", fun.fName,
		"type", fun.funcType,
		"params", fun.paramIds,
		"origin TU", func() string {
			if fun.originTU != nil {
				return fun.originTU.tuName
			}
			return "<nil>"
		}(),
	)

	// Print the instructions, each on a new line, indented by 4 spaces.
	insnsStr := ""
	if len(fun.insns) > 0 {
		var sb strings.Builder
		sb.WriteString("\n    Instructions:\n")
		for _, insn := range fun.insns {
			fmt.Fprintf(&sb, "        %s\n", fun.owningTU.InsnString(insn, false))
		}
		insnsStr += sb.String()
	} else {
		insnsStr += "\n    Instructions:\n    <none>"
	}

	return funcInfo + insnsStr
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
	qualTypes  map[EntityId]QualType   // Holds complete value type information
	variables  map[EntityId]*ValueInfo // Holds information about variables
	literals   map[EntityId]*LiteralInfo
	functions  map[EntityId]*Function
	callSites  map[CallSiteId][]EntityId // Arguments for a call site
	labels     map[LabelId]string
	globalInit EntityId // A special function with one basic block with all the initialization of global variables.

	// 4. Meta information about the TU
	namesToId    map[string]EntityId // Necessary for name lookup during linking
	idsToName    map[EntityId]string // Useful for quick pretty printing
	entityInfo   map[EntityId]any    // For scratch use
	insnInfo     map[InsnId]InsnInfo // For information on an instruction
	idGen        *idgen.IDGenerator
	srcFilesInfo *SrcFilesInfo
	srcLocations map[EntityId]SrcLoc

	// 5. Temporary Information
	// This map is used to map a bit entity id to an internal entity id.
	entityIdMap map[uint64]EntityId
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
		literals:     make(map[EntityId]*LiteralInfo),
		qualTypes:    make(map[EntityId]QualType),
		insnInfo:     make(map[InsnId]InsnInfo),
		callSites:    make(map[CallSiteId][]EntityId),
		labels:       make(map[LabelId]string),
		variables:    make(map[EntityId]*ValueInfo),
		namesToId:    make(map[string]EntityId),
		idsToName:    make(map[EntityId]string),
		entityIdMap:  make(map[uint64]EntityId),
		idGen:        idgen.NewIDGenerator(),
		srcLocations: make(map[EntityId]SrcLoc),
		srcFilesInfo: NewSrcFilesInfo(),
	}

	tu.globalInit = tu.NewFunction(K_00_GLBL_INIT_FUNC_NAME,
		NewQualVT(NewFunctionVT(VoidQT, nil, nil, false, ""), K_QK_QNIL),
		nil, nil).Id()
	return tu
}

func NewValueInfo(name string, eid EntityId, parentId EntityId, qualType QualType) *ValueInfo {
	return &ValueInfo{
		name:     name,
		eid:      eid,
		parentId: parentId,
		qualType: qualType,
	}
}

func (tu *TU) GetUniqueLabelId() LabelId {
	return LabelId(tu.idGen.AllocateID(GenKindPrefix16(K_EK_ELABEL, 0),
		K_EK_ELABEL.SeqIdBitLen()))
}

func (tu *TU) NewCallSiteId() CallSiteId {
	return CallSiteId(tu.idGen.AllocateID(1, 25))
}

func (tu *TU) AddInsn(bb *BasicBlock, insn Insn, srcLoc *SrcLoc) {
	insnId := InsnId(tu.idGen.AllocateID(insn.GetInsnPrefix16(),
		K_EK_EINSN0.SeqIdBitLen()))
	tu.entityInfo[EntityId(insnId)] = &InsnInfo{bbId: bb.id, SrcLoc: *srcLoc}
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
func (tu *TU) NewVar(name string, eKind EntityKind, eid EntityId, parentId EntityId, vType QualType) EntityId {
	valInfo := NewValueInfo(name, eid, parentId, vType)
	id := tu.idGen.AllocateID(GenKindPrefix16(eKind, uint8(vType.GetVT().GetKind())),
		eKind.SeqIdBitLen())
	entityId := EntityId(id)
	valInfo.eid = entityId
	tu.namesToId[name] = entityId
	tu.idsToName[entityId] = name
	tu.variables[entityId] = valInfo
	return entityId
}

func (tu *TU) NewConst(val uint64, qType QualType) EntityId {
	imm, ok := GenImmediate20(val, qType.GetVT().GetKind())
	var id uint32 = 0
	if ok {
		eKind := K_EK_ELIT_NUM_IMM
		id = GenKindPrefix32(eKind, uint8(qType.GetVT().GetKind()))<<eKind.SeqIdBitLen() | uint32(imm)
	} else {
		eKind := K_EK_ELIT_NUM
		id = tu.idGen.AllocateID(GenKindPrefix16(eKind, uint8(qType.GetVT().GetKind())),
			eKind.SeqIdBitLen())
	}

	entityId := EntityId(id)
	tu.literals[entityId] = &LiteralInfo{
		qualType: qType,
		lowVal:   val,
		highVal:  0,
		strVal:   "",
	}
	return entityId
}

func (tu *TU) NewFunction(name string, funcType QualType,
	paramIds []EntityId, body Graph) *Function {
	vkind := funcType.GetVT().(*FunctionVT).returnType.GetVT().GetKind()
	id := EntityId(tu.idGen.AllocateID(GenKindPrefix16(K_EK_EFUNC, uint8(vkind)),
		K_EK_EFUNC.SeqIdBitLen()))

	fun := &Function{
		fid:      id,
		fName:    name,
		funcType: funcType,
		paramIds: paramIds,
		body:     body,
		insns:    nil,
	}

	tu.functions[id] = fun
	tu.namesToId[name] = EntityId(id)
	tu.entityInfo[EntityId(id)] = fun

	return fun
}

func (fun *Function) SetBody(tu *TU, insnSeq []Insn) {
	fun.body = ConstructCFG(insnSeq)
}

func (fun *Function) Id() EntityId {
	return fun.fid
}

func (fun *Function) Name() string {
	return fun.fName
}

func (fun *Function) Type() QualType {
	return fun.funcType
}

func (fun *Function) ParamIds() []EntityId {
	return fun.paramIds
}

func (fun *Function) Body() Graph {
	return fun.body
}

func (tu *TU) GlobalInitFuncId() EntityId {
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

func (tu *TU) GetInternalEntityId(eid uint64) EntityId {
	if eid == 0 || eid == 1 {
		return EntityId(eid) // Special case for global init function and nil entity id.
	}
	if id, ok := tu.entityIdMap[eid]; ok {
		return id
	}
	panic(fmt.Sprintf("Internal entity ID for %d not found in TU %s", eid, tu.tuName))
}

func (tu *TU) InternalEntityIdExists(eid uint64) bool {
	_, ok := tu.entityIdMap[eid]
	return ok
}

func (tu *TU) InsnString(insn Insn, short bool) string {
	exprStr := tu.ExprString
	entityName := tu.NameOfEntityId
	if short {
		exprStr = tu.ExprStringShort
		entityName = func(eid EntityId) string {
			return SimpleName(tu.NameOfEntityId(eid))
		}
	}

	kind := insn.InsnKind()
	switch kind {
	case K_IK_INIL:
		return "I(nil)"
	case K_IK_INOP:
		return "I(nop)"
	case K_IK_IBARRIER:
		return "I(barrier)"
	case K_IK_IRETURN:
		expr := insn.GetFirstHalfExpr()
		return fmt.Sprintf("return %s", exprStr(expr))
	case K_IK_IASGN_SIMPLE:
		lhs := insn.GetFirstHalfExpr()
		rhs := Expr(insn.secondHalf)
		return fmt.Sprintf("%s = %s", exprStr(lhs), exprStr(rhs))
	case K_IK_IASGN_CALL:
		lhs := insn.GetFirstHalfExpr()
		rhs := Expr(insn.secondHalf)
		return fmt.Sprintf("%s = %s", exprStr(lhs), exprStr(rhs))
	case K_IK_IASGN_RHS_OP:
		lhs := insn.GetFirstHalfExpr()
		rhs := Expr(insn.secondHalf)
		return fmt.Sprintf("%s = %s", exprStr(lhs), exprStr(rhs))
	case K_IK_IASGN_LHS_OP:
		rhs := insn.GetFirstHalfExpr()
		lhs := Expr(insn.secondHalf)
		return fmt.Sprintf("%s = %s", exprStr(lhs), exprStr(rhs))
	case K_IK_IASGN_PHI:
		lhs := insn.GetFirstHalfExpr()
		rhs := Expr(insn.secondHalf)
		return fmt.Sprintf("%s = φ(%s)", exprStr(lhs), exprStr(rhs))
	case K_IK_ICALL:
		expr := Expr(insn.secondHalf)
		return fmt.Sprintf("%s", exprStr(expr))
	case K_IK_ICOND:
		cond := insn.GetFirstHalfExpr()
		trueLabel := Expr(insn.secondHalf).GetOpr1()
		falseLabel := Expr(insn.secondHalf).GetOpr2()
		return fmt.Sprintf("if (%s) T:%s F:%s", exprStr(cond),
			entityName(trueLabel), entityName(falseLabel))
	case K_IK_IGOTO:
		label := LabelId(insn.firstHalf & FirstHalfExprMask64)
		return fmt.Sprintf("goto %s", entityName(EntityId(label)))
	case K_IK_ILABEL:
		eid := insn.GetFirstHalfEntityId()
		return fmt.Sprintf("%s:", entityName(eid))
	default:
		return fmt.Sprintf("0UNi(%s)", kind)
	}
}

func (tu *TU) ExprString(expr Expr) string {
	xk := expr.GetXK()
	opr1, opr2 := expr.GetOperands()
	if opr1 != NIL_ID && opr2 == NIL_ID {
		return fmt.Sprintf("((X) %s%s)", xk.OperatorString(), tu.NameOfEntityId(opr1))
	} else if opr1 != NIL_ID && opr2 != NIL_ID {
		return fmt.Sprintf("((X) %s %s %s)", xk.OperatorString(), tu.NameOfEntityId(opr1), tu.NameOfEntityId(opr2))
	}
	return expr.String()
}

func (tu *TU) ExprStringShort(expr Expr) string {
	xk := expr.GetXK()
	opr1, opr2 := expr.GetOperands()
	if opr1 != NIL_ID && opr2 == NIL_ID {
		return fmt.Sprintf("%s%s", xk.OperatorString(), SimpleName(tu.NameOfEntityId(opr1)))
	} else if opr1 != NIL_ID && opr2 != NIL_ID {
		return fmt.Sprintf("%s %s %s", SimpleName(tu.NameOfEntityId(opr1)),
			xk.OperatorString(), SimpleName(tu.NameOfEntityId(opr2)))
	}
	return expr.String() // return a raw expression string (with numeric ids...)
}

func (tu *TU) NameOfEntityId(eid EntityId) string {
	if name, ok := tu.idsToName[eid]; ok {
		return name
	}
	return fmt.Sprintf("0UNe(%s)", eid) // UNNAMED entity
}

func (tu *TU) Dump() {
	// Dump the basic information about the TU
	fmt.Println("========================================================")
	fmt.Println("======= Dumping TU: ", tu.tuName, "STARTED !!")
	fmt.Println("========================================================")
	fmt.Printf("%-12s %d\n", "TU ID:", tu.tuId)
	fmt.Printf("%-12s %s\n", "TU Name:", tu.tuName)
	fmt.Printf("%-12s %s\n", "TU Abspath:", tu.tuAbspath)
	fmt.Printf("%-12s %s\n", "Origin:", tu.origin)

	// Print the entity id map
	fmt.Println("--------------------------------")
	for eid, internalEid := range tu.entityIdMap {
		fmt.Printf("Entity Id: %-20d -> %s\n", eid, internalEid.String())
	}

	// Dump data types
	fmt.Println("--------------------------------")
	dumpDataTypes(tu)
	fmt.Println("--------------------------------")
	dumpLiterals(tu)
	fmt.Println("--------------------------------")
	dumpLabels(tu)
	fmt.Println("--------------------------------")
	dumpVariables(tu)
	fmt.Println("--------------------------------")
	dumpFunctions(tu)
	fmt.Println("========================================================")
	fmt.Println("======= Dumping TU: ", tu.tuName, "FINISHED !!")
	fmt.Println("========================================================")
}

func dumpDataTypes(tu *TU) {
	for eid, qualType := range tu.qualTypes {
		fmt.Println("Data Type:", eid, "-> QualType:", qualType)
	}
}

func dumpLiterals(tu *TU) {
	for eid, literal := range tu.literals {
		fmt.Println("Literal: ", eid, " type: ", ValKind(eid.SubKind()), "->", literal)
	}
}

func dumpVariables(tu *TU) {
	for eid, variable := range tu.variables {
		fmt.Println("Variable: ", eid, "->", variable, " type: ", ValKind(eid.SubKind()))
	}
}

func dumpFunctions(tu *TU) {
	for eid, function := range tu.functions {
		fmt.Println("Function: ", eid, "->", function)
		cfg := ConstructCFG(function.insns)
		fmt.Println("CFG:\n ", GenerateDotGraphForCFG(tu, cfg))
	}
}

func dumpLabels(tu *TU) {
	for labelId, label := range tu.labels {
		fmt.Println("Label: ", EntityId(labelId), "->", label)
	}
}
