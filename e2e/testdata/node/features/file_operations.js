const fs = require('fs');
const path = require('path');

console.log('Testing file operations...');

// 测试读取 /etc/passwd（容器内正常操作）
try {
    const content = fs.readFileSync('/etc/passwd', 'utf8');
    console.log(`Successfully read /etc/passwd (${content.length} characters)`);
} catch (e) {
    console.log(`Failed to read /etc/passwd: ${e.message}`);
}

// 测试写入临时文件
try {
    fs.writeFileSync('/tmp/test.txt', 'Hello from sandbox!\n');
    console.log('Successfully wrote to /tmp/test.txt');
} catch (e) {
    console.log(`Failed to write to /tmp/test.txt: ${e.message}`);
}

// 测试读取刚写入的文件
try {
    const content = fs.readFileSync('/tmp/test.txt', 'utf8');
    console.log(`Successfully read from /tmp/test.txt: ${content.trim()}`);
} catch (e) {
    console.log(`Failed to read from /tmp/test.txt: ${e.message}`);
}

// 测试列出目录内容
try {
    const files = fs.readdirSync('/tmp');
    console.log(`Found ${files.length} files in /tmp`);
} catch (e) {
    console.log(`Failed to list /tmp: ${e.message}`);
}

console.log('File operations test completed');