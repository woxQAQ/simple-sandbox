const { spawn } = require('node:child_process');

function run() {
  return new Promise((resolve) => {
    const codePath = '/workspace/main.js';
    const child = spawn(process.execPath, [codePath], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, NODE_ENV: 'production' },
    });

    let out = '';
    let err = '';
    child.stdout.on('data', (d) => { out += d.toString(); });
    child.stderr.on('data', (d) => { err += d.toString(); });

    child.on('close', (code) => {
      resolve({ stdout: out, stderr: err, exit_code: code || 0, images_b64: [] });
    });
  });
}

(async () => {
  const res = await run();
  process.stdout.write(JSON.stringify(res));
})(); 