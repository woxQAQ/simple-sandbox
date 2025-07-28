#!/usr/bin/env python3
"""
性能测试
测试系统的性能表现和资源使用情况
"""

import pytest
import time
import statistics
import concurrent.futures
from fastapi.testclient import TestClient
from typing import Dict, Any

from src.api.app import app


class TestPerformance:
    """性能测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    def execute_code_with_timing(self, client, language: str, code: str, **kwargs) -> Dict[str, Any]:
        """执行代码并记录时间"""
        start_time = time.time()
        
        request_data = {
            "language": language,
            "code": code,
            "timeout": kwargs.get("timeout", 30),
            "memory_limit": kwargs.get("memory_limit", 128)
        }
        
        if "input_data" in kwargs:
            request_data["input_data"] = kwargs["input_data"]
        
        if "environment_variables" in kwargs:
            request_data["environment_variables"] = kwargs["environment_variables"]
        
        response = client.post("/api/v1/execute", json=request_data)
        
        end_time = time.time()
        api_response_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        return {
            "response": data,
            "api_response_time": api_response_time,
            "execution_time": data.get("execution_time", 0),
            "memory_used": data.get("memory_used", 0)
        }
    
    @pytest.mark.performance
    def test_simple_execution_performance(self, client):
        """测试简单代码执行性能"""
        test_cases = [
            {
                "language": "python",
                "code": "print('Hello, World!')",
                "name": "Python Hello World"
            },
            {
                "language": "nodejs",
                "code": "console.log('Hello, World!');",
                "name": "Node.js Hello World"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            # 执行多次以获得平均性能
            times = []
            for _ in range(5):
                result = self.execute_code_with_timing(
                    client,
                    test_case["language"],
                    test_case["code"]
                )
                
                if result["response"]["status"] == "success":
                    times.append(result["api_response_time"])
            
            if times:
                avg_time = statistics.mean(times)
                results.append({
                    "name": test_case["name"],
                    "avg_response_time": avg_time,
                    "min_time": min(times),
                    "max_time": max(times)
                })
                
                # 性能断言
                assert avg_time < 5.0  # 平均响应时间应小于5秒
                assert min(times) < 3.0  # 最快响应应小于3秒
        
        # 打印性能结果
        for result in results:
            print(f"\n{result['name']} Performance:")
            print(f"  Average: {result['avg_response_time']:.3f}s")
            print(f"  Min: {result['min_time']:.3f}s")
            print(f"  Max: {result['max_time']:.3f}s")
    
    @pytest.mark.performance
    def test_concurrent_execution_performance(self, client):
        """测试并发执行性能"""
        def execute_single_request(request_id: int) -> Dict[str, Any]:
            """执行单个请求"""
            code = f"print('Request {request_id} completed')"
            
            result = self.execute_code_with_timing(
                client,
                "python",
                code
            )
            
            return {
                "request_id": request_id,
                "success": result["response"]["status"] == "success",
                "response_time": result["api_response_time"],
                "execution_time": result["execution_time"]
            }
        
        # 测试不同并发级别
        concurrency_levels = [1, 5, 10]
        
        for concurrency in concurrency_levels:
            print(f"\nTesting concurrency level: {concurrency}")
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [
                    executor.submit(execute_single_request, i)
                    for i in range(concurrency)
                ]
                
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 分析结果
            successful_requests = [r for r in results if r["success"]]
            success_rate = len(successful_requests) / len(results)
            
            if successful_requests:
                avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
                avg_execution_time = statistics.mean([r["execution_time"] for r in successful_requests])
                
                print(f"  Total time: {total_time:.3f}s")
                print(f"  Success rate: {success_rate:.2%}")
                print(f"  Average response time: {avg_response_time:.3f}s")
                print(f"  Average execution time: {avg_execution_time:.3f}s")
                print(f"  Throughput: {len(successful_requests)/total_time:.2f} req/s")
                
                # 性能断言
                assert success_rate >= 0.8  # 至少80%成功率
                assert avg_response_time < 10.0  # 平均响应时间小于10秒
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_performance(self, client):
        """测试内存使用性能"""
        memory_test_cases = [
            {
                "name": "Small memory usage",
                "code": "data = [i for i in range(1000)]; print(f'Created {len(data)} items')",
                "expected_memory_mb": 10
            },
            {
                "name": "Medium memory usage",
                "code": "data = [i for i in range(100000)]; print(f'Created {len(data)} items')",
                "expected_memory_mb": 50
            },
            {
                "name": "Large memory usage",
                "code": "data = [[i] * 1000 for i in range(1000)]; print(f'Created {len(data)} arrays')",
                "expected_memory_mb": 100
            }
        ]
        
        for test_case in memory_test_cases:
            result = self.execute_code_with_timing(
                client,
                "python",
                test_case["code"],
                memory_limit=256  # 给足够的内存限制
            )
            
            if result["response"]["status"] == "success":
                memory_used_mb = result["memory_used"] / (1024 * 1024)
                
                print(f"\n{test_case['name']}:")
                print(f"  Memory used: {memory_used_mb:.2f} MB")
                print(f"  Execution time: {result['execution_time']:.3f}s")
                
                # 内存使用应该在合理范围内
                assert memory_used_mb <= test_case["expected_memory_mb"] * 2  # 允许2倍误差
    
    @pytest.mark.performance
    def test_cpu_intensive_performance(self, client):
        """测试CPU密集型任务性能"""
        cpu_test_cases = [
            {
                "name": "Fibonacci calculation",
                "code": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(25)
print(f'Fibonacci(25) = {result}')
""",
                "max_execution_time": 30
            },
            {
                "name": "Prime number calculation",
                "code": """
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = [i for i in range(2, 1000) if is_prime(i)]
print(f'Found {len(primes)} primes under 1000')
""",
                "max_execution_time": 10
            },
            {
                "name": "Matrix multiplication",
                "code": """
import random

def matrix_multiply(a, b):
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    
    result = [[0 for _ in range(cols_b)] for _ in range(rows_a)]
    
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    
    return result

# 创建50x50矩阵
size = 50
a = [[random.randint(1, 10) for _ in range(size)] for _ in range(size)]
b = [[random.randint(1, 10) for _ in range(size)] for _ in range(size)]

result = matrix_multiply(a, b)
print(f'Matrix multiplication completed: {len(result)}x{len(result[0])}')
""",
                "max_execution_time": 20
            }
        ]
        
        for test_case in cpu_test_cases:
            result = self.execute_code_with_timing(
                client,
                "python",
                test_case["code"],
                timeout=test_case["max_execution_time"] + 10
            )
            
            print(f"\n{test_case['name']}:")
            print(f"  Status: {result['response']['status']}")
            print(f"  Execution time: {result['execution_time']:.3f}s")
            print(f"  API response time: {result['api_response_time']:.3f}s")
            
            if result["response"]["status"] == "success":
                # CPU密集型任务应该在合理时间内完成
                assert result["execution_time"] <= test_case["max_execution_time"]
                assert result["api_response_time"] <= test_case["max_execution_time"] + 5
            elif result["response"]["status"] == "timeout":
                # 如果超时，应该接近超时时间
                assert result["execution_time"] >= test_case["max_execution_time"] * 0.9
    
    @pytest.mark.performance
    def test_io_intensive_performance(self, client):
        """测试I/O密集型任务性能"""
        io_test_cases = [
            {
                "name": "String processing",
                "code": """
# 大量字符串操作
data = "Hello World " * 10000
result = []

for i in range(1000):
    processed = data.upper().lower().replace("World", "Python")
    result.append(len(processed))

print(f'Processed {len(result)} strings, average length: {sum(result)/len(result)}')
"""
            },
            {
                "name": "List operations",
                "code": """
# 大量列表操作
data = list(range(100000))

# 排序
sorted_data = sorted(data, reverse=True)

# 过滤
filtered_data = [x for x in sorted_data if x % 2 == 0]

# 映射
mapped_data = [x * 2 for x in filtered_data[:1000]]

print(f'Original: {len(data)}, Filtered: {len(filtered_data)}, Mapped: {len(mapped_data)}')
"""
            },
            {
                "name": "Dictionary operations",
                "code": """
# 大量字典操作
data = {i: f"value_{i}" for i in range(10000)}

# 查找操作
found_items = []
for i in range(0, 10000, 10):
    if i in data:
        found_items.append(data[i])

# 更新操作
for i in range(5000):
    data[f"new_key_{i}"] = f"new_value_{i}"

print(f'Dictionary size: {len(data)}, Found items: {len(found_items)}')
"""
            }
        ]
        
        for test_case in io_test_cases:
            result = self.execute_code_with_timing(
                client,
                "python",
                test_case["code"]
            )
            
            print(f"\n{test_case['name']}:")
            print(f"  Status: {result['response']['status']}")
            print(f"  Execution time: {result['execution_time']:.3f}s")
            print(f"  Memory used: {result['memory_used']/(1024*1024):.2f} MB")
            
            if result["response"]["status"] == "success":
                # I/O密集型任务应该相对较快
                assert result["execution_time"] < 15.0
    
    @pytest.mark.performance
    def test_startup_time_performance(self, client):
        """测试启动时间性能"""
        # 测试不同语言的启动时间
        languages = ["python", "nodejs"]
        startup_times = {}
        
        for language in languages:
            times = []
            
            # 执行多次简单代码以测量启动时间
            for i in range(5):
                if language == "python":
                    code = "import sys; print('Python version:', sys.version_info[:2])"
                else:
                    code = "console.log('Node.js version:', process.version);"
                
                result = self.execute_code_with_timing(client, language, code)
                
                if result["response"]["status"] == "success":
                    times.append(result["execution_time"])
            
            if times:
                avg_startup_time = statistics.mean(times)
                startup_times[language] = avg_startup_time
                
                print(f"\n{language.title()} startup performance:")
                print(f"  Average startup time: {avg_startup_time:.3f}s")
                print(f"  Min startup time: {min(times):.3f}s")
                print(f"  Max startup time: {max(times):.3f}s")
                
                # 启动时间应该合理
                assert avg_startup_time < 5.0  # 平均启动时间小于5秒
        
        # 比较不同语言的启动时间
        if len(startup_times) > 1:
            fastest = min(startup_times.values())
            slowest = max(startup_times.values())
            ratio = slowest / fastest if fastest > 0 else 1
            
            print("\nStartup time comparison:")
            print(f"  Fastest: {fastest:.3f}s")
            print(f"  Slowest: {slowest:.3f}s")
            print(f"  Ratio: {ratio:.2f}x")
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_stress_test_performance(self, client):
        """测试压力测试性能"""
        # 连续执行大量请求
        num_requests = 20
        results = []
        
        print(f"\nExecuting {num_requests} consecutive requests...")
        
        start_time = time.time()
        
        for i in range(num_requests):
            code = f"""
import time
start = time.time()
result = sum(i*i for i in range(10000))
end = time.time()
print(f'Request {i+1}: Result={{result}}, Time={{end-start:.3f}}s')
"""
            
            result = self.execute_code_with_timing(client, "python", code)
            results.append(result)
            
            if i % 5 == 0:
                print(f"  Completed {i+1}/{num_requests} requests")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        successful_results = [r for r in results if r["response"]["status"] == "success"]
        success_rate = len(successful_results) / len(results)
        
        if successful_results:
            avg_response_time = statistics.mean([r["api_response_time"] for r in successful_results])
            avg_execution_time = statistics.mean([r["execution_time"] for r in successful_results])
            throughput = len(successful_results) / total_time
            
            print("\nStress test results:")
            print(f"  Total requests: {num_requests}")
            print(f"  Successful requests: {len(successful_results)}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Average response time: {avg_response_time:.3f}s")
            print(f"  Average execution time: {avg_execution_time:.3f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            
            # 性能断言
            assert success_rate >= 0.9  # 至少90%成功率
            assert avg_response_time < 10.0  # 平均响应时间小于10秒
            assert throughput > 0.5  # 吞吐量大于0.5 req/s
    
    @pytest.mark.performance
    def test_memory_leak_detection(self, client):
        """测试内存泄漏检测"""
        # 执行多次相同的代码，检查内存使用是否稳定
        code = """
data = [i for i in range(10000)]
processed = [x * 2 for x in data]
result = sum(processed)
print(f'Result: {result}')
"""
        
        memory_usages = []
        
        for i in range(10):
            result = self.execute_code_with_timing(client, "python", code)
            
            if result["response"]["status"] == "success":
                memory_usages.append(result["memory_used"])
        
        if len(memory_usages) >= 5:
            # 检查内存使用是否稳定
            avg_memory = statistics.mean(memory_usages)
            memory_variance = statistics.variance(memory_usages)
            memory_std = statistics.stdev(memory_usages)
            
            print("\nMemory leak detection:")
            print(f"  Executions: {len(memory_usages)}")
            print(f"  Average memory: {avg_memory/(1024*1024):.2f} MB")
            print(f"  Memory std dev: {memory_std/(1024*1024):.2f} MB")
            print(f"  Memory variance: {memory_variance/((1024*1024)**2):.2f} MB²")
            
            # 内存使用应该相对稳定
            coefficient_of_variation = memory_std / avg_memory if avg_memory > 0 else 0
            assert coefficient_of_variation < 0.5  # 变异系数小于50%
    
    @pytest.mark.performance
    def test_response_time_consistency(self, client):
        """测试响应时间一致性"""
        # 执行相同代码多次，检查响应时间的一致性
        code = "print('Consistency test')"
        response_times = []
        
        for _ in range(15):
            result = self.execute_code_with_timing(client, "python", code)
            
            if result["response"]["status"] == "success":
                response_times.append(result["api_response_time"])
        
        if len(response_times) >= 10:
            avg_time = statistics.mean(response_times)
            std_time = statistics.stdev(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print("\nResponse time consistency:")
            print(f"  Executions: {len(response_times)}")
            print(f"  Average time: {avg_time:.3f}s")
            print(f"  Std deviation: {std_time:.3f}s")
            print(f"  Min time: {min_time:.3f}s")
            print(f"  Max time: {max_time:.3f}s")
            print(f"  Range: {max_time - min_time:.3f}s")
            
            # 响应时间应该相对一致
            coefficient_of_variation = std_time / avg_time if avg_time > 0 else 0
            assert coefficient_of_variation < 1.0  # 变异系数小于100%
            assert max_time - min_time < avg_time * 2  # 最大差异不超过平均时间的2倍