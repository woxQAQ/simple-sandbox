package sandbox

import (
	"context"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

// SandboxManager 定义沙盒执行后端的抽象。
// 不同运行时（Docker / CRI / K8s）应实现该接口，以提供统一的执行能力。
// 实现需保证：
// 1) 安全隔离（只读根、能力丢弃、seccomp、非 root 等）
// 2) 资源限制（CPU/内存/PIDs/超时）
// 3) 可复现输出（stdout/stderr/exit code/图像等）
// 4) 对上下文取消/超时的及时响应
// 5) 错误清晰（参数校验错误、排队/限流、执行失败等）
//
// 该接口是交互层与具体运行时实现之间的边界，有助于解耦 API 与执行后端。
type SandboxManager interface {
	// Run 在目标运行时环境中执行用户代码。
	// ctx: 控制执行生命周期；取消或超时应中断执行并返回错误。
	// req: 执行参数（语言、代码片段、资源限制、命名空间等），调用前应通过 Validate。
	// 返回 RunResult：包含 exit code、stdout/stderr、可选的 images_b64 及耗时。
	// 错误：
	// - 参数非法：直接返回错误
	// - 队列已满/被限流：应返回可识别的错误（上层可映射为 429）
	// - 执行中断或超时：返回 context 错误
	Run(ctx context.Context, req models.RunRequest) (models.RunResult, error)
}
