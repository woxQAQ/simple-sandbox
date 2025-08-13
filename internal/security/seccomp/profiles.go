package seccomp

import (
	_ "embed"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

//go:embed python.json
var pythonProfile string

//go:embed node.json
var nodeProfile string

func For(lang string) string {
	switch lang {
	case models.LanguagePython:
		return pythonProfile
	case models.LanguageNode:
		return nodeProfile
	default:
		return pythonProfile
	}
}
