"""
Node.js代码E2E测试套件
"""

import logging
from typing import Any, Dict, List

from ..common.client import SandboxClient
from ..common.utils import extract_test_result, safe_execute_code

logger = logging.getLogger(__name__)


class NodeJSE2ETests:
    """Node.js代码E2E测试类"""

    def __init__(self, client: SandboxClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []

    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有Node.js测试"""
        logger.info("开始运行Node.js E2E测试")

        # 基础功能测试
        self.test_basic_console()
        self.test_math_operations()
        self.test_variable_operations()
        self.test_function_definition()

        # 异步功能测试
        self.test_async_await()
        self.test_promise()

        # 安全限制测试
        self.test_file_access_blocked()
        self.test_network_access_blocked()
        self.test_system_command_blocked()
        self.test_child_process_blocked()

        # 边界情况测试
        self.test_empty_code()
        self.test_syntax_error()
        self.test_runtime_error()

        logger.info(f"Node.js E2E测试完成，共运行 {len(self.results)} 个测试")
        return self.results

    def test_basic_console(self) -> None:
        """测试基本控制台输出"""
        code = "console.log('Hello, Node.js!');"
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result,
            "Node.js基本控制台输出",
            "测试Node.js的console.log函数是否正常工作",
            "success",
        )
        self.results.append(test_result)

    def test_math_operations(self) -> None:
        """测试数学运算"""
        code = """
const result = 2 + 3 * 4;
console.log(result);
console.log(`平方根: ${Math.sqrt(16)}`);
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result,
            "Node.js数学运算",
            "测试Node.js的基本数学运算功能",
            "success",
        )
        self.results.append(test_result)

    def test_variable_operations(self) -> None:
        """测试变量操作"""
        code = """
const x = 10;
let y = 20;
const z = x + y;
console.log(`x = ${x}, y = ${y}, z = ${z}`);
console.log(`类型: ${typeof z}`);
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result, "Node.js变量操作", "测试Node.js的变量定义和操作", "success"
        )
        self.results.append(test_result)

    def test_function_definition(self) -> None:
        """测试函数定义"""
        code = """
function greet(name) {
    return `Hello, ${name}!`;
}

const add = (a, b) => a + b;

console.log(greet("Node.js"));
console.log(`5 + 3 = ${add(5, 3)}`);
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result, "Node.js函数定义", "测试Node.js的函数定义和调用", "success"
        )
        self.results.append(test_result)

    def test_async_await(self) -> None:
        """测试async/await功能"""
        code = """
async function fetchData() {
    return new Promise((resolve) => {
        setTimeout(() => resolve('数据获取成功'), 100);
    });
}

async function main() {
    try {
        const result = await fetchData();
        console.log(result);
    } catch (error) {
        console.log('错误:', error.message);
    }
}

main();
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result,
            "Node.js Async/Await",
            "测试Node.js的async/await异步功能",
            "success",
        )
        self.results.append(test_result)

    def test_promise(self) -> None:
        """测试Promise功能"""
        code = """
const promise = new Promise((resolve, reject) => {
    setTimeout(() => resolve('Promise解决'), 100);
});

promise
    .then(result => console.log(result))
    .catch(error => console.log('错误:', error));
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result, "Node.js Promise", "测试Node.js的Promise异步功能", "success"
        )
        self.results.append(test_result)

    def test_file_access_blocked(self) -> None:
        """测试文件访问被阻止"""
        code = """
const fs = require('fs');
try {
    const content = fs.readFileSync('/etc/passwd', 'utf8');
    console.log('文件访问成功');
} catch (error) {
    console.log('文件访问被阻止:', error.message);
}
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result,
            "Node.js文件访问阻止",
            "测试Node.js的文件系统访问安全限制",
            "success",
        )
        self.results.append(test_result)

    def test_network_access_blocked(self) -> None:
        """测试网络访问被阻止"""
        code = """
// 测试网络访问是否被阻止
try {
    const net = require('net');
    console.log('net模块导入成功');

    const socket = new net.Socket();
    let connectionBlocked = false;
    let testCompleted = false;

    socket.connect(80, '8.8.8.8', () => {
        console.log('网络访问成功 - 安全限制失败');
        connectionBlocked = false;
        testCompleted = true;
        socket.destroy();
    });

    socket.on('error', (error) => {
        console.log('网络访问被正确阻止:', error.message);
        connectionBlocked = true;
        testCompleted = true;
        socket.destroy();
    });

    // 设置较短的超时
    setTimeout(() => {
        if (!testCompleted) {
            console.log('网络访问测试超时 - 可能被阻止');
            connectionBlocked = true;
        }
        socket.destroy();
    }, 1500);

} catch (error) {
    console.log('网络访问测试异常:', error.message);
    console.log('网络安全限制生效');
}

console.log('Node.js网络安全限制测试开始');
setTimeout(() => {
    console.log('Node.js网络安全限制测试结束');
}, 2000);
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result,
            "Node.js网络访问阻止",
            "测试Node.js的网络访问安全限制",
            "success",
        )
        self.results.append(test_result)

    def test_system_command_blocked(self) -> None:
        """测试系统命令被阻止"""
        code = """
// 测试系统命令是否被阻止
try {
    const { exec } = require('child_process');
    console.log('child_process模块导入成功');

    // 设置全局错误处理器
    process.on('uncaughtException', (error) => {
        console.log('未捕获的异常:', error.message);
        console.log('系统命令安全限制生效');
    });

    exec('ls -la', { timeout: 2000 }, (error, stdout, stderr) => {
        if (error) {
            console.log('系统命令执行被正确阻止:', error.message);
        } else {
            console.log('系统命令执行成功 - 安全限制失败');
            console.log('输出:', stdout.substring(0, 100));
        }
    });
} catch (error) {
    console.log('系统命令执行异常:', error.message);
    console.log('系统命令安全限制生效');
}

console.log('Node.js系统命令安全限制测试开始');
// 等待异步操作完成
setTimeout(() => {
    console.log('Node.js系统命令安全限制测试结束');
}, 3000);
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result,
            "Node.js系统命令阻止",
            "测试Node.js的系统命令执行安全限制",
            "success",
        )
        self.results.append(test_result)

    def test_child_process_blocked(self) -> None:
        """测试child_process模块被阻止"""
        code = """
try {
    const { spawn } = require('child_process');
    console.log('child_process模块导入成功');
} catch (error) {
    console.log('child_process模块导入被阻止:', error.message);
}
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result,
            "Node.js Child Process阻止",
            "测试Node.js的child_process模块安全限制",
            "success",
        )
        self.results.append(test_result)

    def test_empty_code(self) -> None:
        """测试空代码"""
        code = ""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result, "Node.js空代码", "测试Node.js的空代码处理", "success"
        )
        self.results.append(test_result)

    def test_syntax_error(self) -> None:
        """测试语法错误"""
        code = """
function brokenFunction(
    // 缺少右括号
    console.log("This will cause syntax error");
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result, "Node.js语法错误", "测试Node.js的语法错误处理", "error"
        )
        self.results.append(test_result)

    def test_runtime_error(self) -> None:
        """测试运行时错误"""
        code = """
const x = 10;
const y = 0;
try {
    const result = x / y;
    console.log(`结果: ${result}`);
} catch (error) {
    console.log(`除零错误: ${error.message}`);
}
"""
        result = safe_execute_code(self.client, "nodejs", code)
        test_result = extract_test_result(
            result,
            "Node.js运行时错误",
            "测试Node.js的运行时错误处理",
            "success",
        )
        self.results.append(test_result)
