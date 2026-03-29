/*
 * This file contains the functions to load and save SPIR protocol buffer files to and from memory.
 *
 * It has the following components:
 * 1. Functions to load SPIR protocol buffer files into memory and
 * make them available for further analysis.
 * 2. Functions to save SPIR protocol buffer files from memory to a file.
 */
package spir

import (
	"fmt"
	"io"
	"os"

	"github.com/adhuliya/span/pkg/logger"

	"google.golang.org/protobuf/proto"
)

func ReadSpirProto(filename string) (*BitTU, error) {
	bitTU, err := &BitTU{}, error(nil)

	// Open the file for reading
	file, openErr := os.Open(filename)
	if openErr != nil {
		err = openErr
		return nil, err
	}
	defer file.Close()

	// Read all contents of the file into memory
	fileData, readErr := io.ReadAll(file)
	if readErr != nil {
		err = readErr
		return nil, err
	}

	// Unmarshal Protobuf data into BitTU
	unmarshalErr := proto.Unmarshal(fileData, bitTU)
	if unmarshalErr != nil {
		err = unmarshalErr
		return nil, err
	}

	return bitTU, err
}

func WriteSpirProto(bitTU *BitTU, filename string) error {
	file, openErr := os.Create(filename)
	if openErr != nil {
		return openErr
	}
	defer file.Close()

	// Serialize BitTU
	serializedData, serializeErr := proto.Marshal(bitTU)
	if serializeErr != nil {
		return serializeErr
	}

	// Write serialized data to file
	_, writeErr := file.Write(serializedData)
	if writeErr != nil {
		return writeErr
	}
	return nil
}

func ConvertBitTUToInternalTU(bitTU *BitTU) *TU {
	tu := NewTU()

	// STEP 0: Populate the basic information for the translation unit.
	PopulateBasicInfo(tu, bitTU)

	// STEP 1: Populate the internal entity IDs for the translation unit.
	PopulateInternalEntityIds(tu, bitTU)

	// STEP 2: Populate the data types for the translation unit.
	PopulateTypesFromBitTU(tu, bitTU)

	// STEP 3: Populate the literals (including labels) for the translation unit.
	PopulateLiterals(tu, bitTU)

	// STEP 4: Populate the global and local variables for the translation unit.
	PopulateVariables(tu, bitTU)

	// // STEP 5: Populate the functions for the translation unit.
	PopulateFunctions(tu, bitTU)

	return tu
}

func PopulateBasicInfo(tu *TU, bitTU *BitTU) {
	tu.tuName = bitTU.TuName
	if bitTU.AbsPath != nil {
		tu.tuAbspath = *bitTU.AbsPath
	}
	if bitTU.Origin != nil {
		tu.origin = *bitTU.Origin
	}
}

func FetchNameFromBitEntityId(bitTU *BitTU, eid uint64) string {
	name := ""
	// ATTEMPT 1: Try to find the name in the EntityInfo map.
	entityInfo, ok := bitTU.EntityInfo[eid]
	if ok {
		if entityInfo.StrVal != nil {
			name = *entityInfo.StrVal
		}
	}

	// ATTEMPT 2: Try to find the name in the DataTypes map.
	if name == "" {
		dataType, ok := bitTU.DataTypes[eid]
		if ok {
			if dataType.TypeName != nil {
				name = *dataType.TypeName
			}
		}
	}

	return name
}

// PopulateInternalEntityIds populates the internal entity IDs for the translation unit.
// It reads the entity information from the bit TU and populates the internal entity IDs for the translation unit.
func PopulateInternalEntityIds(tu *TU, bitTU *BitTU) {
	// 1. Convert all BitEntityInfo entity ids to internal entity ids.
	for eid, entityInfo := range bitTU.EntityInfo {
		if eid != entityInfo.Eid {
			logger.Get().Error("entity ID mismatch", "map key", eid, "EntityInfo.Eid", entityInfo.Eid)
		}
		internalEid := CreateInternalEntityIdFromBitEntityInfo(tu, entityInfo)
		tu.entityIdMap[eid] = internalEid
	}

	// 2. Convert all BitDataType entity ids to internal entity ids.
	for eid, dataType := range bitTU.DataTypes {
		if eid != dataType.TypeId {
			logger.Get().Error("entity ID mismatch", "map key", eid, "BitDataType.TypeId", dataType.TypeId)
		}
		if tu.InternalEntityIdExists(eid) {
			// Entity id already exists: Skip it. (possible for functions)
			continue
		}
		internalEid := CreateInternalEntityIdFromBitDataType(tu, dataType)
		tu.entityIdMap[eid] = internalEid
	}
}

// CreateInternalEntityIdFromBitEntityInfo creates an internal entity ID for the translation unit.
// It only uses the entity kind and sub-kind (vkind) to create the internal entity ID.
func CreateInternalEntityIdFromBitEntityInfo(tu *TU, bitEntityInfo *BitEntityInfo) EntityId {
	prefix16 := GetEntityPrefix16FromBitEntityInfo(bitEntityInfo)
	id := tu.idGen.AllocateID(prefix16, bitEntityInfo.Ekind.SeqIdBitLen())
	return EntityId(id)
}

// GetEntityPrefix16FromBitEntityInfo gets the prefix16 for the entity.
// It uses the entity kind and sub-kind (vkind) to create the prefix16.
func GetEntityPrefix16FromBitEntityInfo(bitEntityInfo *BitEntityInfo) uint16 {
	return GenKindPrefix16(bitEntityInfo.Ekind, uint8(bitEntityInfo.Vkind))
}

func CreateInternalEntityIdFromBitDataType(tu *TU, bitDataType *BitDataType) EntityId {
	prefix16 := GetEntityPrefix16FromBitDataType(bitDataType)
	id := tu.idGen.AllocateID(prefix16, K_EK_EDATA_TYPE.SeqIdBitLen())
	return EntityId(id)
}

func GetEntityPrefix16FromBitDataType(bitDataType *BitDataType) uint16 {
	return GenKindPrefix16(K_EK_EDATA_TYPE, uint8(bitDataType.Vkind))
}

// PopulateTypesFromBitTU populates the value types for the translation unit.
// It reads the entity information from the bit TU and populates the value types for the in-memory TU.
func PopulateTypesFromBitTU(tu *TU, bitTU *BitTU) {
	for eid, entityInfo := range bitTU.EntityInfo {
		internalEid := tu.GetInternalEntityId(eid)
		// Convert if it is a data type and create a QualType for it.
		if entityInfo.Ekind.IsDataType() {
			tu.qualTypes[internalEid] = CreateQualTypeFromBitEntityId(tu, bitTU, eid)
		}
	}

	for eid := range bitTU.DataTypes {
		internalEid := tu.GetInternalEntityId(eid)
		tu.qualTypes[internalEid] = CreateQualTypeFromBitDataType(tu, bitTU, eid)
	}
}

// CreateQualTypeFromBitEntityId creates a QualType from a bit entity id if it is a data type.
func CreateQualTypeFromBitEntityId(tu *TU, bitTU *BitTU, eid uint64) QualType {
	// ATTEMPT 0: If it is already created, return the existing value type.
	internalEid := tu.GetInternalEntityId(eid)
	if _, ok := tu.qualTypes[internalEid]; ok {
		// Already created? Return the existing value type.
		return tu.qualTypes[internalEid]
	}

	// ATTEMPT 1: First try to find eid in EntityInfo map.
	// If it has a DataTypeEid, then create a QualType from that.
	// If it has qualifiers, then return the QualType with the qualifiers.
	// If it has no DataTypeEid, then panic.
	beInfo, ok := bitTU.EntityInfo[eid]
	if ok {
		if beInfo.DataTypeEid != nil {
			qt := CreateQualTypeFromBitDataType(tu, bitTU, *beInfo.DataTypeEid)
			if beInfo.Qtype != nil {
				qt = NewQualVT(qt.GetVT(), QualBits(*beInfo.Qtype))
			}
			tu.qualTypes[internalEid] = qt
			return qt
		}
		if beInfo.Ekind == K_EK_EDATA_TYPE {
			logger.Get().Error("entity info found but no DataTypeEid is present", "entity ID", eid)
			tu.qualTypes[internalEid] = nil
			return nil
		}
	}

	// ATTEMPT 2: Try to find eid in DataTypes map.
	_, ok = bitTU.DataTypes[eid]
	if ok {
		return CreateQualTypeFromBitDataType(tu, bitTU, eid)
	}

	// If we reach here, then the entity id is not found in the EntityInfo or DataTypes maps.
	logger.Get().Error("entity id not found in EntityInfo or DataTypes maps", "entity ID", eid)
	return nil
}

func CreateQualTypeFromBitDataType(tu *TU, bitTU *BitTU, eid uint64) QualType {
	// ATTEMPT 0: If it is already created, return the existing value type.
	internalEid := tu.GetInternalEntityId(eid)
	if _, ok := tu.qualTypes[internalEid]; ok {
		// Already created? Return the existing value type.
		return tu.qualTypes[internalEid]
	}

	bdt, ok := bitTU.DataTypes[eid]
	if !ok {
		logger.Get().Error("data type not found in DataTypes map", "entity ID", eid)
		return nil
	}

	// Create the value type based on the value kind.
	vkind := bdt.Vkind
	qt := QualType(nil)
	switch {
	case vkind.IsBasic():
		qt = CreateBasicQualTypeFromBitDataType(tu, bitTU, eid)
	case vkind.IsPointer():
		qt = CreatePointerQualTypeFromBitDataType(tu, bitTU, eid)
	case vkind.IsArray():
		qt = CreateArrayQualTypeFromBitDataType(tu, bitTU, eid)
	case vkind.IsRecord():
		qt = CreateRecordOrUnionQualTypeFromBitDataType(tu, bitTU, eid)
	case vkind.IsFunction():
		qt = CreateFunctionQualTypeFromBitDataType(tu, bitTU, eid)
	default:
		logger.Get().Error("unknown value kind", "value kind", vkind, "bit entity", eid)
	}
	tu.qualTypes[internalEid] = qt
	return qt
}

func CreateBasicQualTypeFromBitDataType(tu *TU, bitTU *BitTU, eid uint64) QualType {
	btd, ok := bitTU.DataTypes[eid]
	if !ok {
		logger.Get().Error("basic value type not found", "entity ID", eid)
		return nil
	}

	basicVT := &BasicVT{}
	FillBasicVTFromBitDataType(basicVT, btd)
	return NewQualVT(basicVT, QualBits(0))
}

func FillBasicVTFromBitDataType(basicVT *BasicVT, btd *BitDataType) {
	// Get the size and alignment for the basic value type
	size := VTSize(0)
	if btd.Len != nil {
		size = VTSize(*btd.Len)
	}
	align := VTAlign(0)
	if btd.Align != nil {
		align = VTAlign(*btd.Align)
	}

	basicVT.kind = btd.Vkind
	basicVT.size = size
	basicVT.align = align
}

func CreatePointerQualTypeFromBitDataType(tu *TU, bitTU *BitTU, eid uint64) QualType {
	btd, ok := bitTU.DataTypes[eid]
	if !ok {
		logger.Get().Error("pointer value type not found", "entity ID", eid)
		return nil
	}

	subTypeEid := uint64(0)
	if btd.SubTypeEid != nil {
		subTypeEid = *btd.SubTypeEid
	}

	pointerVT := &PointerVT{}
	FillBasicVTFromBitDataType(&pointerVT.BasicVT, btd)
	pointerVT.pointee = CreateQualTypeFromBitDataType(tu, bitTU, subTypeEid)
	return NewQualVT(pointerVT, QualBits(0))
}

func CreateArrayQualTypeFromBitDataType(tu *TU, bitTU *BitTU, eid uint64) QualType {
	btd, ok := bitTU.DataTypes[eid]
	if !ok {
		logger.Get().Error("array value type not found", "entity ID", eid)
		return nil
	}

	subTypeEid := uint64(0)
	if btd.SubTypeEid != nil {
		subTypeEid = *btd.SubTypeEid
	}

	arrayVT := &ArrayVT{}
	FillBasicVTFromBitDataType(&arrayVT.BasicVT, btd)
	arrayVT.elemVT = CreateQualTypeFromBitDataType(tu, bitTU, subTypeEid)
	return NewQualVT(arrayVT, QualBits(0))
}

func CreateRecordOrUnionQualTypeFromBitDataType(tu *TU, bitTU *BitTU, eid uint64) QualType {
	btd, ok := bitTU.DataTypes[eid]
	if !ok {
		logger.Get().Error("record or union value type not found", "entity ID", eid)
		return nil
	}

	recordVT := &RecordVT{}
	// STEP 1: Fill the name and basic value type.
	FillBasicVTFromBitDataType(&recordVT.BasicVT, btd)
	if btd.TypeName != nil {
		recordVT.name = *btd.TypeName
		tu.idsToName[tu.GetInternalEntityId(eid)] = recordVT.name
	}

	// STEP 2: Fill the members
	recordVT.members = make(map[string]QualType)

	// Check if FopIds and FopTypeIds are present and have the same length
	if btd.FopIds != nil && btd.FopTypeEids != nil {
		if len(btd.FopIds) != len(btd.FopTypeEids) {
			logger.Get().Error("number of fopIds and fopTypeEids do not match", "entity ID", eid)
			return nil
		}
		for i, fopId := range btd.FopIds {
			fopTypeId := btd.FopTypeEids[i]

			// Attempt to get member name from EntityInfo in bitTU using the field (fopId)
			memberName := FetchNameFromBitEntityId(bitTU, fopId)

			// Get the member type using CreateQualTypeFromBitEntityId
			memberType := CreateQualTypeFromBitEntityId(tu, bitTU, fopTypeId)
			recordVT.members[memberName] = memberType
		}
	}

	return NewQualVT(recordVT, QualBits(0))
}

func PopulateLiterals(tu *TU, bitTU *BitTU) {
	for eid, entityInfo := range bitTU.EntityInfo {
		if entityInfo.Ekind.IsLiteral() {
			literal := CreateLiteralFromBitEntityInfo(tu, bitTU, eid)
			tu.literals[tu.GetInternalEntityId(eid)] = literal
			tu.idsToName[tu.GetInternalEntityId(eid)] = literal.ValueString()
		} else if entityInfo.Ekind.IsLabel() {
			label := CreateLabelFromBitEntityInfo(tu, bitTU, eid)
			tu.labels[LabelId(tu.GetInternalEntityId(eid))] = label
			logger.Get().Info("created label", "label", label, "entity ID", eid, "internal entity ID", tu.GetInternalEntityId(eid))
			tu.idsToName[tu.GetInternalEntityId(eid)] = label
		}
	}
}

func CreateLabelFromBitEntityInfo(tu *TU, bitTU *BitTU, eid uint64) string {
	logger.Get().Info("creating label from bit entity info", "entity ID", eid)
	internalEid := tu.GetInternalEntityId(eid)
	labelId := LabelId(internalEid)
	if _, ok := tu.labels[labelId]; ok {
		return tu.labels[labelId]
	}

	beInfo, ok := bitTU.EntityInfo[eid]
	if !ok {
		logger.Get().Error("entity info not found", "entity ID", eid)
		return fmt.Sprintf("error:label_%d", eid)
	}

	if beInfo.StrVal == nil {
		logger.Get().Error("label name not found", "entity ID", eid)
		return fmt.Sprintf("label_%d", eid)
	}

	return *beInfo.StrVal
}

func CreateLiteralFromBitEntityInfo(tu *TU, bitTU *BitTU, eid uint64) *LiteralInfo {
	internalEid := tu.GetInternalEntityId(eid)
	if _, ok := tu.literals[internalEid]; ok {
		return tu.literals[internalEid]
	}

	beInfo, ok := bitTU.EntityInfo[eid]
	if !ok {
		logger.Get().Error("entity info not found", "entity ID", eid)
		return nil
	}

	dataTypeEid := uint64(0)
	if beInfo.DataTypeEid != nil {
		dataTypeEid = *beInfo.DataTypeEid
	}

	literal := &LiteralInfo{}
	if dataTypeEid == 0 {
		literal.qualType = NewQualVT(NewBasicVT(beInfo.Vkind), QualBits(0))
	} else {
		literal.qualType = CreateQualTypeFromBitEntityId(tu, bitTU, dataTypeEid)
	}

	if beInfo.LowVal != nil {
		literal.lowVal = *beInfo.LowVal
	}

	if beInfo.HighVal != nil {
		literal.highVal = *beInfo.HighVal
	}

	if beInfo.StrVal != nil {
		literal.strVal = *beInfo.StrVal
	}

	if imm, ok := literal.IsImmediateInt20(); ok {
		prefix := GenKindPrefix16(K_EK_ELIT_NUM_IMM, uint8(literal.qualType.GetVT().GetKind()))
		immEid := uint32(prefix)<<K_EK_ELIT_NUM_IMM.SeqIdBitLen() | uint32(imm&ImmConstMask32)
		tu.entityIdMap[eid] = EntityId(immEid)
	}
	return literal
}

func CreateFunctionQualTypeFromBitDataType(tu *TU, bitTU *BitTU, eid uint64) QualType {
	btd, ok := bitTU.DataTypes[eid]
	if !ok {
		logger.Get().Error("function value type not found", "entity ID", eid)
		return nil
	}

	funcVT := &FunctionVT{}
	FillBasicVTFromBitDataType(&funcVT.BasicVT, btd)

	if btd.SubTypeEid != nil {
		funcVT.returnType = CreateQualTypeFromBitEntityId(tu, bitTU, *btd.SubTypeEid)
	}

	// Check if FopIds and FopTypeIds are present and have the same length
	if btd.FopIds != nil && btd.FopTypeEids != nil {
		if len(btd.FopIds) != len(btd.FopTypeEids) {
			logger.Get().Error("number of fopIds and fopTypeEids do not match", "entity ID", eid)
			return nil
		}
		for i, fopId := range btd.FopIds {
			fopTypeId := btd.FopTypeEids[i]

			paramType := CreateQualTypeFromBitEntityId(tu, bitTU, fopTypeId)
			funcVT.paramIds = append(funcVT.paramIds, tu.GetInternalEntityId(fopId))
			funcVT.paramTypes = append(funcVT.paramTypes, paramType)
		}
	}

	if btd.Variadic != nil && *btd.Variadic {
		funcVT.varArgs = true
	}

	return NewQualVT(funcVT, QualBits(0))
}

func PopulateVariables(tu *TU, bitTU *BitTU) {
	for eid, entityInfo := range bitTU.EntityInfo {
		if entityInfo.Ekind.IsVariable() {
			variable := CreateValueInfoFromBitEntityId(tu, bitTU, eid)
			tu.variables[tu.GetInternalEntityId(eid)] = variable
			tu.idsToName[tu.GetInternalEntityId(eid)] = variable.name
		}
	}
}

// Create the variables and their information from the bit TU.
func CreateValueInfoFromBitEntityId(tu *TU, bitTU *BitTU, eid uint64) *ValueInfo {
	// STEP 0: If it is already created, return the existing value info.
	internalEid := tu.GetInternalEntityId(eid)
	if _, ok := tu.variables[internalEid]; ok {
		return tu.variables[internalEid]
	}

	beInfo, ok := bitTU.EntityInfo[eid]
	if !ok {
		logger.Get().Error("entity info not found", "entity ID", eid)
		return nil
	}

	valueInfo := &ValueInfo{}
	valueInfo.eid = internalEid

	if beInfo.ParentEid != nil {
		valueInfo.parentId = tu.GetInternalEntityId(*beInfo.ParentEid)
	}
	valueInfo.qualType = CreateQualTypeFromBitEntityId(tu, bitTU, eid)
	valueInfo.name = FetchNameFromBitEntityId(bitTU, eid)

	return valueInfo
}

func PopulateFunctions(tu *TU, bitTU *BitTU) {
	logger.Get().Info("populating functions", "number of current functions", len(tu.functions))
	for _, function := range bitTU.Functions {
		funcInfo := CreateFunctionFromBitFunc(tu, bitTU, function)
		logger.Get().Info("creating function from bit func",
			"bit func", function.GetFname(), "fid", function.Fid, "internal function id", funcInfo.Id())
		tu.functions[funcInfo.Id()] = funcInfo
	}
	logger.Get().Info("populated functions", "number of functions", len(tu.functions))
}

func CreateFunctionFromBitFunc(tu *TU, bitTU *BitTU, bitFunc *BitFunc) *Function {
	function := &Function{}
	if bitFunc.Fid == K_00_GLBL_INIT_FUNC_ID {
		function.fid = tu.GlobalInitFuncId()
	} else {
		function.fid = tu.GetInternalEntityId(bitFunc.Fid)
	}
	function.fName = bitFunc.Fname
	tu.idsToName[function.fid] = function.fName
	function.originTU, function.owningTU = tu, tu
	function.funcType = CreateQualTypeFromBitEntityId(tu, bitTU, bitFunc.TypeEid)

	if bitFunc.IsVariadic {
		function.funcType.GetVT().(*FunctionVT).varArgs = bitFunc.IsVariadic
	}

	if bitFunc.CallingConvention != nil {
		function.funcType.GetVT().(*FunctionVT).callingConvention = *bitFunc.CallingConvention
	}

	if bitFunc.Insns != nil {
		function.insns = make([]Insn, len(bitFunc.Insns))
		for i, insn := range bitFunc.Insns {
			function.insns[i] = CreateInsnFromBitInsn(tu, bitTU, insn)
		}
	}

	return function
}

func CreateInsnFromBitInsn(tu *TU, bitTU *BitTU, bitInsn *BitInsn) Insn {
	expr1, expr2 := NIL_X, NIL_X
	if bitInsn.Expr1 != nil {
		expr1 = CreateExprFromBitExpr(tu, bitTU, bitInsn.Expr1)
	}
	if bitInsn.Expr2 != nil {
		expr2 = CreateExprFromBitExpr(tu, bitTU, bitInsn.Expr2)
	}

	switch bitInsn.Ikind {
	case K_IK_IRETURN:
		return ReturnI(expr1)
	case K_IK_INOP:
		return NopI()
	case K_IK_IBARRIER:
		return BarrierI()
	case K_IK_ISELECT:
		panic("ISELECT is not supported yet")
	case K_IK_ICALL:
		return CallI(expr1)
	case K_IK_IASGN_SIMPLE:
		return AssignI(expr1, expr2)
	case K_IK_IASGN_RHS_OP:
		return AssignI(expr1, expr2)
	case K_IK_IASGN_LHS_OP:
		return AssignI(expr1, expr2)
	case K_IK_IASGN_CALL:
		return AssignI(expr1, expr2)
	case K_IK_IASGN_PHI:
		panic("IASGN_PHI is not supported yet")
	case K_IK_ILABEL:
		return LabelI(expr1)
	case K_IK_IGOTO:
		return GotoI(expr1)
	case K_IK_ICOND:
		return IfI(expr1, expr2)
	}
	return NopI()
}

func CreateExprFromBitExpr(tu *TU, bitTU *BitTU, bitExpr *BitExpr) Expr {
	logger.Get().Info("creating expression from bit expr", "bit expr", bitExpr)
	expr := placeXK(bitExpr.Xkind)
	// Handle Call expressions.
	if bitExpr.Xkind.IsCall() {
		callSiteId := tu.NewCallSiteId()
		expr |= placeCallSiteId(callSiteId)
		if bitExpr.Oprnd1Eid != nil {
			expr |= placeCallee(tu.GetInternalEntityId(*bitExpr.Oprnd1Eid))
		}
		if bitExpr.Oprnds != nil {
			for _, oprndEid := range bitExpr.Oprnds {
				tu.callSites[callSiteId] = append(tu.callSites[callSiteId], tu.GetInternalEntityId(oprndEid))
			}
		}
		return Expr(expr)
	}

	// Handle other expressions (unary, binary, etc.).
	if bitExpr.Oprnd1Eid != nil {
		expr |= placeExprOpr1(tu.GetInternalEntityId(*bitExpr.Oprnd1Eid))
	}
	if bitExpr.Oprnd2Eid != nil {
		expr |= placeExprOpr2(tu.GetInternalEntityId(*bitExpr.Oprnd2Eid))
	}
	return Expr(expr)
}
