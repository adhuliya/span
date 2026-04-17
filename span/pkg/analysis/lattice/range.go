package lattice

// This pacakage defines a range lattice.

import (
	"fmt"
	"math"

	"github.com/adhuliya/span/pkg/spir"
)

// The uint64 values store signed and unsigned intergers,
// and float and double values as IEEE 754 floating point numbers.
// The range is inclusive of the min and max values.
type RangeLT struct {
	typ spir.ValKind
	min uint64 // Encoded as for typ
	max uint64 // Encoded as for typ
}

// NewRangeLT constructs a new RangeLT with the given type and endpoints.
func NewRangeLT(typ spir.ValKind, min, max uint64) *RangeLT {
	return &RangeLT{
		typ: typ,
		min: min,
		max: max,
	}
}

func (l *RangeLT) String() string {
	switch l.typ {
	case spir.K_VK_TFLOAT:
		return fmt.Sprintf("RangeLT(float, %.6g, %.6g)", float32frombits(l.min), float32frombits(l.max))
	case spir.K_VK_TDOUBLE:
		return fmt.Sprintf("RangeLT(double, %.12g, %.12g)", float64frombits(l.min), float64frombits(l.max))
	case spir.K_VK_TINT8:
		return fmt.Sprintf("RangeLT(int8, %d, %d)", int8(l.min), int8(l.max))
	case spir.K_VK_TUINT8:
		return fmt.Sprintf("RangeLT(uint8, %d, %d)", uint8(l.min), uint8(l.max))
	case spir.K_VK_TINT16:
		return fmt.Sprintf("RangeLT(int16, %d, %d)", int16(l.min), int16(l.max))
	case spir.K_VK_TUINT16:
		return fmt.Sprintf("RangeLT(uint16, %d, %d)", uint16(l.min), uint16(l.max))
	case spir.K_VK_TINT32:
		return fmt.Sprintf("RangeLT(int32, %d, %d)", int32(l.min), int32(l.max))
	case spir.K_VK_TUINT32:
		return fmt.Sprintf("RangeLT(uint32, %d, %d)", uint32(l.min), uint32(l.max))
	case spir.K_VK_TINT64:
		return fmt.Sprintf("RangeLT(int64, %d, %d)", int64(l.min), int64(l.max))
	case spir.K_VK_TUINT64:
		return fmt.Sprintf("RangeLT(uint64, %d, %d)", l.min, l.max)
	default:
		return fmt.Sprintf("RangeLT(%v, %d, %d)", l.typ, l.min, l.max)
	}
}

// IsTop returns true if the RangeLT represents the top element (empty range: max < min is interpreted
// in the value domain according to type).
func (l *RangeLT) IsTop() bool {
	return rangeIsTop(l.typ, l.min, l.max)
}

// IsBot returns true if the RangeLT represents the bottom element (full range).
func (l *RangeLT) IsBot() bool {
	fmin, fmax := fullRangeForKind(l.typ)
	return l.min == fmin && l.max == fmax
}

// WeakerThan returns true if l contains other's range (less precise).
func (l *RangeLT) WeakerThan(other Lattice) bool {
	ol, ok := other.(*RangeLT)
	if !ok || l.typ != ol.typ {
		return false
	}
	return compareMin(l.typ, l.min, ol.min) <= 0 && compareMax(l.typ, l.max, ol.max) >= 0
}

// Meet computes the meet (GLB: wider union) of two RangeLTs.
func (l *RangeLT) Meet(other Lattice) (Lattice, bool) {
	ol, ok := other.(*RangeLT)
	if !ok || l.typ != ol.typ {
		return l, false
	}
	newMin := meetMin(l.typ, l.min, ol.min)
	newMax := meetMax(l.typ, l.max, ol.max)
	changed := newMin != l.min || newMax != l.max
	return &RangeLT{typ: l.typ, min: newMin, max: newMax}, changed
}

// Join computes the join (LUB: intersection, tighter interval) of two RangeLTs.
func (l *RangeLT) Join(other Lattice) (Lattice, bool) {
	ol, ok := other.(*RangeLT)
	if !ok || l.typ != ol.typ {
		return l, false
	}
	newMin := joinMin(l.typ, l.min, ol.min)
	newMax := joinMax(l.typ, l.max, ol.max)
	changed := newMin != l.min || newMax != l.max
	// Top if empty interval: Compare using value semantics.
	if compareMin(l.typ, newMin, newMax) > 0 {
		// This is an empty range (top)
	}
	return &RangeLT{typ: l.typ, min: newMin, max: newMax}, changed
}

// Widen expands to full (bot) range if other is weaker, otherwise behaves as meet.
func (l *RangeLT) Widen(other Lattice) (Lattice, bool) {
	ol, ok := other.(*RangeLT)
	if !ok || l.typ != ol.typ {
		return l, false
	}
	if ol.WeakerThan(l) {
		fullMin, fullMax := fullRangeForKind(l.typ)
		changed := l.min != fullMin || l.max != fullMax
		return &RangeLT{typ: l.typ, min: fullMin, max: fullMax}, changed
	}
	return l.Meet(other)
}

// Equals checks if two RangeLTs represent the same range and type.
func (l *RangeLT) Equals(other Lattice) bool {
	ol, ok := other.(*RangeLT)
	if !ok {
		return false
	}
	if l.typ != ol.typ {
		return false
	}
	return l.min == ol.min && l.max == ol.max
}

// Convert uint64 bit patterns to value, then compare.
func compareMin(typ spir.ValKind, a, b uint64) int {
	switch typ {
	case spir.K_VK_TINT8:
		return intCompare(int32(int8(a)), int32(int8(b)))
	case spir.K_VK_TUINT8:
		return uintCompare(uint64(uint8(a)), uint64(uint8(b)))
	case spir.K_VK_TINT16:
		return intCompare(int32(int16(a)), int32(int16(b)))
	case spir.K_VK_TUINT16:
		return uintCompare(uint64(uint16(a)), uint64(uint16(b)))
	case spir.K_VK_TINT32:
		return intCompare(int32(a), int32(b))
	case spir.K_VK_TUINT32:
		return uintCompare(uint64(uint32(a)), uint64(uint32(b)))
	case spir.K_VK_TINT64:
		return int64Compare(int64(a), int64(b))
	case spir.K_VK_TUINT64:
		return uintCompare(a, b)
	case spir.K_VK_TFLOAT:
		return float32Compare(float32frombits(a), float32frombits(b))
	case spir.K_VK_TDOUBLE:
		return float64Compare(float64frombits(a), float64frombits(b))
	default:
		return uintCompare(a, b)
	}
}

func compareMax(typ spir.ValKind, a, b uint64) int {
	// Reuse compareMin (same, just for max bound)
	return compareMin(typ, a, b)
}

func intCompare(a, b int32) int {
	if a < b {
		return -1
	} else if a > b {
		return 1
	}
	return 0
}
func int64Compare(a, b int64) int {
	if a < b {
		return -1
	} else if a > b {
		return 1
	}
	return 0
}
func uintCompare(a, b uint64) int {
	if a < b {
		return -1
	} else if a > b {
		return 1
	}
	return 0
}
func float32Compare(a, b float32) int {
	if a < b {
		return -1
	} else if a > b {
		return 1
	}
	return 0
}
func float64Compare(a, b float64) int {
	if a < b {
		return -1
	} else if a > b {
		return 1
	}
	return 0
}

func float32frombits(u uint64) float32 {
	return math.Float32frombits(uint32(u))
}
func float64frombits(u uint64) float64 {
	return math.Float64frombits(u)
}

// min/max helpers for meet/join in correct value domain.
func meetMin(typ spir.ValKind, a, b uint64) uint64 {
	if compareMin(typ, a, b) <= 0 {
		return a
	}
	return b
}
func meetMax(typ spir.ValKind, a, b uint64) uint64 {
	if compareMax(typ, a, b) >= 0 {
		return a
	}
	return b
}
func joinMin(typ spir.ValKind, a, b uint64) uint64 {
	if compareMin(typ, a, b) >= 0 {
		return a
	}
	return b
}
func joinMax(typ spir.ValKind, a, b uint64) uint64 {
	if compareMax(typ, a, b) <= 0 {
		return a
	}
	return b
}

// True if the encoded min>max in the value domain
func rangeIsTop(typ spir.ValKind, min, max uint64) bool {
	return compareMin(typ, min, max) > 0
}

// Returns the min/max representable value for the given type in encoded uint64 form.
func fullRangeForKind(kind spir.ValKind) (uint64, uint64) {
	switch kind {
	case spir.K_VK_TINT32:
		return ToUint64(spir.K_VK_TINT32, int32(math.MinInt32)), ToUint64(spir.K_VK_TINT32, int32(math.MaxInt32))
	case spir.K_VK_TUINT32:
		return ToUint64(spir.K_VK_TUINT32, uint32(0)), ToUint64(spir.K_VK_TUINT32, uint32(math.MaxUint32))
	case spir.K_VK_TINT64:
		return ToUint64(spir.K_VK_TINT64, int64(math.MinInt64)), ToUint64(spir.K_VK_TINT64, int64(math.MaxInt64))
	case spir.K_VK_TUINT64:
		return ToUint64(spir.K_VK_TUINT64, uint64(0)), ToUint64(spir.K_VK_TUINT64, uint64(math.MaxUint64))
	case spir.K_VK_TFLOAT:
		return ToUint64(spir.K_VK_TFLOAT, float32(-math.MaxFloat32)), ToUint64(spir.K_VK_TFLOAT, math.MaxFloat32)
	case spir.K_VK_TDOUBLE:
		return ToUint64(spir.K_VK_TDOUBLE, float64(-math.MaxFloat64)), ToUint64(spir.K_VK_TDOUBLE, math.MaxFloat64)
	default:
		return ToUint64(kind, 0), ToUint64(kind, uint64(math.MaxUint64))
	}
}

// Provides conversion functions for encoding/decoding values as uint64
// according to the type information in spir.ValKind.

// Int/Uint/Float/Double -> uint64 (for uniform lattice encoding)
// And reverse: uint64 to original value (as int, uint, float32, float64)

// ToUint64 encodes a value (as interface{}) according to typ into uint64.
// Returns the encoded value. Panics if the type is mismatched.
func ToUint64(typ spir.ValKind, val interface{}) uint64 {
	switch typ {
	case spir.K_VK_TINT32:
		v, ok := val.(int32)
		if !ok {
			panic("ToUint64: Expected int32 value")
		}
		return uint64(uint32(v))
	case spir.K_VK_TUINT32:
		v, ok := val.(uint32)
		if !ok {
			panic("ToUint64: Expected uint32 value")
		}
		return uint64(v)
	case spir.K_VK_TINT64:
		v, ok := val.(int64)
		if !ok {
			panic("ToUint64: Expected int64 value")
		}
		return uint64(v)
	case spir.K_VK_TUINT64:
		v, ok := val.(uint64)
		if !ok {
			panic("ToUint64: Expected uint64 value")
		}
		return v
	case spir.K_VK_TFLOAT:
		v, ok := val.(float32)
		if !ok {
			panic("ToUint64: Expected float32 value")
		}
		return uint64(math.Float32bits(v))
	case spir.K_VK_TDOUBLE:
		v, ok := val.(float64)
		if !ok {
			panic("ToUint64: Expected float64 value")
		}
		return math.Float64bits(v)
	default:
		panic("ToUint64: Unsupported spir.ValKind")
	}
}

// FromUint64 decodes a uint64-encoded value as per typ, returning as interface{}.
// Needs a type switch by caller for use.
func FromUint64(typ spir.ValKind, bits uint64) interface{} {
	switch typ {
	case spir.K_VK_TINT8:
		return int8(uint8(bits)) // narrowing conversion
	case spir.K_VK_TUINT8:
		return uint8(bits)
	case spir.K_VK_TINT16:
		return int16(uint16(bits))
	case spir.K_VK_TUINT16:
		return uint16(bits)
	case spir.K_VK_TINT32:
		return int32(uint32(bits))
	case spir.K_VK_TUINT32:
		return uint32(bits)
	case spir.K_VK_TINT64:
		return int64(bits)
	case spir.K_VK_TUINT64:
		return bits
	case spir.K_VK_TFLOAT:
		return math.Float32frombits(uint32(bits))
	case spir.K_VK_TDOUBLE:
		return math.Float64frombits(bits)
	default:
		panic("FromUint64: Unsupported spir.ValKind")
	}
}

// Convenience functions for type safety.

// Int32ToUint64 encodes int32 to uint64. Use for spir.K_VK_TINT32.
func Int32ToUint64(v int32) uint64 {
	return uint64(uint32(v))
}

// Uint32ToUint64 encodes uint32 to uint64. Use for spir.K_VK_TUINT32.
func Uint32ToUint64(v uint32) uint64 {
	return uint64(v)
}

// Int64ToUint64 encodes int64 to uint64. Use for spir.K_VK_TINT64.
func Int64ToUint64(v int64) uint64 {
	return uint64(v)
}

// Float32ToUint64 encodes float32 to uint64. Use for spir.K_VK_TFLOAT.
func Float32ToUint64(v float32) uint64 {
	return uint64(math.Float32bits(v))
}

// Float64ToUint64 encodes float64 to uint64. Use for spir.K_VK_TDOUBLE.
func Float64ToUint64(v float64) uint64 {
	return math.Float64bits(v)
}

// Uint64ToInt32 decodes a uint64 to int32 as per spir.K_VK_TINT32.
func Uint64ToInt32(u uint64) int32 {
	return int32(uint32(u))
}

// Uint64ToUint32 decodes a uint64 to uint32 as per spir.K_VK_TUINT32.
func Uint64ToUint32(u uint64) uint32 {
	return uint32(u)
}

// Uint64ToInt64 decodes a uint64 to int64 as per spir.K_VK_TINT64.
func Uint64ToInt64(u uint64) int64 {
	return int64(u)
}

// Uint64ToUint64 is identity for spir.K_VK_TUINT64.
func Uint64ToUint64(u uint64) uint64 {
	return u
}

// Uint64ToFloat32 decodes a uint64 (lower 32 bits) to float32 as per spir.K_VK_TFLOAT.
func Uint64ToFloat32(u uint64) float32 {
	return math.Float32frombits(uint32(u))
}

// Uint64ToFloat64 decodes a uint64 to float64 as per spir.K_VK_TDOUBLE.
func Uint64ToFloat64(u uint64) float64 {
	return math.Float64frombits(u)
}
