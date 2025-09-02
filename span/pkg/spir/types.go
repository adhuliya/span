package spir

import "fmt"

// This file contains the data types used in the SPAN program analysis engine.

// ValKind is an integer type that represents the kind of a value type.
// It is an integer type in the range of 0 to 31 (5 bits).
type ValKind = K_VK

type VTSize uint32 // Size in bytes of the value type
type VTAlign uint8 // Alignment in bytes of the value type

// QualType is an encoded integer that represents the qualified type of a value.
// It is a set of bits that represent types qualified with volatile, const, static, etc.
type QualType = K_QK

type RecordId EntityId

const VKMask uint32 = 0x1F            // Mask to get the ValKind bits
const VKPosMask32 uint32 = 0x1F0_0000 // Mask to get the ValKind bits positioned in uint32
const VKShift32 uint32 = 20           // Shift to get the ValKind bits positioned in uint32

type ValueType interface {
	GetType() ValKind
	GetQType() QualType
	GetSize() VTSize
	GetAlign() VTAlign
}

type BaseVT struct {
	size  VTSize
	qtype QualType
	kind  ValKind
	align VTAlign
}

type PointerVT struct {
	BaseVT
	pointeeVT ValueType
}

type RecordVT struct {
	BaseVT
	name    string
	members map[string]ValueType
	srcLoc  *SrcLoc
}

type FunctionVT struct {
	BaseVT
	name       string
	returnType ValueType
	paramTypes []ValueType
	paramNames []string
	varArgs    bool
}

// VarArgsVT can be used to declare functions with variable args.
type VarArgsVT struct {
	BaseVT
	elemVT ValueType
}

type ArrayVT struct {
	BaseVT
	elemVT ValueType
	size   VTSize
}

func (v *BaseVT) GetQType() QualType {
	return v.qtype
}

func (v *BaseVT) GetType() ValKind {
	return v.kind
}

func (v *BaseVT) GetSize() VTSize {
	return v.size
}

func (v *BaseVT) GetAlign() VTAlign {
	return v.align
}

func newBaseVT(kind ValKind, qtype QualType, size VTSize, align VTAlign) BaseVT {
	return BaseVT{
		qtype: qtype,
		kind:  kind,
		size:  size,
		align: align,
	}
}

// Create simple unit types with default size and alignment.
func NewBasicVT(kind ValKind, qtype QualType) BaseVT {
	if (kind.IsInteger() && kind != K_VK_N_BITS && kind != K_VK_N_UBITS) || kind.IsFloating() || kind == K_VK_VOID {
		return BaseVT{
			qtype: qtype,
			kind:  kind,
			size:  kind.SizeInBytes(),
			align: kind.MinAlignInBytes(),
		}
	}

	panic(fmt.Sprintf("Value kind VT cannot be created: %v", kind))
}

func (kind ValKind) IsFloating() bool {
	return kind >= K_VK_FLOAT16 && kind <= K_VK_DOUBLE
}

func (kind ValKind) IsVoid() bool {
	return kind == K_VK_VOID
}

func (kind ValKind) IsInteger() bool {
	return kind <= K_VK_BOOL && kind >= K_VK_CHAR
}

func (kind ValKind) IsPointer() bool {
	return kind >= K_VK_PTR_TO_VOID && kind <= K_VK_PTR_TO_FUNC
}

func (kind ValKind) IsArray() bool {
	return kind >= K_VK_ARR_FIXED && kind <= K_VK_ARR_PARTIAL
}

func (kind ValKind) IsArrOrPtr() bool {
	return kind.IsArray() || kind.IsPointer()
}

func (kind ValKind) SizeInBytes() VTSize {
	switch kind {
	case K_VK_VOID:
		return 0
	case K_VK_BOOL:
		return 1
	case K_VK_CHAR: // K_VK_UCHAR == K_VK_UINT8
		return 1
	case K_VK_INT8, K_VK_UINT8:
		return 1
	case K_VK_INT16, K_VK_UINT16:
		return 2
	case K_VK_INT32, K_VK_UINT32:
		return 4
	case K_VK_INT64, K_VK_UINT64:
		return 8
	case K_VK_FLOAT32:
		return 4
	case K_VK_FLOAT64:
		return 8
	}

	if kind.IsPointer() {
		return 8 // Assuming 64-bit pointers
	}

	return 0 // All other types are unknown or 0-size by default
}

func (kind ValKind) MinAlignInBytes() VTAlign {
	switch kind {
	case K_VK_VOID:
		return 0
	case K_VK_BOOL:
		return 1
	case K_VK_CHAR: // K_VK_UCHAR == K_VK_UINT8
		return 1
	case K_VK_INT8, K_VK_UINT8:
		return 1
	case K_VK_INT16, K_VK_UINT16:
		return 2
	case K_VK_INT32, K_VK_UINT32:
		return 4
	case K_VK_INT64, K_VK_UINT64:
		return 8
	case K_VK_FLOAT32:
		return 4
	case K_VK_FLOAT64:
		return 8
	}

	if kind.IsPointer() {
		return 8 // Assuming 64-bit pointers
	}

	return 0 // All other types are unknown or 0-aligned by default
}

// Common base value types used in C
var (
	VoidVT   = NewBasicVT(K_VK_VOID, K_QK_QNONE)
	BoolVT   = NewBasicVT(K_VK_BOOL, K_QK_QNONE)
	CharVT   = NewBasicVT(K_VK_CHAR, K_QK_QNONE)
	Int8VT   = NewBasicVT(K_VK_INT8, K_QK_QNONE)
	Int16VT  = NewBasicVT(K_VK_INT16, K_QK_QNONE)
	Int32VT  = NewBasicVT(K_VK_INT32, K_QK_QNONE)
	Int64VT  = NewBasicVT(K_VK_INT64, K_QK_QNONE)
	Uint8VT  = NewBasicVT(K_VK_UINT8, K_QK_QNONE)
	Uint16VT = NewBasicVT(K_VK_UINT16, K_QK_QNONE)
	Uint32VT = NewBasicVT(K_VK_UINT32, K_QK_QNONE)
	Uint64VT = NewBasicVT(K_VK_UINT64, K_QK_QNONE)
	FloatVT  = NewBasicVT(K_VK_FLOAT32, K_QK_QNONE)
	DoubleVT = NewBasicVT(K_VK_FLOAT64, K_QK_QNONE)
)
