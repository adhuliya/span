package main

import (
	"log"
	"os"

	"github.com/adhuliya/span/pkg/logger"
)

func initialize() error {
	// Process command line arguments
	initCmdLine()
	if err := processCmdLine(os.Args[1:]); err != nil {
		return err
	}

	rootCmd.Execute()

	// Initialize logger
	return logger.Initialize(getCmdLine().LogConfig)
}

func finish() {
	logger.Get().Info(">>>>>>> SPAN analysis completed !!!")
}

func main() {
	if err := initialize(); err != nil {
		log.Fatalf("Failed to initialize: %v", err)
	}
	defer finish()

	logger.Get().Info(">>>>>>> SPAN analysis started !!!")
}
