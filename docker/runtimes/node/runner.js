// Node.js 运行器 - 简化版本
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

// 捕获输出
let stdoutData = '';
let stderrData = '';

const originalStdoutWrite = process.stdout.write;
const originalStderrWrite = process.stderr.write;

process.stdout.write = function(string) {
  stdoutData += string;
  return true;
};

process.stderr.write = function(string) {
  stderrData += string;
  return true;
};

let exitCode = 0;

try {
  // 读取代码并执行
  const code = fs.readFileSync(codePath, 'utf8');
  eval(code);
  exitCode = 0;
} catch (error) {
  exitCode = 1;
  stderrData += error.message + '\n';
  if (error.stack) {
    stderrData += error.stack + '\n';
  }
} finally {
  // 恢复原始输出
  process.stdout.write = originalStdoutWrite;
  process.stderr.write = originalStderrWrite;
  
  // 输出结果
  const result = {
    stdout: stdoutData,
    stderr: stderrData,
    exit_code: exitCode,
    artifacts: []
  };
  
  console.log(JSON.stringify(result));
}