package spir

// This file contains the data types used in the SPAN program analysis engine.

type ValueTypeKind int
type ValueTypeSize int
type ValueTypeAlign int
type QualType int

// ValueTypeKind is an integer type that represents the kind of a value type.
// It is an integer type in the range of 0 to 31 (5 bits).
const (
	TY_INT8                   ValueTypeKind = 0
	TY_INT16                  ValueTypeKind = 1
	TY_INT32                  ValueTypeKind = 2
	TY_INT64                  ValueTypeKind = 3
	TY_UINT8                  ValueTypeKind = 4
	TY_CHAR                   ValueTypeKind = TY_UINT8
	TY_UINT16                 ValueTypeKind = 5
	TY_UINT32                 ValueTypeKind = 6
	TY_UINT64                 ValueTypeKind = 7
	TY_N_BITS                 ValueTypeKind = 8
	TY_N_UBITS                ValueTypeKind = 9
	TY_BOOL                   ValueTypeKind = 10
	TY_FLOAT16                ValueTypeKind = 11
	TY_FLOAT32                ValueTypeKind = 12
	TY_FLOAT                  ValueTypeKind = TY_FLOAT32
	TY_FLOAT64                ValueTypeKind = 13
	TY_DOUBLE                 ValueTypeKind = TY_FLOAT64
	TY_PTR_TO_FUNC            ValueTypeKind = 14
	TY_PTR_TO_CHAR            ValueTypeKind = 15
	TY_PTR_TO_VOID            ValueTypeKind = 16
	TY_PTR_TO_PTR             ValueTypeKind = 17
	TY_PTR_TO_RECORD          ValueTypeKind = 18
	TY_PTR_TO_INT             ValueTypeKind = 19
	TY_PTR_TO_FLOAT           ValueTypeKind = 20
	TY_ARR_PTR                ValueTypeKind = 21
	TY_UNION                  ValueTypeKind = 22
	TY_STRUCT                 ValueTypeKind = 23
	TY_FUNC_WITH_DEF          ValueTypeKind = 24
	TY_FUNC_WITH_DEF_VAR_ARGS ValueTypeKind = 25
	TY_FUNC_WITHOUT_DEF       ValueTypeKind = 26
	TY_OTHER                  ValueTypeKind = 27
	TY_APPLE                  ValueTypeKind = 28
	TY_BALL                   ValueTypeKind = 29
	TY_CAT                    ValueTypeKind = 30
	TY_DOG                    ValueTypeKind = 31
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
	qtype QualType
	kind  ValueTypeKind
	size  ValueTypeSize
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

func ValueKindString(valueKind ValueTypeKind) string {
	switch valueKind {
	case TY_INT8:
		return "int8"
	case TY_INT16:
		return "int16"
	case TY_INT32:
		return "int32"
	case TY_INT64:
		return "int64"
	case TY_UINT8:
		return "uint8"
	case TY_UINT16:
		return "uint16"
	case TY_UINT32:
		return "uint32"
	case TY_UINT64:
		return "uint64"
	case TY_BOOL:
		return "bool"
	case TY_FLOAT16:
		return "float16"
	case TY_FLOAT32:
		return "float32"
	case TY_FLOAT64:
		return "float64"
	default:
		return "unknown type"
	}
}

func IsInteger(valueKind ValueTypeKind) bool {
	switch valueKind {
	case TY_INT8, TY_INT16, TY_INT32, TY_INT64,
		TY_UINT8, TY_UINT16, TY_UINT32, TY_UINT64,
		TY_N_BITS, TY_N_UBITS, TY_BOOL:
		return true
	default:
		return false
	}
}

func IsFloat(valueKind ValueTypeKind) bool {
	switch valueKind {
	case TY_FLOAT16, TY_FLOAT32, TY_FLOAT64:
		return true
	default:
		return false
	}
}

func IsPointer(valueKind ValueTypeKind) bool {
	switch valueKind {
	case TY_PTR_TO_FUNC, TY_PTR_TO_CHAR, TY_PTR_TO_VOID,
		TY_PTR_TO_RECORD, TY_PTR_TO_INT, TY_PTR_TO_FLOAT:
		return true
	default:
		return false
	}
}

func IsRecord(valueKind ValueTypeKind) bool {
	switch valueKind {
	case TY_UNION, TY_STRUCT:
		return true
	default:
		return false
	}
}

func IsFunction(valueKind ValueTypeKind) bool {
	switch valueKind {
	case TY_FUNC_WITH_DEF, TY_FUNC_WITH_DEF_VAR_ARGS, TY_FUNC_WITHOUT_DEF:
		return true
	default:
		return false
	}
}

func IsOther(valueKind ValueTypeKind) bool {
	switch valueKind {
	case TY_OTHER, TY_APPLE, TY_BALL, TY_CAT, TY_DOG:
		return true
	default:
		return false
	}
}

// Check if the value kind is within the valid range of 5 bits integer
func IsValidType(valueKind ValueTypeKind) bool {
	return valueKind&^31 == 0
}
