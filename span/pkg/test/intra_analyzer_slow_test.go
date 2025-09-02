//go:build slow

package test

import (
	"testing"
	"time"
)

// SlowTestExample demonstrates a slow test that only runs with slow build tag
func TestSlowExample(t *testing.T) {
	// This test will only run when using: go test -tags=slow
	t.Log("Running slow test")
	time.Sleep(2 * time.Second) // Simulate slow test
	// Add your slow test logic here
}
