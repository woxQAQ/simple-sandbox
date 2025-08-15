package logging

import (
	"go.uber.org/zap"
)

var (
	Logger *zap.Logger
)

// Init initializes a global production JSON logger.
func Init(mode string) error {
	var cfg zap.Config
	switch mode {
	case "release":
		cfg = zap.NewProductionConfig()
	case "debug":
		cfg = zap.NewDevelopmentConfig()
	default:
		cfg = zap.NewDevelopmentConfig()
	}
	cfg.Encoding = "json"
	l, err := cfg.Build()
	if err != nil {
		return err
	}
	Logger = l
	return nil
}

// Sync flushes any buffered log entries.
func Sync() {
	if Logger != nil {
		_ = Logger.Sync()
	}
}
