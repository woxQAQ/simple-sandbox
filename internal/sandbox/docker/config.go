package docker

import (
	"encoding/base64"
	"encoding/json"

	"github.com/woxqaq/simple-sandbox/internal/config"
)

// Config holds Docker-specific configuration
type Config struct {
	// Image registry settings
	Registry   string `yaml:"registry"`
	Repository string `yaml:"repository"`
	Tag        string `yaml:"tag"`

	// Registry authentication
	Username      string `yaml:"username"`
	Password      string `yaml:"password"`
	Auth          string `yaml:"auth"`
	IdentityToken string `yaml:"identity_token"`
}

// GetConfig returns Docker configuration from global YAML config
func GetConfig() *Config {
	yamlCfg := config.GetYAMLConfig()
	langSettings := yamlCfg.Languages["python"] // Default to python for Docker
	
	return &Config{
		Registry:      yamlCfg.Runtime.ImageRegistry,
		Repository:    langSettings.Repository,
		Tag:           langSettings.Tag,
		Username:      yamlCfg.Runtime.RegistryUsername,
		Password:      yamlCfg.Runtime.RegistryPassword,
		Auth:          yamlCfg.Runtime.RegistryAuth,
		IdentityToken: yamlCfg.Runtime.RegistryIdentityToken,
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

// RegistryAuthInfo holds credentials for registry authentication
type RegistryAuthInfo struct {
	Username      string
	Password      string
	Auth          string
	IdentityToken string
	ServerAddress string
}

// RegistryAuthFor returns registry auth info for the given server
func (c *Config) RegistryAuthFor(server string) RegistryAuthInfo {
	return RegistryAuthInfo{
		Username:      c.Username,
		Password:      c.Password,
		Auth:          c.Auth,
		IdentityToken: c.IdentityToken,
		ServerAddress: server,
	}
}

// DockerRegistryAuthHeader builds the base64-encoded JSON header
func (c *Config) DockerRegistryAuthHeader(info RegistryAuthInfo) (string, error) {
	auth := struct {
		Username      string `json:"username,omitempty"`
		Password      string `json:"password,omitempty"`
		Auth          string `json:"auth,omitempty"`
		IdentityToken string `json:"identitytoken,omitempty"`
		ServerAddress string `json:"serveraddress,omitempty"`
	}{
		Username:      info.Username,
		Password:      info.Password,
		Auth:          info.Auth,
		IdentityToken: info.IdentityToken,
		ServerAddress: info.ServerAddress,
	}

	data, err := json.Marshal(auth)
	if err != nil {
		return "", err
	}

	return base64.URLEncoding.EncodeToString(data), nil
}