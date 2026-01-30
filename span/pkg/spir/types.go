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

const VKMask uint32 = 0x1F             // Mask to get the ValKind bits
const VKPosMask32 uint32 = 0x01F0_0000 // Mask to get the ValKind bits positioned in uint32
const VKShift32 uint32 = 20            // Shift to get the ValKind bits positioned in uint32

type ValueType interface {
	GetType() ValKind
	GetQType() QualType
	GetSize() VTSize
	GetAlign() VTAlign
}

type BasicVT struct {
	size  VTSize
	qtype QualType
	kind  ValKind
	align VTAlign
}

type PointerVT struct {
	BasicVT
	pointeeVT ValueType
}

type RecordVT struct {
	BasicVT
	name    string
	members map[string]ValueType
	srcLoc  *SrcLoc
}

type FunctionVT struct {
	BasicVT
	name       string
	returnType ValueType
	paramTypes []ValueType
	paramNames []string
	varArgs    bool
}

// VarArgsVT can be used to declare functions with variable args.
// TODO: For future use.
type VarArgsVT struct {
	BasicVT
	elemVT ValueType
}

type ArrayVT struct {
	BasicVT
	elemVT ValueType
	// Size in number of bytes (not elements) of the array (known at compile time only)
	size VTSize
}

func (v *BasicVT) GetQType() QualType {
	return v.qtype
}

func (v *BasicVT) GetType() ValKind {
	return v.kind
}

func (v *BasicVT) GetSize() VTSize {
	return v.size
}

func (v *BasicVT) GetAlign() VTAlign {
	return v.align
}

// Create simple unit types with default size and alignment.
func NewBasicVT(kind ValKind, qtype QualType) BasicVT {
	if (kind.IsInteger() && kind != K_VK_TN_BITS && kind != K_VK_TN_UBITS) || kind.IsFloating() || kind == K_VK_TVOID {
		return BasicVT{
			qtype: qtype,
			kind:  kind,
			size:  kind.SizeInBytes(),
			align: kind.MinAlignInBytes(),
		}
	}

	panic(fmt.Sprintf("Value kind VT cannot be created: %v", kind))
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
	VoidVT   = NewBasicVT(K_VK_TVOID, K_QK_QNIL)
	BoolVT   = NewBasicVT(K_VK_TBOOL, K_QK_QNIL)
	CharVT   = NewBasicVT(K_VK_TCHAR, K_QK_QNIL)
	Int8VT   = NewBasicVT(K_VK_TINT8, K_QK_QNIL)
	Int16VT  = NewBasicVT(K_VK_TINT16, K_QK_QNIL)
	Int32VT  = NewBasicVT(K_VK_TINT32, K_QK_QNIL)
	Int64VT  = NewBasicVT(K_VK_TINT64, K_QK_QNIL)
	Uint8VT  = NewBasicVT(K_VK_TUINT8, K_QK_QNIL)
	Uint16VT = NewBasicVT(K_VK_TUINT16, K_QK_QNIL)
	Uint32VT = NewBasicVT(K_VK_TUINT32, K_QK_QNIL)
	Uint64VT = NewBasicVT(K_VK_TUINT64, K_QK_QNIL)
	FloatVT  = NewBasicVT(K_VK_TFLOAT32, K_QK_QNIL)
	DoubleVT = NewBasicVT(K_VK_TFLOAT64, K_QK_QNIL)
)
