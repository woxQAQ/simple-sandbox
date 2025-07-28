#!/usr/bin/env python3
"""
Python运行时单元测试
测试Python代码执行功能
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

from src.runtime.python_runtime import PythonRuntime
from src.runtime.models import ExecutionRequest, ExecutionStatus, ResourceLimits


class TestPythonRuntime:
    """Python运行时测试"""
    
    @pytest.fixture
    def runtime(self):
        """创建Python运行时实例"""
        return PythonRuntime()
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.unit
    def test_runtime_initialization(self, runtime):
        """测试运行时初始化"""
        assert runtime.language == "python"
        assert ".py" in runtime.get_supported_extensions()
        assert ".pyw" in runtime.get_supported_extensions()
        assert runtime.get_default_filename() == "main.py"
    
    @pytest.mark.unit
    def test_get_default_resource_limits(self, runtime):
        """测试默认资源限制"""
        limits = runtime.get_default_resource_limits()
        
        assert isinstance(limits, ResourceLimits)
        assert limits.timeout_seconds == 30
        assert limits.memory_limit_mb == 128
        assert limits.cpu_limit_percent == 50
        assert limits.max_file_size_mb == 10
        assert limits.max_output_size_mb == 5
    
    @pytest.mark.unit
    def test_preprocess_code_simple(self, runtime):
        """测试简单代码预处理"""
        code = "print('Hello, World!')"
        processed = runtime.preprocess_code(code)
        
        assert processed == code  # 简单代码不需要预处理
    
    @pytest.mark.unit
    def test_preprocess_code_with_imports(self, runtime):
        """测试带导入的代码预处理"""
        code = "import os\nprint(os.getcwd())"
        processed = runtime.preprocess_code(code)
        
        # 应该包含安全检查
        assert "import os" in processed
    
    @pytest.mark.unit
    def test_preprocess_code_with_dangerous_imports(self, runtime):
        """测试危险导入的代码预处理"""
        code = "import subprocess\nsubprocess.run(['rm', '-rf', '/'])"
        
        with pytest.raises(ValueError, match="危险的导入"):
            runtime.preprocess_code(code)
    
    @pytest.mark.unit
    def test_get_command_basic(self, runtime, temp_dir):
        """测试基本命令生成"""
        code_file = temp_dir / "test.py"
        code_file.write_text("print('hello')")
        
        request = ExecutionRequest(
            code="print('hello')",
            language="python",
            resource_limits=ResourceLimits()
        )
        
        command = runtime.get_command(str(code_file), request)
        
        assert "python" in command[0] or "python3" in command[0]
        assert str(code_file) in command
    
    @pytest.mark.unit
    def test_get_command_with_environment(self, runtime, temp_dir):
        """测试带环境变量的命令生成"""
        code_file = temp_dir / "test.py"
        code_file.write_text("import os; print(os.environ.get('TEST_VAR'))")
        
        request = ExecutionRequest(
            code="import os; print(os.environ.get('TEST_VAR'))",
            language="python",
            resource_limits=ResourceLimits(),
            environment_variables={"TEST_VAR": "test_value"}
        )
        
        command = runtime.get_command(str(code_file), request)
        
        assert "python" in command[0] or "python3" in command[0]
        assert str(code_file) in command
    
    @pytest.mark.unit
    @patch('subprocess.run')
    def test_execute_success(self, mock_subprocess, runtime, temp_dir):
        """测试成功执行"""
        # 模拟成功的subprocess执行
        mock_result = Mock()
        mock_result.stdout = "Hello, World!"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        request = ExecutionRequest(
            code="print('Hello, World!')",
            language="python",
            resource_limits=ResourceLimits(timeout_seconds=30, memory_limit_mb=128)
        )
        
        with patch.object(runtime, '_create_temp_file') as mock_create_file:
            mock_create_file.return_value = temp_dir / "test.py"
            
            with patch('time.time', side_effect=[0, 1.5]):
                result = runtime.execute(request)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.stdout == "Hello, World!"
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.execution_time == 1.5
        assert result.error_message is None
    
    @pytest.mark.unit
    @patch('subprocess.run')
    def test_execute_syntax_error(self, mock_subprocess, runtime, temp_dir):
        """测试语法错误执行"""
        # 模拟语法错误的subprocess执行
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "SyntaxError: invalid syntax"
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        request = ExecutionRequest(
            code="print('hello'",  # 语法错误
            language="python",
            resource_limits=ResourceLimits()
        )
        
        with patch.object(runtime, '_create_temp_file') as mock_create_file:
            mock_create_file.return_value = temp_dir / "test.py"
            
            with patch('time.time', side_effect=[0, 0.1]):
                result = runtime.execute(request)
        
        assert result.status == ExecutionStatus.ERROR
        assert result.stderr == "SyntaxError: invalid syntax"
        assert result.exit_code == 1
        assert "语法错误" in result.error_message or "SyntaxError" in result.error_message
    
    @pytest.mark.unit
    @patch('subprocess.run')
    def test_execute_timeout(self, mock_subprocess, runtime, temp_dir):
        """测试执行超时"""
        # 模拟超时异常
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired(cmd=["python"], timeout=30)
        
        request = ExecutionRequest(
            code="import time; time.sleep(60)",
            language="python",
            resource_limits=ResourceLimits(timeout_seconds=30)
        )
        
        with patch.object(runtime, '_create_temp_file') as mock_create_file:
            mock_create_file.return_value = temp_dir / "test.py"
            
            with patch('time.time', side_effect=[0, 30.0]):
                result = runtime.execute(request)
        
        assert result.status == ExecutionStatus.TIMEOUT
        assert result.execution_time == 30.0
        assert "超时" in result.error_message or "timeout" in result.error_message.lower()
    
    @pytest.mark.unit
    @patch('subprocess.run')
    def test_execute_with_input(self, mock_subprocess, runtime, temp_dir):
        """测试带输入的执行"""
        mock_result = Mock()
        mock_result.stdout = "Hello, Alice!"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        request = ExecutionRequest(
            code="name = input('Enter name: '); print(f'Hello, {name}!')",
            language="python",
            resource_limits=ResourceLimits(),
            input_data="Alice"
        )
        
        with patch.object(runtime, '_create_temp_file') as mock_create_file:
            mock_create_file.return_value = temp_dir / "test.py"
            
            with patch('time.time', side_effect=[0, 1.0]):
                result = runtime.execute(request)
        
        # 验证subprocess.run被调用时传入了input参数
        mock_subprocess.assert_called_once()
        call_kwargs = mock_subprocess.call_args[1]
        assert call_kwargs.get('input') == "Alice"
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.stdout == "Hello, Alice!"
    
    @pytest.mark.unit
    @patch('subprocess.run')
    def test_execute_memory_limit_exceeded(self, mock_subprocess, runtime, temp_dir):
        """测试内存限制超出"""
        # 模拟内存超出错误
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "MemoryError: Unable to allocate memory"
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        request = ExecutionRequest(
            code="data = [0] * (10**9)  # 尝试分配大量内存",
            language="python",
            resource_limits=ResourceLimits(memory_limit_mb=64)
        )
        
        with patch.object(runtime, '_create_temp_file') as mock_create_file:
            mock_create_file.return_value = temp_dir / "test.py"
            
            with patch('time.time', side_effect=[0, 2.0]):
                result = runtime.execute(request)
        
        assert result.status == ExecutionStatus.ERROR
        assert "MemoryError" in result.stderr
        assert result.exit_code == 1
    
    @pytest.mark.unit
    def test_create_temp_file(self, runtime):
        """测试临时文件创建"""
        code = "print('Hello, World!')"
        
        with runtime._create_temp_file(code) as temp_file:
            assert temp_file.exists()
            assert temp_file.suffix == ".py"
            content = temp_file.read_text()
            assert content == code
        
        # 文件应该在上下文管理器退出后被删除
        assert not temp_file.exists()
    
    @pytest.mark.unit
    def test_validate_code_safe(self, runtime):
        """测试安全代码验证"""
        safe_code = "print('Hello, World!')"
        
        # 安全代码不应该抛出异常
        runtime._validate_code(safe_code)
    
    @pytest.mark.unit
    def test_validate_code_dangerous_imports(self, runtime):
        """测试危险导入验证"""
        dangerous_codes = [
            "import subprocess",
            "from os import system",
            "import socket",
            "__import__('subprocess')",
            "exec('import subprocess')",
            "eval('__import__(\"subprocess\")')"
        ]
        
        for code in dangerous_codes:
            with pytest.raises(ValueError, match="危险的导入|不安全的操作"):
                runtime._validate_code(code)
    
    @pytest.mark.unit
    def test_validate_code_dangerous_functions(self, runtime):
        """测试危险函数验证"""
        dangerous_codes = [
            "open('/etc/passwd', 'r')",
            "exec('print(1)')",
            "eval('1+1')",
            "compile('print(1)', '<string>', 'exec')",
            "globals()['__builtins__']",
            "locals()['__builtins__']"
        ]
        
        for code in dangerous_codes:
            with pytest.raises(ValueError, match="危险的函数|不安全的操作"):
                runtime._validate_code(code)
    
    @pytest.mark.unit
    @patch('psutil.Process')
    def test_get_memory_usage(self, mock_process_class, runtime):
        """测试内存使用量获取"""
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 64 * 1024 * 1024  # 64MB in bytes
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process
        
        memory_mb = runtime._get_memory_usage(1234)
        
        assert memory_mb == 64.0
        mock_process_class.assert_called_once_with(1234)
    
    @pytest.mark.unit
    @patch('psutil.Process')
    def test_get_memory_usage_process_not_found(self, mock_process_class, runtime):
        """测试进程不存在时的内存使用量获取"""
        import psutil
        mock_process_class.side_effect = psutil.NoSuchProcess(1234)
        
        memory_mb = runtime._get_memory_usage(1234)
        
        assert memory_mb == 0.0
    
    @pytest.mark.unit
    def test_setup_environment_variables(self, runtime):
        """测试环境变量设置"""
        env_vars = {"TEST_VAR": "test_value", "ANOTHER_VAR": "another_value"}
        
        with patch.dict(os.environ, {}, clear=True):
            runtime._setup_environment_variables(env_vars)
            
            assert os.environ["TEST_VAR"] == "test_value"
            assert os.environ["ANOTHER_VAR"] == "another_value"
    
    @pytest.mark.unit
    def test_cleanup_environment_variables(self, runtime):
        """测试环境变量清理"""
        env_vars = {"TEST_VAR": "test_value"}
        
        with patch.dict(os.environ, {"TEST_VAR": "old_value"}, clear=False):
            runtime._setup_environment_variables(env_vars)
            assert os.environ["TEST_VAR"] == "test_value"
            
            runtime._cleanup_environment_variables(env_vars)
            assert "TEST_VAR" not in os.environ