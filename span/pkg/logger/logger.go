package logger

import (
	"log/slog"
	"os"
)

var logger *slog.Logger

type LogConfig struct {
	Level        string
	ShowTime     bool // FIXME: handle this
	ShowSource   bool
	ShowFunction bool // FIXME: handle this
	UseJSON      bool
}

func NewLogConfig(level string) *LogConfig {
	return &LogConfig{
		Level:        level,
		ShowTime:     false,
		ShowSource:   true,
		ShowFunction: false,
		UseJSON:      false,
	}
}

func Initialize(config *LogConfig) error {
	var level slog.Level
	switch config.Level {
	case "debug":
		level = slog.LevelDebug
	case "info":
		level = slog.LevelInfo
	case "warn":
		level = slog.LevelWarn
	case "error":
		level = slog.LevelError
	default:
		level = slog.LevelInfo
	}

	opts := &slog.HandlerOptions{
		Level:     level,
		AddSource: config.ShowSource,
		ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
			// Remove the time attribute
			if a.Key == slog.TimeKey && !config.ShowTime {
				return slog.Attr{}
			}
			return a
		},
	}
	var handler slog.Handler

	if config.UseJSON {
		handler = slog.NewJSONHandler(os.Stdout, opts)
	} else {
		handler = slog.NewTextHandler(os.Stdout, opts)
	}

	logger = slog.New(handler)
	logger.Info("Logger initialized",
		slog.String("level", config.Level),
		slog.Bool("show_time", config.ShowTime),
		slog.Bool("show_source", config.ShowSource),
		slog.Bool("show_function", config.ShowFunction),
		slog.Bool("use_json", config.UseJSON),
	)
	return nil
}

func Get() *slog.Logger {
	return logger
}
