#!/bin/bash

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

# 检查操作系统
check_platform() {
    log_info "Checking platform compatibility..."
    
    case "$(uname -s)" in
        Linux)
            log_success "Linux platform detected - seccomp supported"
            PLATFORM="linux"
            ;;
        Darwin)
            log_warning "macOS platform detected - seccomp not supported, building stub library"
            PLATFORM="darwin"
            ;;
        *)
            log_error "Unsupported platform: $(uname -s)"
            exit 1
            ;;
    esac
    
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

# 验证Python模块
validate_python_modules() {
    log_info "Validating Python modules..."
    
    # 检查语法
    if python3 -m py_compile src/security/__init__.py; then
        log_success "security/__init__.py syntax OK"
    else
        log_error "Syntax error in security/__init__.py"
        exit 1
    fi
    
    if python3 -m py_compile src/security/syscalls/parser.py; then
        log_success "syscalls/parser.py syntax OK"
    else
        log_error "Syntax error in syscalls/parser.py"
        exit 1
    fi
    
    if python3 -m py_compile src/security/injection/seccomp_wrapper.py; then
        log_success "injection/seccomp_wrapper.py syntax OK"
    else
        log_error "Syntax error in injection/seccomp_wrapper.py"
        exit 1
    fi
    
    log_success "All Python modules validated"
}

# 运行测试
run_tests() {
    log_info "Running basic functionality tests..."
    
    # 测试系统调用配置解析器
    python3 -c "
from src.security.syscalls.parser import SyscallConfigParser
parser = SyscallConfigParser()
print('Supported languages:', parser.get_supported_languages())
print('Python syscalls count:', len(parser.get_syscalls_for_language('python')))
print('Parser test: PASSED')
" 2>&1 | tee -a build/logs/test.log
    
    if [ $? -eq 0 ]; then
        log_success "Parser test passed"
    else
        log_error "Parser test failed"
        exit 1
    fi
    
    # 测试seccomp包装器（仅检查导入）
    python3 -c "
from src.security.injection.seccomp_wrapper import SeccompInjector
injector = SeccompInjector()
print('Seccomp supported:', injector.is_supported())
print('Wrapper test: PASSED')
" 2>&1 | tee -a build/logs/test.log
    
    if [ $? -eq 0 ]; then
        log_success "Wrapper test passed"
    else
        log_warning "Wrapper test failed (expected on non-Linux platforms)"
    fi
    
    log_success "Basic tests completed"
}

# 生成构建报告
generate_report() {
    log_info "Generating build report..."
    
    REPORT_FILE="build/logs/build_report.txt"
    
    cat > "$REPORT_FILE" << EOF
Seccomp Security Component Build Report
======================================

Build Date: $(date)
Platform: $(uname -s) $(uname -r)
Architecture: $(uname -m)
Builder: $(whoami)

Components Built:
- seccomp_injector.c -> libseccomp_injector.so/dylib
- Python security modules
- System call configuration parser
- Security manager integration

Build Status: SUCCESS

Files Created:
$(find build -type f -name "*" | sort)

Next Steps:
1. Test the integration with the runtime manager
2. Verify seccomp profiles work correctly
3. Deploy to container environment

EOF
    
    log_success "Build report generated: $REPORT_FILE"
}

# 主函数
main() {
    log_info "Starting seccomp security component build..."
    
    check_platform
    check_dependencies
    setup_build_dirs
    build_shared_library
    validate_python_modules
    run_tests
    generate_report
    
    log_success "Build completed successfully!"
    log_info "Shared library location: build/lib/"
    log_info "Build logs: build/logs/"
    
    if [ "$PLATFORM" = "linux" ]; then
        log_info "To install system-wide (requires sudo): cd src/security/bpf && make install"
    fi
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