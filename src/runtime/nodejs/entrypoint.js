const koffi = require("koffi")
const libseccomp = koffi.load("./libseccomp_injector_nodejs.so")
const inject_seccomp_profile = libseccomp.func("int inject_seccomp_profile(int, int)")

const decryptCode = (code, key) => {
  // 解码base64，与Python实现保持一致
  const encrypted = Buffer.from(code, 'base64');
  const keyBytes = Buffer.from(key, 'base64');

  // 使用bytearray类似的方式处理
  const codeArray = new Uint8Array(encrypted);
  const keyLen = keyBytes.length;

  // XOR解密，与Python实现保持一致
  for (let i = 0; i < codeArray.length; i++) {
    codeArray[i] ^= keyBytes[i % keyLen];
  }

  // 解码为UTF-8字符串，与Python实现保持一致
  return Buffer.from(codeArray).toString('utf8');
}

const argv = process.argv

const code = decryptCode('{{ code }}', argv[3])
inject_seccomp_profile(parseInt(argv[4]), parseInt(argv[5]))
eval(code)
