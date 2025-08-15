# Simple Sandbox

一个用Go语言开发的安全代码执行沙盒，支持多种容器运行时和完整的安全隔离机制。

## 核心特性

* **多容器运行时支持**: 兼容Docker和Kubernetes两种容器运行时

* **多语言支持**: Python和Node.js运行时，支持matplotlib图像生成

* **企业级安全**: seccomp系统调用过滤、只读文件系统、非root用户执行

* **生产就绪**: 结构化日志、优雅关闭、并发控制、资源限制

* **云原生**: 原生支持Kubernetes部署，多架构镜像支持

* **RESTful API**: 标准化的HTTP接口，支持代码执行和状态查询

## 架构设计

### 安全机制

* **系统调用过滤**: 基于seccomp的定制化系统调用白名单

* **文件系统隔离**: 只读根文件系统 + tmpfs临时目录

* **权限控制**: 丢弃所有Linux能力，以非特权用户运行

* **网络隔离**: 完全禁用网络访问

* **资源限制**: 内存、CPU、进程数量严格限制

### 容器运行时

* **Docker**: 原生Docker API支持，自动镜像拉取和认证

* **Kubernetes**: 通过Pod和ConfigMap实现，支持集群部署

* **统一接口**: SandboxManager抽象层，运行时完全解耦

## 快速开始

### 构建和运行

```bash
# 构建主程序
go build -o sandboxd ./cmd/sandboxd

# 启动服务器
./sandboxd -addr :8080
```

### Docker部署

```bash
# 构建API服务器镜像
docker build -f docker/apiserver/Dockerfile -t sandbox-api .

# 构建语言运行时镜像
docker build -f docker/runtimes/python/Dockerfile -t sandbox-python docker/runtimes/python/
docker build -f docker/runtimes/node/Dockerfile -t sandbox-node docker/runtimes/node/

# 运行服务
docker run -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock sandbox-api
```

### Kubernetes部署

```bash
# 配置运行时为k8s
export SANDBOX_CONFIG=config/sandbox.yaml

# 启动服务（需要适当的RBAC权限）
./sandboxd -addr :8080
```

## API使用

### 执行代码

```bash
curl -X POST http://localhost:8080/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "code": "print(\"Hello, World!\")",
    "time_limit_ms": 5000,
    "memory_mb": 128
  }'
```

### 响应格式

```json
{
  "exit_code": 0,
  "stdout": "Hello, World!\n",
  "stderr": "",
  "artifacts": [],
  "duration_ms": 234
}
```

## 代码示例

### Python示例（支持matplotlib）

```json
{
  "language": "python",
  "code": "import matplotlib.pyplot as plt\nimport numpy as np\n\nx = np.linspace(0, 2*np.pi, 100)\ny = np.sin(x)\n\nplt.figure(figsize=(8, 6))\nplt.plot(x, y)\nplt.title('Sine Wave')\nplt.show()\n\nprint('图表已生成')",
  "time_limit_ms": 10000,
  "memory_mb": 256
}
```

### Node.js示例

```json
{
  "language": "node",
  "code": "console.log('Hello from Node.js!');\nconsole.log('Current time:', new Date().toISOString());",
  "time_limit_ms": 5000,
  "memory_mb": 128
}
```

## 配置

### 配置管理

项目主要通过YAML配置文件进行配置管理。唯一的环境变量是 `SANDBOX_CONFIG`，用于指定配置文件路径：

```bash
# 指定配置文件路径（可选，默认为 ./config/sandbox.yaml）
SANDBOX_CONFIG=./config/sandbox.yaml
```

参考 `.env.example` 文件了解更多详情。

### YAML配置文件

主要配置通过 `config/sandbox.yaml` 文件管理，参考 `config/sandbox.yaml.example`：

```yaml
# sandbox.yaml
runtime:
  backend: "docker"                    # 运行时后端: docker | k8s
  max_concurrency: 4                   # 最大并发数
  max_queue: 32                        # 最大队列长度
  image_registry: "docker.io"          # 镜像仓库地址
  registry_username: ""                # 私有仓库用户名
  registry_password: ""                # 私有仓库密码
  registry_auth: ""                    # 私有仓库认证信息
  registry_identity_token: ""          # 私有仓库身份令牌
  k8s_image_pull_secret: ""            # Kubernetes镜像拉取密钥

languages:
  python:
    repository: "sandbox-python"        # Python镜像仓库
    tag: "latest"                       # 镜像标签
    registry: "docker.io"               # 镜像仓库（可覆盖全局设置）
    seccomp:
      mode: "runtimeDefault"            # seccomp模式
      localhost_ref: ""                 # 本地配置文件引用
  node:
    repository: "sandbox-node"          # Node.js镜像仓库
    tag: "latest"                       # 镜像标签
    registry: "docker.io"               # 镜像仓库（可覆盖全局设置）
    seccomp:
      mode: "runtimeDefault"            # seccomp模式
      localhost_ref: ""                 # 本地配置文件引用
```

## 项目结构

```
cmd/sandboxd/           # 主程序入口
internal/
  ├── api/              # HTTP API服务器
  ├── config/           # 配置管理
  ├── logging/          # 结构化日志
  ├── models/           # 数据模型
  ├── sandbox/          # 沙盒管理核心
  │   ├── docker/       # Docker运行时
  │   ├── k8s/          # Kubernetes运行时
  │   ├── limited/      # 并发控制
  │   └── common/       # 通用工具
  └── security/         # 安全配置
      └── seccomp/      # seccomp配置文件
docker/
  ├── apiserver/        # API服务器镜像
  └── runtimes/         # 语言运行时镜像
      ├── python/       # Python运行时
      └── node/         # Node.js运行时
```

## 安全特性

### 系统调用过滤

* Python和Node.js分别使用定制的seccomp配置

* 默认拒绝所有系统调用，仅允许必要的白名单调用

* 严格禁止网络、文件系统修改、进程创建等危险操作

### 容器安全

* 只读根文件系统，防止恶意文件写入

* tmpfs内存文件系统用于临时文件

* 非root用户执行（UID 65532）

* 丢弃所有Linux能力

* 严格的资源限制（内存、CPU、进程数）

### 网络隔离

* Docker: NetworkDisabled=true

* Kubernetes: 无网络策略配置

* 完全阻断外部网络访问

## 监控和日志

* 使用zap提供结构化JSON日志

* 支持请求追踪和错误监控

* 详细的执行时间和资源使用统计

* 优雅关闭和信号处理

## 许可证

本项目采用MIT许可证。详情请参阅[LICENSE](LICENSE)文件。
