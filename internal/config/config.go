package config

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"io/fs"
	"os"
	"strconv"

	"github.com/woxqaq/simple-sandbox/internal/models"
	"gopkg.in/yaml.v3"
)

// RuntimeConfig holds all runtime environment configurations
type RuntimeConfig struct {
	Backend        string `env:"SANDBOX_BACKEND" default:"docker"`
	MaxConcurrency int    `env:"SANDBOX_MAX_CONCURRENCY" default:"4"`
	MaxQueue       int    `env:"SANDBOX_MAX_QUEUE" default:"32"`
	ImageRegistry  string `env:"SANDBOX_IMAGE_REGISTRY" default:"docker.io"`
	CRISocket      string `env:"SANDBOX_CRI_SOCKET" default:"unix:///run/containerd/containerd.sock"`

	// Registry authentication
	RegistryUsername      string `env:"SANDBOX_REGISTRY_USERNAME"`
	RegistryPassword      string `env:"SANDBOX_REGISTRY_PASSWORD"`
	RegistryAuth          string `env:"SANDBOX_REGISTRY_AUTH"`
	RegistryIdentityToken string `env:"SANDBOX_REGISTRY_IDENTITY_TOKEN"`

	// Kubernetes settings
	K8sImagePullSecret string `env:"SANDBOX_K8S_IMAGE_PULL_SECRET"`
}

var runtimeConfig *RuntimeConfig

// GetRuntimeConfig returns the loaded runtime configuration (lazy loaded)
func GetRuntimeConfig() *RuntimeConfig {
	if runtimeConfig != nil {
		return runtimeConfig
	}

	runtimeConfig = &RuntimeConfig{
		Backend:               getEnv("SANDBOX_BACKEND", "docker"),
		MaxConcurrency:        getEnvInt("SANDBOX_MAX_CONCURRENCY", 4),
		MaxQueue:              getEnvInt("SANDBOX_MAX_QUEUE", 32),
		ImageRegistry:         getEnv("SANDBOX_IMAGE_REGISTRY", "docker.io"),
		CRISocket:             getEnv("SANDBOX_CRI_SOCKET", "unix:///run/containerd/containerd.sock"),
		RegistryUsername:      getEnv("SANDBOX_REGISTRY_USERNAME", ""),
		RegistryPassword:      getEnv("SANDBOX_REGISTRY_PASSWORD", ""),
		RegistryAuth:          getEnv("SANDBOX_REGISTRY_AUTH", ""),
		RegistryIdentityToken: getEnv("SANDBOX_REGISTRY_IDENTITY_TOKEN", ""),
		K8sImagePullSecret:    getEnv("SANDBOX_K8S_IMAGE_PULL_SECRET", ""),
	}

	return runtimeConfig
}

// getEnv returns environment variable or default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvInt returns environment variable as integer or default value
func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// ImageRef represents a container image reference parts.
type ImageRef struct {
	Registry   string
	Repository string
	Tag        string
}

// Registry returns the global registry host from runtime configuration
func Registry() string {
	return GetRuntimeConfig().ImageRegistry
}

// ImageRefFor returns the image reference for a given language.
// Registry comes from runtime config, repository/tag from YAML config.
func ImageRefFor(lang string) ImageRef {
	registry := Registry()
	ls := getLangSettings(lang)

	repo := ls.Repository
	if repo == "" {
		switch lang {
		case models.LanguagePython:
			repo = "sandbox-python"
		case models.LanguageNode:
			repo = "sandbox-node"
		default:
			repo = "sandbox-unknown"
		}
	}

	tag := ls.Tag
	if tag == "" {
		tag = "latest"
	}

	return ImageRef{Registry: registry, Repository: repo, Tag: tag}
}

// ImageFor returns the full image reference string (registry/repository:tag) for a language.
func ImageFor(lang string) string {
	ref := ImageRefFor(lang)
	return ref.Registry + "/" + ref.Repository + ":" + ref.Tag
}

// RegistryAuthInfo holds credentials and tokens to authenticate against a container registry.
type RegistryAuthInfo struct {
	Username      string
	Password      string
	Auth          string
	IdentityToken string
	ServerAddress string
}

// RegistryAuthFor returns registry auth info for the given server from runtime configuration.
func RegistryAuthFor(server string) RegistryAuthInfo {
	cfg := GetRuntimeConfig()
	return RegistryAuthInfo{
		Username:      cfg.RegistryUsername,
		Password:      cfg.RegistryPassword,
		Auth:          cfg.RegistryAuth,
		IdentityToken: cfg.RegistryIdentityToken,
		ServerAddress: server,
	}
}

// DockerRegistryAuthHeader builds the base64-encoded JSON header for Docker ImagePullOptions.RegistryAuth.
func DockerRegistryAuthHeader(info RegistryAuthInfo) (string, error) {
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

// K8sImagePullSecret returns the global imagePullSecret name used in Pod specs.
func K8sImagePullSecret() string {
	return GetRuntimeConfig().K8sImagePullSecret
}

// YAML Configuration structures
type SeccompLangConfig struct {
	CRIMode         string `yaml:"cri_mode"`
	CRILocalhostRef string `yaml:"cri_localhost_ref"`
	K8sMode         string `yaml:"k8s_mode"`
	K8sLocalhostRef string `yaml:"k8s_localhost_ref"`
}

type LanguageSettings struct {
	Repository string            `yaml:"repository"`
	Tag        string            `yaml:"tag"`
	Seccomp    SeccompLangConfig `yaml:"seccomp"`
}

// SandboxConfig holds all YAML-based application configurations
type SandboxConfig struct {
	Languages map[string]LanguageSettings `yaml:"languages"`
}

var yamlConfig *SandboxConfig

// Init loads YAML config from SANDBOX_CONFIG path or default "sandbox.yaml" in CWD.
func Init() error {
	path := os.Getenv("SANDBOX_CONFIG")
	if path == "" {
		path = "sandbox.yaml"
	}

	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			yamlConfig = &SandboxConfig{Languages: map[string]LanguageSettings{}}
			return nil
		}
		return err
	}

	var cfg SandboxConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return err
	}

	if cfg.Languages == nil {
		cfg.Languages = map[string]LanguageSettings{}
	}

	yamlConfig = &cfg
	return nil
}

// GetYAMLConfig returns the loaded YAML configuration
func GetYAMLConfig() *SandboxConfig {
	if yamlConfig == nil {
		return &SandboxConfig{Languages: map[string]LanguageSettings{}}
	}
	return yamlConfig
}

// getLangSettings returns language settings from YAML configuration
func getLangSettings(lang string) LanguageSettings {
	if yamlConfig == nil || yamlConfig.Languages == nil {
		return LanguageSettings{}
	}

	key := lang
	if settings, ok := yamlConfig.Languages[key]; ok {
		return settings
	}

	return LanguageSettings{}
}

// SeccompSetting is the resolved seccomp profile for a language and backend.
type SeccompSetting struct {
	Mode         string // runtimeDefault|unconfined|localhost
	LocalhostRef string // for localhost mode
}

// SeccompForCRI returns the CRI seccomp setting for the given language.
func SeccompForCRI(lang string) SeccompSetting {
	settings := getLangSettings(lang)
	mode := settings.Seccomp.CRIMode
	if mode == "" {
		mode = "runtimeDefault"
	}
	return SeccompSetting{
		Mode:         mode,
		LocalhostRef: settings.Seccomp.CRILocalhostRef,
	}
}

// SeccompForK8s returns the K8s seccomp setting for the given language.
func SeccompForK8s(lang string) SeccompSetting {
	settings := getLangSettings(lang)
	mode := settings.Seccomp.K8sMode
	if mode == "" {
		mode = "runtimeDefault"
	}
	return SeccompSetting{
		Mode:         mode,
		LocalhostRef: settings.Seccomp.K8sLocalhostRef,
	}
}
