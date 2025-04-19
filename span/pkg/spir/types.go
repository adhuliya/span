package spir

// This file contains the data types used in the SPAN program analysis engine.

type ValueTypeKind uint8
type ValueTypeSize uint32
type ValueTypeAlign uint8
type QualType uint16
type RecordId EntityId

// ValueTypeKind is an integer type that represents the kind of a value type.
// It is an integer type in the range of 0 to 31 (5 bits).
//
//go:generate stringer -type=ValueTypeKind
const (
	TY_CHAR          ValueTypeKind = 0
	TY_INT8          ValueTypeKind = 1
	TY_INT16         ValueTypeKind = 2
	TY_INT32         ValueTypeKind = 3
	TY_INT64         ValueTypeKind = 4
	TY_UINT8         ValueTypeKind = 5
	TY_UCHAR         ValueTypeKind = TY_UINT8
	TY_UINT16        ValueTypeKind = 6
	TY_UINT32        ValueTypeKind = 7
	TY_UINT64        ValueTypeKind = 8
	TY_N_BITS        ValueTypeKind = 9
	TY_N_UBITS       ValueTypeKind = 10
	TY_BOOL          ValueTypeKind = 11
	TY_FLOAT16       ValueTypeKind = 12
	TY_FLOAT32       ValueTypeKind = 13
	TY_FLOAT         ValueTypeKind = TY_FLOAT32
	TY_FLOAT64       ValueTypeKind = 14
	TY_DOUBLE        ValueTypeKind = TY_FLOAT64
	TY_PTR_TO_VOID   ValueTypeKind = 15
	TY_PTR_TO_PTR    ValueTypeKind = 16
	TY_PTR_TO_ARR    ValueTypeKind = 17 // A pointer to an array of elements
	TY_PTR_TO_CHAR   ValueTypeKind = 18
	TY_PTR_TO_INT    ValueTypeKind = 19
	TY_PTR_TO_FLOAT  ValueTypeKind = 20
	TY_PTR_TO_RECORD ValueTypeKind = 21
	TY_PTR_TO_FUNC   ValueTypeKind = 22
	TY_ARR           ValueTypeKind = 23
	TY_UNION         ValueTypeKind = 24
	TY_STRUCT        ValueTypeKind = 25

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

func NewValueTypeBase(qtype QualType, kind ValueTypeKind, size ValueTypeSize, align ValueTypeAlign) *ValueTypeBase {
	return &ValueTypeBase{
		qtype: qtype,
		kind:  kind,
		size:  size,
		align: align,
	}
}

func IsInteger(kind ValueTypeKind) bool {
	if kind <= TY_BOOL && kind >= TY_CHAR {
		return true
	}
	return false
}

func IsPointer(kind ValueTypeKind) bool {
	if kind >= TY_PTR_TO_VOID && kind <= TY_ARR {
		return true
	}
	return false
}

func IsArray(kind ValueTypeKind) bool {
	if kind == TY_ARR {
		return true
	}
	return false
}
