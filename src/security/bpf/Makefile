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
OBJS = $(SRCS:.c=.o)
TARGET = libseccomp_injector.$(LIB_EXT)

# 构建目录
BUILD_DIR = ../../../build/lib
INSTALL_DIR = /usr/local/lib

# 默认目标
all: $(TARGET)

# 创建构建目录
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

# 编译目标文件
%.o: %.c seccomp_injector.h
	$(CC) $(CFLAGS) $(ARCH_FLAGS) $(PLATFORM_FLAGS) -c $< -o $@

# 链接共享库
$(TARGET): $(OBJS) | $(BUILD_DIR)
	$(CC) $(LDFLAGS) -o $(BUILD_DIR)/$(TARGET) $(OBJS)
	@echo "Built $(TARGET) for $(UNAME_S)/$(ARCH)"

# 清理
clean:
	@rm -f $(OBJS)
	@rm -f $(BUILD_DIR)/$(TARGET)
	@echo "Cleaned build artifacts"

# 测试编译（不链接）
test-compile: $(OBJS)
	@echo "Compilation test passed"

# 显示构建信息
info:
	@echo "Platform: $(UNAME_S)"
	@echo "Architecture: $(ARCH)"
	@echo "Compiler: $(CC)"
	@echo "CFLAGS: $(CFLAGS) $(ARCH_FLAGS) $(PLATFORM_FLAGS)"
	@echo "LDFLAGS: $(LDFLAGS)"
	@echo "Target: $(TARGET)"
	@echo "Build directory: $(BUILD_DIR)"

# 检查依赖
check-deps:
	@echo "Checking build dependencies..."
	@which $(CC) > /dev/null || (echo "Error: $(CC) not found" && exit 1)
	@echo "All dependencies satisfied"

# 帮助
help:
	@echo "Available targets:"
	@echo "  all          - Build the shared library (default)"
	@echo "  clean        - Remove build artifacts"
	@echo "  test-compile - Test compilation without linking"
	@echo "  info         - Show build configuration"
	@echo "  check-deps   - Check build dependencies"
	@echo "  help         - Show this help message"

.PHONY: all clean install uninstall test-compile info check-deps help