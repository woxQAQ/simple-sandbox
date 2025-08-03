"""
Node.js扩展运行时测试
测试Node.js AST管理器和相关功能（已移除transformer功能）
"""

from src.runtime.nodejs.extensions import NodeJSASTManager


class TestNodeJSASTManager:
    """Node.js AST管理器测试"""

    def test_manager_creation(self):
        """测试管理器创建"""
        manager = NodeJSASTManager()
        assert manager is not None

    def test_transform_code_no_transformation(self):
        """测试代码转换（直接返回原始代码）"""
        manager = NodeJSASTManager()
        code = "console.log('Hello World');"
        result = manager.transform_code(code)
        assert result == code

    def test_transform_code_with_context(self):
        """测试带上下文的代码转换"""
        manager = NodeJSASTManager()
        code = "console.log('Hello World');"
        context = {"language": "nodejs"}
        result = manager.transform_code(code, context)
        assert result == code

    def test_transform_code_empty_context(self):
        """测试空上下文的代码转换"""
        manager = NodeJSASTManager()
        code = "console.log('Hello World');"
        result = manager.transform_code(code, None)
        assert result == code

    def test_transform_code_complex_code(self):
        """测试复杂代码转换"""
        manager = NodeJSASTManager()
        code = """
        function factorial(n) {
            if (n <= 1) return 1;
            return n * factorial(n - 1);
        }
        console.log(factorial(5));
        """
        result = manager.transform_code(code)
        assert result == code

    def test_transform_code_with_special_characters(self):
        """测试包含特殊字符的代码转换"""
        manager = NodeJSASTManager()
        code = "console.log('Hello\\nWorld\\t!');"
        result = manager.transform_code(code)
        assert result == code

    def test_transform_code_empty_string(self):
        """测试空字符串转换"""
        manager = NodeJSASTManager()
        code = ""
        result = manager.transform_code(code)
        assert result == code

    def test_transform_code_with_comments(self):
        """测试包含注释的代码转换"""
        manager = NodeJSASTManager()
        code = """
        // 这是一个注释
        console.log('Hello'); /* 另一个注释 */
        """
        result = manager.transform_code(code)
        assert result == code