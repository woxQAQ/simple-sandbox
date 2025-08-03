"""
本地测试环境工具
提供本地模拟容器沙盒环境的功能
"""

import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ContextManager, Dict

from src.config import get_test_config


class TestSandboxEnvironment:
    """测试沙盒环境类"""

    def __init__(self):
        self.config = get_test_config()
        self.temp_dirs = []

    def setup(self) -> None:
        """设置测试环境"""
        # 设置测试环境变量
        os.environ["TEST_MODE"] = "true"
        os.environ["DEBUG_MODE"] = "true"
        os.environ["SANDBOX_USER_ID"] = "1000"
        os.environ["SANDBOX_GROUP_ID"] = "1000"

        # 创建临时目录模拟容器环境
        self._create_test_directories()

    def cleanup(self) -> None:
        """清理测试环境"""
        # 清理临时目录
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

        # 清理环境变量
        for key in ["TEST_MODE", "DEBUG_MODE", "SANDBOX_USER_ID", "SANDBOX_GROUP_ID"]:
            if key in os.environ:
                del os.environ[key]

    def _create_test_directories(self) -> None:
        """创建测试目录"""
        # 创建临时安全库目录
        python_lib_dir = Path(self.config.python_security_lib_dir)
        nodejs_lib_dir = Path(self.config.nodejs_security_lib_dir)

        if not python_lib_dir.exists():
            python_lib_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dirs.append(python_lib_dir)

        if not nodejs_lib_dir.exists():
            nodejs_lib_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dirs.append(nodejs_lib_dir)

        # 复制安全库文件到测试目录
        self._copy_security_libraries(python_lib_dir, nodejs_lib_dir)

    def _copy_security_libraries(
        self, python_lib_dir: Path, nodejs_lib_dir: Path
    ) -> None:
        """复制安全库文件到测试目录"""
        # 查找项目中的安全库文件
        project_root = Path(__file__).parent.parent.parent
        build_lib_dir = project_root / "build" / "lib"

        if build_lib_dir.exists():
            import shutil

            # 复制Python安全库
            python_lib_file = build_lib_dir / "libseccomp_injector_python.so"
            if python_lib_file.exists():
                target_python_lib = (
                    python_lib_dir / "libseccomp_injector_python.so"
                )
                if python_lib_file != target_python_lib:
                    shutil.copy2(python_lib_file, target_python_lib)

            # 复制Node.js安全库
            nodejs_lib_file = build_lib_dir / "libseccomp_injector_nodejs.so"
            if nodejs_lib_file.exists():
                target_nodejs_lib = (
                    nodejs_lib_dir / "libseccomp_injector_nodejs.so"
                )
                if nodejs_lib_file != target_nodejs_lib:
                    shutil.copy2(nodejs_lib_file, target_nodejs_lib)

    def get_test_config(self) -> Dict[str, Any]:
        """获取测试配置"""
        return self.config.to_dict()

    @contextmanager
    def context(self) -> ContextManager["TestSandboxEnvironment"]:
        """上下文管理器"""
        self.setup()
        try:
            yield self
        finally:
            self.cleanup()


class TestRuntimeManager:
    """测试运行时管理器"""

    def __init__(self):
        self.sandbox = TestSandboxEnvironment()

    def create_python_runtime(self):
        """创建Python运行时测试实例"""
        from src.runtime.python.runtime import PythonRuntime

        return PythonRuntime()

    def create_nodejs_runtime(self):
        """创建Node.js运行时测试实例"""
        from src.runtime.nodejs.runtime import NodeJSRuntime

        return NodeJSRuntime()

    @contextmanager
    def runtime_context(self):
        """运行时测试上下文"""
        with self.sandbox.context():
            yield self


# 全局测试环境实例
test_sandbox = TestSandboxEnvironment()
test_runtime_manager = TestRuntimeManager()


def setup_test_environment():
    """设置测试环境的便捷函数"""
    return test_sandbox.setup()


def cleanup_test_environment():
    """清理测试环境的便捷函数"""
    return test_sandbox.cleanup()


@contextmanager
def test_environment_context():
    """测试环境上下文管理器"""
    with test_sandbox.context():
        yield


def create_test_runtime_manager():
    """创建测试运行时管理器"""
    return TestRuntimeManager()


# 测试数据
TEST_CASES = {
    "python": {
        "simple": {
            "code": "print('Hello, World!')",
            "expected_stdout": "Hello, World!\n",
            "expected_stderr": "",
            "expected_exit_code": 0,
        },
        "error": {
            "code": "1/0",
            "expected_stdout": "",
            "expected_stderr_contains": "ZeroDivisionError",
            "expected_exit_code": 1,
        },
        "syntax_error": {
            "code": "print('Hello, World!')",
            "expected_stdout": "",
            "expected_stderr_contains": "SyntaxError",
            "expected_exit_code": 1,
        },
        "with_input": {
            "code": "name = input(); print(f'Hello, {name}!')",
            "input_data": "Alice",
            "expected_stdout": "Hello, Alice!\n",
            "expected_stderr": "",
            "expected_exit_code": 0,
        },
    },
    "nodejs": {
        "simple": {
            "code": "console.log('Hello, World!');",
            "expected_stdout": "Hello, World!\n",
            "expected_stderr": "",
            "expected_exit_code": 0,
        },
        "error": {
            "code": "console.log(undefinedVar);",
            "expected_stdout": "",
            "expected_stderr_contains": "ReferenceError",
            "expected_exit_code": 1,
        },
        "syntax_error": {
            "code": "console.log('Hello, World!')",
            "expected_stdout": "",
            "expected_stderr_contains": "SyntaxError",
            "expected_exit_code": 1,
        },
        "with_input": {
            "code": "const readline = require('readline'); const rl = readline.createInterface({input: process.stdin, output: process.stdout}); rl.question('', (name) => { console.log(`Hello, ${name}!`); rl.close(); });",
            "input_data": "Alice",
            "expected_stdout": "Hello, Alice!\n",
            "expected_stderr": "",
            "expected_exit_code": 0,
        },
    },
}


def get_test_case(language: str, case_name: str) -> Dict[str, Any]:
    """获取测试用例"""
    try:
        return TEST_CASES[language][case_name]
    except KeyError:
        raise ValueError(f"Unknown test case: {language}.{case_name}")


def run_test_case(
    language: str, case_name: str, runtime_manager: TestRuntimeManager = None
) -> Dict[str, Any]:
    """运行测试用例"""
    if runtime_manager is None:
        runtime_manager = test_runtime_manager

    test_case = get_test_case(language, case_name)

    with runtime_manager.runtime_context():
        if language == "python":
            runtime = runtime_manager.create_python_runtime()
        elif language == "nodejs":
            runtime = runtime_manager.create_nodejs_runtime()
        else:
            raise ValueError(f"Unsupported language: {language}")

        result = runtime.execute(
            code=test_case["code"], input_data=test_case.get("input_data", "")
        )

        return {
            "test_case": case_name,
            "language": language,
            "result": result,
            "expected": test_case,
            "passed": _check_test_result(result, test_case),
        }


def _check_test_result(result, expected) -> bool:
    """检查测试结果"""
    # 检查退出码
    if result.exit_code != expected.get("expected_exit_code", 0):
        return False

    # 检查标准输出
    if result.stdout != expected.get("expected_stdout", ""):
        return False

    # 检查标准错误
    if "expected_stderr_contains" in expected:
        if expected["expected_stderr_contains"] not in result.stderr:
            return False
    elif result.stderr != expected.get("expected_stderr", ""):
        return False

    return True
