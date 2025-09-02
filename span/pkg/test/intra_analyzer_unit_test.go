//go:build unit

package test

import (
	"testing"
)

// UnitTestExample demonstrates a unit test that only runs with unit build tag
func TestUnitExample(t *testing.T) {
	// This test will only run when using: go test -tags=unit
	t.Log("Running unit test")
	// Add your unit test logic here
}
