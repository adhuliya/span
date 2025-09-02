//go:build release

package errs

// Assert is a no-op in release builds
func Assert(cond bool, msg string) {}

// HandlePanic is a no-op in release builds
func HandlePanic(skip int) {}

// HandlePanicAndPrintStackTrace is a no-op in release builds
func HandlePanicAndPrintStackTrace() {}
