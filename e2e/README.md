# Simple Sandbox E2E Tests

这是 Simple Sandbox 项目的端到端（E2E）测试套件，使用 Ginkgo 和 Gomega 测试框架实现。

## 概述

E2E 测试套件提供全面的测试覆盖，包括：

- **API 接口测试**：验证 `/v1/run` 端点的各种场景
- **运行时测试**：测试 Python 和 Node.js 代码执行
- **安全机制测试**：验证文件系统隔离、网络隔离、权限控制等
- **配置测试**：测试 YAML 配置加载和各种配置选项

## 前置要求

- Go 1.24+
- Docker（用于容器运行时测试）
- Ginkgo 测试框架

## 快速开始

### 1. 安装依赖

```bash
cd e2e
make deps
```

### 2. 构建 Docker 镜像

```bash
make docker-build
```

### 3. 运行测试

```bash
# 运行所有测试
make test

# 运行详细输出的测试
make test-verbose

# 运行特定测试套件
make test-api      # API 测试
make test-runtime  # 运行时测试
make test-security # 安全测试
make test-config   # 配置测试
```

## 测试结构

```
e2e/
├── README.md              # 本文档
├── Makefile              # 测试管理命令
├── go.mod                # Go 模块定义
├── e2e_suite_test.go     # 测试套件入口
├── api_test.go           # API 接口测试
├── runtime_test.go       # 运行时测试
├── security_test.go      # 安全机制测试
├── config_test.go        # 配置测试
├── utils/
│   └── test_utils.go     # 测试工具和辅助函数
└── testdata/
    ├── test_codes.go     # 测试代码样例
    └── test_config.yaml  # 测试配置文件
```

## 测试类别

### API 接口测试 (`api_test.go`)

测试 HTTP API 的各种场景：

- ✅ 正常请求处理
- ✅ 错误处理和异常情况
- ✅ 参数验证
- ✅ 资源限制（内存、CPU、时间）
- ✅ 超时处理

### 运行时测试 (`runtime_test.go`)

测试不同编程语言的代码执行：

**Python 运行时：**
- ✅ 基础代码执行
- ✅ 模块导入和异常处理
- ✅ Matplotlib 图表生成
- ✅ NumPy 数值计算
- ✅ Artifacts 输出处理

**Node.js 运行时：**
- ✅ 基础代码执行
- ✅ 模块加载和错误处理
- ✅ 异步代码和 Promise
- ✅ 空 Artifacts 处理

### 安全机制测试 (`security_test.go`)

验证沙盒的安全隔离机制：

- ✅ 文件系统隔离（防止访问敏感文件）
- ✅ 网络隔离（阻止外部网络访问）
- ✅ 系统调用限制（Seccomp 过滤）
- ✅ 用户权限控制（非 root 执行）
- ✅ 资源限制（内存、时间）
- ✅ 容器安全（防止容器逃逸）

### 配置测试 (`config_test.go`)

测试配置系统的各种场景：

- ✅ YAML 配置文件加载
- ✅ 默认配置处理
- ✅ 无效配置处理
- ✅ Docker 后端配置
- ✅ Kubernetes 后端配置
- ✅ 并发控制配置
- ✅ 语言特定配置

## 测试工具

### TestServer (`utils/test_utils.go`)

管理测试服务器的生命周期：

```go
testServer := utils.NewTestServer("8080")
err := testServer.Start()
defer testServer.Stop()
```

### HTTPClient (`utils/test_utils.go`)

封装 HTTP 客户端，简化 API 调用：

```go
httpClient := utils.NewHTTPClient(testServer.GetBaseURL())
result, err := httpClient.RunCode(&models.RunRequest{
    Language: "python",
    Code:     "print('Hello, World!')",
})
```

### 断言辅助函数

提供专门的断言函数：

```go
// 检查 artifact 是否存在
utils.AssertArtifactExists(result.Artifacts, "image")

// 检查 artifact 数量
utils.AssertArtifactCount(result.Artifacts, "image", 2)
```

## 测试数据

### 代码样例 (`testdata/test_codes.go`)

包含各种测试用的代码片段：

- `PythonCodes`: Python 测试代码集合
- `NodeCodes`: Node.js 测试代码集合
- `ExpectedOutputs`: 预期输出结果

### 配置模板 (`testdata/test_config.yaml`)

提供测试专用的配置文件模板。

## 运行选项

### 基本测试命令

```bash
# 运行所有测试
make test

# 详细输出
make test-verbose

# 并行执行
make test-parallel

# 快速验证
make test-smoke
```

### 特定测试套件

```bash
# 只运行 API 测试
make test-api

# 只运行安全测试
make test-security

# 只运行配置测试
make test-config
```

### 高级选项

```bash
# 生成覆盖率报告
make test-coverage

# 生成测试报告
make test-report

# 监视文件变化并自动运行测试
make test-watch

# 完整测试（包括验证和构建）
make test-full
```

## 环境配置

### Docker 配置

测试需要以下 Docker 镜像：

- `sandbox-python:latest` - Python 运行时
- `sandbox-node:latest` - Node.js 运行时
- `sandbox-api:latest` - API 服务器

使用 `make docker-build` 构建所有镜像。

### 配置文件

测试使用专门的配置文件 `testdata/test_config.yaml`，针对测试环境进行了优化：

- 降低并发数以便测试
- 使用较短的超时时间
- 简化的镜像配置

## 故障排除

### 常见问题

1. **Docker 镜像不存在**
   ```bash
   make docker-build
   ```

2. **端口冲突**
   - 测试使用端口 8081-8091
   - 确保这些端口未被占用

3. **权限问题**
   - 确保 Docker 守护进程正在运行
   - 确保当前用户有 Docker 权限

4. **测试超时**
   - 检查系统资源是否充足
   - 考虑增加超时时间

### 调试技巧

1. **查看详细日志**
   ```bash
   make test-verbose
   ```

2. **运行单个测试**
   ```bash
   ginkgo run --focus="specific test name"
   ```

3. **跳过耗时测试**
   ```bash
   ginkgo run --skip="slow tests"
   ```

## 贡献指南

### 添加新测试

1. 在相应的测试文件中添加测试用例
2. 更新 `testdata/test_codes.go` 添加测试代码
3. 运行测试确保通过
4. 更新文档

### 测试最佳实践

1. **使用描述性的测试名称**
2. **每个测试应该独立且可重复**
3. **使用适当的超时时间**
4. **清理测试资源**
5. **使用有意义的断言消息**

## 持续集成

测试套件设计为在 CI/CD 环境中运行：

```yaml
# GitHub Actions 示例
- name: Run E2E Tests
  run: |
    cd e2e
    make validate
    make test-full
```

## 性能考虑

- 测试使用较小的资源限制以加快执行
- 并行执行以减少总时间
- 智能跳过不可用的功能（如 K8s）
- 缓存 Docker 镜像以避免重复构建

## 许可证

本测试套件遵循与主项目相同的许可证。