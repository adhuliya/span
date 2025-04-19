package spir

// This file defines the SourceLocation type.

type SourceFileId uint32

// The source location is encoded in a 32-bit unsigned integer.
// The first bit is unused.
// The next 21 bits are identified to a specific source file.
// The next 10 bits are used to identify the byte position in the file.
// Line number is not explicity stored, but it can be inferred from the byte position.
type SourceLocation uint32

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
