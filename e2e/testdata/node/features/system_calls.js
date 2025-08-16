const os = require('os');
const { execSync } = require('child_process');

console.log('Testing system calls...');

// 获取进程信息
console.log(`Current PID: ${process.pid}`);
console.log(`Current UID: ${process.getuid()}`);
console.log(`Current GID: ${process.getgid()}`);

// 测试 whoami 命令
try {
    const result = execSync('whoami', { encoding: 'utf8', timeout: 5000 });
    console.log(`whoami output: ${result.trim()}`);
} catch (e) {
    console.log(`whoami failed: ${e.message}`);
}

// 测试 ps 命令
try {
    const result = execSync('ps aux', { encoding: 'utf8', timeout: 5000 });
    const lines = result.trim().split('\n');
    console.log(`ps command executed, found ${lines.length} processes`);
} catch (e) {
    console.log(`ps command failed: ${e.message}`);
}

// 测试基本的文件系统访问
try {
    const files = require('fs').readdirSync('/proc');
    console.log(`Successfully listed /proc directory: ${files.length} entries`);
} catch (e) {
    console.log(`Failed to list /proc: ${e.message}`);
}

console.log('System calls test completed');