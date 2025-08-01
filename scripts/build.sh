#!/usr/bin/env bash

# 确保使用正确的命令路径
# export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# 构建脚本 - 自动化seccomp安全组件的构建过程
# 支持Linux平台的amd64和arm64架构

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查操作系统 - 仅支持Linux
check_platform() {
    log_info "Checking platform compatibility..."

    if [ "$(uname -s)" != "Linux" ]; then
        log_error "This build system only supports Linux. Current platform: $(uname -s)"
        exit 1
    fi

    log_success "Linux platform detected - seccomp supported"
    PLATFORM="linux"

    ARCH=$(uname -m)
    log_info "Architecture: $ARCH"

    case "$ARCH" in
        x86_64|amd64)
            log_success "x86_64 architecture supported"
            ;;
        aarch64|arm64)
            log_success "ARM64 architecture supported"
            ;;
        *)
            log_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
}

# 检查依赖
check_dependencies() {
    log_info "Checking build dependencies..."

    # 检查编译器
    if ! command -v gcc &> /dev/null; then
        log_error "gcc compiler not found. Please install build-essential or equivalent."
        exit 1
    fi

    # 检查make
    if ! command -v make &> /dev/null; then
        log_error "make not found. Please install make."
        exit 1
    fi

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "python3 not found. Please install Python 3."
        exit 1
    fi

    log_success "All dependencies satisfied"
}

# 创建构建目录
setup_build_dirs() {
    log_info "Setting up build directories..."

    mkdir -p build/lib
    mkdir -p build/logs

    log_success "Build directories created"
}

# 构建C共享库
build_shared_library() {
    log_info "Building seccomp injector shared library..."

    cd src/security/bpf

    # 清理之前的构建
    make clean 2>/dev/null || true

    # 构建
    if make all 2>&1 | tee ../../../build/logs/build.log; then
        log_success "Shared library built successfully"
    else
        log_error "Failed to build shared library. Check build/logs/build.log for details."
        cd ../../..
        exit 1
    fi

    cd ../../..
}

# 主函数
main() {
    log_info "Starting seccomp security component build..."

    check_platform
    check_dependencies
    setup_build_dirs
    build_shared_library

    log_success "Build completed successfully!"
    log_info "Shared library location: build/lib/"
    log_info "Build logs: build/logs/"
    log_info "Sandbox runtime libraries: /var/sandbox/"

    log_info "To install system-wide (requires sudo): cd src/security/bpf && make install"
}

# 处理命令行参数
case "${1:-}" in
    "clean")
        log_info "Cleaning build artifacts..."
        rm -rf build/
        cd src/security/bpf && make clean
        log_success "Clean completed"
        ;;
    "test")
        log_info "Running tests only..."
        validate_python_modules
        run_tests
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [clean|test]"
        echo "  clean - Remove all build artifacts"
        echo "  test  - Run tests only"
        echo "  (no args) - Full build"
        exit 1
        ;;
esac
