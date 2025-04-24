package spir

// This file defines the SourceLocation type.

type SourceFileId uint32

// EntitySrcId is used to identify the entity whose source location is to be saved.
// The upper 32 bits are reserved for the Instruction ID.
// The lower 32 bits are used to identify the entity ID.
type EntitySrcId uint64

// The source location is encoded in a 32-bit unsigned integer.
// The first bit is unused.
// The next 21 bits are identified to a specific source file.
// The next 10 bits are used to identify the byte position in the file.
// Line number is not explicity stored, but it can be inferred from the byte position.
type SrcLocation uint32

type SourceLocation struct {
	srcFileId SourceFileId
	line      uint32 // The line number in the source file
	column    uint32 // The column number in the source file
	bytePos   uint32 // The byte position in the source file (optional)
}

type SourceFileInfo struct {
	id   SourceFileId
	Name string // The name of the source file
	// The range of source location ids associated with this file.
	from uint32
	to   uint32
}

type SourceLocationInfo struct {
	sourceFileInfos      map[SourceFileId]SourceFileInfo
	freeSourceLocationId uint32
}

func NewSourceLocationInfo() *SourceLocationInfo {
	return &SourceLocationInfo{
		sourceFileInfos:      make(map[SourceFileId]SourceFileInfo),
		freeSourceLocationId: 0,
	}
}
