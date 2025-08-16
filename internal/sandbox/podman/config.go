package podman

import (
	"encoding/base64"
	"encoding/json"

	"github.com/woxqaq/simple-sandbox/internal/config"
)

// Config holds Podman-specific configuration
type Config struct {
	// Registry authentication
	Username      string `yaml:"username"`
	Password      string `yaml:"password"`
	Auth          string `yaml:"auth"`
	IdentityToken string `yaml:"identity_token"`
}

// GetConfig returns Podman configuration from global YAML config
func GetConfig() *Config {
	yamlCfg := config.GetYAMLConfig()

	return &Config{
		Username:      yamlCfg.Runtime.RegistryUsername,
		Password:      yamlCfg.Runtime.RegistryPassword,
		Auth:          yamlCfg.Runtime.RegistryAuth,
		IdentityToken: yamlCfg.Runtime.RegistryIdentityToken,
	}
}

// RegistryAuthInfo holds credentials for registry authentication
type RegistryAuthInfo struct {
	Username      string
	Password      string
	Auth          string
	IdentityToken string
	ServerAddress string
}

// PodmanRegistryAuthHeader encodes itself into Podman's registry auth format
func (i RegistryAuthInfo) PodmanRegistryAuthHeader() (string, error) {
	auth := map[string]interface{}{
		"username":      i.Username,
		"password":      i.Password,
		"auth":          i.Auth,
		"identitytoken": i.IdentityToken,
		"serveraddress": i.ServerAddress,
	}

	data, err := json.Marshal(auth)
	if err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(data), nil
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
