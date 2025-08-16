const http = require('http');
const dns = require('dns');
const net = require('net');

console.log('Testing network access...');

// 测试HTTP访问
const req = http.get('http://httpbin.org/get', (res) => {
    console.log('HTTP access succeeded - this should be blocked');
    res.on('data', () => {});
}).on('error', (e) => {
    console.log(`Network access failed: ${e.message}`);
});
req.setTimeout(3000, () => {
    req.destroy();
    console.log('HTTP request timed out (expected)');
});

// 测试DNS解析
dns.lookup('google.com', (err, address) => {
    if (err) {
        console.log(`DNS resolution failed: ${err.message}`);
    } else {
        console.log('DNS resolution succeeded - this should be blocked');
    }
});

// 测试原始套接字连接
const socket = new net.Socket();
socket.setTimeout(3000);
socket.connect(53, '8.8.8.8', () => {
    console.log('Raw socket connection succeeded - this should be blocked');
    socket.destroy();
}).on('error', (e) => {
    console.log(`Raw socket connection failed: ${e.message}`);
});

setTimeout(() => {
    console.log('Network test completed - network access should be blocked in sandbox');
}, 4000);