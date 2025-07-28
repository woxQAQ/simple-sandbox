# Makefile for seccomp injector shared library
# 支持Linux平台的amd64和arm64架构

# 编译器和标志
CC = gcc
CFLAGS = -Wall -Wextra -O2 -fPIC -std=c99
LDFLAGS = -shared

# 目标架构检测
ARCH := $(shell uname -m)
ifeq ($(ARCH),x86_64)
    ARCH_FLAGS = -DARCH_X86_64
else ifeq ($(ARCH),aarch64)
    ARCH_FLAGS = -DARCH_AARCH64
else ifeq ($(ARCH),arm64)
    ARCH_FLAGS = -DARCH_AARCH64
else
    $(error Unsupported architecture: $(ARCH))
endif

# 平台检测 - 仅支持Linux
UNAME_S := $(shell uname -s)
ifneq ($(UNAME_S),Linux)
    $(error This build system only supports Linux. Current platform: $(UNAME_S))
endif

PLATFORM_FLAGS = -DLINUX
LIB_EXT = so
LDFLAGS += -Wl,-soname,libseccomp_injector.$(LIB_EXT).1

# 源文件和目标文件
SRCS = seccomp_injector.c
OBJS_PYTHON = seccomp_injector_python.o
OBJS_NODEJS = seccomp_injector_nodejs.o
PYTHON_TARGET = libseccomp_injector_python.$(LIB_EXT)
NODEJS_TARGET = libseccomp_injector_nodejs.$(LIB_EXT)

# 构建目录
BUILD_DIR = ../../../build/lib
INSTALL_DIR = /usr/local/lib

# 默认目标
all: $(PYTHON_TARGET) $(NODEJS_TARGET)

# 创建构建目录
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

# 编译Python版本的目标文件
$(OBJS_PYTHON): $(SRCS) seccomp_injector.h syscalls_generated.h
	$(CC) $(CFLAGS) $(ARCH_FLAGS) $(PLATFORM_FLAGS) -DLANG_PYTHON -c $< -o $@

# 编译Node.js版本的目标文件
$(OBJS_NODEJS): $(SRCS) seccomp_injector.h syscalls_generated.h
	$(CC) $(CFLAGS) $(ARCH_FLAGS) $(PLATFORM_FLAGS) -DLANG_NODEJS -c $< -o $@

# 生成系统调用定义文件
syscalls_generated.h:
	@echo "Generating syscall definitions..."
	@python3 generate_syscalls.py > syscalls_generated.h
	@echo "Syscall definitions generated in syscalls_generated.h"

# 链接Python版本的共享库
$(PYTHON_TARGET): $(OBJS_PYTHON) | $(BUILD_DIR)
	$(CC) $(LDFLAGS) -o $(BUILD_DIR)/$(PYTHON_TARGET) $(OBJS_PYTHON)
	@echo "Built $(PYTHON_TARGET) for $(UNAME_S)/$(ARCH)"

# 链接Node.js版本的共享库
$(NODEJS_TARGET): $(OBJS_NODEJS) | $(BUILD_DIR)
	$(CC) $(LDFLAGS) -o $(BUILD_DIR)/$(NODEJS_TARGET) $(OBJS_NODEJS)
	@echo "Built $(NODEJS_TARGET) for $(UNAME_S)/$(ARCH)"

# 清理
clean:
	@rm -f $(OBJS_PYTHON) $(OBJS_NODEJS)
	@rm -f $(BUILD_DIR)/$(PYTHON_TARGET) $(BUILD_DIR)/$(NODEJS_TARGET)
	@rm -f syscalls_generated.h
	@echo "Cleaned build artifacts"

# 测试编译（不链接）
test-compile: $(OBJS_PYTHON) $(OBJS_NODEJS)
	@echo "Compilation test passed"

# 单独构建目标
python: $(PYTHON_TARGET)
nodejs: $(NODEJS_TARGET)

# 安装
install: $(PYTHON_TARGET) $(NODEJS_TARGET)
	sudo cp $(BUILD_DIR)/$(PYTHON_TARGET) $(INSTALL_DIR)/
	sudo cp $(BUILD_DIR)/$(NODEJS_TARGET) $(INSTALL_DIR)/
	sudo ldconfig

# 卸载
uninstall:
	sudo rm -f $(INSTALL_DIR)/$(PYTHON_TARGET)
	sudo rm -f $(INSTALL_DIR)/$(NODEJS_TARGET)
	sudo ldconfig

# 显示构建信息
info:
	@echo "Platform: $(UNAME_S)"
	@echo "Architecture: $(ARCH)"
	@echo "Compiler: $(CC)"
	@echo "CFLAGS: $(CFLAGS) $(ARCH_FLAGS) $(PLATFORM_FLAGS)"
	@echo "LDFLAGS: $(LDFLAGS)"
	@echo "Python Target: $(PYTHON_TARGET)"
	@echo "Node.js Target: $(NODEJS_TARGET)"
	@echo "Build directory: $(BUILD_DIR)"

# 检查依赖
check-deps:
	@echo "Checking build dependencies..."
	@which $(CC) > /dev/null || (echo "Error: $(CC) not found" && exit 1)
	@echo "All dependencies satisfied"

# 帮助
help:
	@echo "Available targets:"
	@echo "  all          - Build all shared libraries (default)"
	@echo "  python       - Build Python shared library only"
	@echo "  nodejs       - Build Node.js shared library only"
	@echo "  clean        - Remove build artifacts"
	@echo "  install      - Install shared libraries"
	@echo "  uninstall    - Uninstall shared libraries"
	@echo "  test-compile - Test compilation without linking"
	@echo "  info         - Show build configuration"
	@echo "  check-deps   - Check build dependencies"
	@echo "  help         - Show this help message"

.PHONY: all clean install uninstall test-compile info check-deps help python nodejs