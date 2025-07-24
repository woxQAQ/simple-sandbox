import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_python_code():
    """提供示例Python代码"""
    return '''
def fibonacci(n):
    """计算斐波那契数列"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
'''

@pytest.fixture
def sample_nodejs_code():
    """提供示例Node.js代码"""
    return '''
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

const result = fibonacci(10);
console.log(`Fibonacci(10) = ${result}`);
'''

@pytest.fixture
def invalid_python_code():
    """提供无效的Python代码"""
    return 'print("Hello"  # 缺少右括号'

@pytest.fixture
def invalid_nodejs_code():
    """提供无效的Node.js代码"""
    return 'console.log("Hello"  // 缺少分号'