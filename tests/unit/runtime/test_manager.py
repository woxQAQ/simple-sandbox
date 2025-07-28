#!/usr/bin/env python3
"""
运行时管理器单元测试
测试运行时管理器的功能
"""

import pytest
from unittest.mock import patch

from src.runtime.manager import RuntimeManager
from src.runtime.models import ExecutionRequest, ExecutionResult, ExecutionStatus, ResourceLimits, Language
from src.runtime.python_runtime import PythonRuntime
from src.runtime.nodejs_runtime import NodeJSRuntime


class TestRuntimeManager:
    """运行时管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建运行时管理器实例"""
        return RuntimeManager()
    
    @pytest.mark.unit
    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert isinstance(manager, RuntimeManager)
        assert hasattr(manager, '_runtimes')
        assert len(manager._runtimes) >= 2  # 至少支持Python和Node.js
    
    @pytest.mark.unit
    def test_get_supported_languages(self, manager):
        """测试获取支持的语言"""
        languages = manager.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) >= 2
        
        language_names = [lang.value for lang in languages]
        assert "python" in language_names
        assert "nodejs" in language_names
    
    @pytest.mark.unit
    def test_get_runtime_python(self, manager):
        """测试获取Python运行时"""
        runtime = manager.get_runtime(Language.PYTHON)
        
        assert isinstance(runtime, PythonRuntime)
        assert runtime.language == "python"
    
    @pytest.mark.unit
    def test_get_runtime_nodejs(self, manager):
        """测试获取Node.js运行时"""
        runtime = manager.get_runtime(Language.NODEJS)
        
        assert isinstance(runtime, NodeJSRuntime)
        assert runtime.language == "nodejs"
    
    @pytest.mark.unit
    def test_get_runtime_unsupported_language(self, manager):
        """测试获取不支持的语言运行时"""
        with pytest.raises(ValueError, match="不支持的语言|Unsupported language"):
            manager.get_runtime("unsupported_language")
    
    @pytest.mark.unit
    def test_get_runtime_by_string(self, manager):
        """测试通过字符串获取运行时"""
        python_runtime = manager.get_runtime("python")
        nodejs_runtime = manager.get_runtime("nodejs")
        
        assert isinstance(python_runtime, PythonRuntime)
        assert isinstance(nodejs_runtime, NodeJSRuntime)
    
    @pytest.mark.unit
    @patch('src.runtime.PythonRuntime.execute')
    def test_execute_python_code(self, mock_execute, manager):
        """测试执行Python代码"""
        # 模拟成功的执行结果
        mock_result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="Hello, World!",
            stderr="",
            execution_time=1.5,
            memory_used_mb=64.0,
            exit_code=0
        )
        mock_execute.return_value = mock_result
        
        request = ExecutionRequest(
            code="print('Hello, World!')",
            language="python",
            resource_limits=ResourceLimits()
        )
        
        result = manager.execute(request)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.stdout == "Hello, World!"
        mock_execute.assert_called_once_with(request)
    
    @pytest.mark.unit
    @patch('src.runtime.NodeJSRuntime.execute')
    def test_execute_nodejs_code(self, mock_execute, manager):
        """测试执行Node.js代码"""
        mock_result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="Hello, World!",
            stderr="",
            execution_time=2.0,
            memory_used_mb=96.0,
            exit_code=0
        )
        mock_execute.return_value = mock_result
        
        request = ExecutionRequest(
            code="console.log('Hello, World!');",
            language="nodejs",
            resource_limits=ResourceLimits()
        )
        
        result = manager.execute(request)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.stdout == "Hello, World!"
        mock_execute.assert_called_once_with(request)
    
    @pytest.mark.unit
    def test_execute_unsupported_language(self, manager):
        """测试执行不支持的语言代码"""
        request = ExecutionRequest(
            code="print('hello')",
            language="unsupported",
            resource_limits=ResourceLimits()
        )
        
        with pytest.raises(ValueError, match="不支持的语言|Unsupported language"):
            manager.execute(request)
    
    @pytest.mark.unit
    @patch('src.runtime.PythonRuntime.execute')
    def test_execute_with_error(self, mock_execute, manager):
        """测试执行错误处理"""
        mock_result = ExecutionResult(
            status=ExecutionStatus.ERROR,
            stdout="",
            stderr="SyntaxError: invalid syntax",
            execution_time=0.1,
            memory_used_mb=32.0,
            exit_code=1,
            error_message="代码执行失败"
        )
        mock_execute.return_value = mock_result
        
        request = ExecutionRequest(
            code="print('hello'",  # 语法错误
            language="python",
            resource_limits=ResourceLimits()
        )
        
        result = manager.execute(request)
        
        assert result.status == ExecutionStatus.ERROR
        assert result.stderr == "SyntaxError: invalid syntax"
        assert result.error_message == "代码执行失败"
    
    @pytest.mark.unit
    @patch('src.runtime.PythonRuntime.execute')
    def test_execute_with_timeout(self, mock_execute, manager):
        """测试执行超时处理"""
        mock_result = ExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            stdout="部分输出",
            stderr="",
            execution_time=30.0,
            memory_used_mb=128.0,
            exit_code=None,
            error_message="执行超时"
        )
        mock_execute.return_value = mock_result
        
        request = ExecutionRequest(
            code="import time; time.sleep(60)",
            language="python",
            resource_limits=ResourceLimits(timeout_seconds=30)
        )
        
        result = manager.execute(request)
        
        assert result.status == ExecutionStatus.TIMEOUT
        assert result.error_message == "执行超时"
        assert result.execution_time == 30.0
    
    @pytest.mark.unit
    def test_get_language_info_python(self, manager):
        """测试获取Python语言信息"""
        info = manager.get_language_info(Language.PYTHON)
        
        assert info.name == "python"
        assert ".py" in info.extensions
        assert ".pyw" in info.extensions
        assert info.version is not None
    
    @pytest.mark.unit
    def test_get_language_info_nodejs(self, manager):
        """测试获取Node.js语言信息"""
        info = manager.get_language_info(Language.NODEJS)
        
        assert info.name == "nodejs"
        assert ".js" in info.extensions
        assert ".mjs" in info.extensions
        assert ".cjs" in info.extensions
        assert info.version is not None
    
    @pytest.mark.unit
    def test_get_language_info_unsupported(self, manager):
        """测试获取不支持语言的信息"""
        with pytest.raises(ValueError, match="不支持的语言|Unsupported language"):
            manager.get_language_info("unsupported")
    
    @pytest.mark.unit
    def test_get_all_language_info(self, manager):
        """测试获取所有语言信息"""
        all_info = manager.get_all_language_info()
        
        assert isinstance(all_info, list)
        assert len(all_info) >= 2
        
        language_names = [info.name for info in all_info]
        assert "python" in language_names
        assert "nodejs" in language_names
    
    @pytest.mark.unit
    def test_validate_request_valid(self, manager):
        """测试有效请求验证"""
        request = ExecutionRequest(
            code="print('hello')",
            language="python",
            resource_limits=ResourceLimits()
        )
        
        # 有效请求不应该抛出异常
        manager._validate_request(request)
    
    @pytest.mark.unit
    def test_validate_request_empty_code(self, manager):
        """测试空代码验证"""
        request = ExecutionRequest(
            code="",
            language="python",
            resource_limits=ResourceLimits()
        )
        
        with pytest.raises(ValueError, match="代码不能为空|Code cannot be empty"):
            manager._validate_request(request)
    
    @pytest.mark.unit
    def test_validate_request_whitespace_only_code(self, manager):
        """测试仅包含空白字符的代码验证"""
        request = ExecutionRequest(
            code="   \n\t  ",
            language="python",
            resource_limits=ResourceLimits()
        )
        
        with pytest.raises(ValueError, match="代码不能为空|Code cannot be empty"):
            manager._validate_request(request)
    
    @pytest.mark.unit
    def test_validate_request_invalid_language(self, manager):
        """测试无效语言验证"""
        request = ExecutionRequest(
            code="print('hello')",
            language="invalid_language",
            resource_limits=ResourceLimits()
        )
        
        with pytest.raises(ValueError, match="不支持的语言|Unsupported language"):
            manager._validate_request(request)
    
    @pytest.mark.unit
    def test_validate_request_invalid_timeout(self, manager):
        """测试无效超时时间验证"""
        request = ExecutionRequest(
            code="print('hello')",
            language="python",
            resource_limits=ResourceLimits(timeout_seconds=0)
        )
        
        with pytest.raises(ValueError, match="超时时间必须大于0|Timeout must be greater than 0"):
            manager._validate_request(request)
    
    @pytest.mark.unit
    def test_validate_request_invalid_memory_limit(self, manager):
        """测试无效内存限制验证"""
        request = ExecutionRequest(
            code="print('hello')",
            language="python",
            resource_limits=ResourceLimits(memory_limit_mb=0)
        )
        
        with pytest.raises(ValueError, match="内存限制必须大于0|Memory limit must be greater than 0"):
            manager._validate_request(request)
    
    @pytest.mark.unit
    def test_validate_request_excessive_memory_limit(self, manager):
        """测试过大内存限制验证"""
        request = ExecutionRequest(
            code="print('hello')",
            language="python",
            resource_limits=ResourceLimits(memory_limit_mb=2048)  # 超过最大值
        )
        
        with pytest.raises(ValueError, match="内存限制过大|Memory limit too large"):
            manager._validate_request(request)
    
    @pytest.mark.unit
    def test_validate_request_excessive_timeout(self, manager):
        """测试过大超时时间验证"""
        request = ExecutionRequest(
            code="print('hello')",
            language="python",
            resource_limits=ResourceLimits(timeout_seconds=301)  # 超过最大值
        )
        
        with pytest.raises(ValueError, match="超时时间过长|Timeout too long"):
            manager._validate_request(request)
    
    @pytest.mark.unit
    def test_runtime_caching(self, manager):
        """测试运行时缓存"""
        # 多次获取同一语言的运行时应该返回同一个实例
        runtime1 = manager.get_runtime(Language.PYTHON)
        runtime2 = manager.get_runtime(Language.PYTHON)
        
        assert runtime1 is runtime2
    
    @pytest.mark.unit
    @patch('src.runtime.PythonRuntime.execute')
    def test_execute_with_custom_resource_limits(self, mock_execute, manager):
        """测试使用自定义资源限制执行"""
        mock_result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="Hello, World!",
            stderr="",
            execution_time=1.0,
            memory_used_mb=32.0,
            exit_code=0
        )
        mock_execute.return_value = mock_result
        
        custom_limits = ResourceLimits(
            timeout_seconds=60,
            memory_limit_mb=256,
            cpu_limit_percent=75,
            max_file_size_mb=20,
            max_output_size_mb=10
        )
        
        request = ExecutionRequest(
            code="print('Hello, World!')",
            language="python",
            resource_limits=custom_limits
        )
        
        result = manager.execute(request)
        
        assert result.status == ExecutionStatus.SUCCESS
        mock_execute.assert_called_once_with(request)
        
        # 验证传递的资源限制
        called_request = mock_execute.call_args[0][0]
        assert called_request.resource_limits.timeout_seconds == 60
        assert called_request.resource_limits.memory_limit_mb == 256
        assert called_request.resource_limits.cpu_limit_percent == 75
    
    @pytest.mark.unit
    @patch('src.runtime.PythonRuntime.execute')
    def test_execute_with_input_data(self, mock_execute, manager):
        """测试带输入数据的执行"""
        mock_result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="Hello, Alice!",
            stderr="",
            execution_time=1.0,
            memory_used_mb=64.0,
            exit_code=0
        )
        mock_execute.return_value = mock_result
        
        request = ExecutionRequest(
            code="name = input('Enter name: '); print(f'Hello, {name}!')",
            language="python",
            resource_limits=ResourceLimits(),
            input_data="Alice"
        )
        
        result = manager.execute(request)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.stdout == "Hello, Alice!"
        
        # 验证传递的输入数据
        called_request = mock_execute.call_args[0][0]
        assert called_request.input_data == "Alice"
    
    @pytest.mark.unit
    @patch('src.runtime.PythonRuntime.execute')
    def test_execute_with_environment_variables(self, mock_execute, manager):
        """测试带环境变量的执行"""
        mock_result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="test_value",
            stderr="",
            execution_time=1.0,
            memory_used_mb=64.0,
            exit_code=0
        )
        mock_execute.return_value = mock_result
        
        request = ExecutionRequest(
            code="import os; print(os.environ.get('TEST_VAR'))",
            language="python",
            resource_limits=ResourceLimits(),
            environment_variables={"TEST_VAR": "test_value"}
        )
        
        result = manager.execute(request)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.stdout == "test_value"
        
        # 验证传递的环境变量
        called_request = mock_execute.call_args[0][0]
        assert called_request.environment_variables["TEST_VAR"] == "test_value"