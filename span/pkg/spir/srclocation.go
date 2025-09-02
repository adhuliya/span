package spir

// This file defines the SourceLocation type.

type SrcFileId uint32

// The source location is encoded in a 32-bit unsigned integer.
// The first bit is unused.
// The next 21 bits are identified to a specific source file (source location id)
// The next 10 bits are used to identify the byte position in the file.
// Line number is not explicity stored, but it can be inferred from the byte position.
type SrcLocEnc uint32 // For possible future use.

type SrcFile struct {
	id   SrcFileId
	Name string // The name/path of the source file
	// The range of encoded source location ids associated with this file.
	from uint32
	to   uint32
}

type SrcLocInfo struct {
	srcFileIdMap  map[string]SrcFileId
	srcFiles      map[SrcFileId]SrcFile
	fileIdCounter uint32
	freeSrcLocId  uint32
}

func NewSrcLocInfo() *SrcLocInfo {
	return &SrcLocInfo{
		srcFiles:      make(map[SrcFileId]SrcFile),
		fileIdCounter: 0,
		freeSrcLocId:  0,
	}
}

func (info *SrcLocInfo) GetId(fileName string) SrcFileId {
	if id, ok := info.srcFileIdMap[fileName]; ok {
		return id
	}
	info.fileIdCounter++
	fileId := SrcFileId(info.fileIdCounter)
	info.srcFileIdMap[fileName] = fileId
	info.srcFiles[fileId] = SrcFile{
		id:   fileId,
		Name: fileName,
		from: 0,
		to:   0,
	}
	return fileId
}

// SrcLoc structure holds the source location information with file information.
// Information in SrcLocEnc is decoded into this struct as needed.
type SrcLoc struct {
	srcFileId SrcFileId // The source file id
	line      uint32    // The line number in the source file
	col       uint32    // The column number in the source file
	bytePos   uint32    // The byte position in the source file (optional)
}

func NewSrcLoc(srcFileId SrcFileId, line uint32, col uint32, bytePos uint32) SrcLoc {
	return SrcLoc{
		srcFileId: srcFileId,
		line:      line,
		col:       col,
		bytePos:   bytePos,
	}
}
