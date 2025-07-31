# overall instructions

- The answer results in Chinese.
- When you run any command in the shell, instead of using the `cd` command to switch to the target directory, you should concatenate the full relative path where the path is required in the command being executed.
- When you want to run tests, use the makefile as possible.


## mcp servers

There are several mcp tools you can use:

- you can use `sequencethinking` mcp tools to deeply think when you have a complex problem to solve
  - plan the steps and thinkings with `sequencethinking`.
  - you NEED to think at least 5 steps in divergent brainstorming with thinking branches

# project layout

```
sandbox/
├── main.py                    # 主程序入口，支持命令行参数启动服务器
├── CLAUDE.md                 # 项目说明文档
├── README.md                 # 项目README
├── LICENSE                   # 许可证文件
├── Dockerfile               # Docker构建文件
├── pyproject.toml           # Python项目配置
├── pytest.ini              # 测试配置
├── makefile                 # 构建脚本
├── shell.nix               # Nix开发环境配置
├── uv.lock                 # UV依赖锁文件
├── server.log              # 服务器日志文件
│
├── .github/                # GitHub Actions工作流
│   └── workflows/
│       ├── cicd-pull-request.yaml  # PR CI/CD工作流
│       ├── cicd-push.yaml          # 推送CI/CD工作流
│       └── release-image.yml       # 镜像发布工作流
│
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── api/               # API服务器模块
│   │   ├── __init__.py
│   │   └── app.py         # 简化的HTTP服务器实现
│   ├── runtime/           # 代码运行时模块
│   │   ├── __init__.py
│   │   ├── base.py        # 运行时基类
│   │   ├── manager.py     # 进程管理器
│   │   ├── models.py      # 数据模型
│   │   ├── python_runtime.py  # Python运行时实现
│   │   ├── nodejs_runtime.py  # Node.js运行时实现
│   │   ├── const/         # 常量定义
│   │   ├── extensions/    # 代码扩展系统
│   │   │   ├── __init__.py
│   │   │   ├── python.py
│   │   │   ├── node.py
│   │   │   ├── runtime_ast_manager.py  # 运行时AST管理器
│   │   │   ├── plugins/   # 语言特定插件
│   │   │   │   ├── python/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── console_plugin.py
│   │   │   │   │   └── matplotlib_plugin.py
│   │   │   │   └── nodejs/
│   │   │   │       ├── console_plugin.js
│   │   │   │       ├── import_plugin.js
│   │   │   │       ├── index.js
│   │   │   │       └── process_plugin.js
│   │   │   └── transformer/  # 代码转换器
│   │   │       ├── __init__.py
│   │   │       ├── python/
│   │   │       │   ├── __init__.py
│   │   │       │   └── transformer.py
│   │   │       └── nodejs/
│   │   │           ├── node_modules/
│   │   │           ├── package.json
│   │   │           ├── package-lock.json
│   │   │           └── transformer.js
│   ├── security/          # 安全模块
│   │   ├── __init__.py
│   │   ├── injection/     # seccomp注入器
│   │   │   └── seccomp_wrapper.py
│   │   ├── bpf/          # BPF相关组件
│   │   │   ├── Makefile
│   │   │   ├── seccomp_injector.c  # C语言注入器
│   │   │   ├── seccomp_injector.h
│   │   │   ├── seccomp_injector.o  # 编译后的目标文件
│   │   │   ├── seccomp_injector_python.o
│   │   │   ├── seccomp_injector_nodejs.o
│   │   │   ├── generate_syscalls.py
│   │   │   └── syscalls_generated.h
│   │   ├── static/       # 静态安全配置
│   │   │   ├── python.json
│   │   │   └── nodejs.json
│   │   └── syscalls/     # 系统调用定义
│   └── utils/            # 工具模块
│       └── __init__.py
│
├── scripts/               # 部署和构建脚本
│   ├── entrypoint.sh     # Docker入口点脚本
│   ├── install_nodejs.sh # Node.js安装脚本
│   └── build.sh         # 构建脚本
│
├── tests/                # 测试目录
│   ├── unit/            # 单元测试
│   │   └── extensions/  # 扩展模块测试
│   │       ├── plugins/ # 插件测试
│   │       └── test_nodejs_extension_runtime.py
│   │       └── test_python_extension_runtime.py
│   ├── integration/     # 集成测试
│   │   ├── test_extension_integration.py
│   │   ├── test_runtime_integration.py
│   │   └── test_security_integration.py
│   ├── e2e/            # 端到端测试
│   ├── performance/    # 性能测试
│   └── security/       # 安全测试
│
├── deploy/              # 部署配置
│   └── helm/           # Kubernetes Helm Chart
│       └── sandbox/
│           ├── Chart.yaml
│           ├── values.yaml
│           └── templates/
│               ├── NOTES.txt
│               ├── _helpers.tpl
│               ├── deployment.yaml
│               ├── hpa.yaml
│               ├── ingress.yaml
│               ├── service.yaml
│               ├── serviceaccount.yaml
│               └── tests/
│                   └── test-connection.yaml
│
├── build/               # 构建输出目录
```

## 核心架构

### HTTP服务器层 (src/api/)
- **app.py**: 使用Python内置`http.server`实现的轻量级HTTP服务器
- 支持CORS、JSON请求处理、错误处理
- 提供RESTful API接口

### 运行时层 (src/runtime/)
- **base.py**: 定义运行时抽象基类
- **python_runtime.py**: Python代码执行环境
- **nodejs_runtime.py**: Node.js代码执行环境
- **manager.py**: 进程管理和资源限制
- **extensions/**: 代码扩展和转换系统

### 安全层 (src/security/)
- **seccomp_wrapper.py**: seccomp系统调用过滤
- **bpf/**: BPF相关安全组件
- **static/**: 预定义的安全策略配置

### 部署和构建
- **Dockerfile**: 多阶段构建，包含Python和Node.js运行时
- **scripts/**: 部署和安装脚本
- **deploy/helm/**: Kubernetes部署配置

## API端点

- `GET /` - 根路径，返回服务信息
- `GET /api/v1/health` - 健康检查
- `GET /api/v1/languages` - 支持的语言列表
- `POST /api/v1/execute` - 代码执行

## 使用方式

```bash
# 开发环境运行
python main.py --port 8000 --verbose

# Docker运行
docker build -t code-sandbox .
docker run -p 8000:8000 code-sandbox
```
