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

## 测试

### E2E 测试指南

项目使用 Ginkgo 和 Gomega 框架进行端到端测试，测试套件位于 `e2e/` 目录。

#### 测试结构
```
e2e/
├── README.md                    # 测试说明文档
├── Makefile                     # 测试管理命令
├── go.mod                       # Go 模块定义
├── e2e_suite_test.go            # 测试套件入口
├── api_test.go                  # API 接口测试
├── runtime_test.go              # 运行时测试
├── security_test.go             # 安全机制测试
├── config_test.go               # 配置测试
├── utils/test_utils.go          # 测试工具和辅助函数
├── testdata/
│   ├── test_codes.go            # 测试代码样例
│   └── test_config.yaml         # 测试配置文件
└── LOCAL_IMAGES_GUIDE.md        # 本地镜像测试指南
```

#### 测试类别
- **API 测试** (`api_test.go`): 验证 `/v1/run` 端点的各种场景
- **运行时测试** (`runtime_test.go`): 测试 Python 和 Node.js 代码执行
- **安全测试** (`security_test.go`): 验证文件系统隔离、网络隔离、权限控制等
- **配置测试** (`config_test.go`): 测试 YAML 配置加载和各种配置选项

#### 测试命令
```bash
# 进入测试目录
cd e2e

# 安装测试依赖
make deps

# 构建本地镜像（使用 Podman）
make podman-build

# 运行所有测试
make test

# 运行详细输出的测试
make test-verbose

# 构建镜像并运行测试（一步完成）
make local-test

# 运行特定测试套件
make test-api      # API 测试
make test-runtime  # 运行时测试
make test-security # 安全测试
make test-config   # 配置测试
```

#### 测试配置
测试使用 `testdata/test_config.yaml` 配置文件：
- 使用 Podman 作为容器后端
- 本地镜像名称：`localhost/sandbox-python` 和 `localhost/sandbox-node`
- 降低并发数以便测试（max_concurrency: 2）

#### 测试工具
- **TestServer**: 管理测试服务器生命周期
- **HTTPClient**: 封装 HTTP 客户端，简化 API 调用
- **断言辅助函数**: 专门的断言函数用于验证 artifacts 和执行结果

#### 开发工作流
1. 修改运行时代码：编辑 `docker/runtimes/python/` 或 `docker/runtimes/node/`
2. 重新构建镜像：`make podman-build`
3. 运行测试：`make test`
4. 验证功能：检查测试结果

#### 故障排除
- 确保镜像构建成功：`podman images | grep sandbox`
- 检查配置文件是否正确
- 查看详细测试日志：`make test-verbose`
- 确保端口 8081 未被占用（测试服务器使用）
