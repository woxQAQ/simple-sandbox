# 安全代码沙箱部署指南

## 项目概述

这是一个基于Docker的安全代码执行沙箱系统，支持Python和Node.js代码的安全执行，具备以下特性：

- 完全隔离的容器环境
- 基于seccomp的安全策略
- 内存和CPU资源限制
- 超时控制
- 可扩展的插件系统
- RESTful API接口

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- Linux 系统（推荐Ubuntu 20.04+）
- 至少2GB内存
- 2核CPU以上

## 快速部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd secure-code-sandbox
```

### 2. 构建镜像

```bash
docker-compose build
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 测试API
 curl -X POST http://localhost:8000/api/v1/execute/python \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "timeout": 30,
    "memory_limit": 128
  }'
```

## 生产环境部署

### 1. 环境准备

```bash
# 创建专用用户
sudo useradd -r -s /bin/false sandbox

# 创建目录
sudo mkdir -p /opt/sandbox
sudo chown sandbox:sandbox /opt/sandbox

# 复制文件
sudo cp -r * /opt/sandbox/
sudo chown -R sandbox:sandbox /opt/sandbox
```

### 2. 配置防火墙

```bash
# UFW配置
sudo ufw allow 8000/tcp
sudo ufw enable

# 或者使用iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### 3. 系统优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 内核参数优化
echo "net.core.somaxconn = 1024" | sudo tee -a /etc/sysctl.conf
echo "vm.max_map_count = 262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 4. 使用Docker Swarm部署

```bash
# 初始化Swarm
docker swarm init

# 部署服务
docker stack deploy -c docker-compose.yml sandbox

# 查看服务状态
docker service ls
```

## Kubernetes部署

### 1. 创建命名空间

```yaml
# k8s-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sandbox
  labels:
    name: sandbox
```

### 2. 创建配置映射

```yaml
# k8s-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sandbox-config
  namespace: sandbox
data:
  MAX_WORKERS: "4"
  MEMORY_LIMIT: "512"
  TIMEOUT_LIMIT: "30"
```

### 3. 创建部署

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sandbox-api
  namespace: sandbox
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sandbox-api
  template:
    metadata:
      labels:
        app: sandbox-api
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: sandbox
        image: secure-code-sandbox:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        envFrom:
        - configMapRef:
            name: sandbox-config
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
        - name: var-tmp-volume
          mountPath: /var/tmp
      volumes:
      - name: tmp-volume
        emptyDir: {}
      - name: var-tmp-volume
        emptyDir: {}
```

### 4. 创建服务

```yaml
# k8s-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: sandbox-service
  namespace: sandbox
spec:
  selector:
    app: sandbox-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 5. 应用配置

```bash
kubectl apply -f k8s-namespace.yaml
kubectl apply -f k8s-config.yaml
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MAX_WORKERS | 4 | 最大工作进程数 |
| MEMORY_LIMIT | 512 | 默认内存限制(MB) |
| TIMEOUT_LIMIT | 30 | 默认超时时间(秒) |
| LOG_LEVEL | INFO | 日志级别 |
| CORS_ORIGINS | ["*"] | CORS允许的来源 |

### 安全配置

#### Docker安全选项

- **用户隔离**: 使用非root用户运行应用
- **能力限制**: 移除所有不必要的Linux能力
- **文件系统**: 只读根文件系统
- **Seccomp**: 限制系统调用
- **AppArmor**: 可选的额外安全层

#### 资源限制

```yaml
# docker-compose.yml中的资源限制
resources:
  limits:
    cpus: '2.0'
    memory: 2G
  reservations:
    cpus: '1.0'
    memory: 1G
```

## API使用指南

### 1. 执行代码

```bash
curl -X POST http://localhost:8000/api/v1/execute/python \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "timeout": 30,
    "memory_limit": 128,
    "input_data": "",
    "env_vars": {}
  }'
```

### 2. 执行Node.js代码

```bash
curl -X POST http://localhost:8000/api/v1/execute/nodejs \
  -H "Content-Type: application/json" \
  -d '{
    "code": "console.log(\"Hello from Node.js!\");",
    "timeout": 30,
    "memory_limit": 128
  }'
```

### 3. 获取支持的插件信息

```bash
curl http://localhost:8000/api/v1/plugins
```

### 4. 获取特定语言的插件信息

```bash
curl http://localhost:8000/api/v1/plugins/python
```

## 插件开发

### 创建自定义插件

1. 创建插件类:

```python
from src.runtime.extensions.base import LanguagePlugin, CodeTransformer

class CustomTransformer(CodeTransformer):
    def transform(self, code: str, context) -> str:
        # 实现转换逻辑
        return transformed_code

class CustomLanguagePlugin(LanguagePlugin):
    def __init__(self):
        super().__init__("custom_lang")
        self.register_transformer(CustomTransformer())
    
    def get_supported_extensions(self):
        return [".custom"]
    
    def get_default_filename(self):
        return "main.custom"
```

2. 注册插件:

```python
from src.runtime.extensions.registry import extension_manager
extension_manager.register_custom_plugin(CustomLanguagePlugin())
```

## 监控和日志

### 日志配置

日志文件位于 `/var/log/sandbox/`:
- `app.log`: 应用程序日志
- `security.log`: 安全相关日志
- `performance.log`: 性能日志

### 监控指标

- 请求处理时间
- 内存使用量
- CPU使用率
- 错误率
- 并发用户数

### Prometheus集成

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sandbox'
    static_configs:
      - targets: ['localhost:8000']
```

## 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 检查日志
   docker-compose logs sandbox
   
   # 检查系统资源
   docker system df
   ```

2. **内存不足**
   ```bash
   # 调整内存限制
   docker-compose down
   # 修改docker-compose.yml中的内存限制
   docker-compose up -d
   ```

3. **权限问题**
   ```bash
   # 检查文件权限
   ls -la /opt/sandbox/
   
   # 修复权限
   sudo chown -R sandbox:sandbox /opt/sandbox
   ```

### 性能调优

1. **增加工作进程数**
   ```bash
   export MAX_WORKERS=8
   docker-compose up -d
   ```

2. **调整Docker资源限制**
   ```json
   {
     "default-ulimits": {
       "nofile": {
         "Soft": 65536,
         "Hard": 65536
       }
     }
   }
   ```

## 安全最佳实践

1. **网络隔离**
   - 使用专用网络
   - 限制出站连接
   - 使用防火墙规则

2. **镜像安全**
   - 使用官方基础镜像
   - 定期更新镜像
   - 扫描漏洞

3. **访问控制**
   - 使用API密钥认证
   - 实施速率限制
   - 记录所有访问日志

4. **资源限制**
   - 设置内存限制
   - 设置CPU限制
   - 设置磁盘配额

## 备份和恢复

### 备份策略

```bash
# 创建备份
#!/bin/bash
BACKUP_DIR="/backup/sandbox/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

docker-compose exec sandbox tar czf $BACKUP_DIR/config.tar.gz /app/config
docker commit sandbox_api $BACKUP_DIR/image_backup.tar
```

### 恢复过程

```bash
# 从备份恢复
docker load < image_backup.tar
docker-compose up -d
```

## 升级指南

### 版本升级

1. **备份当前配置**
2. **拉取新镜像**
   ```bash
   docker-compose pull
   ```
3. **滚动更新**
   ```bash
   docker-compose up -d --no-deps sandbox
   ```
4. **验证升级**
   ```bash
   curl http://localhost:8000/health
   ```

### 回滚计划

```bash
# 如果升级失败，回滚到上一版本
docker-compose down
docker tag sandbox:latest sandbox:backup
docker tag sandbox:previous sandbox:latest
docker-compose up -d
```

## 联系和支持

如有问题，请通过以下方式联系：
- GitHub Issues: [项目Issues页面](https://github.com/your-org/secure-code-sandbox/issues)
- 邮件: support@yourcompany.com
- 文档: [项目Wiki](https://github.com/your-org/secure-code-sandbox/wiki)