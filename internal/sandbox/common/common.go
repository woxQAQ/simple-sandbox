package common

import (
	"bytes"
	"encoding/json"
	"errors"

	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/constants"
	"github.com/woxqaq/simple-sandbox/internal/models"
)

// RunnerJSON is the standard JSON payload produced by the in-container runner.
type RunnerJSON struct {
	Stdout    string              `json:"stdout"`
	Stderr    string              `json:"stderr"`
	Artifacts []models.Artifact   `json:"artifacts,omitempty"`
	ExitCode  int                 `json:"exit_code"`
}

// ParseRunnerJSONFromBytes parses the last JSON object from raw logs into RunnerJSON.
// Logs may contain non-JSON prefixes; we locate the last '{' as the start.
func ParseRunnerJSONFromBytes(raw []byte) (*RunnerJSON, error) {
	idx := bytes.LastIndexByte(raw, '{')
	if idx < 0 {
		return nil, errors.New("no json found in logs")
	}
	var r RunnerJSON
	if err := json.Unmarshal(raw[idx:], &r); err != nil {
		return nil, err
	}
	return &r, nil
}

// CodeFilenameForLanguage returns the filename for the given language.
func CodeFilenameForLanguage(lang string) string {
	switch lang {
	case models.LanguagePython:
		return constants.PythonMainFile
	case models.LanguageNode:
		return constants.NodeMainFile
	default:
		return constants.GenericMainFile
	}
}

// ImageRef represents a container image reference triplet.
type ImageRef struct {
	Registry   string
	Repository string
	Tag        string
}

func (r ImageRef) String() string {
	return r.Registry + "/" + r.Repository + ":" + r.Tag
}

// ResolveImageRef resolves image reference using global YAML config and language.
func ResolveImageRef(yamlCfg *config.SandboxConfig, lang string) ImageRef {
	langSettings, ok := yamlCfg.Languages[lang]
	if !ok {
		langSettings = yamlCfg.Languages[models.LanguagePython]
	}

	registry := langSettings.Registry
	if registry == "" {
		registry = yamlCfg.Runtime.ImageRegistry
	}
	if registry == "" {
		registry = constants.DefaultRegistry
	}

	repo := langSettings.Repository
	if repo == "" {
		repo = constants.DefaultPythonRepo
	}

	tag := langSettings.Tag
	if tag == "" {
		tag = constants.DefaultImageTag
	}

	return ImageRef{Registry: registry, Repository: repo, Tag: tag}
}

// ImageRefFor is a convenience wrapper using the global YAML config.
func ImageRefFor(lang string) ImageRef {
	return ResolveImageRef(config.GetYAMLConfig(), lang)
}

// ImageFor returns the full image reference string.
func ImageFor(lang string) string {
	r := ImageRefFor(lang)
	return r.String()
}
