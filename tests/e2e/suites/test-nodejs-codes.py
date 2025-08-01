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
        assert (
            "错误输出测试" in response.error
            or "错误输出测试" in response.output
        )

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
    """Node.js安全限制测试 - 基于seccomp系统调用过滤"""

    def test_ptrace_blocked(self, client):
        """测试ptrace系统调用被阻止"""
        code = """
const fs = require('fs');
const os = require('os');

// 使用syscall进行ptrace测试
try {
    // 通过尝试访问/proc/self/mem来测试内存访问限制
    fs.open('/proc/self/mem', 'r', (err, fd) => {
        if (err) {
            console.log(`内存访问被阻止: ${err.message}`);
        } else {
            console.log('内存访问成功');
            fs.close(fd, () => {});
        }
    });
    
    // 等待异步操作完成
    setTimeout(() => {
        console.log('ptrace测试完成');
    }, 100);
    
} catch (error) {
    console.log(`ptrace测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被阻止" in response.output

    def test_chmod_blocked(self, client):
        """测试chmod系统调用被阻止"""
        code = """
const fs = require('fs');

try {
    // 尝试修改文件权限
    fs.chmod('/tmp/test.txt', 0o777, (err) => {
        if (err) {
            console.log(`chmod被seccomp规则阻止: ${err.message}`);
        } else {
            console.log('chmod操作成功');
        }
    });
    
    setTimeout(() => {
        console.log('chmod测试完成');
    }, 100);
    
} catch (error) {
    console.log(`chmod测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被seccomp规则阻止" in response.output

    def test_mkdir_blocked(self, client):
        """测试mkdir系统调用被阻止"""
        code = """
const fs = require('fs');

try {
    // 尝试在受限目录创建目录
    fs.mkdir('/root/test_dir', { recursive: true }, (err) => {
        if (err) {
            console.log(`mkdir被seccomp规则阻止: ${err.message}`);
        } else {
            console.log('mkdir操作成功');
        }
    });
    
    setTimeout(() => {
        console.log('mkdir测试完成');
    }, 100);
    
} catch (error) {
    console.log(`mkdir测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被seccomp规则阻止" in response.output

    def test_unlink_blocked(self, client):
        """测试unlink系统调用被阻止"""
        code = """
const fs = require('fs');

try {
    // 尝试删除系统文件
    fs.unlink('/etc/passwd', (err) => {
        if (err) {
            console.log(`unlink被seccomp规则阻止: ${err.message}`);
        } else {
            console.log('unlink操作成功');
        }
    });
    
    setTimeout(() => {
        console.log('unlink测试完成');
    }, 100);
    
} catch (error) {
    console.log(`unlink测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被seccomp规则阻止" in response.output

    def test_rename_blocked(self, client):
        """测试rename系统调用被阻止"""
        code = """
const fs = require('fs');

try {
    // 尝试重命名系统文件
    fs.rename('/etc/passwd', '/etc/passwd.bak', (err) => {
        if (err) {
            console.log(`rename被seccomp规则阻止: ${err.message}`);
        } else {
            console.log('rename操作成功');
        }
    });
    
    setTimeout(() => {
        console.log('rename测试完成');
    }, 100);
    
} catch (error) {
    console.log(`rename测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被seccomp规则阻止" in response.output

    def test_rmdir_blocked(self, client):
        """测试rmdir系统调用被阻止"""
        code = """
const fs = require('fs');

try {
    // 尝试删除系统目录
    fs.rmdir('/etc', (err) => {
        if (err) {
            console.log(`rmdir被seccomp规则阻止: ${err.message}`);
        } else {
            console.log('rmdir操作成功');
        }
    });
    
    setTimeout(() => {
        console.log('rmdir测试完成');
    }, 100);
    
} catch (error) {
    console.log(`rmdir测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被seccomp规则阻止" in response.output

    def test_mount_blocked(self, client):
        """测试mount系统调用被阻止"""
        code = """
const fs = require('fs');

// 尝试挂载操作（通过mount系统调用的间接测试）
try {
    // 尝试创建和挂载tmpfs（这会被seccomp阻止）
    fs.mkdir('/tmp/test_mount', { recursive: true }, (err) => {
        if (err) {
            console.log(`目录创建被阻止: ${err.message}`);
        } else {
            console.log('目录创建成功');
        }
    });
    
    // 尝试通过mount命令（这会被seccomp阻止）
    const { exec } = require('child_process');
    exec('mount -t tmpfs none /tmp/test_mount', (error, stdout, stderr) => {
        if (error) {
            console.log(`mount操作被seccomp阻止: ${error.message}`);
        } else {
            console.log('mount操作成功');
        }
    });
    
    setTimeout(() => {
        console.log('mount测试完成');
    }, 1000);
    
} catch (error) {
    console.log(`mount测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被seccomp阻止" in response.output

    def test_chown_blocked(self, client):
        """测试chown系统调用被阻止"""
        code = """
const fs = require('fs');

try {
    // 尝试修改文件所有者
    fs.chown('/tmp/test.txt', 1000, 1000, (err) => {
        if (err) {
            console.log(`chown被seccomp规则阻止: ${err.message}`);
        } else {
            console.log('chown操作成功');
        }
    });
    
    setTimeout(() => {
        console.log('chown测试完成');
    }, 100);
    
} catch (error) {
    console.log(`chown测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被seccomp规则阻止" in response.output

    def test_symlink_blocked(self, client):
        """测试symlink系统调用被阻止"""
        code = """
const fs = require('fs');

try {
    // 尝试创建符号链接
    fs.symlink('/tmp/target', '/tmp/link', (err) => {
        if (err) {
            console.log(`symlink被seccomp规则阻止: ${err.message}`);
        } else {
            console.log('symlink操作成功');
        }
    });
    
    setTimeout(() => {
        console.log('symlink测试完成');
    }, 100);
    
} catch (error) {
    console.log(`symlink测试异常: ${error.message}`);
}
"""
        response = client.execute_nodejs_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被seccomp规则阻止" in response.output


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
            "missing " in response.error
            or "SyntaxError" in response.error
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
            or "undefinedVariable" in response.error
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
        assert (
            "TypeError" in response.error
            or "not a function" in response.error
            or "notAFunction is not a function" in response.error
        )

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
