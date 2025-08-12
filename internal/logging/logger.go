package logging

import (
	"go.uber.org/zap"
)

var (
	Logger *zap.Logger
)

// Init initializes a global production JSON logger.
func Init() error {
	cfg := zap.NewProductionConfig()
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
