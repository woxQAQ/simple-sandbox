package config

import (
	"os"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

type ImageRef struct {
	Registry   string
	Repository string
	Tag        string
}

func get(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func ImageRefFor(lang models.Language) ImageRef {
	switch lang {
	case models.LanguagePython:
		return ImageRef{
			Registry:   get("SANDBOX_IMAGE_PYTHON_REGISTRY", "docker.io"),
			Repository: get("SANDBOX_IMAGE_PYTHON_REPOSITORY", "sandbox-python"),
			Tag:        get("SANDBOX_IMAGE_PYTHON_TAG", "latest"),
		}
	case models.LanguageNode:
		return ImageRef{
			Registry:   get("SANDBOX_IMAGE_NODE_REGISTRY", "docker.io"),
			Repository: get("SANDBOX_IMAGE_NODE_REPOSITORY", "sandbox-node"),
			Tag:        get("SANDBOX_IMAGE_NODE_TAG", "latest"),
		}
	default:
		return ImageRef{Registry: "docker.io", Repository: "sandbox-unknown", Tag: "latest"}
	}
}
