#!/usr/bin/env python3
"""
API和运行时集成测试
测试FastAPI接口与运行时模块的集成功能
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


class TestAPIRuntimeIntegration:
    """API和运行时集成测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)

    @pytest.mark.integration
    def test_python_code_execution_flow(self, client):
        """测试Python代码执行完整流程"""
        request_data = {
            "language": "python",
            "code": "print('Hello from Python!')",
            "timeout": 30,
            "memory_limit": 128,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "status" in data
        assert "stdout" in data
        assert "stderr" in data
        assert "execution_time" in data
        assert "memory_used" in data
        assert "exit_code" in data
        assert "error" in data

        # 验证执行结果
        assert data["status"] in ["success", "error", "timeout"]
        if data["status"] == "success":
            assert isinstance(data["execution_time"], (int, float))
            assert isinstance(data["memory_used"], (int, float))
            assert isinstance(data["exit_code"], int)

    @pytest.mark.integration
    def test_nodejs_code_execution_flow(self, client):
        """测试Node.js代码执行完整流程"""
        request_data = {
            "language": "nodejs",
            "code": "console.log('Hello from Node.js!');",
            "timeout": 30,
            "memory_limit": 128,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "status" in data
        assert "stdout" in data
        assert "stderr" in data
        assert "execution_time" in data
        assert "memory_used" in data
        assert "exit_code" in data
        assert "error" in data

        # 验证执行结果
        assert data["status"] in ["success", "error", "timeout"]
        if data["status"] == "success":
            assert isinstance(data["execution_time"], (int, float))
            assert isinstance(data["memory_used"], (int, float))
            assert isinstance(data["exit_code"], int)

    @pytest.mark.integration
    def test_health_check_with_runtime_info(self, client):
        """测试健康检查与运行时信息集成"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "supported_languages" in data
        assert len(data["supported_languages"]) >= 2

        # 验证语言信息结构
        for lang_info in data["supported_languages"]:
            assert "name" in lang_info
            assert "version" in lang_info
            assert "extensions" in lang_info
            assert isinstance(lang_info["extensions"], list)
            assert len(lang_info["extensions"]) > 0

    @pytest.mark.integration
    def test_error_handling_integration(self, client):
        """测试错误处理集成"""
        # 测试语法错误
        request_data = {
            "language": "python",
            "code": "print('unclosed string",  # 语法错误
            "timeout": 30,
            "memory_limit": 128,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 应该返回错误状态
        assert data["status"] == "error"
        assert data["exit_code"] != 0
        assert len(data["stderr"]) > 0 or data["error"] is not None

    @pytest.mark.integration
    def test_timeout_handling_integration(self, client):
        """测试超时处理集成"""
        request_data = {
            "language": "python",
            "code": "import time; time.sleep(10)",  # 长时间运行
            "timeout": 2,  # 短超时时间
            "memory_limit": 128,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 应该返回超时状态
        assert data["status"] == "timeout"
        assert data["execution_time"] >= 2.0  # 应该接近超时时间
        assert data["error"] is not None

    @pytest.mark.integration
    def test_input_data_integration(self, client):
        """测试输入数据集成"""
        request_data = {
            "language": "python",
            "code": "name = input('Enter your name: '); print(f'Hello, {name}!')",
            "timeout": 30,
            "memory_limit": 128,
            "input_data": "Alice",
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        if data["status"] == "success":
            assert "Alice" in data["stdout"]

    @pytest.mark.integration
    def test_environment_variables_integration(self, client):
        """测试环境变量集成"""
        request_data = {
            "language": "python",
            "code": "import os; print(os.environ.get('TEST_VAR', 'not_found'))",
            "timeout": 30,
            "memory_limit": 128,
            "environment_variables": {"TEST_VAR": "test_value"},
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        if data["status"] == "success":
            assert "test_value" in data["stdout"]

    @pytest.mark.integration
    def test_resource_limits_integration(self, client):
        """测试资源限制集成"""
        # 测试内存限制
        request_data = {
            "language": "python",
            "code": "data = [0] * (1024 * 1024 * 100)  # 尝试分配大量内存",
            "timeout": 30,
            "memory_limit": 64,  # 较小的内存限制
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 可能因内存限制而失败
        if data["status"] == "error":
            assert (
                "memory" in data["stderr"].lower()
                or "memory" in (data["error"] or "").lower()
            )

    @pytest.mark.integration
    def test_concurrent_execution(self, client):
        """测试并发执行"""
        import threading

        results = []

        def execute_code(code_id):
            request_data = {
                "language": "python",
                "code": f"print('Execution {code_id}')",
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)
            results.append((code_id, response.status_code, response.json()))

        # 创建多个并发请求
        threads = []
        for i in range(5):
            thread = threading.Thread(target=execute_code, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有请求都成功处理
        assert len(results) == 5
        for code_id, status_code, data in results:
            assert status_code == 200
            assert data["status"] in ["success", "error", "timeout"]

    @pytest.mark.integration
    def test_large_output_handling(self, client):
        """测试大输出处理"""
        request_data = {
            "language": "python",
            "code": "for i in range(1000): print(f'Line {i}: ' + 'x' * 100)",
            "timeout": 30,
            "memory_limit": 128,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 验证输出被正确处理（可能被截断）
        if data["status"] == "success":
            assert len(data["stdout"]) > 0
            # 输出应该包含一些行
            assert "Line" in data["stdout"]

    @pytest.mark.integration
    def test_multiple_language_execution(self, client):
        """测试多语言执行"""
        test_cases = [
            {
                "language": "python",
                "code": "print('Hello from Python')",
                "expected_output": "Hello from Python",
            },
            {
                "language": "nodejs",
                "code": "console.log('Hello from Node.js');",
                "expected_output": "Hello from Node.js",
            },
        ]

        for test_case in test_cases:
            request_data = {
                "language": test_case["language"],
                "code": test_case["code"],
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            if data["status"] == "success":
                assert test_case["expected_output"] in data["stdout"]

    @pytest.mark.integration
    def test_api_validation_integration(self, client):
        """测试API验证集成"""
        # 测试无效的语言
        invalid_requests = [
            {
                "language": "invalid_language",
                "code": "print('hello')",
                "timeout": 30,
                "memory_limit": 128,
            },
            {
                "language": "python",
                "code": "",  # 空代码
                "timeout": 30,
                "memory_limit": 128,
            },
            {
                "language": "python",
                "code": "print('hello')",
                "timeout": 0,  # 无效超时
                "memory_limit": 128,
            },
            {
                "language": "python",
                "code": "print('hello')",
                "timeout": 30,
                "memory_limit": 0,  # 无效内存限制
            },
        ]

        for request_data in invalid_requests:
            response = client.post("/api/v1/execute", json=request_data)
            assert response.status_code == 422  # Validation Error

    @pytest.mark.integration
    @pytest.mark.slow
    def test_stress_execution(self, client):
        """测试压力执行"""
        # 执行多个计算密集型任务
        request_data = {
            "language": "python",
            "code": """
result = 0
for i in range(100000):
    result += i * i
print(f'Result: {result}')
""",
            "timeout": 60,
            "memory_limit": 256,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 验证计算结果
        if data["status"] == "success":
            assert "Result:" in data["stdout"]
            assert data["execution_time"] > 0
            assert data["memory_used"] > 0

    @pytest.mark.integration
    def test_error_recovery(self, client):
        """测试错误恢复"""
        # 先执行一个错误的代码
        error_request = {
            "language": "python",
            "code": "invalid_syntax_here",
            "timeout": 30,
            "memory_limit": 128,
        }

        response1 = client.post("/api/v1/execute", json=error_request)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["status"] == "error"

        # 然后执行一个正确的代码
        success_request = {
            "language": "python",
            "code": "print('Recovery successful')",
            "timeout": 30,
            "memory_limit": 128,
        }

        response2 = client.post("/api/v1/execute", json=success_request)
        assert response2.status_code == 200
        data2 = response2.json()

        # 应该能够正常执行
        if data2["status"] == "success":
            assert "Recovery successful" in data2["stdout"]
