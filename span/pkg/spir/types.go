package spir

// This file contains the data types used in the SPAN program analysis engine.

type ValueTypeKind uint8
type ValueTypeSize uint32
type ValueTypeAlign uint8
type QualType uint16
type RecordId EntityId

const ValueTypeKindMask uint32 = 0x1F        // Mask to get the ValueTypeKind bits
const ValueTypeKindMask32 uint32 = 0x1F_0000 // Mask to get the ValueTypeKind bits

// ValueTypeKind is an integer type that represents the kind of a value type.
// It is an integer type in the range of 0 to 31 (5 bits).
//
//go:generate stringer -type=ValueTypeKind
const (
	TY_CHAR          ValueTypeKind = 1
	TY_INT8          ValueTypeKind = 2
	TY_INT16         ValueTypeKind = 3
	TY_INT32         ValueTypeKind = 4
	TY_INT64         ValueTypeKind = 5
	TY_UINT8         ValueTypeKind = 6
	TY_UCHAR         ValueTypeKind = TY_UINT8
	TY_UINT16        ValueTypeKind = 7
	TY_UINT32        ValueTypeKind = 8
	TY_UINT64        ValueTypeKind = 9
	TY_N_BITS        ValueTypeKind = 10
	TY_N_UBITS       ValueTypeKind = 11
	TY_BOOL          ValueTypeKind = 12
	TY_FLOAT16       ValueTypeKind = 13
	TY_FLOAT32       ValueTypeKind = 14
	TY_FLOAT         ValueTypeKind = TY_FLOAT32
	TY_FLOAT64       ValueTypeKind = 15
	TY_DOUBLE        ValueTypeKind = TY_FLOAT64
	TY_PTR_TO_VOID   ValueTypeKind = 16
	TY_PTR_TO_PTR    ValueTypeKind = 17
	TY_PTR_TO_ARR    ValueTypeKind = 18 // A pointer to an array of elements
	TY_PTR_TO_CHAR   ValueTypeKind = 19
	TY_PTR_TO_INT    ValueTypeKind = 20
	TY_PTR_TO_FLOAT  ValueTypeKind = 21
	TY_PTR_TO_RECORD ValueTypeKind = 22
	TY_PTR_TO_FUNC   ValueTypeKind = 23
	TY_ARR           ValueTypeKind = 24
	TY_UNION         ValueTypeKind = 25
	TY_STRUCT        ValueTypeKind = 26
	TY_VOID          ValueTypeKind = 27

	TY_OTHER ValueTypeKind = 31
)

// QualType is an encoded integer that represents the qualified type of a value.
// It is a set of bits that represent types qualified with volatile, const, static, etc.
const (
	QUAL_TYPE_NONE            QualType = 0 // no qualification
	QUAL_TYPE_CONST           QualType = 1 // constant value
	QUAL_TYPE_CONST_DEST      QualType = 2 // constant destination value
	QUAL_TYPE_FUNCTION_STATIC QualType = 4 // function static
	QUAL_TYPE_GLOBAL_STATIC   QualType = 8 // global static
	QUAL_TYPE_VOLATILE        QualType = 16
	QUAL_TYPE_WEAK            QualType = 32  // weak symbol
	QUAL_TYPE_THREAD_LOCAL    QualType = 64  // thread local storage
	QUAL_TYPE_UNINITIALIZED   QualType = 128 // for uninitialized (generally global) variables
	QUAL_TYPE_EXTERNAL        QualType = 256
	QUAL_TYPE_NO_DEFINITION   QualType = QUAL_TYPE_EXTERNAL
)

type ValueType interface {
	GetQType() QualType
	GetType() ValueTypeKind
	GetSize() ValueTypeSize
	GetAlign() ValueTypeAlign
}

type ValueTypeBase struct {
	size  ValueTypeSize
	qtype QualType
	kind  ValueTypeKind
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

func (v *ValueTypeBase) GetType() ValueTypeKind {
	return v.kind
}

func (v *ValueTypeBase) GetSize() ValueTypeSize {
	return v.size
}

func (v *ValueTypeBase) GetAlign() ValueTypeAlign {
	return v.align
}

func NewValueTypeBase(kind ValueTypeKind, qtype QualType,
	size ValueTypeSize, align ValueTypeAlign) ValueTypeBase {
	return ValueTypeBase{
		qtype: qtype,
		kind:  kind,
		size:  size,
		align: align,
	}
}

func NewBasicValueType(kind ValueTypeKind, qtype QualType) *ValueTypeBase {
	if kind.IsInteger() && kind != TY_N_BITS && kind != TY_N_UBITS {
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

func (kind ValueTypeKind) FloatingAlignInBytes() ValueTypeAlign {
	switch kind {
	case TY_FLOAT16:
		return 2
	case TY_FLOAT32:
		return 4
	case TY_FLOAT64:
		return 8
	default:
		return 0
	}
}

func (kind ValueTypeKind) FloatingSizeInBytes() ValueTypeSize {
	switch kind {
	case TY_FLOAT16:
		return 2
	case TY_FLOAT32:
		return 4
	case TY_FLOAT64:
		return 8
	default:
		return 0
	}
}

func (kind ValueTypeKind) IsFloating() bool {
	return kind >= TY_FLOAT16 && kind <= TY_DOUBLE
}

func (kind ValueTypeKind) IsVoid() bool {
	return kind == TY_VOID
}

func (kind ValueTypeKind) IsInteger() bool {
	return kind <= TY_BOOL && kind >= TY_CHAR
}

func (kind ValueTypeKind) IsPointer() bool {
	return kind >= TY_PTR_TO_VOID && kind <= TY_ARR
}

func (kind ValueTypeKind) IsArray() bool {
	return kind == TY_ARR
}

func (kind ValueTypeKind) IntegerSizeInBytes() ValueTypeSize {
	switch kind {
	case TY_CHAR: // TY_UCHAR == TY_UINT8
		return 1
	case TY_INT8, TY_UINT8:
		return 1
	case TY_INT16, TY_UINT16:
		return 2
	case TY_INT32, TY_UINT32:
		return 4
	case TY_INT64, TY_UINT64:
		return 8
	default:
		return 0
	}
}

func (kind ValueTypeKind) IntegerAlignInBytes() ValueTypeAlign {
	switch kind {
	case TY_CHAR: // TY_UCHAR == TY_UINT8
		return 1
	case TY_INT8, TY_UINT8:
		return 1
	case TY_INT16, TY_UINT16:
		return 2
	case TY_INT32, TY_UINT32:
		return 4
	case TY_INT64, TY_UINT64:
		return 8
	default:
		return 0
	}
}
