package testdata

// PythonCodes 包含各种 Python 测试代码
var PythonCodes = map[string]string{
	"hello_world": `print("Hello, World!")`,

	"simple_math": `
result = 2 + 3
print(f"2 + 3 = {result}")
`,

	"matplotlib_plot": `
import matplotlib.pyplot as plt
import numpy as np

# 创建简单的图表
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', linewidth=2)
plt.title('Sine Wave')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True)
plt.show()
`,

	"error_code": `
# 这段代码会产生错误
print("Before error")
raise ValueError("This is a test error")
print("After error")  # 这行不会执行
`,

	"infinite_loop": `
# 无限循环测试（用于测试超时）
while True:
    pass
`,

	"memory_intensive": `
# 内存密集型测试
data = []
for i in range(1000000):
    data.append(f"item_{i}" * 100)
print(f"Created {len(data)} items")
`,

	"file_operations": `
# 文件操作测试
try:
    with open('/etc/passwd', 'r') as f:
        content = f.read()
    print("Successfully read /etc/passwd")
except Exception as e:
    print(f"Failed to read /etc/passwd: {e}")

try:
    with open('/tmp/test.txt', 'w') as f:
        f.write("Hello from sandbox")
    print("Successfully wrote to /tmp/test.txt")
except Exception as e:
    print(f"Failed to write to /tmp/test.txt: {e}")
`,

	"network_test": `
# 网络访问测试
import urllib.request

try:
    response = urllib.request.urlopen('http://httpbin.org/get', timeout=5)
    print("Network access successful")
except Exception as e:
    print(f"Network access failed: {e}")
`,

	"system_calls": `
# 系统调用测试
import os
import subprocess

print(f"Current PID: {os.getpid()}")
print(f"Current UID: {os.getuid()}")
print(f"Current GID: {os.getgid()}")

try:
    result = subprocess.run(['whoami'], capture_output=True, text=True, timeout=5)
    print(f"whoami output: {result.stdout.strip()}")
except Exception as e:
    print(f"whoami failed: {e}")

try:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
    print(f"ps command executed, output length: {len(result.stdout)}")
except Exception as e:
    print(f"ps command failed: {e}")
`,
}

// NodeCodes 包含各种 Node.js 测试代码
var NodeCodes = map[string]string{
	"hello_world": `console.log("Hello, World!");`,

	"simple_math": `
const result = 2 + 3;
console.log('2 + 3 = ' + result);
`,

	"async_code": `
async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    console.log("Starting async operation...");
    await delay(1000);
    console.log("Async operation completed!");
}

main().catch(console.error);
`,

	"error_code": `
console.log("Before error");
throw new Error("This is a test error");
console.log("After error");  // 这行不会执行
`,

	"infinite_loop": `
// 无限循环测试（用于测试超时）
while (true) {
    // 空循环
}
`,

	"memory_intensive": `
// 内存密集型测试
const data = [];
for (let i = 0; i < 1000000; i++) {
    data.push(('item_' + i).repeat(100));
}
console.log('Created ' + data.length + ' items');
`,

	"file_operations": `
// 文件操作测试
const fs = require('fs');

try {
    const content = fs.readFileSync('/etc/passwd', 'utf8');
    console.log("Successfully read /etc/passwd");
} catch (e) {
    console.log('Failed to read /etc/passwd: ' + e.message);
}

try {
    fs.writeFileSync('/tmp/test.txt', 'Hello from sandbox');
    console.log("Successfully wrote to /tmp/test.txt");
} catch (e) {
    console.log('Failed to write to /tmp/test.txt: ' + e.message);
}
`,

	"network_test": `
// 网络访问测试
const http = require('http');

const req = http.get('http://httpbin.org/get', (res) => {
    console.log('Network access successful');
    res.on('data', () => {});
    res.on('end', () => {
        console.log('Response received');
    });
});

req.on('error', (e) => {
    console.log('Network access failed: ' + e.message);
});

req.setTimeout(5000, () => {
    req.destroy();
    console.log('Request timeout');
});
`,

	"system_calls": `
// 系统调用测试
const { execSync } = require('child_process');

console.log('Current PID: ' + process.pid);
console.log('Current UID: ' + process.getuid());
console.log('Current GID: ' + process.getgid());

try {
    const whoami = execSync('whoami', { encoding: 'utf8', timeout: 5000 });
    console.log('whoami output: ' + whoami.trim());
} catch (e) {
    console.log('whoami failed: ' + e.message);
}

try {
    const ps = execSync('ps aux', { encoding: 'utf8', timeout: 5000 });
    console.log('ps command executed, output length: ' + ps.length);
} catch (e) {
    console.log('ps command failed: ' + e.message);
}
`,
}

// ExpectedOutputs 包含预期的输出结果
var ExpectedOutputs = map[string]map[string]interface{}{
	"python_hello_world": {
		"stdout":    "Hello, World!\n",
		"stderr":    "",
		"exit_code": 0,
	},
	"python_simple_math": {
		"stdout":    "2 + 3 = 5\n",
		"stderr":    "",
		"exit_code": 0,
	},
	"python_error_code": {
		"stdout":    "Before error\n",
		"exit_code": 1,
	},
	"node_hello_world": {
		"stdout":    "Hello, World!\n",
		"stderr":    "",
		"exit_code": 0,
	},
	"node_simple_math": {
		"stdout":    "2 + 3 = 5\n",
		"stderr":    "",
		"exit_code": 0,
	},
	"node_error_code": {
		"stdout":    "Before error\n",
		"exit_code": 1,
	},
}
