package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// APIInfo represents information about an API
type APIInfo struct {
	Package     string
	Name        string
	Type        string // "function", "method", "type", "constant", "variable"
	Exported    bool
	File        string
	Line        int
	Description string
}

// ProjectAPI represents the complete API structure
type ProjectAPI struct {
	Packages map[string][]APIInfo
	Commands []APIInfo
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run scripts/list_apis.go <project-root>")
		fmt.Println("Example: go run scripts/list_apis.go .")
		os.Exit(1)
	}

	projectRoot := os.Args[1]
	api := &ProjectAPI{
		Packages: make(map[string][]APIInfo),
		Commands: []APIInfo{},
	}

	// Analyze the project
	err := analyzeProject(projectRoot, api)
	if err != nil {
		fmt.Printf("Error analyzing project: %v\n", err)
		os.Exit(1)
	}

	// Print the results
	printAPI(api)
}

func analyzeProject(root string, api *ProjectAPI) error {
	return filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip vendor, test files, and non-Go files
		if info.IsDir() {
			if info.Name() == "vendor" || info.Name() == ".git" {
				return filepath.SkipDir
			}
			return nil
		}

		if !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
			return nil
		}

		// Parse the Go file
		fset := token.NewFileSet()
		node, err := parser.ParseFile(fset, path, nil, parser.ParseComments)
		if err != nil {
			return err
		}

		// Extract package name
		packageName := node.Name.Name
		if packageName == "main" {
			// Handle main packages (commands)
			analyzeMainPackage(node, fset, path, api)
		} else {
			// Handle library packages
			analyzePackage(node, fset, path, api)
		}

		return nil
	})
}

func analyzeMainPackage(node *ast.File, fset *token.FileSet, filePath string, api *ProjectAPI) {
	// Look for Cobra commands
	ast.Inspect(node, func(n ast.Node) bool {
		switch x := n.(type) {
		case *ast.ValueSpec:
			if len(x.Names) > 0 && len(x.Values) > 0 {
				name := x.Names[0].Name
				if strings.HasSuffix(name, "Cmd") {
					// This might be a Cobra command
					api.Commands = append(api.Commands, APIInfo{
						Package:     "main",
						Name:        name,
						Type:        "command",
						Exported:    ast.IsExported(name),
						File:        filePath,
						Line:        fset.Position(x.Pos()).Line,
						Description: extractComment(x.Doc),
					})
				}
			}
		}
		return true
	})
}

func analyzePackage(node *ast.File, fset *token.FileSet, filePath string, api *ProjectAPI) {
	packageName := node.Name.Name
	var apis []APIInfo

	ast.Inspect(node, func(n ast.Node) bool {
		switch x := n.(type) {
		case *ast.FuncDecl:
			// Function or method
			apiType := "function"
			if x.Recv != nil {
				apiType = "method"
			}

			apis = append(apis, APIInfo{
				Package:     packageName,
				Name:        x.Name.Name,
				Type:        apiType,
				Exported:    ast.IsExported(x.Name.Name),
				File:        filePath,
				Line:        fset.Position(x.Pos()).Line,
				Description: extractComment(x.Doc),
			})

		case *ast.GenDecl:
			switch x.Tok {
			case token.TYPE:
				// Type declarations
				for _, spec := range x.Specs {
					if typeSpec, ok := spec.(*ast.TypeSpec); ok {
						apis = append(apis, APIInfo{
							Package:     packageName,
							Name:        typeSpec.Name.Name,
							Type:        "type",
							Exported:    ast.IsExported(typeSpec.Name.Name),
							File:        filePath,
							Line:        fset.Position(x.Pos()).Line,
							Description: extractComment(x.Doc),
						})
					}
				}

			case token.CONST:
				// Constants
				for _, spec := range x.Specs {
					if valueSpec, ok := spec.(*ast.ValueSpec); ok {
						for _, name := range valueSpec.Names {
							apis = append(apis, APIInfo{
								Package:     packageName,
								Name:        name.Name,
								Type:        "constant",
								Exported:    ast.IsExported(name.Name),
								File:        filePath,
								Line:        fset.Position(x.Pos()).Line,
								Description: extractComment(x.Doc),
							})
						}
					}
				}

			case token.VAR:
				// Variables
				for _, spec := range x.Specs {
					if valueSpec, ok := spec.(*ast.ValueSpec); ok {
						for _, name := range valueSpec.Names {
							apis = append(apis, APIInfo{
								Package:     packageName,
								Name:        name.Name,
								Type:        "variable",
								Exported:    ast.IsExported(name.Name),
								File:        filePath,
								Line:        fset.Position(x.Pos()).Line,
								Description: extractComment(x.Doc),
							})
						}
					}
				}
			}
		}
		return true
	})

	if len(apis) > 0 {
		api.Packages[packageName] = append(api.Packages[packageName], apis...)
	}
}

func extractComment(group *ast.CommentGroup) string {
	if group == nil {
		return ""
	}
	return strings.TrimSpace(group.Text())
}

func printAPI(api *ProjectAPI) {
	fmt.Println("=== SPAN Project API Documentation ===\n")

	// Print commands
	if len(api.Commands) > 0 {
		fmt.Println("## Commands")
		fmt.Println()
		for _, cmd := range api.Commands {
			fmt.Printf("- **%s** (%s:%d)\n", cmd.Name, cmd.File, cmd.Line)
			if cmd.Description != "" {
				fmt.Printf("  %s\n", cmd.Description)
			}
			fmt.Println()
		}
	}

	// Print packages
	var packages []string
	for pkg := range api.Packages {
		packages = append(packages, pkg)
	}
	sort.Strings(packages)

	for _, pkg := range packages {
		apis := api.Packages[pkg]
		fmt.Printf("## Package: %s\n\n", pkg)

		// Group by type
		grouped := groupByType(apis)
		for _, apiType := range []string{"type", "function", "method", "constant", "variable"} {
			if apis, exists := grouped[apiType]; exists {
				fmt.Printf("### %s\n\n", strings.Title(apiType))
				for _, api := range apis {
					exported := ""
					if api.Exported {
						exported = " (exported)"
					}
					fmt.Printf("- **%s**%s (%s:%d)\n", api.Name, exported, api.File, api.Line)
					if api.Description != "" {
						fmt.Printf("  %s\n", api.Description)
					}
					fmt.Println()
				}
			}
		}
	}
}

func groupByType(apis []APIInfo) map[string][]APIInfo {
	grouped := make(map[string][]APIInfo)
	for _, api := range apis {
		grouped[api.Type] = append(grouped[api.Type], api)
	}
	return grouped
} 