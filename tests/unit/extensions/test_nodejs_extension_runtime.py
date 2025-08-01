"""
Node.js扩展运行时测试
测试Node.js AST管理器和相关功能
"""

import subprocess
from unittest.mock import Mock, patch

from src.runtime.nodejs.extensions import (
    NodeASTPlugin,
    NodeJSASTManager,
)


class TestNodeASTPlugin:
    """Node.js AST插件基类测试"""

    def test_plugin_creation(self):
        """测试插件创建"""
        plugin = NodeASTPlugin("test_plugin")
        assert plugin.name == "test_plugin"
        assert plugin.priority == 100

    def test_plugin_with_custom_priority(self):
        """测试自定义优先级"""
        plugin = NodeASTPlugin("test_plugin", priority=50)
        assert plugin.priority == 50

    def test_plugin_with_different_name(self):
        """测试不同名称"""
        plugin = NodeASTPlugin("another_plugin")
        assert plugin.name == "another_plugin"


class TestNodeJSASTManager:
    """Node.js AST管理器测试"""

    def test_manager_creation(self):
        """测试管理器创建"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            manager = NodeJSASTManager()
            assert manager.js_transformer_path == "/fake/path/transformer.js"

    def test_transform_code_success(self):
        """测试代码转换成功"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = (
                    '{"success": true, "transformed": "transformed_code"}'
                )
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "original_code", {"key": "value"}
                )

                assert result == "transformed_code"
                mock_run.assert_called_once()

    def test_transform_code_failure(self):
        """测试代码转换失败"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 1
                mock_result.stderr = "Error message"
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "original_code", {"key": "value"}
                )

                # 转换失败时应该返回原代码
                assert result == "original_code"

    def test_transform_code_timeout(self):
        """测试代码转换超时"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("node", 10)

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "original_code", {"key": "value"}
                )

                # 超时时应该返回原代码
                assert result == "original_code"

    def test_transform_code_file_not_found(self):
        """测试Node.js未找到"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError()

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "original_code", {"key": "value"}
                )

                # Node.js未找到时应该返回原代码
                assert result == "original_code"

    def test_transform_code_invalid_json(self):
        """测试无效JSON响应"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "invalid json"
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "original_code", {"key": "value"}
                )

                # 无效JSON时应该返回原代码
                assert result == "original_code"

    def test_transform_code_missing_success_field(self):
        """测试缺少success字段"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = '{"transformed": "transformed_code"}'
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "original_code", {"key": "value"}
                )

                # 缺少success字段时应该返回原代码
                assert result == "original_code"

    def test_transform_code_success_false(self):
        """测试success为false"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = '{"success": false, "error": "Some error"}'
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "original_code", {"key": "value"}
                )

                # success为false时应该返回原代码
                assert result == "original_code"

    def test_transform_code_empty_context(self):
        """测试空上下文"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = (
                    '{"success": true, "transformed": "transformed_code"}'
                )
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                result = manager.transform_code("original_code", {})

                assert result == "transformed_code"

    def test_transform_code_complex_context(self):
        """测试复杂上下文"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = (
                    '{"success": true, "transformed": "transformed_code"}'
                )
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                context = {
                    "filename": "test.js",
                    "user_id": "test_user",
                    "metadata": {"key": "value"},
                }
                result = manager.transform_code("original_code", context)

                assert result == "transformed_code"

    def test_transform_code_special_characters(self):
        """测试特殊字符"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = (
                    '{"success": true, "transformed": "transformed_code"}'
                )
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "console.log('hello\\nworld')", {}
                )

                assert result == "transformed_code"

    def test_subprocess_called_with_correct_args(self):
        """测试subprocess调用参数"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = '{"success": true, "transformed": "test"}'
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                manager.transform_code("test", {})

                # 验证调用参数
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                assert "node" in call_args[0][0]
                assert "/fake/path/transformer.js" in call_args[0][0]
                assert "timeout" in call_args[1]
