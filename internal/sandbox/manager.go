package sandbox

import (
	"context"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

// SandboxManager abstracts a sandbox execution backend (Docker/CRI/K8s).
// Implementations must provide strong isolation, enforce resource limits, produce
// reproducible outputs, react promptly to context cancellation/timeouts, and
// expose clear error boundaries.
type SandboxManager interface {
	// Run executes user code in the target runtime.
	// - ctx controls lifecycle; timeouts/cancellation must take effect immediately
	// - req must be validated; includes language/code/resource limits/namespace
	// Returns exit code, stdout/stderr, optional images, and duration
	Run(ctx context.Context, req *models.RunRequest) (*models.RunResult, error)
}
