package lattice

// FactId uniquely identifies a data flow fact and its history of values.
// The 64 bits are encoded as follows:
//   - 3  bits : For future use
//   - 12 bits : Analysis id
//   - 34 bits : Unique id (split like (2 fact kind bits, 32 instr/BB id bits))
//       * 32 bits : Id of the instruction / BB / function
//       * 2  bits : Fact at IN, OUT, IN & OUT of the instruction, BB or function
//   - 15 bits : Version of the fact (increments per update)
//
// The FactId can be used as key by dropping the 'version' part.

type FactId uint64

// NEW BIT LAYOUT (little-endian/LSB to MSB):
// [0-14]   15b Version
// [15-48]  34b Unique ID (InstrId + FactKind)
//            - [15-16] FactKind (2b)
//            - [17-48] InstrId (32b)
// [49-60]  12b AnalysisId
// [61-63]  3b Reserved

// Bit sizes
const (
	FactIdVersionBits  = 15
	FactIdUniqueBits   = 34
	FactIdAnalysisBits = 12
	FactIdReservedBits = 3

	FactIdFactKindBits = 2
	FactIdInstrIdBits  = 32
)

// Bit shifts for each field
const (
	FactIdVersionShift  = 0
	FactIdUniqueShift   = FactIdVersionShift + FactIdVersionBits   // 15
	FactIdAnalysisShift = FactIdUniqueShift + FactIdUniqueBits     // 49
	FactIdReservedShift = FactIdAnalysisShift + FactIdAnalysisBits // 61

	FactIdFactKindShift = FactIdUniqueShift                        // 15
	FactIdInstrIdShift  = FactIdFactKindShift + FactIdFactKindBits // 17
)

// Masks for each field (before shifting)
const (
	FactIdVersionMask  = (1 << FactIdVersionBits) - 1
	FactIdUniqueMask   = (1 << FactIdUniqueBits) - 1
	FactIdAnalysisMask = (1 << FactIdAnalysisBits) - 1
	FactIdReservedMask = (1 << FactIdReservedBits) - 1

	FactIdFactKindMask = (1 << FactIdFactKindBits) - 1
	FactIdInstrIdMask  = (1 << FactIdInstrIdBits) - 1
)

// Getters
func (f FactId) Version() uint64 {
	return (uint64(f) >> FactIdVersionShift) & FactIdVersionMask
}

func (f FactId) UniqueId() uint64 {
	return (uint64(f) >> FactIdUniqueShift) & FactIdUniqueMask
}

func (f FactId) FactKind() uint64 {
	return (uint64(f) >> FactIdFactKindShift) & FactIdFactKindMask
}

func (f FactId) InstrId() uint64 {
	return (uint64(f) >> FactIdInstrIdShift) & FactIdInstrIdMask
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
	curVersion := f.Version()
	newVersion := (curVersion + 1) & FactIdVersionMask
	return f.WithVersion(newVersion)
}

// ZeroVersion returns a new FactId with the version part set to 0,
// leaving all other fields unchanged. Useful when you want to identify the
// fact ignoring its version (e.g., for equality checks modulo version).
func (f FactId) ZeroVersion() FactId {
	return f.WithVersion(0)
}

// Setters (returns new FactId; immutable style)

// WithVersion sets the version bits (does not alter other data)
func (f FactId) WithVersion(version uint64) FactId {
	v := (uint64(f) & ^(uint64(FactIdVersionMask) << FactIdVersionShift)) | ((version & uint64(FactIdVersionMask)) << FactIdVersionShift)
	return FactId(v)
}

// WithInstrId sets the InstrId bits (does not alter FactKind etc)
func (f FactId) WithInstrId(instrId uint64) FactId {
	// Clear the instr id region and set
	v := uint64(f)
	v &^= (FactIdInstrIdMask << FactIdInstrIdShift)
	v |= (instrId & FactIdInstrIdMask) << FactIdInstrIdShift
	return FactId(v)
}

// WithFactKind sets the fact kind bits (does not alter InstrId etc)
func (f FactId) WithFactKind(factKind uint64) FactId {
	v := uint64(f)
	v &^= (FactIdFactKindMask << FactIdFactKindShift)
	v |= (factKind & FactIdFactKindMask) << FactIdFactKindShift
	return FactId(v)
}

// WithUniqueId sets the full UniqueId field (InstrId + FactKind)
func (f FactId) WithUniqueId(unique uint64) FactId {
	v := uint64(f)
	v &^= (FactIdUniqueMask << FactIdUniqueShift)
	v |= (unique & FactIdUniqueMask) << FactIdUniqueShift
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
