package main

import (
	"os"

	"github.com/adhuliya/span/pkg/logger"
	"github.com/spf13/cobra"
)

func initialize() *cobra.Command {
	rootCmd = processCmdLine(os.Args[1:])

	// other initialization code can go here

	return rootCmd
}

func finish() {
	logger.Get().Info(">>>>>>> SPAN finished !!!")
}

func main() {
	rootCmd := initialize()
	defer finish()

	logger.Get().Info(">>>>>>> SPAN started !!!")

	// Execute the root command
	if err := rootCmd.Execute(); err != nil {
		logger.Get().Error("Error executing command", "error", err)
		os.Exit(1)
	}
}
