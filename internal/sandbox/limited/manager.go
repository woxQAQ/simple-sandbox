package limited

import (
	"context"
	"errors"

	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
)

var ErrQueueFull = errors.New("queue full")

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
	for i := 0; i < maxConcurrent; i++ {
		go qm.worker()
	}
	return qm
}

func (q *QueueingManager) Run(ctx context.Context, req models.RunRequest) (models.RunResult, error) {
	resC := make(chan result, 1)
	j := job{ctx: ctx, req: req, resC: resC}
	select {
	case q.jobs <- j:
		// enqueued
	case <-ctx.Done():
		return models.RunResult{}, ctx.Err()
	default:
		return models.RunResult{}, ErrQueueFull
	}
	select {
	case out := <-resC:
		return out.res, out.err
	case <-ctx.Done():
		return models.RunResult{}, ctx.Err()
	}
}

func (q *QueueingManager) worker() {
	for j := range q.jobs {
		res, err := q.inner.Run(j.ctx, j.req)
		j.resC <- result{res: res, err: err}
	}
}
