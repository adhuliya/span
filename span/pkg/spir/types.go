package spir

import "fmt"

// This file contains the data types used in the SPAN program analysis engine.

// ValKind is an integer type that represents the kind of a value type.
// It is an integer type in the range of 0 to 31 (5 bits).
type ValKind = K_VK

type VTSize uint32 // Size in bits of the value type
type VTAlign uint8 // Alignment in bytes of the value type

// QualBits is an encoded integer that represents the qualified type of a value.
// It is a set of bits that represent types qualified with volatile, const, static, etc.
type QualBits = K_QK

type RecordId EntityId

const VKMask uint32 = 0x1F             // Mask to get the ValKind bits
const VKPosMask32 uint32 = 0x01F0_0000 // Mask to get the ValKind bits positioned in uint32
const VKShift32 uint32 = 20            // Shift to get the ValKind bits positioned in uint32

// A ValueType is a QualifiedType as well
type ValueType interface {
	GetKind() ValKind
	GetSize() VTSize
	GetAlign() VTAlign
	String() string
}

// A QualType has QualBits and a ValueType.
type QualType interface {
	GetQBits() QualBits
	GetVT() ValueType
	String() string
}

// A QualVT is a QualType with a ValueType.
type QualVT struct {
	vt    ValueType
	qBits QualBits
}

func (v QualVT) String() string {
	return fmt.Sprintf("QualVT(vt=%v, qBits=%v)", v.vt, v.qBits)
}

type BasicVT struct {
	size  VTSize
	kind  ValKind
	align VTAlign
}

func (v BasicVT) String() string {
	return fmt.Sprintf("BasicVT(kind=%v, size=%v, align=%v)", v.kind, v.size, v.align)
}

type PointerVT struct {
	BasicVT
	pointee QualType
}

func (v PointerVT) String() string {
	return fmt.Sprintf("PointerVT(pointee=%v, %v)", v.pointee, v.BasicVT)
}

type RecordVT struct {
	BasicVT
	name    string
	members map[string]QualType
	srcLoc  *SrcLoc
}

func (v RecordVT) String() string {
	return fmt.Sprintf("RecordVT(name=%v, members=%v, %v)", v.name, v.members, v.BasicVT)
}

type FunctionVT struct {
	BasicVT
	returnType        QualType
	paramIds          []EntityId
	paramTypes        []QualType
	varArgs           bool
	callingConvention string
}

func (v FunctionVT) String() string {
	return fmt.Sprintf("FunctionVT(returnType=%v, paramIds=%v, paramTypes=%v, varArgs=%v, callingConvention=%v, %v)", v.returnType, v.paramIds, v.paramTypes, v.varArgs, v.callingConvention, v.BasicVT)
}

func NewFunctionVT(returnType QualType, paramIds []EntityId,
	paramTypes []QualType, varArgs bool, callingConvention string) *FunctionVT {
	return &FunctionVT{
		returnType:        returnType,
		paramIds:          paramIds,
		paramTypes:        paramTypes,
		varArgs:           varArgs,
		callingConvention: callingConvention,
	}
}

// VarArgsVT can be used to declare functions with variable args.
// TODO: For future use.
type VarArgsVT struct {
	BasicVT
	elemVT QualType
}

type ArrayVT struct {
	BasicVT
	elemVT QualType
	// Size in number of bytes (not elements) of the array (known at compile time only)
	size VTSize
}

func (v BasicVT) GetKind() ValKind {
	return v.kind
}

func (v BasicVT) GetSize() VTSize {
	return v.size
}

func (v BasicVT) GetAlign() VTAlign {
	return v.align
}

// Create simple unit types with default size and alignment.
func NewBasicVT(kind ValKind) BasicVT {
	if (kind.IsInteger() && kind != K_VK_TN_BITS && kind != K_VK_TN_UBITS) || kind.IsFloating() || kind == K_VK_TVOID {
		return BasicVT{
			kind:  kind,
			size:  kind.SizeInBytes(),
			align: kind.MinAlignInBytes(),
		}
	}

	panic(fmt.Sprintf("Value kind VT cannot be created: %v", kind))
}

func NewQualVT(vt ValueType, qBits QualBits) *QualVT {
	return &QualVT{
		vt:    vt,
		qBits: qBits,
	}
}

func (v *QualVT) GetVT() ValueType {
	return v.vt
}

func (v *QualVT) GetQBits() QualBits {
	return v.qBits
}

func (kind ValKind) IsFloating() bool {
	return kind >= K_VK_TFLOAT16 && kind <= K_VK_TDOUBLE
}

func (kind ValKind) IsVoid() bool {
	return kind == K_VK_TVOID
}

func (kind ValKind) IsInteger() bool {
	return kind <= K_VK_TBOOL && kind >= K_VK_TCHAR
}

func (kind ValKind) IsPointer() bool {
	return kind >= K_VK_TPTR_TO_VOID && kind <= K_VK_TPTR_TO_FUNC
}

func (kind ValKind) IsArray() bool {
	return kind >= K_VK_TARR_FIXED && kind <= K_VK_TARR_PARTIAL
}

func (kind ValKind) IsBasic() bool {
	return kind >= K_VK_TCHAR && kind <= K_VK_TLONG_DOUBLE
}

func (kind ValKind) IsSingedInteger() bool {
	return kind >= K_VK_TINT8 && kind <= K_VK_TINT64
}

func (kind ValKind) IsRecordOrUnion() bool {
	return kind >= K_VK_TUNION && kind <= K_VK_TCLASS
}

func (kind ValKind) IsRecord() bool {
	return kind >= K_VK_TUNION && kind <= K_VK_TCLASS
}

func (kind ValKind) IsUnion() bool {
	return kind == K_VK_TUNION
}

func (kind ValKind) IsFunction() bool {
	return kind == K_VK_TPTR_TO_FUNC
}

func (kind ValKind) IsArrOrPtr() bool {
	return kind.IsArray() || kind.IsPointer()
}

func (kind ValKind) SizeInBytes() VTSize {
	switch kind {
	case K_VK_TVOID:
		return 0
	case K_VK_TBOOL:
		return 1
	case K_VK_TCHAR: // K_VK_TUCHAR == K_VK_TUINT8
		return 1
	case K_VK_TINT8, K_VK_TUINT8:
		return 1
	case K_VK_TINT16, K_VK_TUINT16:
		return 2
	case K_VK_TINT32, K_VK_TUINT32:
		return 4
	case K_VK_TINT64, K_VK_TUINT64:
		return 8
	case K_VK_TFLOAT32:
		return 4
	case K_VK_TFLOAT64:
		return 8
	}

	if kind.IsPointer() {
		return 8 // Assuming 64-bit pointers
	}

	return 0 // All other types are unknown or 0-size by default
}

func (kind ValKind) MinAlignInBytes() VTAlign {
	switch kind {
	case K_VK_TVOID:
		return 0
	case K_VK_TBOOL:
		return 1
	case K_VK_TCHAR: // K_VK_TUCHAR == K_VK_TUINT8
		return 1
	case K_VK_TINT8, K_VK_TUINT8:
		return 1
	case K_VK_TINT16, K_VK_TUINT16:
		return 2
	case K_VK_TINT32, K_VK_TUINT32:
		return 4
	case K_VK_TINT64, K_VK_TUINT64:
		return 8
	case K_VK_TFLOAT32:
		return 4
	case K_VK_TFLOAT64:
		return 8
	}

	if kind.IsPointer() {
		return 8 // Assuming 64-bit pointers
	}

	return 0 // All other types are unknown or 0-aligned by default
}

// Common base value types used in C
var (
	VoidVT   = NewBasicVT(K_VK_TVOID)
	BoolVT   = NewBasicVT(K_VK_TBOOL)
	CharVT   = NewBasicVT(K_VK_TCHAR)
	Int8VT   = NewBasicVT(K_VK_TINT8)
	Int16VT  = NewBasicVT(K_VK_TINT16)
	Int32VT  = NewBasicVT(K_VK_TINT32)
	Int64VT  = NewBasicVT(K_VK_TINT64)
	Uint8VT  = NewBasicVT(K_VK_TUINT8)
	Uint16VT = NewBasicVT(K_VK_TUINT16)
	Uint32VT = NewBasicVT(K_VK_TUINT32)
	Uint64VT = NewBasicVT(K_VK_TUINT64)
	FloatVT  = NewBasicVT(K_VK_TFLOAT32)
	DoubleVT = NewBasicVT(K_VK_TFLOAT64)

	VoidQT   = NewQualVT(&VoidVT, K_QK_QNIL)
	BoolQT   = NewQualVT(&BoolVT, K_QK_QNIL)
	CharQT   = NewQualVT(&CharVT, K_QK_QNIL)
	Int8QT   = NewQualVT(&Int8VT, K_QK_QNIL)
	Int16QT  = NewQualVT(&Int16VT, K_QK_QNIL)
	Int32QT  = NewQualVT(&Int32VT, K_QK_QNIL)
	Int64QT  = NewQualVT(&Int64VT, K_QK_QNIL)
	Uint8QT  = NewQualVT(&Uint8VT, K_QK_QNIL)
	Uint16QT = NewQualVT(&Uint16VT, K_QK_QNIL)
	Uint32QT = NewQualVT(&Uint32VT, K_QK_QNIL)
	Uint64QT = NewQualVT(&Uint64VT, K_QK_QNIL)
	FloatQT  = NewQualVT(&FloatVT, K_QK_QNIL)
	DoubleQT = NewQualVT(&DoubleVT, K_QK_QNIL)
)
