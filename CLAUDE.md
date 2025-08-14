# overall instructions

- The answer results in Chinese.
- When you run any command in the shell, instead of using the `cd` command to switch to the target directory, you should concatenate the full relative path where the path is required in the command being executed.

## code styles

### overall

- if you add comments, explain WHY you code the following logic instead of WHAT the following logic is.
- reduce comments, a better function name is better than writing extend comment to explain the function
- coding with Go standard conventions and best practices
- AVOID using UNNECESSARY design pattern if you are doing anything that is easy.
- Keep functions focused and single-purpose

### best practices

- Use Go standard library patterns and conventions
- Prefer composition over inheritance
- Use interfaces for abstraction and decoupling
- Handle errors explicitly and gracefully
- Use context for cancellation and timeouts
- Follow Go naming conventions (CamelCase for exported, camelCase for unexported)

### type hints

- Use Go's type system effectively
- Define clear interfaces for contracts
- Use structs for data models
- Leverage Go's strong typing

## mcp servers

There are several mcp tools you can use:

- you can use `sequencethinking` mcp tools to deeply think when you have a complex problem to solve
  - plan the steps and thinkings with `sequencethinking`.
  - you NEED to think at least 5 steps in divergent brainstorming with thinking branches

# project layout

```
simple-sandbox/
├── cmd/sandboxd/           # 主程序入口
├── internal/               # 内部包
│   ├── api/               # HTTP API服务器
│   ├── config/            # 配置管理
│   ├── constants/         # 常量定义
│   ├── logging/           # 结构化日志
│   ├── models/            # 数据模型
│   ├── sandbox/           # 沙盒管理核心
│   │   ├── docker/        # Docker运行时
│   │   ├── k8s/           # Kubernetes运行时
│   │   ├── podman/        # Podman运行时
│   │   ├── limited/       # 并发控制
│   │   ├── common/        # 通用工具
│   │   └── cri/           # CRI运行时接口
│   ├── security/          # 安全配置
│   │   └── seccomp/       # seccomp配置文件
│   └── types/             # 类型定义
├── docker/                # Docker相关配置
│   ├── apiserver/         # API服务器镜像
│   └── runtimes/          # 语言运行时镜像
│       ├── python/        # Python运行时
│       └── node/          # Node.js运行时
├── config/                # 配置文件
├── e2e/                   # 端到端测试
├── go.mod/go.sum          # Go模块依赖
├── Makefile              # 构建脚本
├── README.md             # 项目说明
└── LICENSE               # 许可证文件
```

## 核心架构

### 主程序入口 (cmd/sandboxd/)
- **main.go**: 程序入口点，初始化配置、日志、沙盒管理器和HTTP服务器
- 支持优雅关闭和信号处理
- 通过环境变量或命令行参数配置

### HTTP服务器层 (internal/api/)
- **server.go**: 使用标准库`net/http`实现的轻量级HTTP服务器
- 支持JSON请求处理和错误处理
- 提供RESTful API接口：`POST /v1/run`
- 内置请求队列和并发控制

### 沙盒管理层 (internal/sandbox/)
- **manager.go**: SandboxManager接口定义，抽象不同运行时后端
- **factory.go**: 根据环境配置创建具体的沙盒管理器
- **common/**: 通用工具函数和镜像管理
- **limited/**: 队列和并发控制包装器

### 运行时实现
- **docker/**: 使用Docker Go SDK的容器运行时实现
- **k8s/**: 基于Kubernetes Pod的运行时实现
- **podman/**: 使用Podman CLI的容器运行时实现
- 每个运行时都支持资源限制、安全隔离和超时控制

### 安全层 (internal/security/)
- **seccomp/**: 为Python和Node.js定制的系统调用过滤配置
- 支持runtimeDefault和自定义配置文件
- 严格的权限控制和资源限制

### 配置和日志
- **config/**: YAML配置文件管理
- **logging/**: 基于zap的结构化日志系统
- **models/**: 请求数据模型和验证逻辑

### 运行时镜像 (docker/runtimes/)
- **python/**: Python运行时，支持matplotlib图像生成
- **node/**: Node.js运行时，基于Alpine Linux
- 每个运行时都包含安全配置和资源限制

## API端点

- `POST /v1/run` - 执行代码，返回执行结果
- 支持Python和Node.js语言
- 提供资源限制（内存、CPU、时间）和并发控制
- 返回执行状态、输出、错误和可选的artifacts

## 构建和部署

### 本地构建
```bash
go build -o sandboxd ./cmd/sandboxd
```

### Docker镜像
```bash
docker build -f docker/apiserver/Dockerfile -t sandbox-api .
docker build -f docker/runtimes/python/Dockerfile -t sandbox-python docker/runtimes/python/
docker build -f docker/runtimes/node/Dockerfile -t sandbox-node docker/runtimes/node/
```

### 测试
- e2e/: 端到端测试
- 支持本地镜像测试和集成测试
