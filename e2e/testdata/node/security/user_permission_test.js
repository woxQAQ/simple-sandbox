const os = require('os');

const uid = process.getuid();
const gid = process.getgid();

console.log('Running as UID: ' + uid);
console.log('Running as GID: ' + gid);
console.log('Username: ' + os.userInfo().username);
console.log('Home directory: ' + os.userInfo().homedir);

// 检查是否为 root
if (uid === 0) {
    console.log('WARNING: Running as root!');
} else {
    console.log('GOOD: Running as non-root user');
}