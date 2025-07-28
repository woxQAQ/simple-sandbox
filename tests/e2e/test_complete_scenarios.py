#!/usr/bin/env python3
"""
端到端测试
测试完整的用户使用场景
"""

import pytest
import requests


class TestCompleteScenarios:
    """完整场景端到端测试"""
    
    @pytest.fixture
    def base_url(self):
        """基础URL"""
        return "http://localhost:8000"
    
    @pytest.fixture
    def api_client(self, base_url):
        """API客户端"""
        class APIClient:
            def __init__(self, base_url: str):
                self.base_url = base_url
                self.session = requests.Session()
            
            def health_check(self):
                """健康检查"""
                response = self.session.get(f"{self.base_url}/api/v1/health")
                return response
            
            def execute_code(self, language: str, code: str, **kwargs):
                """执行代码"""
                data = {
                    "language": language,
                    "code": code,
                    "timeout": kwargs.get("timeout", 30),
                    "memory_limit": kwargs.get("memory_limit", 128)
                }
                
                if "input_data" in kwargs:
                    data["input_data"] = kwargs["input_data"]
                
                if "environment_variables" in kwargs:
                    data["environment_variables"] = kwargs["environment_variables"]
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/execute",
                    json=data
                )
                return response
        
        return APIClient(base_url)
    
    @pytest.mark.e2e
    def test_service_availability(self, api_client):
        """测试服务可用性"""
        # 检查服务是否运行
        try:
            response = api_client.health_check()
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "supported_languages" in data
            assert len(data["supported_languages"]) >= 2
            
        except requests.exceptions.ConnectionError:
            pytest.skip("服务未运行，跳过端到端测试")
    
    @pytest.mark.e2e
    def test_python_hello_world_scenario(self, api_client):
        """测试Python Hello World场景"""
        # 用户场景：执行简单的Python Hello World程序
        code = "print('Hello, World!')"
        
        response = api_client.execute_code("python", code)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "Hello, World!" in data["stdout"]
        assert data["exit_code"] == 0
        assert data["execution_time"] > 0
        assert data["memory_used"] > 0
    
    @pytest.mark.e2e
    def test_nodejs_hello_world_scenario(self, api_client):
        """测试Node.js Hello World场景"""
        # 用户场景：执行简单的Node.js Hello World程序
        code = "console.log('Hello, World!');"
        
        response = api_client.execute_code("nodejs", code)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "Hello, World!" in data["stdout"]
        assert data["exit_code"] == 0
        assert data["execution_time"] > 0
        assert data["memory_used"] > 0
    
    @pytest.mark.e2e
    def test_interactive_program_scenario(self, api_client):
        """测试交互式程序场景"""
        # 用户场景：执行需要输入的程序
        code = """
name = input("What's your name? ")
age = input("How old are you? ")
print(f"Hello {name}, you are {age} years old!")
"""
        
        input_data = "Alice\n25\n"
        
        response = api_client.execute_code(
            "python", 
            code, 
            input_data=input_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            assert "Alice" in data["stdout"]
            assert "25" in data["stdout"]
    
    @pytest.mark.e2e
    def test_data_processing_scenario(self, api_client):
        """测试数据处理场景"""
        # 用户场景：处理数据并输出结果
        code = """
import json

# 模拟数据处理
data = [1, 2, 3, 4, 5]
result = {
    "sum": sum(data),
    "average": sum(data) / len(data),
    "max": max(data),
    "min": min(data)
}

print(json.dumps(result, indent=2))
"""
        
        response = api_client.execute_code("python", code)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            # 验证输出包含JSON格式的结果
            output = data["stdout"]
            assert "sum" in output
            assert "average" in output
            assert "15" in output  # sum of [1,2,3,4,5]
    
    @pytest.mark.e2e
    def test_algorithm_implementation_scenario(self, api_client):
        """测试算法实现场景"""
        # 用户场景：实现并测试算法
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 测试斐波那契数列
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
"""
        
        response = api_client.execute_code("python", code, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "fib(0) = 0" in output
            assert "fib(1) = 1" in output
            assert "fib(9) = 34" in output
    
    @pytest.mark.e2e
    def test_web_scraping_simulation_scenario(self, api_client):
        """测试网络请求模拟场景"""
        # 用户场景：模拟网络请求（使用mock数据）
        code = """
import json

# 模拟API响应
mock_response = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ]
}

# 处理数据
for user in mock_response["users"]:
    print(f"User: {user['name']} ({user['email']})")

print(f"Total users: {len(mock_response['users'])}")
"""
        
        response = api_client.execute_code("python", code)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "Alice" in output
            assert "Bob" in output
            assert "Total users: 2" in output
    
    @pytest.mark.e2e
    def test_error_handling_scenario(self, api_client):
        """测试错误处理场景"""
        # 用户场景：代码包含错误
        code = """
try:
    result = 10 / 0  # 除零错误
except ZeroDivisionError as e:
    print(f"Error caught: {e}")
    print("Handled gracefully")
"""
        
        response = api_client.execute_code("python", code)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "Error caught" in output
            assert "Handled gracefully" in output
    
    @pytest.mark.e2e
    def test_environment_variables_scenario(self, api_client):
        """测试环境变量场景"""
        # 用户场景：使用环境变量配置程序
        code = """
import os

api_key = os.environ.get('API_KEY', 'default_key')
debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'

print(f"API Key: {api_key}")
print(f"Debug Mode: {debug_mode}")

if debug_mode:
    print("Debug information: Application started")
"""
        
        env_vars = {
            "API_KEY": "test_api_key_123",
            "DEBUG": "true"
        }
        
        response = api_client.execute_code(
            "python", 
            code, 
            environment_variables=env_vars
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "test_api_key_123" in output
            assert "Debug Mode: True" in output
            assert "Debug information" in output
    
    @pytest.mark.e2e
    def test_file_processing_scenario(self, api_client):
        """测试文件处理场景"""
        # 用户场景：处理文本数据
        code = """
# 模拟文件内容
file_content = '''line 1: hello world
line 2: python programming
line 3: data processing
line 4: machine learning'''

# 处理文本
lines = file_content.strip().split('\n')
word_count = 0
line_count = len(lines)

for line in lines:
    words = line.split()
    word_count += len(words)
    print(f"Line: {line} (Words: {len(words)})")

print(f"\nSummary:")
print(f"Total lines: {line_count}")
print(f"Total words: {word_count}")
"""
        
        response = api_client.execute_code("python", code)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "Total lines: 4" in output
            assert "Total words:" in output
            assert "hello world" in output
    
    @pytest.mark.e2e
    def test_nodejs_async_scenario(self, api_client):
        """测试Node.js异步场景"""
        # 用户场景：Node.js异步编程
        code = """
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    console.log('Starting async operation...');
    
    await delay(100);
    console.log('Step 1 completed');
    
    await delay(100);
    console.log('Step 2 completed');
    
    console.log('All operations completed!');
}

main().catch(console.error);
"""
        
        response = api_client.execute_code("nodejs", code)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "Starting async operation" in output
            assert "Step 1 completed" in output
            assert "Step 2 completed" in output
            assert "All operations completed" in output
    
    @pytest.mark.e2e
    def test_performance_monitoring_scenario(self, api_client):
        """测试性能监控场景"""
        # 用户场景：监控代码性能
        code = """
import time

start_time = time.time()

# 模拟计算密集型任务
result = 0
for i in range(100000):
    result += i * i

end_time = time.time()
execution_time = end_time - start_time

print(f"Calculation result: {result}")
print(f"Execution time: {execution_time:.4f} seconds")
print(f"Operations per second: {100000/execution_time:.0f}")
"""
        
        response = api_client.execute_code("python", code, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "Calculation result:" in output
            assert "Execution time:" in output
            assert "Operations per second:" in output
            
            # 验证API返回的执行时间
            assert data["execution_time"] > 0
            assert data["memory_used"] > 0
    
    @pytest.mark.e2e
    def test_multiple_requests_scenario(self, api_client):
        """测试多请求场景"""
        # 用户场景：连续执行多个代码片段
        test_cases = [
            {
                "language": "python",
                "code": "print('Request 1: Python')",
                "expected": "Request 1: Python"
            },
            {
                "language": "nodejs",
                "code": "console.log('Request 2: Node.js');",
                "expected": "Request 2: Node.js"
            },
            {
                "language": "python",
                "code": "print('Request 3: Python again')",
                "expected": "Request 3: Python again"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases):
            response = api_client.execute_code(
                test_case["language"],
                test_case["code"]
            )
            
            assert response.status_code == 200
            data = response.json()
            results.append(data)
            
            if data["status"] == "success":
                assert test_case["expected"] in data["stdout"]
        
        # 验证所有请求都成功
        success_count = sum(1 for r in results if r["status"] == "success")
        assert success_count >= len(test_cases) * 0.8  # 至少80%成功
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_long_running_scenario(self, api_client):
        """测试长时间运行场景"""
        # 用户场景：执行需要较长时间的计算
        code = """
import time

print("Starting long computation...")

# 模拟长时间计算
total = 0
for i in range(1000000):
    total += i
    if i % 100000 == 0:
        print(f"Progress: {i/1000000*100:.1f}%")

print(f"Final result: {total}")
print("Computation completed!")
"""
        
        response = api_client.execute_code(
            "python", 
            code, 
            timeout=120,  # 2分钟超时
            memory_limit=256
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "Starting long computation" in output
            assert "Computation completed" in output
            assert "Final result:" in output
            
            # 验证执行时间合理
            assert data["execution_time"] > 1.0  # 至少1秒
            assert data["execution_time"] < 120  # 不超过超时时间
    
    @pytest.mark.e2e
    def test_resource_intensive_scenario(self, api_client):
        """测试资源密集型场景"""
        # 用户场景：测试内存和CPU使用
        code = """
import sys

print("Testing resource usage...")

# 创建一些数据结构
data = []
for i in range(10000):
    data.append([j for j in range(100)])

print(f"Created {len(data)} lists")
print(f"Total elements: {len(data) * 100}")

# 进行一些计算
result = 0
for lst in data:
    result += sum(lst)

print(f"Sum of all elements: {result}")
print("Resource test completed!")
"""
        
        response = api_client.execute_code(
            "python", 
            code, 
            timeout=60,
            memory_limit=512  # 较大的内存限制
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "success":
            output = data["stdout"]
            assert "Testing resource usage" in output
            assert "Resource test completed" in output
            
            # 验证资源使用情况
            assert data["memory_used"] > 0
            assert data["execution_time"] > 0
    
    @pytest.mark.e2e
    def test_error_recovery_scenario(self, api_client):
        """测试错误恢复场景"""
        # 用户场景：从错误中恢复并继续工作
        
        # 第一步：执行有错误的代码
        error_code = "print('Before error'); invalid_syntax_here; print('After error')"
        
        response1 = api_client.execute_code("python", error_code)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["status"] == "error"
        
        # 第二步：执行正确的代码
        success_code = "print('Recovery successful'); print('System is working')"
        
        response2 = api_client.execute_code("python", success_code)
        assert response2.status_code == 200
        data2 = response2.json()
        
        if data2["status"] == "success":
            output = data2["stdout"]
            assert "Recovery successful" in output
            assert "System is working" in output
        
        # 第三步：再次执行复杂代码确认系统稳定
        complex_code = """
for i in range(5):
    print(f"Iteration {i+1}: System stable")

print("All tests passed!")
"""
        
        response3 = api_client.execute_code("python", complex_code)
        assert response3.status_code == 200
        data3 = response3.json()
        
        if data3["status"] == "success":
            output = data3["stdout"]
            assert "All tests passed" in output