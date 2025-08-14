const fs = require('fs');

function run() {
  return new Promise((resolve, reject) => {
    // Try to get code from environment variable first
    const codeFromEnv = process.env.SANDBOX_CODE;
    let code = '';
    
    if (codeFromEnv) {
      code = codeFromEnv;
    } else {
      // Fallback to reading from workspace (original behavior)
      const codePath = '/workspace/main.js';
      if (!fs.existsSync(codePath)) {
        resolve({
          stdout: '',
          stderr: 'Code file not found: ' + codePath,
          exit_code: 1,
          artifacts: []
        });
        return;
      }
      
      try {
        code = fs.readFileSync(codePath, 'utf8');
      } catch (readError) {
        resolve({
          stdout: '',
          stderr: 'Failed to read code file: ' + readError.message,
          exit_code: 1,
          artifacts: []
        });
        return;
      }
    }
    
    // Capture stdout and stderr
    let stdout = '';
    let stderr = '';
    
    const originalConsoleLog = console.log;
    const originalConsoleError = console.error;
    
    console.log = (...args) => {
      stdout += args.join(' ') + '\n';
    };
    
    console.error = (...args) => {
      stderr += args.join(' ') + '\n';
    };
    
    try {
      // Execute the code directly using eval
      eval(code);
      
      // Restore console functions
      console.log = originalConsoleLog;
      console.error = originalConsoleError;
      
      resolve({
        stdout: stdout,
        stderr: stderr,
        exit_code: 0,
        artifacts: []
      });
    } catch (error) {
      // Restore console functions
      console.log = originalConsoleLog;
      console.error = originalConsoleError;
      
      resolve({
        stdout: stdout,
        stderr: stderr + error.toString() + '\n',
        exit_code: 1,
        artifacts: []
      });
    }
  });
}

(async () => {
  try {
    // Debug: Check environment variables
    const codeFromEnv = process.env.SANDBOX_CODE;
    const debugResult = {
      stdout: '',
      stderr: 'DEBUG: SANDBOX_CODE env var: ' + (codeFromEnv ? 'present (' + codeFromEnv.length + ' chars)' : 'not present'),
      exit_code: 1,
      artifacts: []
    };
    console.log(JSON.stringify(debugResult));
    
    const res = await run();
    console.log(JSON.stringify(res));
  } catch (error) {
    const errorResult = {
      stdout: '',
      stderr: 'DEBUG: Runner error: ' + (error.message || error.toString()),
      exit_code: 1,
      artifacts: []
    };
    console.log(JSON.stringify(errorResult));
  }
})();