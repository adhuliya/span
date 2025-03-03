package main

import (
	"github.com/adhuliya/span/pkg/logger"
	"github.com/spf13/cobra"
)

type CmdLine struct {
	LogConfig logger.LogConfig
	Command   string
}

var (
	cmdLine CmdLine
	rootCmd = &cobra.Command{
		Use:   "span",
		Short: "Synergistic Program Analyzer",
		Long:  `SPAN is a program analysis engine for analyzing C programs`,
	}
)

// All command line options are initialized and setup here.
func initCmdLine() {
	rootCmd.PersistentFlags().StringVar(&cmdLine.LogConfig.Level, "log-level", "info", "Set logging level (debug, info, warn, error)")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.LogConfig.ShowTime, "log-time", false, "Show timestamp in logs")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.LogConfig.ShowSource, "log-source", true, "Show source location in logs")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.LogConfig.ShowFunction, "log-func", false, "Show function name in logs")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.LogConfig.UseJSON, "log-json", false, "Use JSON format for logging")

	// Add subcommands
	rootCmd.AddCommand(analyzeCmd)
	rootCmd.AddCommand(linkCmd)
}

var analyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze a SPIR file",
	Run: func(cmd *cobra.Command, args []string) {
		cmdLine.Command = "analyze"
		// TODO: Implement analyze
	},
}

var linkCmd = &cobra.Command{
	Use:   "link",
	Short: "Link multiple SPIR files",
	Run: func(cmd *cobra.Command, args []string) {
		cmdLine.Command = "link"
		// TODO: Implement link
	},
}

func processCmdLine(args []string) error {
	rootCmd.SetArgs(args)
	err := Run(func() error {
		return logger.Initialize(cmdLine.LogConfig)
	}, nil)
	return err
}

func executeAnalyze() error {
	// TODO: Implement analyze
	return nil
}

func executeLink() error {
	// TODO: Implement link
	return nil
}

func getCmdLine() *CmdLine {
	return &cmdLine
}
