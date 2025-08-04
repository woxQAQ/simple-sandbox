# overall instructions

- The answer results in Chinese.
- When you run any command in the shell, instead of using the `cd` command to switch to the target directory, you should concatenate the full relative path where the path is required in the command being executed.

## code styles

### overall

- if you add comments, explain WHY you code the following logic instead of WHAT the following logic is.
- reduce comments, a better function name is better than writing extend comment to explain the function
- coding python with PEP 8 style guidelines.
- AVOID using UNNECESSARY design pattern if you are doing anything that is easy.
- Keep functions focused and single-purpose

### best practices

- Use docstrings for modules, classes, and functions
- Use list comprehensions for simple transformations
- Prefer pathlib over os.path for file operations
- Use context managers (with statements) for resource management
- Use logging module instead of print statements

### type hint

- Document complex types with comments

## mcp servers

There are several mcp tools you can use:

- you can use `sequencethinking` mcp tools to deeply think when you have a complex problem to solve
  - plan the steps and thinkings with `sequencethinking`.
  - you NEED to think at least 5 steps in divergent brainstorming with thinking branches

# project layout

```
sandbox/
├── main.py                    # 主程序入口
├── README.md                 # 项目说明
├── LICENSE                   # 许可证文件
├── Dockerfile               # Docker构建文件
├── pyproject.toml           # Python项目配置
├── makefile                 # 构建脚本
├── shell.nix               # Nix开发环境配置
├── .github/                # GitHub Actions工作流
├── src/                    # 源代码目录
│   ├── api/               # HTTP服务器模块
│   ├── runtime/           # 代码运行时模块
│   │   ├── common/        # 公共运行时组件
│   │   ├── python/        # Python运行时实现
│   │   └── nodejs/        # Node.js运行时实现
│   ├── security/          # 安全模块
│   │   ├── bpf/          # BPF相关组件
│   │   ├── static/       # 静态安全配置
│   │   └── syscalls/     # 系统调用定义
│   └── utils/            # 工具模块
├── scripts/               # 部署和构建脚本
├── tests/                # 测试目录
│   ├── integration/     # 集成测试
│   ├── unit/            # 单元测试
│   └── utils/           # 工具测试
├── deploy/              # 部署配置
│   └── helm/           # Kubernetes Helm Chart
├── docker/               # Docker相关配置
├── config.py             # 配置文件
├── models.py             # 数据模型
```

## 核心架构

### HTTP服务器层 (src/api/)
- **app.py**: 使用Python内置`http.server`实现的轻量级HTTP服务器
- 支持CORS、JSON请求处理、错误处理
- 提供RESTful API接口
- 内置请求速率限制和并发控制

### 运行时层 (src/runtime/)
- **common/**: 公共运行时组件和基类定义
- **python/**: Python代码执行环境，包含插件系统和AST转换
- **nodejs/**: Node.js代码执行环境，使用koffi FFI库进行系统调用
- 每个运行时都支持独立的进程管理和资源隔离

### 安全层 (src/security/)
- **bpf/**: BPF相关安全组件，包含C语言seccomp注入器
- **static/**: 静态安全配置，为不同语言定义系统调用过滤规则
- **syscalls/**: 系统调用定义和权限管理
- 多层安全防护：seccomp系统调用过滤、进程隔离、权限控制

### 工具和配置
- **utils/**: 通用工具函数和加密工具
- **config.py**: 全局配置管理
- **models.py**: 数据模型定义

### 部署和构建
- **docker/**: Docker相关配置，支持多架构构建
- **scripts/**: 部署和构建脚本
- **deploy/helm/**: Kubernetes Helm Chart部署配置
- **.github/**: GitHub Actions CI/CD工作流

## API端点

- `GET /` - 根路径，返回服务信息
- `GET /api/v1/health` - 健康检查
- `POST /api/v1/execute` - 代码执行
