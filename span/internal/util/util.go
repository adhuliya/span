package util

import (
	"fmt"
	"runtime"
)

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
