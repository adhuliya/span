package lattice

import "testing"

// mkFactId builds a FactId from field values (each argument is masked by the corresponding width).
func mkFactId(version, factPoint, instrId, analysisId, reserved uint64) FactId {
	v := (version & FactIdVersionMask) << FactIdVersionShift
	v |= (factPoint & FactIdUB_PointMask) << FactIdUB_PointShift
	v |= (instrId & FactIdUB_EntityIdMask) << FactIdUB_EntityIdShift
	v |= (analysisId & FactIdAnalysisMask) << FactIdAnalysisShift
	v |= (reserved & FactIdReservedMask) << FactIdReservedShift
	return FactId(v)
}

func TestFactId_Getters(t *testing.T) {
	f := mkFactId(100, 2, 0xdeadbeef, 0xabc, 5)
	if got := f.Version(); got != 100 {
		t.Errorf("Version() = %d, want 100", got)
	}
	if got := f.FactPoint(); got != 2 {
		t.Errorf("FactPoint() = %d, want 2", got)
	}
	if got := f.InstrId(); got != 0xdeadbeef {
		t.Errorf("InstrId() = %#x, want 0xdeadbeef", got)
	}
	if got := f.AnalysisId(); got != 0xabc {
		t.Errorf("AnalysisId() = %#x, want 0xabc", got)
	}
	if got := f.Reserved(); got != 5 {
		t.Errorf("Reserved() = %d, want 5", got)
	}
	wantUnique := uint64(2 | (0xdeadbeef << FactIdUB_PointBits))
	if got := f.UniqueId(); got != wantUnique {
		t.Errorf("UniqueId() = %#x, want %#x", got, wantUnique)
	}
}

func TestFactId_UniqueId_matches_FactKind_and_InstrId(t *testing.T) {
	for _, fk := range []uint64{0, 1, 2, 3} {
		for _, iid := range []uint64{0, 1, 0xffffffff} {
			f := mkFactId(0, fk, iid, 0, 0)
			want := (fk & FactIdUB_PointMask) | ((iid & FactIdUB_EntityIdMask) << FactIdUB_PointBits)
			if got := f.UniqueId(); got != want {
				t.Errorf("UniqueId for fk=%d iid=%#x: got %#x want %#x", fk, iid, got, want)
			}
		}
	}
}

func TestFactId_WithVersion(t *testing.T) {
	base := mkFactId(10, 1, 0x123, 0x456, 3)
	got := base.WithVersion(999)
	if got.Version() != 999 {
		t.Errorf("WithVersion: Version() = %d, want 999", got.Version())
	}
	if got.FactPoint() != base.FactPoint() || got.InstrId() != base.InstrId() ||
		got.AnalysisId() != base.AnalysisId() || got.Reserved() != base.Reserved() {
		t.Errorf("WithVersion changed other fields: %+v vs base %+v", fieldSnapshot(got), fieldSnapshot(base))
	}
	// overflow masks to low 15 bits
	overflow := base.WithVersion(1<<20 | 7)
	if overflow.Version() != 7 {
		t.Errorf("WithVersion should mask: got %d want 7", overflow.Version())
	}
}

func TestFactId_WithInstrId(t *testing.T) {
	base := mkFactId(1, 2, 0x111, 0x222, 1)
	got := base.WithInstrId(0xfeedface)
	if got.InstrId() != 0xfeedface {
		t.Errorf("InstrId = %#x", got.InstrId())
	}
	if got.Version() != base.Version() || got.FactPoint() != base.FactPoint() ||
		got.AnalysisId() != base.AnalysisId() || got.Reserved() != base.Reserved() {
		t.Errorf("WithInstrId changed other fields")
	}
	masked := base.WithInstrId(0xffffffffffffffff)
	if masked.InstrId() != FactIdUB_EntityIdMask {
		t.Errorf("WithInstrId mask: got %#x", masked.InstrId())
	}
}

func TestFactId_WithFactPoint(t *testing.T) {
	base := mkFactId(5, 0, 0xabc, 0xdef, 2)
	got := base.WithFactPoint(3)
	if got.FactPoint() != 3 {
		t.Errorf("FactPoint = %d", got.FactPoint())
	}
	if got.InstrId() != base.InstrId() {
		t.Errorf("WithFactPoint altered InstrId")
	}
	masked := base.WithFactPoint(99)
	if masked.FactPoint() != (99 & FactIdUB_PointMask) {
		t.Errorf("WithFactPoint mask: got %d", masked.FactPoint())
	}
}

func TestFactId_WithUB(t *testing.T) {
	base := mkFactId(7, 1, 0x100, 0x200, 4)
	u := uint64(0x3ffffffff) // max 34 bits
	got := base.WithUB(u)
	if got.UniqueId() != u&FactIdUB_Mask {
		t.Errorf("UniqueId = %#x want %#x", got.UniqueId(), u&FactIdUB_Mask)
	}
	if got.Version() != base.Version() || got.AnalysisId() != base.AnalysisId() || got.Reserved() != base.Reserved() {
		t.Errorf("WithUB changed fields outside unique region")
	}
}

func TestFactId_WithAnalysisId(t *testing.T) {
	base := mkFactId(1, 0, 0, 0xaaa, 0)
	got := base.WithAnalysisId(0xbbb)
	if got.AnalysisId() != 0xbbb {
		t.Errorf("AnalysisId = %#x", got.AnalysisId())
	}
	if got.Version() != base.Version() {
		t.Errorf("version changed")
	}
	overflow := base.WithAnalysisId(0xfffff)
	if overflow.AnalysisId() != FactIdAnalysisMask {
		t.Errorf("analysis mask: got %#x", overflow.AnalysisId())
	}
}

func TestFactId_WithReserved(t *testing.T) {
	base := mkFactId(0, 0, 0, 0, 0)
	got := base.WithReserved(6)
	if got.Reserved() != 6 {
		t.Errorf("Reserved = %d", got.Reserved())
	}
	masked := base.WithReserved(9)
	if masked.Reserved() != (9 & FactIdReservedMask) {
		t.Errorf("reserved mask: got %d", masked.Reserved())
	}
}

func TestFactId_IncVersion(t *testing.T) {
	f := mkFactId(FactIdVersionMask, 0, 0, 0, 0)
	next := f.IncVersion()
	if next.Version() != 0 {
		t.Errorf("IncVersion wrap: got %d want 0", next.Version())
	}
	if next.FactPoint() != f.FactPoint() || next.InstrId() != f.InstrId() {
		t.Errorf("IncVersion changed non-version fields")
	}
	low := mkFactId(41, 2, 3, 4, 1)
	if low.IncVersion().Version() != 42 {
		t.Errorf("IncVersion increment failed")
	}
}

func TestFactId_ZeroVersion(t *testing.T) {
	f := mkFactId(12345, 1, 2, 3, 4)
	z := f.ZeroVersion()
	if z.Version() != 0 {
		t.Errorf("ZeroVersion: version %d", z.Version())
	}
	if z.UniqueId() != f.UniqueId() || z.AnalysisId() != f.AnalysisId() || z.Reserved() != f.Reserved() {
		t.Errorf("ZeroVersion changed other fields")
	}
}

func TestFactId_AsKey(t *testing.T) {
	f := mkFactId(777, 2, 0xabc, 0xdef, 1)
	k := f.AsKey()
	z := f.ZeroVersion()
	if k != z {
		t.Errorf("AsKey() = %#x, ZeroVersion() = %#x", uint64(k), uint64(z))
	}
	if uint64(k) != f.BaseKey() {
		t.Errorf("AsKey raw %#x != BaseKey %#x", uint64(k), f.BaseKey())
	}
	a := mkFactId(1, 2, 0xabc, 0xdef, 1)
	b := mkFactId(99, 2, 0xabc, 0xdef, 1)
	m := map[FactId]string{a.AsKey(): "same"}
	if m[b.AsKey()] != "same" {
		t.Errorf("map key: different versions should collide on AsKey()")
	}
	if _, ok := m[f]; ok {
		t.Errorf("raw FactId with non-zero version should not hit AsKey()-only map")
	}
}

func TestFactId_BaseKey(t *testing.T) {
	f := mkFactId(999, 1, 0x55, 0x66, 2)
	key := f.BaseKey()
	z := f.ZeroVersion()
	if uint64(z) != key {
		t.Errorf("BaseKey %#x != ZeroVersion raw %#x", key, uint64(z))
	}
	if FactId(key).Version() != 0 {
		t.Errorf("BaseKey should clear version")
	}
	if FactId(key).InstrId() != f.InstrId() {
		t.Errorf("BaseKey cleared too much")
	}
}

type factFields struct {
	v, fk, iid, aid, r uint64
}

func fieldSnapshot(f FactId) factFields {
	return factFields{f.Version(), f.FactPoint(), f.InstrId(), f.AnalysisId(), f.Reserved()}
}

func TestFactId_const_layout(t *testing.T) {
	// Guard against accidental edits to shifts/masks breaking the documented layout.
	if FactIdVersionShift != 0 || FactIdVersionBits != 15 {
		t.Fatal("version field layout changed")
	}
	if FactIdUniqueShift != 15 || FactIdUB_BitCount != 34 {
		t.Fatal("unique field layout changed")
	}
	if FactIdAnalysisShift != 49 || FactIdAnalysisBits != 12 {
		t.Fatal("analysis field layout changed")
	}
	if FactIdReservedShift != 61 || FactIdReservedBits != 3 {
		t.Fatal("reserved field layout changed")
	}
	if FactIdUB_PointShift != 15 || FactIdUB_EntityIdShift != 17 {
		t.Fatal("fact kind / instr id layout changed")
	}
}
