import pytest
from src.runtime import NodeJSRuntime, ExecutionStatus


class TestNodeJSRuntime:
    """测试Node.js运行时"""

    def setup_method(self):
        self.runtime = NodeJSRuntime()

    def test_simple_execution(self):
        """测试简单代码执行"""
        code = 'console.log("Hello, Node.js!");'
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello, Node.js!" in result.stdout
        assert result.stderr == ""
        assert result.execution_time > 0

    def test_syntax_error(self):
        """测试语法错误处理"""
        code = 'console.log("Hello"  // 缺少分号'
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.ERROR
        assert "SyntaxError" in result.stderr

    def test_timeout_handling(self):
        """测试超时处理"""
        code = '''
const start = Date.now();
while (Date.now() - start < 10000) {
    // 忙等待10秒
}
console.log("This should not print");
'''
        result = self.runtime.execute(code, timeout=1, memory_limit=64)
        
        assert result.status == ExecutionStatus.TIMEOUT

    def test_console_error_handling(self):
        """测试console.error处理"""
        code = '''
console.log("This is stdout");
console.error("This is stderr");
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "This is stdout" in result.stdout
        assert "This is stderr" in result.stderr

    def test_variable_declaration(self):
        """测试变量声明"""
        code = '''
const name = "Alice";
let age = 25;
var city = "New York";
console.log(`${name} is ${age} years old from ${city}`);
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Alice is 25 years old from New York" in result.stdout

    def test_array_operations(self):
        """测试数组操作"""
        code = '''
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
console.log(doubled.join(", "));
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "2, 4, 6, 8, 10" in result.stdout

    def test_async_await(self):
        """测试async/await"""
        code = '''
async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    console.log("Start");
    await delay(100);
    console.log("End");
}

main();
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Start" in result.stdout
        assert "End" in result.stdout

    def test_json_parsing(self):
        """测试JSON解析"""
        code = '''
const jsonString = '{"name": "Alice", "age": 25}';
const obj = JSON.parse(jsonString);
console.log(`${obj.name} is ${obj.age}`);
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Alice is 25" in result.stdout

    def test_reference_error(self):
        """测试引用错误"""
        code = '''
console.log(undefinedVariable);
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.ERROR
        assert "ReferenceError" in result.stderr

    def test_type_error(self):
        """测试类型错误"""
        code = '''
const num = 123;
num.toUpperCase(); // 数字没有toUpperCase方法
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.ERROR
        assert "TypeError" in result.stderr

    def test_environment_variables(self):
        """测试环境变量"""
        code = '''
console.log(`TEST_VAR: ${process.env.TEST_VAR || "not found"}`);
'''
        env_vars = {"TEST_VAR": "test_value"}
        result = self.runtime.execute(
            code, timeout=5, memory_limit=64, env_vars=env_vars
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "TEST_VAR: test_value" in result.stdout

    def test_memory_limit(self):
        """测试内存限制"""
        code = '''
// 创建大数组测试内存限制
const bigArray = new Array(1000000).fill(0);
console.log("Array created");
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=32)
        
        # 32MB应该不足以容纳100万元素的数组
        assert result.status in [ExecutionStatus.MEMORY_EXCEEDED, ExecutionStatus.ERROR]