//go:build !release

package errs

import (
	"fmt"
	"runtime"
)

// Assert is a simple assertion function that panics if the condition is false.
func Assert(cond bool, msg string) {
	if !cond {
		panic(msg)
	}
}

// Handles panic by skipping the given number of call frames,
// to reach the function that caused the panic.
func HandlePanic(skip int) {
	if r := recover(); r != nil {
		// Print the recovered error
		fmt.Println("Recovered from panic:", r)

		// Get the call stack
		pc, file, line, ok := runtime.Caller(skip) // Adjust the depth as needed
		if ok {
			fn := runtime.FuncForPC(pc)
			fmt.Printf("Panic occurred in function: %s\n", fn.Name())
			fmt.Printf("At: %s:%d\n", file, line)
		} else {
			fmt.Println("Could not get caller info")
		}
	}
}

// Print the stack trace in case of a panic.
func HandlePanicAndPrintStackTrace() {
	if r := recover(); r != nil {
		fmt.Println("Recovered from panic:", r)

		// Capture up to 32 stack frames
		const size = 32
		var pcs [size]uintptr
		n := runtime.Callers(3, pcs[:]) // skip 3 frames: Callers, HandlePanic, and defer

		frames := runtime.CallersFrames(pcs[:n])

		fmt.Println("Stack trace:")
		for {
			frame, more := frames.Next()
			fmt.Printf("- %s\n  %s:%d\n", frame.Function, frame.File, frame.Line)
			if !more {
				break
			}
		}
	}
}
