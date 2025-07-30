# e2e测试框架

完整的端到端测试框架，用于测试代码沙箱的Python和Node.js执行功能。

## 目录结构

```
tests/e2e/
├── common/               # 共用逻辑
│   ├── containers.py     # Docker容器操作
│   ├── config.py         # 配置管理
│   └── client.py         # API客户端
├── suites/               # 测试套件
│   ├── test-python-codes.py    # Python代码测试
│   └── test-nodejs-codes.py    # Node.js代码测试
├── .env                  # 环境配置
├── .env.example          # 配置示例
├── e2e.py               # 测试入口
├── Makefile             # 快捷命令
└── README.md           # 说明文档
```

## 功能特性

### 测试覆盖范围
- **基本执行功能**: Hello World、变量操作、函数定义、数据结构操作
- **插件功能测试**: 控制台、matplotlib、数学、导入、进程等插件
- **安全限制测试**: 文件操作、网络操作、系统命令、危险模块阻止
- **错误处理测试**: 语法错误、运行时错误、异常处理
- **性能测试**: 执行时间、资源使用、超时控制

### 支持的语言
- **Python**: 完整的Python代码执行测试
- **Node.js**: 完整的JavaScript代码执行测试

## 快速开始

### 1. 安装依赖

```bash
cd tests/e2e
make install-deps
```

### 2. 启动服务器

在项目根目录启动服务器：

```bash
python main.py --port 8000
```

### 3. 运行测试

```bash
# 运行完整测试套件
make run-tests

# 或直接运行
python e2e.py

# 运行特定语言测试
make test-python
make test-nodejs

# 运行安全性测试
make test-security

# 运行插件测试
make test-plugins
```

## 测试结果

测试完成后会生成详细的HTML报告和Markdown报告：

- `reports/test_report.html` - 详细的HTML测试报告
- `reports/e2e_report_*.md` - Markdown格式的测试报告

## 测试用例统计

### Python测试 (25个用例)
- 基本执行功能: 5个
- 插件功能测试: 3个
- 安全限制测试: 4个
- 允许的操作测试: 4个
- 错误处理测试: 4个

### Node.js测试 (35个用例)
- 基本执行功能: 5个
- 插件功能测试: 4个
- 安全限制测试: 4个
- 允许的操作测试: 6个
- 异步操作测试: 3个
- 错误处理测试: 4个

### 总计: 60个测试用例

## 配置说明

### 环境变量

通过`.env`文件配置测试环境：

```bash
# Docker配置
DOCKER_IMAGE_NAME=code-sandbox
DOCKER_CONTAINER_NAME=sandbox-test
DOCKER_PORT_MAPPING=8000:8000

# 测试配置
CONTAINER_STARTUP_TIMEOUT=60
HEALTH_CHECK_INTERVAL=5
TEST_TIMEOUT=30

# API配置
API_BASE_URL=http://localhost:8000
API_HEALTH_ENDPOINT=/api/v1/health
API_EXECUTE_ENDPOINT=/api/v1/execute
```

### 自定义配置

可以修改`.env`文件来调整测试参数：

- `TEST_TIMEOUT`: 单个测试的超时时间
- `CONTAINER_STARTUP_TIMEOUT`: 容器启动超时时间
- `API_BASE_URL`: 服务器API地址

## Makefile命令

```bash
make help              # 显示帮助信息
make install-deps      # 安装测试依赖
make run-tests         # 运行完整测试套件
make clean             # 清理测试环境
make build-image       # 构建Docker镜像
make start-container   # 启动测试容器
make stop-container    # 停止测试容器
make show-logs         # 显示容器日志
make report            # 生成测试报告
make all               # 完整的测试流程
make quick-test        # 快速测试（需要容器运行）
make health-check      # 健康检查
make test-python       # 仅测试Python
make test-nodejs       # 仅测试Node.js
make test-security     # 仅测试安全性
make test-plugins      # 仅测试插件
make dev-mode          # 开发模式
make debug             # 调试模式
make performance-test  # 性能测试
make stress-test       # 压力测试
```

## 测试报告示例

### 基本功能测试结果
- ✅ 健康检查: 通过
- ✅ Python执行: 通过
- ✅ Node.js执行: 通过
- ✅ 语言支持: ['python', 'nodejs']

### 插件测试结果
- ✅ Python Console插件: 正常处理标准输出
- ✅ Python Matplotlib插件: 成功创建图表
- ✅ Node.js Console插件: 多级别日志输出
- ✅ Node.js Import插件: 核心模块导入正常

### 安全测试结果
- ✅ 文件操作阻止: 成功阻止/etc/passwd读取
- ✅ 网络操作阻止: 成功阻止socket连接
- ✅ 系统命令阻止: 成功阻止subprocess调用
- ✅ 危险模块阻止: 成功限制os.system调用

## 扩展测试

### 添加新的测试用例

1. 在相应的测试文件中添加新的测试方法
2. 使用@pytest装饰器标记测试
3. 编写断言来验证预期结果

```python
def test_new_feature(self, client):
    """测试新功能"""
    code = '''
    # 新功能代码
    print("新功能测试")
    '''
    response = client.execute_python_code(code)
    assert response.success
    assert "新功能测试" in response.output
```

### 添加新的测试套件

1. 在`suites/`目录下创建新的测试文件
2. 导入必要的模块和fixtures
3. 编写测试类和测试方法

## 故障排除

### 常见问题

1. **服务器未启动**
   - 确保服务器在8000端口运行
   - 检查服务器日志

2. **测试超时**
   - 增加TEST_TIMEOUT配置
   - 检查服务器性能

3. **依赖问题**
   - 运行`make install-deps`安装依赖
   - 检查Python版本兼容性

4. **权限问题**
   - 确保Docker服务运行
   - 检查文件权限

### 调试模式

使用调试模式查看详细日志：

```bash
make debug
```

或在代码中设置日志级别：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 贡献指南

1. 遵循现有的代码风格
2. 添加适当的测试用例
3. 更新文档
4. 确保所有测试通过

## 许可证

遵循项目的许可证协议。