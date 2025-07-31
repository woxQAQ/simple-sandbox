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

# 创建沙盒目录结构
setup_sandbox_directories() {
    log_info "Setting up sandbox directories..."

    # 创建沙盒根目录和语言子目录
    mkdir -p /var/sandbox/python
    mkdir -p /var/sandbox/nodejs

    # 设置权限
    chmod 755 /var/sandbox
    chmod 755 /var/sandbox/python
    chmod 755 /var/sandbox/nodejs

    log_success "Sandbox directories created"
}

# 安全复制文件
copy_file_safely() {
    local src="$1"
    local dest="$2"

    if [ -L "$src_file" ]; then
        # If src_file is a symbolic link, copy it without changing permissions
        cp -P "$src_file" "$dest_file"
    elif [ -b "$src_file" ] || [ -c "$src_file" ]; then
        # If src_file is a device file, copy it and change permissions
        cp "$src_file" "$dest_file"
        chmod 444 "$dest_file"
    else
        # Otherwise, create a hard link and change the permissions to read-only
        ln -f "$src_file" "$dest_file" 2>/dev/null || { cp "$src_file" "$dest_file" && chmod 444 "$dest_file"; }
    fi
}

# 复制Python运行时库
copy_python_runtime_libraries() {
    log_info "Copying Python runtime libraries..."

    # Python运行时库路径
    local python_lib_paths
    python_lib_paths="/usr/local/lib/python3.10 /usr/lib/python3.10 /usr/lib/python3 /usr/lib/x86_64-linux-gnu"

    local sandbox_dir="/var/sandbox/python"
    local copied_count=0

    for lib_path in $python_lib_paths; do
        if [ -d "$lib_path" ]; then
            local target_path="$sandbox_dir${lib_path}"
            log_info "Processing Python library: $lib_path"

            if copy_file_safely "$lib_path" "$target_path"; then
                copied_count=$((copied_count + 1))
            fi
        else
            log_warning "Python library path not found: $lib_path"
        fi
    done

    log_success "Copied $copied_count Python runtime libraries"
}

# 复制网络配置文件
copy_network_configs() {
    log_info "Copying network configuration files..."

    # 网络配置文件列表
    local network_files
    network_files="/etc/ssl/certs/ca-certificates.crt /etc/nsswitch.conf /etc/resolv.conf /run/systemd/resolve/stub-resolv.conf /etc/hosts"

    # 需要复制网络配置的运行时
    local runtimes
    runtimes="python nodejs"

    for runtime in $runtimes; do
        local sandbox_dir="/var/sandbox/$runtime"
        local etc_dir="$sandbox_dir/etc"

        # 创建etc目录结构
        mkdir -p "$etc_dir/ssl/certs"
        mkdir -p "$etc_dir"

        local copied_count=0

        for network_file in $network_files; do
            if [ -f "$network_file" ] || [ -L "$network_file" ]; then
                local target_path="$sandbox_dir$network_file"

                if copy_file_safely "$network_file" "$target_path"; then
                    copied_count=$((copied_count + 1))
                fi
            else
                log_warning "Network file not found: $network_file"
            fi
        done

        log_success "Copied $copied_count network configuration files for $runtime"
    done
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
    setup_sandbox_directories
    copy_python_runtime_libraries
    copy_network_configs

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
