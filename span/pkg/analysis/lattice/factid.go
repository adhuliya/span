package lattice

// FactId uniquely identifies a data flow fact and its history of values.
// The 64 bits are encoded as follows:
//   - 2  bits : For future use
//   - 12 bits : Analysis id
//   - 35 bits : Unique Bits (UB = EntityId + FactPoint)
//       * 32 bits : Id of the instruction / BB / function
//       * 3  bits : Fact at IN, OUT, IN & OUT of the instruction, BB or function
//   - 15 bits : Version of the fact (increments per update)
//
// The FactId can be used as key by dropping the 'version' part.

type FactId uint64

const NIL_FACT_ID FactId = 0

// NEW BIT LAYOUT (little-endian/LSB to MSB):
// [0-14]   15b Version
// [15-49]  35b Unique Bits (UB = EntityId + FactPoint)
//            - [15-17] FactPoint (3b)
//            - [18-49] InstrId (32b)
// [50-61]  12b AnalysisId
// [62-63]  2b Reserved

// Bit sizes
const (
	FactIdVersionBits = 15

	FactIdUB_PointBits    = 3
	FactIdUB_EntityIdBits = 32
	FactIdUB_BitCount     = FactIdUB_PointBits + FactIdUB_EntityIdBits

	FactIdAnalysisBits = 12
	FactIdReservedBits = 2
)

// Bit shifts for each field
const (
	FactIdVersionShift  = 0
	FactIdUniqueShift   = FactIdVersionShift + FactIdVersionBits
	FactIdAnalysisShift = FactIdUniqueShift + FactIdUB_BitCount
	FactIdReservedShift = FactIdAnalysisShift + FactIdAnalysisBits

	FactIdUB_PointShift    = FactIdUniqueShift
	FactIdUB_EntityIdShift = FactIdUB_PointShift + FactIdUB_PointBits
)

// Masks for each field (before shifting)
const (
	FactIdVersionMask  = (1 << FactIdVersionBits) - 1
	FactIdUB_Mask      = (1 << FactIdUB_BitCount) - 1
	FactIdAnalysisMask = (1 << FactIdAnalysisBits) - 1
	FactIdReservedMask = (1 << FactIdReservedBits) - 1

	FactIdUB_PointMask    = (1 << FactIdUB_PointBits) - 1
	FactIdUB_EntityIdMask = (1 << FactIdUB_EntityIdBits) - 1
)

const (
	FactIdUB_Point_NONE     = 0
	FactIdUB_Point_IN       = 1
	FactIdUB_Point_OUT      = 2
	FactIdUB_Point_INOUT    = 3
	FactIdUB_Point_TRUEOUT  = 4
	FactIdUB_Point_FALSEOUT = 5
)

// Getters
func (f FactId) Version() uint64 {
	return (uint64(f) >> FactIdVersionShift) & FactIdVersionMask
}

func (f FactId) UniqueId() uint64 {
	return (uint64(f) >> FactIdUniqueShift) & FactIdUB_Mask
}

func (f FactId) FactPoint() uint64 {
	return (uint64(f) >> FactIdUB_PointShift) & FactIdUB_PointMask
}

func (f FactId) InstrId() uint64 {
	return (uint64(f) >> FactIdUB_EntityIdShift) & FactIdUB_EntityIdMask
}

func (f FactId) AnalysisId() uint64 {
	return (uint64(f) >> FactIdAnalysisShift) & FactIdAnalysisMask
}

func (f FactId) Reserved() uint64 {
	return (uint64(f) >> FactIdReservedShift) & FactIdReservedMask
}

// IncVersion returns a new FactId with the version part incremented by 1,
// wrapping around to 0 if it exceeds the maximum value for the version bits.
func (f FactId) IncVersion() FactId {
	incVersion := f.Version() + 1
	newVersion := incVersion & FactIdVersionMask
	if newVersion == 0 {
		panic("version overflow")
	}
	return f.WithVersion(newVersion)
}

// ZeroVersion returns a new FactId with the version part set to 0,
// leaving all other fields unchanged. Useful when you want to identify the
// fact ignoring its version (e.g., for equality checks modulo version).
func (f FactId) ZeroVersion() FactId {
	return f.WithVersion(0)
}

// AsKey returns f with the version cleared to zero. It matches ZeroVersion and
// is intended as the map key type when entries should not distinguish versions.
func (f FactId) AsKey() FactId {
	return f.ZeroVersion()
}

// Setters (returns new FactId; immutable style)

// WithVersion sets the version bits (does not alter other data)
func (f FactId) WithVersion(version uint64) FactId {
	v := (uint64(f) & ^(uint64(FactIdVersionMask) << FactIdVersionShift)) | ((version & uint64(FactIdVersionMask)) << FactIdVersionShift)
	return FactId(v)
}

// WithInstrId sets the InstrId bits (does not alter FactPoint etc)
func (f FactId) WithInstrId(instrId uint64) FactId {
	// Clear the instr id region and set
	v := uint64(f)
	v &^= (FactIdUB_EntityIdMask << FactIdUB_EntityIdShift)
	v |= (instrId & FactIdUB_EntityIdMask) << FactIdUB_EntityIdShift
	return FactId(v)
}

// WithFactPoint sets the fact point bits (does not alter EntityId etc)
func (f FactId) WithFactPoint(factPoint uint64) FactId {
	v := uint64(f)
	v &^= (FactIdUB_PointMask << FactIdUB_PointShift)
	v |= (factPoint & FactIdUB_PointMask) << FactIdUB_PointShift
	return FactId(v)
}

// WithUB sets the full UB field (EntityId + FactPoint)
func (f FactId) WithUB(ub uint64) FactId {
	v := uint64(f)
	v &^= FactIdUB_Mask << FactIdUniqueShift
	v |= (ub & FactIdUB_Mask) << FactIdUniqueShift
	return FactId(v)
}

// WithAnalysisId sets the analysis id field
func (f FactId) WithAnalysisId(aid uint64) FactId {
	v := uint64(f)
	v &^= (FactIdAnalysisMask << FactIdAnalysisShift)
	v |= (aid & FactIdAnalysisMask) << FactIdAnalysisShift
	return FactId(v)
}

// WithReserved sets the reserved bits (future use)
func (f FactId) WithReserved(reserved uint64) FactId {
	v := uint64(f)
	v &^= (FactIdReservedMask << FactIdReservedShift)
	v |= (reserved & FactIdReservedMask) << FactIdReservedShift
	return FactId(v)
}

// Utility: BaseKey strips the version part for use as a map key.
func (f FactId) BaseKey() uint64 {
	return uint64(f) & ^(uint64(FactIdVersionMask) << FactIdVersionShift)
}
