package limited

import (
	"context"

	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
)

// QueueingManager provides bounded queuing and fixed-size worker concurrency.

type job struct {
	ctx  context.Context
	req  models.RunRequest
	resC chan result
}

type result struct {
	res models.RunResult
	err error
}

type QueueingManager struct {
	inner sandbox.SandboxManager
	jobs  chan job
}

func NewQueueingManager(inner sandbox.SandboxManager, maxConcurrent int, maxQueue int) *QueueingManager {
	qm := &QueueingManager{
		inner: inner,
		jobs:  make(chan job, maxQueue),
	}
	for range maxConcurrent {
		go qm.worker()
	}
	return qm
}

func (q *QueueingManager) Run(ctx context.Context, req *models.RunRequest) (*models.RunResult, error) {
	resC := make(chan result, 1)
	// Create a new context without timeout for the inner manager
	// This allows the podman manager to handle timeouts properly and return RunResult instead of errors
	innerCtx := context.Background()
	// Copy request to avoid data races if caller mutates after enqueue
	j := job{ctx: innerCtx, req: *req, resC: resC}
	// Block when the queue is full; respect ctx cancellation/timeout
	select {
	case q.jobs <- j:
		// enqueued
	case <-ctx.Done():
		return nil, ctx.Err()
	}
	select {
	case out := <-resC:
		return &out.res, out.err
		// Don't check ctx.Done() here - let the inner manager handle timeouts properly
		// This allows the podman manager to return RunResult for timeouts instead of errors
	}
}

func (q *QueueingManager) worker() {
	for j := range q.jobs {
		res, err := q.inner.Run(j.ctx, &j.req)
		if res != nil {
			j.resC <- result{res: *res, err: err}
		} else {
			j.resC <- result{err: err}
		}
	}
}
