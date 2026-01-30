package spir

import "fmt"

// This file defines EntityId, its related types, constants and utility functions.
// EntityId is a 32-bit unsigned integer used to uniquely identify entities in the SPAN IR.

// An Entity ID is a 32 bit unsigned integer which is used to identify an entity.
// The upper 7 to 12 bits are used to identify the entity kind.
//
//	-- The most significant 2 bits are always masked to zero.
//	-- The next 5 bits is the EntityKind.
//	-- If the EntityKind has a sub-kind, then the next 5 bits are used to represent the sub-kind.
//	   E.g. K_EK_EVAR_LOCL has a sub-kind K_VK_INT, K_VK_FLOAT, K_VK_DOUBLE, etc.
//	-- The remaining lower 20 to 25 bits are used to assign a sequential ID to the entity.
type EntityId uint32

const NIL_ID EntityId = 0

// The EntityKind (EK) type is used to represent the kind of an entity in the SPAN IR.
// It is an integer type in the range of 0 to 31 (5 bits)
// that can take on various values to indicate different kinds of entities.
type EntityKind = K_EK

type EId = EntityId

func (e EntityId) String() string {
	return EntityIdString(e, 'x')
}

// EntityIdString prints the different parts of a 32-bit entity ID separated by hyphens.
// The format is: <top-2-bits>-<entity-kind>-<sub-kind>-<seq-id>
// base can be 'd' for decimal, 'o' for octal, or 'x' for hexadecimal
func EntityIdString(id EntityId, base byte) string {
	// Extract the parts
	topBits := uint32(id) >> EIdBitLength
	eKind, subKind, seqId := id.Kind(), id.SubKind(), id.SeqId()

	switch base {
	case 'o':
		return fmt.Sprintf("0o%o-0o%o-0o%o-0o%o", topBits, eKind, subKind, seqId)
	case 'd':
		return fmt.Sprintf("%d-%d-%d-%d", topBits, eKind, subKind, seqId)
	default: // hexadecimal
		return fmt.Sprintf("0x%x-0x%x-0x%x-0x%x", topBits, eKind, subKind, seqId)
	}
}

// EntityId shifts and masks (whole - no divisions)
const EIdBitLength uint8 = 30
const EIdMask32 EntityId = 0x3FFF_FFFF
const EIdShift32 uint8 = 0
const EIdPosMask64 uint64 = 0x3FFF_FFFF_0000_0000
const EIdShift64 uint8 = 32

// EntityKind (EK) is a 5-bit integer that represents the kind of an entity.
const EKPosMask16 uint16 = 0x3E00
const EKShift16 uint8 = 9
const EKPosMask32 uint32 = 0x3E00_0000
const EKShift32 uint8 = 25
const EKPosMask64 uint64 = 0x3E00_0000_0000_0000
const EKShift64 uint8 = 57

// EntitySubKind (ESK) is a 5-bit integer that represents the sub-kind of an entity.
const ESKPosMask16 uint16 = 0x01F0
const ESKShift16 uint8 = 4
const ESKPosMask32 uint32 = 0x01F0_0000
const ESKShift32 uint8 = 20
const ESKPosMask64 uint64 = 0x01F0_0000_0000_0000
const ESKShift64 uint8 = 52

const SeqId20Mask32 uint32 = 0x000F_FFFF
const SeqId20BitCount uint8 = 20
const SeqId20Mask64 uint64 = 0x0000_0000_0000_000F_FFFF

const SeqId25Mask32 uint32 = 0x01FF_FFFF
const SeqId25BitCount uint8 = 25
const SeqId25Mask64 uint64 = 0x0000_0000_01FF_FFFF

const ImmConstBitCount uint8 = 20
const ImmConstMask32 uint32 = 0x000F_FFFF
const ImmConstMask64 uint64 = 0x0000_0000_000F_FFFF

// BLOCK START: API to extract EntityId components and properties

// TrueId returns the zeroed out non-id part of the EntityId.
func (entityId EntityId) TrueId() EntityId {
	return entityId & EIdMask32
}

// IsTrueId returns true if the EntityId is a true entity ID.
func (entityId EntityId) IsTrueId() bool {
	return entityId == entityId.TrueId()
}

// Kind extracts the EntityKind from an EntityId.
// The EntityKind is encoded in bits 25-29 of the EntityId.
func (entityId EntityId) Kind() EntityKind {
	return EntityKind((entityId & EIdMask32) >> EKShift32)
}

// SubKind returns the EntitySubKind from an EntityId.
func (entityId EntityId) SubKind() uint8 {
	subKindBitLen := entityId.Kind().SubKindBitLen()
	if subKindBitLen == 0 {
		return 0
	} else {
		return uint8((uint32(entityId) & ESKPosMask32) >> ESKShift32)
	}
}

// KindAndSubKind16 returns the EntityKind and its sub-kind (if present) as a 16 bit prefix.
func (entityId EntityId) KindAndSubKind16() uint16 {
	return GenKindPrefix16(entityId.Kind(), entityId.SubKind())
}

// SeqId returns the sequence ID part of the EntityId.
func (entityId EntityId) SeqId() uint32 {
	return uint32(entityId) & ((1 << entityId.SeqIdBitLen()) - 1)
}

// SeqIdBitLen returns the number of bits in the sequence ID part of the EntityId.
func (entityId EntityId) SeqIdBitLen() uint8 {
	return entityId.Kind().SeqIdBitLen()
}

// BLOCK END: API to extract EntityId components and properties

// GenImmediate20 generates a 20 bit immediate value only if the value is an integer and fits in 20 bits.
// FIXME: What about sign?
func GenImmediate20(val uint64, vType ValKind) (uint32, bool) {
	if vType.IsInteger() && val == val&ImmConstMask64 {
		return uint32(val & ImmConstMask64), true
	}
	return 0, false
}

// GenKindPrefix16 places the entity kind and sub-kind in the 16 bit prefix.
func GenKindPrefix16(eKind EntityKind, eSubKind uint8) uint16 {
	if eKind.HasSubKind() {
		return uint16(eKind.place16() | (uint16(eSubKind) << ESKShift16))
	} else {
		return uint16(eKind)
	}
}

// GenKindPrefix32 places the entity kind and sub-kind in the 32 bit prefix.
func GenKindPrefix32(eKind EntityKind, eSubKind uint8) uint32 {
	if eKind.HasSubKind() {
		return uint32(eKind.place32() | (uint32(eSubKind) << ESKShift32))
	} else {
		return uint32(eKind)
	}
}

// Does the entity kind have a sub-kind?
// A sub-kind uses another 5 bits to represent the sub type of the entity.
func (eKind EntityKind) HasSubKind() bool {
	if (eKind >= K_EK_EBB && eKind <= K_EK_ESRC_FILE) ||
		eKind == K_EK_ELABEL {
		return false
	}
	return true
}

// Get the sub-kind length in bits
func (eKind EntityKind) SubKindBitLen() uint8 {
	if eKind.HasSubKind() {
		return 5
	}
	return 0
}

func (eKind EntityKind) SeqIdBitLen() uint8 {
	return EKShift32 - eKind.SubKindBitLen()
}

func (eKind EntityKind) place16() uint16 {
	return uint16(eKind) << EKShift16
}

func (eKind EntityKind) place32() uint32 {
	return uint32(eKind) << EKShift32
}

func (eKind EntityKind) place64() uint64 {
	return uint64(eKind) << EKShift64
}

// BLOCK START: API to check entity kind

func (eKind EntityKind) IsVariable() bool {
	if eKind >= K_EK_EVAR_GLBL && eKind <= K_EK_EVAR_LOCL_OTHER {
		return true
	}
	return false
}

func (eKind EntityKind) IsLiteral() bool {
	if eKind == K_EK_ELIT_NUM || eKind == K_EK_ELIT_STR {
		return true
	}
	return false
}

func (eKind EntityKind) IsFunction() bool {
	if eKind == K_EK_EFUNC || eKind == K_EK_EFUNC_VARGS {
		return true
	}
	return false
}

// BLOCK END: API to check entity kind
