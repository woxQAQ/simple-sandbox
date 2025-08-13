package k8s

import (
	"github.com/woxqaq/simple-sandbox/internal/config"
)

// Config holds Kubernetes-specific configuration
type Config struct {
	// Kubernetes settings
	ImagePullSecret string `yaml:"image_pull_secret"`
	Namespace       string `yaml:"namespace"`
}

// GetConfig returns Kubernetes configuration from global YAML config
func GetConfig() *Config {
	yamlCfg := config.GetYAMLConfig()

	return &Config{
		ImagePullSecret: yamlCfg.Runtime.K8sImagePullSecret,
		Namespace:       "default", // Default namespace
	}
}

// K8sImagePullSecret returns the imagePullSecret name used in Pod specs
func (c *Config) K8sImagePullSecret() string {
	return c.ImagePullSecret
}
