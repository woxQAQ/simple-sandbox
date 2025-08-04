# Code Sandbox

一个安全的代码执行沙箱，支持多语言运行时和安全隔离。

## 核心功能

- **多语言支持**: Python 和 Node.js 运行时
- **安全隔离**: seccomp 系统调用过滤和 BPF 安全机制
- **API 接口**: RESTful API，支持代码执行、健康检查
- **并发控制**: 请求速率限制和并发请求管理
- **容器化部署**: Docker 多架构支持

## 快速开始

### 本地运行

```bash
# 安装依赖
uv sync

# 启动服务器
python main.py --port 8000 --debug
```

### Docker 运行

```bash
# 构建镜像
docker build -t code-sandbox .

# 运行容器
docker run -p 8000:8000 code-sandbox
```

## API 使用

### 执行代码

```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "code": "print(\"Hello, World!\")"
  }'
```

### 支持的语言

```bash
curl http://localhost:8000/api/v1/languages
```

### 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

## 代码示例

### Python 示例

```json
{
  "language": "python",
  "code": "print(\"Hello from Python!\")\nprint(2 + 2)"
}
```

### Node.js 示例

```json
{
  "language": "nodejs",
  "code": "console.log(\"Hello from Node.js!\");\nconsole.log(2 + 2);"
}
```

## 配置选项

```bash
python main.py --help

# 使用说明:
#   --port PORT       服务器端口 (默认: 8000)
#   --host HOST       服务器地址 (默认: 0.0.0.0)
#   --debug           启用调试模式
```

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。