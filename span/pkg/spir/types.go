package spir

// This file contains the data types used in the SPAN program analysis engine.

// ValKind is an integer type that represents the kind of a value type.
// It is an integer type in the range of 0 to 31 (5 bits).
type ValKind = K_VK

type ValueTypeSize uint32
type ValueTypeAlign uint8

// QualType is an encoded integer that represents the qualified type of a value.
// It is a set of bits that represent types qualified with volatile, const, static, etc.
type QualType = K_QK

type RecordId EntityId

const ValueTypeKindMask uint32 = 0x1F        // Mask to get the ValueTypeKind bits
const ValueTypeKindMask32 uint32 = 0x1F_0000 // Mask to get the ValueTypeKind bits

type ValueType interface {
	GetQType() QualType
	GetType() ValKind
	GetSize() ValueTypeSize
	GetAlign() ValueTypeAlign
}

type ValueTypeBase struct {
	size  ValueTypeSize
	qtype QualType
	kind  ValKind
	align ValueTypeAlign
}

type PointerValueType struct {
	ValueTypeBase
	targetType ValueType
}

type RecordValueType struct {
	ValueTypeBase
	members map[string]ValueType
}

type FunctionValueType struct {
	ValueTypeBase
	returnType ValueType
	paramTypes []ValueType
	paramNames []string
	varArgs    bool
}

type VariableArgsValueType struct {
	ValueTypeBase
	elementType ValueType
}

type ArrayValueType struct {
	ValueTypeBase
	elementType ValueType
	size        ValueTypeSize
}

func (v *ValueTypeBase) GetQType() QualType {
	return v.qtype
}

func (v *ValueTypeBase) GetType() ValKind {
	return v.kind
}

func (v *ValueTypeBase) GetSize() ValueTypeSize {
	return v.size
}

func (v *ValueTypeBase) GetAlign() ValueTypeAlign {
	return v.align
}

func NewValueTypeBase(kind ValKind, qtype QualType,
	size ValueTypeSize, align ValueTypeAlign) ValueTypeBase {
	return ValueTypeBase{
		qtype: qtype,
		kind:  kind,
		size:  size,
		align: align,
	}
}

func NewBasicValueType(kind ValKind, qtype QualType) *ValueTypeBase {
	if kind.IsInteger() && kind != K_VK_N_BITS && kind != K_VK_N_UBITS {
		return &ValueTypeBase{
			qtype: qtype,
			kind:  kind,
			size:  kind.IntegerSizeInBytes(),
			align: kind.IntegerAlignInBytes(),
		}
	} else if kind.IsFloating() {
		return &ValueTypeBase{
			qtype: qtype,
			kind:  kind,
			size:  kind.FloatingSizeInBytes(),
			align: kind.FloatingAlignInBytes(),
		}
	} else if kind.IsVoid() {
		return &ValueTypeBase{
			qtype: qtype,
			kind:  kind,
			size:  0,
			align: 0,
		}
	}
	return nil
}

func (kind ValKind) FloatingAlignInBytes() ValueTypeAlign {
	switch kind {
	case K_VK_FLOAT16:
		return 2
	case K_VK_FLOAT32:
		return 4
	case K_VK_FLOAT64:
		return 8
	default:
		return 0
	}
}

func (kind ValKind) FloatingSizeInBytes() ValueTypeSize {
	switch kind {
	case K_VK_FLOAT16:
		return 2
	case K_VK_FLOAT32:
		return 4
	case K_VK_FLOAT64:
		return 8
	default:
		return 0
	}
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
	return kind >= K_VK_PTR_TO_VOID && kind <= K_VK_ARR
}

func (kind ValKind) IsArray() bool {
	return kind == K_VK_ARR
}

func (kind ValKind) IntegerSizeInBytes() ValueTypeSize {
	switch kind {
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
	default:
		return 0
	}
}

func (kind ValKind) IntegerAlignInBytes() ValueTypeAlign {
	switch kind {
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
	default:
		return 0
	}
}
