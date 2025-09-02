#!/bin/bash

# Simple script to list APIs in a Go project using built-in Go tools

set -e

PROJECT_ROOT="${1:-.}"
OUTPUT_FILE="${2:-api_documentation.md}"

echo "=== SPAN Project API Documentation ===" > "$OUTPUT_FILE"
echo "Generated on: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "## Commands" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# List commands using go doc
echo "### Available Commands" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Find main packages and their commands
find "$PROJECT_ROOT" -name "main.go" -type f | while read -r main_file; do
    dir=$(dirname "$main_file")
    echo "**Package:** $dir" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Get command help if it's a Cobra command
    if cd "$dir" 2>/dev/null; then
        if go build -o /tmp/span_test . 2>/dev/null; then
            echo "**Available Commands:**" >> "$OUTPUT_FILE"
            ./span_test --help 2>/dev/null | sed 's/^/  /' >> "$OUTPUT_FILE" || true
            echo "" >> "$OUTPUT_FILE"
            rm -f /tmp/span_test
        fi
        cd - > /dev/null
    fi
done

echo "## Packages" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# List all packages
find "$PROJECT_ROOT" -name "*.go" -not -name "*_test.go" | \
    xargs grep -l "^package " | \
    sed 's|/[^/]*$||' | \
    sort -u | \
    while read -r pkg_dir; do
        pkg_name=$(basename "$pkg_dir")
        echo "### Package: $pkg_name" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        # Get package documentation
        if cd "$pkg_dir" 2>/dev/null; then
            echo "**Package Documentation:**" >> "$OUTPUT_FILE"
            go doc . 2>/dev/null | sed 's/^/  /' >> "$OUTPUT_FILE" || echo "  No documentation available" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
            
            # List exported functions and types
            echo "**Exported Functions and Types:**" >> "$OUTPUT_FILE"
            go list -f '{{range .GoFiles}}{{.}} {{end}}' . 2>/dev/null | \
                xargs grep -h "^func [A-Z]" 2>/dev/null | \
                sed 's/^/  /' >> "$OUTPUT_FILE" || true
            
            go list -f '{{range .GoFiles}}{{.}} {{end}}' . 2>/dev/null | \
                xargs grep -h "^type [A-Z]" 2>/dev/null | \
                sed 's/^/  /' >> "$OUTPUT_FILE" || true
            
            echo "" >> "$OUTPUT_FILE"
            cd - > /dev/null
        fi
    done

echo "## Quick API Reference" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Generate quick reference using go list
echo "### All Packages" >> "$OUTPUT_FILE"
go list ./... 2>/dev/null | sed 's/^/  - /' >> "$OUTPUT_FILE" || echo "  No packages found" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "### Build Information" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "**Go Version:** $(go version)" >> "$OUTPUT_FILE"
echo "**Module:** $(go list -m 2>/dev/null || echo 'Not a module')" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "API documentation generated in: $OUTPUT_FILE"