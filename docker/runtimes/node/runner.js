// Node.js 运行器 - 简化版本
// 依赖容器安全隔离，重定向 console 输出

const fs = require('fs');

const codePath = '/workspace/main.js';

if (!fs.existsSync(codePath)) {
  console.log(JSON.stringify({
    stdout: '',
    stderr: 'Code file not found: ' + codePath,
    exit_code: 1,
    artifacts: []
  }));
  process.exit(0);
}

// 捕获 console 输出
const output = {
  stdout: '',
  stderr: ''
};

const originalLog = console.log;
const originalError = console.error;

console.log = (...args) => {
  output.stdout += args.join(' ') + '\n';
  originalLog(...args); // 同时输出到真实控制台
};

console.error = (...args) => {
  output.stderr += args.join(' ') + '\n';
  originalError(...args); // 同时输出到真实控制台
};

try {
  require(codePath);
  console.log(JSON.stringify({
    stdout: output.stdout,
    stderr: output.stderr,
    exit_code: 0,
    artifacts: []
  }));
} catch (error) {
  console.log(JSON.stringify({
    stdout: output.stdout,
    stderr: output.stderr + error.message + '\n',
    exit_code: 1,
    artifacts: []
  }));
}