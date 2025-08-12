package sandbox

import (
	"context"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

type SandboxManager interface {
	Run(ctx context.Context, req models.RunRequest) (models.RunResult, error)
}
