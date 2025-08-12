package config

import (
	"os"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

type SeccompSetting struct {
	Mode         string // runtimeDefault|unconfined|localhost
	LocalhostRef string // for localhost mode
}

func getOverride(baseKey string, lang models.Language) string {
	switch lang {
	case models.LanguagePython:
		if v := os.Getenv(baseKey + "_PYTHON"); v != "" {
			return v
		}
	case models.LanguageNode:
		if v := os.Getenv(baseKey + "_NODE"); v != "" {
			return v
		}
	}
	return os.Getenv(baseKey)
}

func SeccompForCRI(lang models.Language) SeccompSetting {
	mode := getOverride("SANDBOX_CRI_SECCOMP_MODE", lang)
	if mode == "" {
		mode = "runtimeDefault"
	}
	ref := getOverride("SANDBOX_CRI_SECCOMP_LOCALHOST_REF", lang)
	return SeccompSetting{Mode: mode, LocalhostRef: ref}
}

func SeccompForK8s(lang models.Language) SeccompSetting {
	mode := getOverride("SANDBOX_K8S_SECCOMP_MODE", lang)
	if mode == "" {
		mode = "runtimeDefault"
	}
	ref := getOverride("SANDBOX_K8S_SECCOMP_LOCALHOST_REF", lang)
	return SeccompSetting{Mode: mode, LocalhostRef: ref}
}
