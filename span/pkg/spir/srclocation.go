package spir

// This file defines the SourceLocation type.

type FileId EntityId

// The source location is encoded in a 32-bit unsigned integer.
// The first bit is unused.
// The next 21 bits are identified to a specific source file (source location id)
// The next 10 bits are used to identify the byte position in the file.
// Line number is not explicity stored, but it can be inferred from the byte position.
type SrcLocEnc uint32 // For possible future use.

type SrcFile struct {
	id        FileId
	name      string // The name/path of the source file
	directory string // The directory of the source file
}

type SrcFilesInfo struct {
	fileIdMap     map[string]FileId
	files         map[FileId]SrcFile
	fileIdCounter uint32
	freeSrcLocId  uint32
}

func NewSrcFilesInfo() *SrcFilesInfo {
	return &SrcFilesInfo{
		fileIdMap:     make(map[string]FileId),
		files:         make(map[FileId]SrcFile),
		fileIdCounter: 0,
		freeSrcLocId:  0,
	}
}

// SrcLoc structure holds the source location information.
type SrcLoc struct {
	line uint32 // The line number in the source file
	col  uint32 // The column number in the source file
}

func NewSrcLoc(line uint32, col uint32) SrcLoc {
	return SrcLoc{
		line: line,
		col:  col,
	}
}

func (sl SrcLoc) GetLine() uint32 {
	return sl.line
}

func (sl SrcLoc) GetCol() uint32 {
	return sl.col
}
