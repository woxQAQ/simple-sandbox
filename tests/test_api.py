from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


class TestAPI:
    """测试API端点"""

    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "supported_languages" in data
        assert len(data["supported_languages"]) >= 2

    def test_get_languages(self):
        """测试获取支持的语言列表"""
        response = client.get("/api/v1/languages")
        assert response.status_code == 200

        data = response.json()
        assert "languages" in data
        languages = data["languages"]
        assert len(languages) >= 2

        # 检查Python
        python_lang = next(
            (lang for lang in languages if lang["name"] == "python"), None
        )
        assert python_lang is not None
        assert ".py" in python_lang["extensions"]

        # 检查Node.js
        node_lang = next(
            (lang for lang in languages if lang["name"] == "nodejs"), None
        )
        assert node_lang is not None
        assert ".js" in node_lang["extensions"]

    def test_execute_python_success(self):
        """测试Python代码执行成功"""
        payload = {
            "language": "python",
            "code": "print('Hello from Python!')",
            "timeout": 5,
            "memory_limit": 64,
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "Hello from Python!" in data["stdout"]
        assert data["stderr"] == ""
        assert data["execution_time"] > 0

    def test_execute_nodejs_success(self):
        """测试Node.js代码执行成功"""
        payload = {
            "language": "nodejs",
            "code": "console.log('Hello from Node.js!');",
            "timeout": 5,
            "memory_limit": 64,
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "Hello from Node.js!" in data["stdout"]
        assert data["stderr"] == ""
        assert data["execution_time"] > 0

    def test_execute_invalid_language(self):
        """测试无效语言"""
        payload = {
            "language": "invalid",
            "code": "print('test')",
            "timeout": 5,
            "memory_limit": 64,
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 400
        assert "Unsupported language" in response.json()["detail"]

    def test_execute_python_syntax_error(self):
        """测试Python语法错误"""
        payload = {
            "language": "python",
            "code": "print('Hello'  # 缺少右括号",
            "timeout": 5,
            "memory_limit": 64,
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "error"
        assert (
            "SyntaxError" in data["stderr"] or "syntax error" in data["stderr"]
        )

    def test_execute_timeout(self):
        """测试超时处理"""
        payload = {
            "language": "python",
            "code": "import time\ntime.sleep(5)\nprint('timeout')",
            "timeout": 1,
            "memory_limit": 64,
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "timeout"

    def test_execute_with_input(self):
        """测试带输入的执行"""
        payload = {
            "language": "python",
            "code": "name = input('Name: ')\nprint(f'Hello, {name}!')",
            "timeout": 5,
            "memory_limit": 64,
            "input_data": "Alice",
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "Hello, Alice!" in data["stdout"]

    def test_execute_with_environment_variables(self):
        """测试带环境变量的执行"""
        payload = {
            "language": "python",
            "code": 'import os\nprint(f\'TEST_VAR: {os.getenv("TEST_VAR", "not found")}\')',
            "timeout": 5,
            "memory_limit": 64,
            "environment_variables": {"TEST_VAR": "test_value"},
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "TEST_VAR: test_value" in data["stdout"]

    def test_execute_large_code(self):
        """测试大代码处理"""
        large_code = "print('Hello')\n" * 1000
        payload = {
            "language": "python",
            "code": large_code,
            "timeout": 5,
            "memory_limit": 64,
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_execute_oversized_code(self):
        """测试超大代码处理"""
        oversized_code = "a" * (1024 * 1024 + 1)  # 超过1MB
        payload = {
            "language": "python",
            "code": oversized_code,
            "timeout": 5,
            "memory_limit": 64,
        }

        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 413
        assert "Code size exceeds" in response.json()["detail"]

    def test_invalid_json(self):
        """测试无效JSON"""
        response = client.post(
            "/api/v1/execute",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields(self):
        """测试缺少必填字段"""
        payload = {"language": "python"}  # 缺少code字段
        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 422

    def test_invalid_timeout(self):
        """测试无效的超时时间"""
        payload = {
            "language": "python",
            "code": "print('test')",
            "timeout": 0,  # 无效值
            "memory_limit": 64,
        }
        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 422

    def test_invalid_memory_limit(self):
        """测试无效的内存限制"""
        payload = {
            "language": "python",
            "code": "print('test')",
            "timeout": 5,
            "memory_limit": 8,  # 无效值
        }
        response = client.post("/api/v1/execute", json=payload)
        assert response.status_code == 422
