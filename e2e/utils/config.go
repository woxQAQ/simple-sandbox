package utils

import (
	"os"
	"path/filepath"
)

// getConfigFromEnvironment 从环境变量获取配置文件路径
func getConfigFromEnvironment() string {
	// 优先使用 TEST_CONFIG 环境变量
	if config := os.Getenv("TEST_CONFIG"); config != "" {
		return config
	}
	// 兼容 SANDBOX_CONFIG 环境变量
	if config := os.Getenv("SANDBOX_CONFIG"); config != "" {
		return config
	}
	// 默认配置文件路径
	return filepath.Join("testdata", "test_config.yaml")
}