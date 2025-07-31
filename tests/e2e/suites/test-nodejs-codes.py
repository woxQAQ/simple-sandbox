"""
Node.js代码测试套件
测试Node.js代码执行、插件功能、安全限制等
"""

import logging

logger = logging.getLogger(__name__)


class TestNodeJSBasicExecution:
    """Node.js基本执行测试"""

    def test_hello_world(self, client):
        """测试Hello World"""
        code = 'console.log("Hello, World!");'
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "Hello, World!" in response.output
        assert response.execution_time is not None

    def test_variable_operations(self, client):
        """测试变量操作"""
        code = """
let x = 10;
let y = 20;
let z = x + y;
console.log(`结果: ${z}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "结果: 30" in response.output

    def test_function_definition(self, client):
        """测试函数定义"""
        code = """
function greet(name) {
    return `Hello, ${name}!`;
}

const result = greet("Node.js");
console.log(result);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "Hello, Node.js!" in response.output

    def test_array_operations(self, client):
        """测试数组操作"""
        code = """
const numbers = [1, 2, 3, 4, 5];
numbers.push(6);
const doubled = numbers.map(x => x * 2);
console.log(`翻倍后的数组: [${doubled.join(', ')}]`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "翻倍后的数组: [2, 4, 6, 8, 10, 12]" in response.output

    def test_object_operations(self, client):
        """测试对象操作"""
        code = """
const person = {
    name: "Alice",
    age: 25,
    city: "Beijing"
};

person.job = "Engineer";
const age = person.age || 0;

console.log(`姓名: ${person.name}`);
console.log(`年龄: ${age}`);
console.log(`职业: ${person.job}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "姓名: Alice" in response.output
        assert "职业: Engineer" in response.output


class TestNodeJSPlugins:
    """Node.js插件测试"""

    def test_console_plugin(self, client):
        """测试控制台插件"""
        code = """
// 测试标准输出
console.log("标准输出测试");

// 测试标准错误
console.error("错误输出测试");

// 测试不同级别的日志
console.info("信息日志");
console.warn("警告日志");

console.log("控制台测试完成");
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "标准输出测试" in response.output
        assert "错误输出测试" in response.output

    def test_import_plugin(self, client):
        """测试导入插件"""
        code = """
// 测试模块导入
const path = require('path');
const os = require('os');

console.log(`当前平台: ${os.platform()}`);
console.log(`CPU架构: ${os.arch()}`);
console.log(`路径分隔符: ${path.sep}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "当前平台:" in response.output
        assert "CPU架构:" in response.output

    def test_process_plugin(self, client):
        """测试进程插件"""
        code = """
// 测试进程信息
console.log(`Node.js版本: ${process.version}`);
console.log(`进程ID: ${process.pid}`);
console.log(`当前工作目录: ${process.cwd()}`);

// 测试环境变量
console.log(`PATH长度: ${process.env.PATH ? process.env.PATH.length : 0}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "Node.js版本:" in response.output
        assert "进程ID:" in response.output

    def test_buffer_operations(self, client):
        """测试Buffer操作"""
        code = """
// 测试Buffer操作
const buffer = Buffer.from('Hello, Node.js!', 'utf8');
const base64 = buffer.toString('base64');
const hex = buffer.toString('hex');

console.log(`原始字符串: ${buffer.toString()}`);
console.log(`Base64编码: ${base64}`);
console.log(`十六进制: ${hex}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "原始字符串: Hello, Node.js!" in response.output


class TestNodeJSSecurity:
    """Node.js安全限制测试"""

    def test_file_operations_blocked(self, client):
        """测试文件操作被阻止"""
        code = """
const fs = require('fs');

try {
    // 尝试读取系统文件
    const content = fs.readFileSync('/etc/passwd', 'utf8');
    console.log("文件读取成功");
    console.log(content);
} catch (error) {
    console.log(`文件读取被阻止: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被阻止" in response.output
            or "permission denied" in response.output.lower()
        )

    def test_network_operations_blocked(self, client):
        """测试网络操作被阻止"""
        code = """
const http = require('http');

try {
    // 尝试HTTP请求
    const options = {
        hostname: 'google.com',
        port: 80,
        path: '/',
        method: 'GET'
    };
    
    const req = http.request(options, (res) => {
        console.log(`状态码: ${res.statusCode}`);
    });
    
    req.on('error', (error) => {
        console.log(`网络操作被阻止: ${error.message}`);
    });
    
    req.end();
    
    // 给异步操作一些时间
    setTimeout(() => {
        console.log("网络测试完成");
    }, 1000);
    
} catch (error) {
    console.log(`网络操作被阻止: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被阻止" in response.output

    def test_child_process_blocked(self, client):
        """测试子进程被阻止"""
        code = """
const { exec } = require('child_process');

try {
    // 尝试执行系统命令
    exec('ls -la', (error, stdout, stderr) => {
        if (error) {
            console.log(`系统命令被阻止: ${error.message}`);
        } else {
            console.log("命令执行成功");
            console.log(stdout);
        }
    });
    
    // 给异步操作一些时间
    setTimeout(() => {
        console.log("进程测试完成");
    }, 1000);
    
} catch (error) {
    console.log(`系统命令被阻止: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被阻止" in response.output

    def test_fs_module_restrictions(self, client):
        """测试文件系统模块限制"""
        code = """
const fs = require('fs');

try {
    // 尝试创建文件
    fs.writeFileSync('/tmp/test.txt', 'test content');
    console.log("文件创建成功");
    
    // 尝试删除文件
    fs.unlinkSync('/tmp/test.txt');
    console.log("文件删除成功");
} catch (error) {
    console.log(`文件系统操作被阻止: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被阻止" in response.output


class TestNodeJSAllowedOperations:
    """Node.js允许的操作测试"""

    def test_string_operations(self, client):
        """测试字符串操作"""
        code = """
const text = "Hello, Node.js!";
const upperText = text.toUpperCase();
const lowerText = text.toLowerCase();
const reversedText = text.split('').reverse().join('');

console.log(`大写: ${upperText}`);
console.log(`小写: ${lowerText}`);
console.log(`反转: ${reversedText}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "大写: HELLO, NODE.JS!" in response.output

    def test_math_operations(self, client):
        """测试数学运算"""
        code = """
// 测试数学运算
const sqrtResult = Math.sqrt(16);
const piValue = Math.PI;
const sinValue = Math.sin(Math.PI / 2);
const randomValue = Math.random();

console.log(`平方根: ${sqrtResult}`);
console.log(`π值: ${piValue}`);
console.log(`sin(π/2): ${sinValue}`);
console.log(`随机数: ${randomValue}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "平方根: 4" in response.output
        assert "sin(π/2): 1" in response.output

    def test_array_methods(self, client):
        """测试数组方法"""
        code = """
const numbers = [1, 2, 3, 4, 5];

// 测试各种数组方法
const doubled = numbers.map(x => x * 2);
const evens = numbers.filter(x => x % 2 === 0);
const sum = numbers.reduce((acc, x) => acc + x, 0);
const sorted = numbers.sort((a, b) => b - a);

console.log(`原数组: [${numbers.join(', ')}]`);
console.log(`翻倍: [${doubled.join(', ')}]`);
console.log(`偶数: [${evens.join(', ')}]`);
console.log(`求和: ${sum}`);
console.log(`降序: [${sorted.join(', ')}]`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "翻倍: [2, 4, 6, 8, 10]" in response.output
        assert "求和: 15" in response.output

    def test_date_operations(self, client):
        """测试日期操作"""
        code = """
const now = new Date();
const isoString = now.toISOString();
const dateString = now.toLocaleDateString();
const timeString = now.toLocaleTimeString();

console.log(`当前时间: ${isoString}`);
console.log(`日期: ${dateString}`);
console.log(`时间: ${timeString}`);

// 测试日期计算
const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
console.log(`明天: ${tomorrow.toLocaleDateString()}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "当前时间:" in response.output
        assert "日期:" in response.output

    def test_json_operations(self, client):
        """测试JSON操作"""
        code = """
const person = {
    name: "Alice",
    age: 25,
    city: "Beijing",
    hobbies: ["reading", "coding"]
};

// 序列化为JSON
const jsonString = JSON.stringify(person, null, 2);
console.log("JSON字符串:");
console.log(jsonString);

// 解析JSON
const parsedPerson = JSON.parse(jsonString);
console.log(`解析后的姓名: ${parsedPerson.name}`);
console.log(`爱好数量: ${parsedPerson.hobbies.length}`);
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "JSON字符串:" in response.output
        assert "解析后的姓名: Alice" in response.output

    def test_exception_handling(self, client):
        """测试异常处理"""
        code = """
try {
    // 故意抛出错误
    const result = 10 / 0;
    console.log(`结果: ${result}`);
} catch (error) {
    console.log(`捕获到错误: ${error.message}`);
} finally {
    console.log("异常处理完成");
}

// 测试自定义错误
try {
    throw new Error("这是一个自定义错误");
} catch (error) {
    console.log(`自定义错误: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "异常处理完成" in response.output
        assert "自定义错误: 这是一个自定义错误" in response.output


class TestNodeJSAsyncOperations:
    """Node.js异步操作测试"""

    def test_settimeout(self, client):
        """测试setTimeout"""
        code = """
console.log("开始计时...");

setTimeout(() => {
    console.log("1秒后执行");
}, 1000);

setTimeout(() => {
    console.log("2秒后执行");
}, 2000);

console.log("计时器已设置");
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "开始计时..." in response.output
        assert "计时器已设置" in response.output

    def test_promise_operations(self, client):
        """测试Promise操作"""
        code = """
// 创建Promise
const promise = new Promise((resolve, reject) => {
    setTimeout(() => {
        resolve("Promise成功执行");
    }, 500);
});

// 使用Promise
promise.then(result => {
    console.log(result);
}).catch(error => {
    console.log(`Promise失败: ${error}`);
});

console.log("Promise已创建");
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "Promise已创建" in response.output

    def test_async_await(self, client):
        """测试async/await"""
        code = """
// 模拟异步函数
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// async函数
async function asyncFunction() {
    console.log("开始执行async函数");
    await delay(300);
    console.log("等待300ms后");
    await delay(200);
    console.log("再等待200ms后");
    return "async函数完成";
}

// 调用async函数
asyncFunction().then(result => {
    console.log(result);
});

console.log("async函数已调用");
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "开始执行async函数" in response.output
        assert "async函数已调用" in response.output


class TestNodeJSErrorHandling:
    """Node.js错误处理测试"""

    def test_syntax_error(self, client):
        """测试语法错误"""
        code = """
// 故意的语法错误
console.log("Hello"
"""
        response = client.execute_nodejs_code(code)

        assert not response.success, "应该执行失败"
        assert (
            "SyntaxError" in response.error
            or "was never closed" in response.error
        )

    def test_reference_error(self, client):
        """测试引用错误"""
        code = """
// 尝试访问未定义的变量
console.log(undefinedVariable);
"""
        response = client.execute_nodejs_code(code)

        assert not response.success, "应该执行失败"
        assert (
            "ReferenceError" in response.error
            or "is not defined" in response.error
        )

    def test_type_error(self, client):
        """测试类型错误"""
        code = """
// 尝试对非函数调用
const notAFunction = "hello";
notAFunction();
"""
        response = client.execute_nodejs_code(code)

        assert not response.success, "应该执行失败"
        assert "TypeError" in response.error

    def test_range_error(self, client):
        """测试范围错误"""
        code = """
// 创建过大的数组
try {
    const largeArray = new Array(Number.MAX_VALUE);
    console.log("数组创建成功");
} catch (error) {
    console.log(`范围错误: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "范围错误:" in response.output
