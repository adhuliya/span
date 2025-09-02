//go:build (integration || e2e) && !skip

package test

import (
	"os"
	"testing"
)

// ComprehensiveTestExample demonstrates tests that run in integration or e2e environments
// but can be skipped with the skip tag
func TestComprehensiveExample(t *testing.T) {
	// This test runs when using: go test -tags=integration or go test -tags=e2e
	// But can be skipped with: go test -tags=skip
	t.Log("Running comprehensive test")

	// Example of environment-based test logic
	if os.Getenv("CI") == "true" {
		t.Log("Running in CI environment")
	}

	// Add your comprehensive test logic here
}

// TestWithMultipleTags demonstrates using multiple build constraints
func TestWithMultipleTags(t *testing.T) {
	// This test demonstrates conditional logic based on build tags
	t.Log("Test with multiple tag support")
}
