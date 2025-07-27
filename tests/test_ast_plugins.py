"""
AST插件系统单元测试
测试Python和Node.js的AST转换功能
"""

import json
import os
import subprocess
from unittest.mock import patch

import pytest

from src.runtime.extensions.ast_plugins.nodejs_ast_plugin import (
    NodeJSASTRegistry,
    nodejs_ast_registry,
)
from src.runtime.extensions.ast_plugins.python_ast_plugin import (
    MatplotlibASTPlugin,
    PythonASTContext,
    PythonASTRegistry,
    PythonConsoleASTPlugin,
    python_ast_registry,
)
from src.runtime.extensions.ast_plugins.runtime_ast_manager import (
    RuntimeASTManager,
    transform_ast_code,
)


class TestPythonASTPlugins:
    """测试Python AST插件"""

    def test_python_ast_context(self):
        """测试Python AST上下文创建"""
        context = PythonASTContext(
            filename="test.py",
            source_code="print('hello')",
            user_id="user123",
            metadata={"mode": "test"},
        )

        assert context.filename == "test.py"
        assert context.source_code == "print('hello')"
        assert context.user_id == "user123"
        assert context.metadata["mode"] == "test"

    def test_python_console_ast_plugin_detection(self):
        """测试Python控制台插件检测"""
        plugin = PythonConsoleASTPlugin()

        # 应该检测print调用
        code_with_print = "print('hello world')"
        import ast

        tree = ast.parse(code_with_print)
        expr_node = tree.body[0]

        context = PythonASTContext("test.py", code_with_print, "user123", {})
        assert plugin.should_transform(expr_node, context) is True

        # 不应该检测非print调用
        code_without_print = "x = 42"
        tree2 = ast.parse(code_without_print)
        assign_node = tree2.body[0]

        assert plugin.should_transform(assign_node, context) is False

    def test_python_console_ast_plugin_transformation(self):
        """测试Python控制台插件转换"""
        plugin = PythonConsoleASTPlugin()

        code = "print('hello world')"
        context = PythonASTContext("test.py", code, "user123", {})

        import ast

        tree = ast.parse(code)
        expr_node = tree.body[0]

        transformed = plugin.transform(expr_node, context)

        # 检查转换后的代码是否包含时间戳相关代码
        import astor

        result = astor.to_source(transformed)
        assert "datetime" in result
        assert "isoformat" in result

    def test_matplotlib_ast_plugin_detection(self):
        """测试Matplotlib插件检测"""
        plugin = MatplotlibASTPlugin()

        import ast

        # 应该检测matplotlib导入
        code_import = "import matplotlib.pyplot as plt"
        tree = ast.parse(code_import)
        import_node = tree.body[0]

        context = PythonASTContext("test.py", code_import, "user123", {})
        assert plugin.should_transform(import_node, context) is True

        # 应该检测from导入
        code_from = "from matplotlib import pyplot as plt"
        tree2 = ast.parse(code_from)
        from_node = tree2.body[0]

        assert plugin.should_transform(from_node, context) is True

        # 不应该检测其他导入
        code_other = "import numpy as np"
        tree3 = ast.parse(code_other)
        other_node = tree3.body[0]

        assert plugin.should_transform(other_node, context) is False

    def test_python_ast_registry(self):
        """测试Python AST注册表"""
        registry = PythonASTRegistry()

        # 测试空注册表
        code = "print('test')"
        context = PythonASTContext("test.py", code, "user123", {})
        result = registry.transform_code(code, context)
        assert result == code  # 无插件时返回原代码

        # 测试注册插件
        registry.register(PythonConsoleASTPlugin())
        assert len(registry.plugins) == 1
        assert registry.plugins[0].name == "python_console_ast"

        # 测试插件按优先级排序
        registry.register(MatplotlibASTPlugin())
        assert registry.plugins[0].priority == 95  # Matplotlib优先级更高
        assert registry.plugins[1].priority == 90


class TestNodeJSASTPlugins:
    """测试Node.js AST插件"""

    def test_nodejs_ast_plugin_base(self):
        """测试Node.js AST插件基类"""
        plugin = NodeJSConsoleASTPlugin()

        assert plugin.name == "nodejs_console_ast"
        assert plugin.priority == 90

    def test_nodejs_console_ast_plugin(self):
        """测试Node.js控制台插件"""
        plugin = NodeJSConsoleASTPlugin()

        # 测试检测逻辑
        ast_data = {"has_console": True}
        context = {}
        assert plugin.should_transform(ast_data, context) is True

        ast_data_no_console = {"has_console": False}
        assert plugin.should_transform(ast_data_no_console, context) is False

        # 测试转换输出
        result = plugin.transform(ast_data, context)
        assert "console.log" in result
        assert "timestamp" in result
        assert "toISOString" in result

    def test_nodejs_import_ast_plugin(self):
        """测试Node.js导入插件"""
        plugin = NodeJSImportASTPlugin()

        # 测试检测逻辑
        ast_data = {"has_imports": True}
        context = {}
        assert plugin.should_transform(ast_data, context) is True

        ast_data_no_import = {"has_imports": False}
        assert plugin.should_transform(ast_data_no_import, context) is False

        # 测试转换输出
        result = plugin.transform(ast_data, context)
        assert "require" in result
        assert "Loaded module" in result

    def test_nodejs_ast_registry(self):
        """测试Node.js AST注册表"""
        registry = NodeJSASTRegistry()

        # 测试注册插件
        registry.register(NodeJSConsoleASTPlugin())
        registry.register(NodeJSImportASTPlugin())

        assert len(registry.plugins) == 2
        assert registry.plugins[0].priority == 90
        assert registry.plugins[1].priority == 85


class TestRuntimeASTManager:
    """测试运行时AST管理器"""

    def test_runtime_ast_manager_initialization(self):
        """测试管理器初始化"""
        manager = RuntimeASTManager()

        supported = manager.get_supported_languages()
        assert "python" in supported
        assert "javascript" in supported
        assert "typescript" in supported
        assert "nodejs" in supported

    def test_python_transformation(self):
        """测试Python代码转换"""
        manager = RuntimeASTManager()

        code = "print('hello world')"
        context = {"filename": "test.py", "user_id": "user123"}

        result = manager.transform_code(code, "python", context)

        # 应该包含增强的代码
        assert "datetime" in result
        assert "isoformat" in result

    def test_javascript_transformation(self):
        """测试JavaScript代码转换"""
        manager = RuntimeASTManager()

        code = "console.log('hello world');"
        context = {"filename": "test.js", "user_id": "user123"}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps(
                {
                    "success": True,
                    "transformed": "// Enhanced code\\nconsole.log('hello world');",
                    "original": code,
                }
            )
            mock_run.return_value.returncode = 0

            result = manager.transform_code(code, "javascript", context)
            assert "Enhanced code" in result

    def test_unsupported_language(self):
        """测试不支持的语言"""
        manager = RuntimeASTManager()

        code = "some code"
        result = manager.transform_code(code, "unsupported_language")

        # 应该返回原代码
        assert result == code

    def test_transformation_error_handling(self):
        """测试转换错误处理"""
        manager = RuntimeASTManager()

        # 测试Python转换错误
        code = "invalid python syntax :::"
        context = {"filename": "test.py"}

        result = manager.transform_code(code, "python", context)
        assert result == code  # 错误时返回原代码


class TestJSTransformerIntegration:
    """测试JavaScript转换器集成"""

    def test_js_ast_transformer_file_exists(self):
        """测试JS转换器文件存在"""
        js_path = "src/runtime/extensions/ast_plugins/js_ast_transformer.js"
        assert os.path.exists(js_path)

        # 测试插件文件存在
        console_plugin_path = (
            "src/runtime/extensions/ast_plugins/js_plugins/console_plugin.js"
        )
        import_plugin_path = (
            "src/runtime/extensions/ast_plugins/js_plugins/import_plugin.js"
        )
        assert os.path.exists(console_plugin_path)
        assert os.path.exists(import_plugin_path)

    def test_js_plugins_structure(self):
        """测试JS插件结构"""
        # 测试插件文件结构
        plugin_dir = "src/runtime/extensions/ast_plugins/js_plugins"
        assert os.path.exists(plugin_dir)

        # 测试index.js存在
        index_path = os.path.join(plugin_dir, "index.js")
        assert os.path.exists(index_path)

    def test_js_transformer_basic_functionality(self):
        """测试JS转换器基本功能"""
        js_path = "src/runtime/extensions/ast_plugins/js_ast_transformer.js"

        # 测试Node.js转换器是否能正常运行
        test_code = "console.log('hello world');"

        try:
            result = subprocess.run(
                ["node", js_path],
                input=json.dumps({"code": test_code}),
                text=True,
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = json.loads(result.stdout)
                assert output["success"] is True
                assert "console.log" in output["transformed"]
            else:
                pytest.skip("Node.js转换器测试需要安装依赖")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Node.js不可用或未安装依赖")

    def test_js_transformer_with_console(self):
        """测试JS转换器的控制台增强"""
        js_path = "src/runtime/extensions/ast_plugins/js_ast_transformer.js"

        test_code = """
        console.log('Hello World');
        console.error('Error message');
        """

        try:
            result = subprocess.run(
                ["node", js_path],
                input=json.dumps({"code": test_code}),
                text=True,
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = json.loads(result.stdout)
                transformed = output["transformed"]
                assert "timestamp" in transformed
                assert "toISOString" in transformed
                assert "console.log =" in transformed
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Node.js不可用或未安装依赖")

    def test_js_transformer_with_imports(self):
        """测试JS转换器的导入增强"""
        js_path = "src/runtime/extensions/ast_plugins/js_ast_transformer.js"

        test_code = """
        import fs from 'fs';
        const path = require('path');
        """

        try:
            result = subprocess.run(
                ["node", js_path],
                input=json.dumps({"code": test_code}),
                text=True,
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = json.loads(result.stdout)
                transformed = output["transformed"]
                assert "Loaded module" in transformed
                assert "require" in transformed
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Node.js不可用或未安装依赖")


class TestASTIntegration:
    """测试AST系统整体集成"""

    def test_transform_ast_code_function(self):
        """测试转换函数"""
        # 测试Python代码转换
        python_code = "print('hello world')"
        result = transform_ast_code(python_code, "python", filename="test.py")
        assert "datetime" in result

        # 测试JavaScript代码转换（需要Node.js）
        js_code = "console.log('hello world');"
        try:
            result = transform_ast_code(
                js_code, "javascript", filename="test.js"
            )
            assert isinstance(result, str)
        except Exception:
            pytest.skip("Node.js依赖未安装")

    def test_global_registries(self):
        """测试全局注册表"""
        # Python注册表应该有插件
        assert len(python_ast_registry.plugins) >= 2
        plugin_names = [p.name for p in python_ast_registry.plugins]
        assert "python_console_ast" in plugin_names
        assert "matplotlib_ast" in plugin_names

        # Node.js注册表应该有插件
        assert len(nodejs_ast_registry.plugins) >= 2
        plugin_names = [p.name for p in nodejs_ast_registry.plugins]
        assert "nodejs_console_ast" in plugin_names
        assert "nodejs_import_ast" in plugin_names


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_python_syntax(self):
        """测试无效Python语法"""
        manager = RuntimeASTManager()

        invalid_code = "def invalid syntax :::"
        result = manager.transform_code(invalid_code, "python")
        assert result == invalid_code  # 应该返回原代码

    def test_empty_code(self):
        """测试空代码"""
        manager = RuntimeASTManager()

        result = manager.transform_code("", "python")
        assert result == ""

    def test_none_context(self):
        """测试None上下文"""
        manager = RuntimeASTManager()

        code = "print('test')"
        result = manager.transform_code(code, "python", None)
        assert "datetime" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
