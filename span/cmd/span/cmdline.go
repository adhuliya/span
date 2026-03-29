package main

import (
	"strings"

	"github.com/adhuliya/span/pkg/logger"
	"github.com/adhuliya/span/pkg/spir"
	"github.com/spf13/cobra"
)

type CmdLine struct {
	LogConfig  logger.LogConfig
	Command    string
	InputFiles []string // Positional (non-flag) arguments: typically input file paths.
	DumpTUTxt  bool
}

var (
	cmdLine CmdLine
	rootCmd = &cobra.Command{
		Use:   "span",
		Short: "Synergistic Program Analyzer",
		Long:  `SPAN is a program analysis engine for analyzing C11 standard programs. It can analyze single or multiple SPIR files.`,
	}
)

// All command line options are configured and setup here.
func configureCommand() {
	rootCmd.PersistentFlags().StringVar(&cmdLine.LogConfig.Level, "log-level", "info", "Set logging level (debug, info, warn, error)")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.LogConfig.ShowTime, "log-time", false, "Show timestamp in logs")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.LogConfig.ShowSource, "log-source", true, "Show source location in logs")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.LogConfig.ShowFunction, "log-func", false, "Show function name in logs")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.LogConfig.UseJSON, "log-json", false, "Use JSON format for logging")
	rootCmd.PersistentFlags().BoolVar(&cmdLine.DumpTUTxt, "dump-txt",
		false, "Dump the TU in text format (default: false)")

	// Add subcommands
	rootCmd.AddCommand(analyzeCmd)
	rootCmd.AddCommand(loacCmd())
}

var analyzeCmd = &cobra.Command{
	Use:   "analyze [flags] [files...]",
	Short: "Analyze a SPIR file",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		cmdLine.Command = "analyze"
		cmdLine.InputFiles = args
		logger.Get().Info("Analyzing SPIR file...")
		// TODO: Implement analyze
	},
}

var loacCmd = func() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "load [flags] [files...]",
		Short: "Load SPIR protocol buffer file(s) into memory",
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			cmdLine.Command = "load"
			cmdLine.InputFiles = args
			executeLoad()
		},
	}
	return cmd
}

// processCmdLine processes the command line arguments and initializes the logger.
// It returns an error if the initialization fails.
// The function is designed to be called from the main function.
func processCmdLine(args []string) *cobra.Command {
	configureCommand()

	// Set the command line arguments
	rootCmd.SetArgs(args)

	// Initialize the logger
	err := FirstError(func() error {
		return logger.Initialize(&cmdLine.LogConfig)
	}, nil)

	if err != nil {
		panic("Failed to initialize process command line: %v" + err.Error())
	}

	return rootCmd
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

func executeLoad() {
	// This function loads all SPIR protocol buffer files listed in the command line args.
	// It iterates through all arguments, filters for files ending with ".spir.pb",
	// loads each one using ReadSpirProto, converts it to an internal TU, and errors
	// out on any file not ending with ".spir.pb".

	args := getCmdLine().InputFiles

	if len(args) == 0 {
		logger.Get().Error("No input files specified")
		return
	}

	for _, file := range args {
		if !strings.HasSuffix(file, ".spir.pb") {
			logger.Get().Error("Invalid file extension for: " + file + " (expected .spir.pb)")
			return
		}
		logger.Get().Info("Loading SPIR protocol buffer file: " + file)
		bitTU, err := spir.ReadSpirProto(file)
		if err != nil {
			logger.Get().Error("Failed to read SPIR proto file: "+file, "error", err)
			return
		}

		tu := spir.ConvertBitTUToInternalTU(bitTU)
		if tu == nil {
			logger.Get().Error("Failed to convert to internal TU for file: " + file)
			return
		}

		// Optionally store or process the TU here, e.g., add it to a list for later use.
		logger.Get().Info("Successfully loaded and converted SPIR file: " + file)
		if getCmdLine().DumpTUTxt {
			logger.Get().Info("Dumping TU in text format: " + file)
			tu.Dump()
		}
	}

}
