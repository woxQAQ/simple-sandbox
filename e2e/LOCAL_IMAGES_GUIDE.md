# 本地镜像测试指南

## 概述

e2e 测试现在已配置为使用本地构建的镜像，这样可以在修改语言运行时后立即进行测试，无需推送到远程仓库。

## 配置变更

### 1. 测试配置文件修改

在 `testdata/test_config.yaml` 中：
- `image_registry` 设置为空字符串（使用本地镜像）
- `repository` 改为本地镜像名称：
  - `sandbox-python` (原: `woxqaq/sandbox-python`)
  - `sandbox-node` (原: `woxqaq/sandbox-node`)

### 2. Makefile 增强

新增的目标：
- `podman-build`: 使用 podman 构建本地镜像
- `local-test`: 构建本地镜像并运行测试
- 修复了构建上下文路径问题

## 使用方法

### 构建本地镜像

```bash
# 使用 podman 构建（推荐，与测试环境一致）
make podman-build

# 或使用 docker 构建
make docker-build
```

### 运行测试

```bash
# 构建本地镜像并运行测试（一步完成）
make local-test

# 或分步执行
make podman-build
make test
```

### 验证镜像

```bash
# 检查本地镜像
podman images | grep sandbox

# 运行验证脚本
./verify_local_images.sh
```

## 镜像信息

构建成功后，你将看到以下本地镜像：
- `localhost/sandbox-python:latest` - Python 运行时
- `localhost/sandbox-node:latest` - Node.js 运行时

## 开发工作流

1. **修改运行时代码**：编辑 `docker/runtimes/python/` 或 `docker/runtimes/node/` 中的文件
2. **重新构建镜像**：`make podman-build`
3. **运行测试**：`make test`
4. **验证功能**：检查测试结果或手动验证

## 注意事项

- 本地镜像优先级高于远程镜像
- 确保 podman 正常运行（`podman ps` 应该成功）
- 如果遇到构建问题，检查 Dockerfile 路径和构建上下文
- 测试失败不一定意味着镜像有问题，可能是测试环境或配置问题

## 故障排除

### 构建失败
- 检查 podman 是否正常运行
- 确认网络连接正常（需要拉取基础镜像）
- 检查磁盘空间是否充足

### 测试失败
- 确认镜像构建成功：`podman images | grep sandbox`
- 检查配置文件是否正确
- 查看详细的测试日志

### 权限问题
- 确保当前用户有权限运行 podman
- 检查文件权限设置