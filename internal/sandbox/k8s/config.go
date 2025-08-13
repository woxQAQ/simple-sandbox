package k8s

import (
	"github.com/woxqaq/simple-sandbox/internal/config"
)

// Config holds Kubernetes-specific configuration
type Config struct {
	// Image settings
	Registry   string `yaml:"registry"`
	Repository string `yaml:"repository"`
	Tag        string `yaml:"tag"`

	// Kubernetes settings
	ImagePullSecret string `yaml:"image_pull_secret"`
	Namespace       string `yaml:"namespace"`
}

// GetConfig returns Kubernetes configuration from global YAML config
func GetConfig() *Config {
	yamlCfg := config.GetYAMLConfig()
	langSettings := yamlCfg.Languages["python"] // Default to python for K8s
	
	return &Config{
		Registry:        yamlCfg.Runtime.ImageRegistry,
		Repository:      langSettings.Repository,
		Tag:             langSettings.Tag,
		ImagePullSecret: yamlCfg.Runtime.K8sImagePullSecret,
		Namespace:       "default", // Default namespace
	}
}

// ImageRef represents a container image reference parts
type ImageRef struct {
	Registry   string
	Repository string
	Tag        string
}

// ImageRefFor returns the image reference for a given language
func (c *Config) ImageRefFor(lang string) ImageRef {
	registry := c.Registry
	if registry == "" {
		registry = "docker.io"
	}

	yamlCfg := config.GetYAMLConfig()
	langSettings, ok := yamlCfg.Languages[lang]
	if !ok {
		langSettings = yamlCfg.Languages["python"] // Fallback to python
	}

	repo := langSettings.Repository
	if repo == "" {
		repo = "sandbox-python"
	}

	tag := langSettings.Tag
	if tag == "" {
		tag = "latest"
	}

	return ImageRef{
		Registry:   registry,
		Repository: repo,
		Tag:        tag,
	}
}

// ImageFor returns the full image reference string
func (c *Config) ImageFor(lang string) string {
	ref := c.ImageRefFor(lang)
	return ref.Registry + "/" + ref.Repository + ":" + ref.Tag
}

// K8sImagePullSecret returns the imagePullSecret name used in Pod specs
func (c *Config) K8sImagePullSecret() string {
	return c.ImagePullSecret
}