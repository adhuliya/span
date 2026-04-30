package lattice

import (
	"math"
	"testing"

	"github.com/adhuliya/span/pkg/spir"
)

// --- Step 1: Test Helpers ---

// Helper to construct a range by value, using values before conversion.
func mkRange(typ spir.ValKind, min, max interface{}) *RangeLattice {
	return NewRangeLT(typ, ToUint64(typ, min), ToUint64(typ, max))
}

// Helper: quickly get float bits.
func f32(x float32) uint64 { return ToUint64(spir.K_VK_TFLOAT, x) }
func f64(x float64) uint64 { return ToUint64(spir.K_VK_TDOUBLE, x) }

// --- Step 2: Test NewRangeLT and String ---

func TestRangeLT_String_and_Construct(t *testing.T) {
	type test struct {
		typ  spir.ValKind
		min  interface{}
		max  interface{}
		want string
	}
	tests := []test{
		{spir.K_VK_TINT8, int8(-3), int8(7), "RangeLT(int8, -3, 7)"},
		{spir.K_VK_TUINT8, uint8(7), uint8(10), "RangeLT(uint8, 7, 10)"},
		{spir.K_VK_TINT16, int16(-55), int16(12), "RangeLT(int16, -55, 12)"},
		{spir.K_VK_TUINT16, uint16(12), uint16(56), "RangeLT(uint16, 12, 56)"},
		{spir.K_VK_TINT32, int32(-1), int32(123456), "RangeLT(int32, -1, 123456)"},
		{spir.K_VK_TUINT32, uint32(9), uint32(88), "RangeLT(uint32, 9, 88)"},
		{spir.K_VK_TINT64, int64(-123), int64(123), "RangeLT(int64, -123, 123)"},
		{spir.K_VK_TUINT64, uint64(99), uint64(123), "RangeLT(uint64, 99, 123)"},
		{spir.K_VK_TFLOAT, float32(-3.5), float32(2.1), "RangeLT(float, -3.5, 2.1)"},
		{spir.K_VK_TDOUBLE, float64(-101.245), float64(905.353), "RangeLT(double, -101.245, 905.353)"},
	}
	for _, test := range tests {
		r := mkRange(test.typ, test.min, test.max)
		got := r.String()
		if got != test.want {
			t.Errorf("RangeLT.String() = %q, want %q (typ: %v)", got, test.want, test.typ)
		}
	}
}

// --- Step 3: Test IsTop (empty range) and IsBot (full range) ---

func TestRangeLT_IsTop_IsBot(t *testing.T) {
	// Top: max < min (value-wise)
	// Bot: full range
	top := NewRangeLT(spir.K_VK_TINT32, ToUint64(spir.K_VK_TINT32, int32(10)), ToUint64(spir.K_VK_TINT32, int32(5)))
	bot := mkRange(spir.K_VK_TUINT8, uint8(0), uint8(math.MaxUint8))
	if !top.IsTop() {
		t.Errorf("Expected IsTop for improper range")
	}
	if top.IsBot() {
		t.Errorf("Top should not be Bot")
	}
	if !bot.IsBot() {
		t.Errorf("Expected Bot for full range")
	}
	if bot.IsTop() {
		t.Errorf("Bot should not be Top")
	}
}

// --- Step 4: Test Equals ---

func TestRangeLT_Equals(t *testing.T) {
	r1 := mkRange(spir.K_VK_TINT16, int16(-50), int16(50))
	r2 := mkRange(spir.K_VK_TINT16, int16(-50), int16(50))
	r3 := mkRange(spir.K_VK_TINT16, int16(-51), int16(50))
	r4 := mkRange(spir.K_VK_TUINT16, uint16(0), uint16(100))

	if !r1.Equals(r2) {
		t.Errorf("Equal ranges should be equal")
	}
	if r1.Equals(r3) {
		t.Errorf("Unequal ranges shouldn't be equal")
	}
	if r1.Equals(r4) {
		t.Errorf("Different types should not be equal")
	}
}

// --- Step 5: Test WeakerThan ---

func TestRangeLT_WeakerThan(t *testing.T) {
	r1 := mkRange(spir.K_VK_TINT32, int32(-3), int32(7))
	r3 := mkRange(spir.K_VK_TINT32, int32(-4), int32(8))
	r4 := mkRange(spir.K_VK_TUINT32, uint32(0), uint32(9))
	if !r3.WeakerThan(r1) {
		t.Errorf("Range containing other's range should be weaker")
	}
	if r1.WeakerThan(r3) {
		t.Errorf("Smaller not weaker than larger")
	}
	if r1.WeakerThan(r4) {
		t.Errorf("Different types: should be false")
	}
}

// --- Step 6: Test Meet (GLB) and Join (LUB) ---

func TestRangeLT_Meet_Join(t *testing.T) {
	type test struct {
		typ                spir.ValKind
		a, b               interface{}
		c, d               interface{}
		expMeet1, expMeet2 interface{}
		expJoin1, expJoin2 interface{}
	}
	tests := []test{
		// Overlap
		{spir.K_VK_TINT16, int16(-5), int16(10), int16(0), int16(20),
			int16(-5), int16(20), int16(0), int16(10)},
		// Disjoint - meet expands, join is empty
		{spir.K_VK_TUINT8, uint8(20), uint8(30), uint8(50), uint8(60),
			uint8(20), uint8(60), uint8(50), uint8(30)},
		// Identical
		{spir.K_VK_TINT32, int32(-1), int32(1), int32(-1), int32(1),
			int32(-1), int32(1), int32(-1), int32(1)},
	}
	for _, tc := range tests {
		x := mkRange(tc.typ, tc.a, tc.b)
		y := mkRange(tc.typ, tc.c, tc.d)
		meet, _ := x.Meet(y)
		join, _ := x.Join(y)

		mWant := mkRange(tc.typ, tc.expMeet1, tc.expMeet2)
		jWant := mkRange(tc.typ, tc.expJoin1, tc.expJoin2)

		if !meet.(*RangeLattice).Equals(mWant) {
			t.Errorf("Meet(%v, %v): got %v, want %v", x, y, meet, mWant)
		}
		if !join.(*RangeLattice).Equals(jWant) {
			t.Errorf("Join(%v, %v): got %v, want %v", x, y, join, jWant)
		}
	}
}

// --- Step 7: Test Widen ---

func TestRangeLT_Widen(t *testing.T) {
	base := mkRange(spir.K_VK_TUINT32, uint32(10), uint32(100))
	weaker := mkRange(spir.K_VK_TUINT32, uint32(0), uint32(200))
	fullMin, fullMax := fullRangeForKind(spir.K_VK_TUINT32)
	got, changed := base.Widen(weaker)
	if !changed {
		t.Errorf("Widen with weaker should change")
	}
	if !got.(*RangeLattice).Equals(NewRangeLT(spir.K_VK_TUINT32, fullMin, fullMax)) {
		t.Errorf("Widen to weaker failed")
	}
	// Should fallback to meet if other not weaker
	nw := mkRange(spir.K_VK_TUINT32, uint32(20), uint32(80))
	got2, changed2 := base.Widen(nw)
	m, mChanged := base.Meet(nw)
	if !got2.(*RangeLattice).Equals(m.(*RangeLattice)) {
		t.Errorf("Widen (not weaker than base) should match Meet: got %v want %v", got2, m)
	}
	if changed2 != mChanged {
		t.Errorf("Widen changed=%v, want same as Meet changed=%v", changed2, mChanged)
	}
}

// --- Step 8: Corner Case for Empty/Top Ranges ---

func TestRangeLT_Empty_Top(t *testing.T) {
	// max < min and type is float: top/empty
	r := NewRangeLT(spir.K_VK_TFLOAT, ToUint64(spir.K_VK_TFLOAT, float32(10)), ToUint64(spir.K_VK_TFLOAT, float32(-10)))
	if !r.IsTop() {
		t.Errorf("float empty range IsTop")
	}
	// for int8
	r2 := NewRangeLT(spir.K_VK_TINT8, ToUint64(spir.K_VK_TINT8, int8(5)), ToUint64(spir.K_VK_TINT8, int8(-5)))
	if !r2.IsTop() {
		t.Errorf("int8 empty range IsTop")
	}
}

// --- Step 9: Edge conversions (ToUint64 / FromUint64) and encoding ---

func TestRangeLT_ToUint64_FromUint64(t *testing.T) {
	cases := []struct {
		typ spir.ValKind
		val interface{}
	}{
		{spir.K_VK_TINT32, int32(-2147483648)},
		{spir.K_VK_TUINT32, uint32(4294967295)},
		{spir.K_VK_TINT64, int64(-9223372036854775808)},
		{spir.K_VK_TUINT64, uint64(18446744073709551615)},
		{spir.K_VK_TFLOAT, float32(math.MaxFloat32)},
		{spir.K_VK_TDOUBLE, float64(math.MaxFloat64)},
		{spir.K_VK_TINT8, int8(-128)},
		{spir.K_VK_TUINT8, uint8(255)},
		{spir.K_VK_TINT16, int16(-32768)},
		{spir.K_VK_TUINT16, uint16(65535)},
	}
	for _, c := range cases {
		u := ToUint64(c.typ, c.val)
		back := FromUint64(c.typ, u)
		switch c.typ {
		case spir.K_VK_TFLOAT:
			if math.Abs(float64(back.(float32)-c.val.(float32))) > 1e-6 {
				t.Errorf("float32 roundtrip failed for %v", c.val)
			}
		case spir.K_VK_TDOUBLE:
			// Accept some small tolerance due to float64 precision
			if math.Abs(back.(float64)-c.val.(float64)) > 1e-9 {
				t.Errorf("float64 roundtrip failed for %v", c.val)
			}
		default:
			if back != c.val {
				t.Errorf("ToUint64/FromUint64 mismatch for kind %v: got %v want %v", c.typ, back, c.val)
			}
		}
	}
}

// --- Step 10: Exhaustive compareMin logic for edge types ---

func TestRangeLT_compareMin_Max(t *testing.T) {
	// Just a smoke test for all kinds, doesn't need to be exhaustive.
	vals := []uint64{0, 1, 127, 128, 255, uint64(math.MaxInt32), uint64(math.MaxUint32)}
	kinds := []spir.ValKind{
		spir.K_VK_TINT8, spir.K_VK_TUINT8,
		spir.K_VK_TINT16, spir.K_VK_TUINT16,
		spir.K_VK_TINT32, spir.K_VK_TUINT32,
		spir.K_VK_TINT64, spir.K_VK_TUINT64,
		spir.K_VK_TFLOAT, spir.K_VK_TDOUBLE,
	}
	for _, k := range kinds {
		for _, a := range vals {
			for _, b := range vals {
				_ = compareMin(k, a, b)
				_ = compareMax(k, a, b)
			}
		}
	}
}

// --- Step 11: Join/Meet with mismatched types returns self and false ---

// fakeLattice implements the Lattice interface for testing type mismatch handling.
type fakeLattice struct{}

func (f fakeLattice) IsTop() bool                   { return false }
func (f fakeLattice) IsBot() bool                   { return false }
func (f fakeLattice) Meet(Lattice) (Lattice, bool)  { return f, false }
func (f fakeLattice) Join(Lattice) (Lattice, bool)  { return f, false }
func (f fakeLattice) Widen(Lattice) (Lattice, bool) { return f, false }
func (f fakeLattice) Equals(Lattice) bool           { return false }
func (f fakeLattice) WeakerThan(Lattice) bool       { return false }
func (f fakeLattice) String() string                { return "fakeLattice" }

func TestRangeLT_TypeMismatchReturnsSelf(t *testing.T) {
	r := mkRange(spir.K_VK_TINT32, int32(-3), int32(3))
	fake := fakeLattice{}
	got, changed := r.Meet(fake)
	if got != r || changed {
		t.Errorf("Meet with type mismatch should return self, changed=false; got %p changed=%v", got, changed)
	}
	got, changed = r.Join(fake)
	if got != r || changed {
		t.Errorf("Join with type mismatch should return self, changed=false; got %p changed=%v", got, changed)
	}
	got, changed = r.Widen(fake)
	if got != r || changed {
		t.Errorf("Widen with type mismatch should return self, changed=false; got %p changed=%v", got, changed)
	}
	if r.Equals(fake) {
		t.Errorf("Equals(type mismatch) should be false")
	}
	if r.WeakerThan(fake) {
		t.Errorf("WeakerThan(type mismatch) should be false")
	}
}

// --- Step 12: FullRangeForKind returns correct full min/max ---

func TestRangeLT_String_unknownKind(t *testing.T) {
	r := NewRangeLT(spir.K_VK_TBOOL, 7, 42)
	got := r.String()
	want := "RangeLT(TBOOL, 7, 42)"
	if got != want {
		t.Errorf("String() = %q, want %q", got, want)
	}
}

func TestRangeLT_compareMin_defaultUsesUintOrder(t *testing.T) {
	// K_VK_TBOOL is not handled in compareMin; falls through to uintCompare.
	if compareMin(spir.K_VK_TBOOL, 3, 9) >= 0 {
		t.Error("expected compareMin(TBOOL, 3, 9) < 0")
	}
	if compareMin(spir.K_VK_TBOOL, 9, 3) <= 0 {
		t.Error("expected compareMin(TBOOL, 9, 3) > 0")
	}
}

func TestRangeLT_Join_disjointIsTop_int32(t *testing.T) {
	a := mkRange(spir.K_VK_TINT32, int32(1), int32(5))
	b := mkRange(spir.K_VK_TINT32, int32(100), int32(200))
	join, _ := a.Join(b)
	if !join.(*RangeLattice).IsTop() {
		t.Errorf("disjoint int32 join should be top: got %v IsTop=%v", join, join.(*RangeLattice).IsTop())
	}
}

func TestRangeLT_meetMin_joinMax_branches(t *testing.T) {
	a, b := uint64(20), uint64(10)
	if got := meetMin(spir.K_VK_TUINT8, a, b); got != b {
		t.Errorf("meetMin(20,10) = %v, want %v", got, b)
	}
	if got := joinMax(spir.K_VK_TUINT8, a, b); got != b {
		t.Errorf("joinMax(20,10) = %v, want %v", got, b)
	}
}

func TestRangeLT_FromUint64_unsupportedPanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("expected panic for unsupported ValKind in FromUint64")
		}
	}()
	_ = FromUint64(spir.K_VK_TBOOL, 0)
}

func TestRangeLT_convenienceEncoders(t *testing.T) {
	if v := int32(-99); Uint64ToInt32(Int32ToUint64(v)) != v {
		t.Errorf("Int32/Uint64 roundtrip")
	}
	if v := uint32(0xDEADBEEF); Uint64ToUint32(Uint32ToUint64(v)) != v {
		t.Errorf("Uint32 roundtrip")
	}
	if v := int64(-1 << 40); Uint64ToInt64(Int64ToUint64(v)) != v {
		t.Errorf("Int64 roundtrip")
	}
	if v := uint64(0xC0FFEE); Uint64ToUint64(v) != v {
		t.Errorf("Uint64 identity")
	}
	if v := float32(-1.25); Uint64ToFloat32(Float32ToUint64(v)) != v {
		t.Errorf("Float32 roundtrip")
	}
	if v := float64(3.141592653589793); Uint64ToFloat64(Float64ToUint64(v)) != v {
		t.Errorf("Float64 roundtrip")
	}
}

func Test_fullRangeForKind(t *testing.T) {
	kinds := []spir.ValKind{
		spir.K_VK_TINT32,
		spir.K_VK_TUINT32,
		spir.K_VK_TINT64,
		spir.K_VK_TUINT64,
		spir.K_VK_TFLOAT,
		spir.K_VK_TDOUBLE,
		spir.K_VK_TINT8,
		spir.K_VK_TUINT8,
		spir.K_VK_TINT16,
		spir.K_VK_TUINT16,
	}
	for _, k := range kinds {
		min, max := fullRangeForKind(k)
		// Endpoints are uint64 encodings; signed/float order is not raw uint order.
		if rangeIsTop(k, min, max) {
			t.Errorf("fullRangeForKind: empty/top range for %v, min=%v, max=%v", k, min, max)
		}
	}
}
