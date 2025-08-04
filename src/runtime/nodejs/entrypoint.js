const koffi = require("koffi")
const libseccomp = koffi.load("./libseccomp_injector_nodejs.so")
const inject_seccomp_profile = libseccomp.func("int inject_seccomp_profile(int, int)")

const decryptCode = (code, key) => {
  // 解码base64，与Python实现保持一致
  const encrypted = Buffer.from(code, 'base64');
  const keyBytes = Buffer.from(key, 'base64');

  // XOR解密，与Python实现保持一致
  const decrypted = Buffer.alloc(encrypted.length);
  for (let i = 0; i < encrypted.length; i++) {
    decrypted[i] = encrypted[i] ^ keyBytes[i % keyBytes.length];
  }

  // 解码为UTF-8字符串，与Python实现保持一致
  return decrypted.toString('utf8');
}

const argv = process.argv

const code = decryptCode('{{ code }}', argv[2])
inject_seccomp_profile(parseInt(argv[3]), parseInt(argv[4]))
eval(code)
