const koffi = require("koffi")
const libseccomp = koffi.load("./libseccomp_injector_nodejs.so")
const inject_seccomp_profile = libseccomp.func("int inject_seccomp_profile(int, int)")

const decryptCode = (code, key) => {
  const encrypted = Buffer.from(code, 'base64');
  const keyBytes = Buffer.from(key, 'base64');
  const decrypted = Buffer.alloc(encrypted.length);

  for (let i = 0; i < encrypted.length; i++) {
    decrypted[i] = encrypted[i] ^ keyBytes[i % keyBytes.length];
  }

  // 找到实际的字符串结束位置（去除末尾的填充字节）
  let endPos = encrypted.length;
  while (endPos > 0 && decrypted[endPos - 1] === 0) {
    endPos--;
  }

  // 转换为UTF-8字符串
  return decrypted.slice(0, endPos).toString('utf8');
}

const argv = process.argv

const code = decryptCode('{{ code }}', argv[3])
inject_seccomp_profile(parseInt(argv[4]), parseInt(argv[5]))
eval(code)
