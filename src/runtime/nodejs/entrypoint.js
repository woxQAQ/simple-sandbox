const koffi = require("koffi")
const libseccomp = koffi.load("./libseccomp_injector_python.so")
const inject_seccomp_profile = libseccomp.func("int inject_seccomp_profile(int, int)")

const decryptCode = (code, key) => {
  const encrypted = Buffer.from(code, 'base64');
  const keyBytes = Buffer.from(key, 'base64');
  const decrypted = Buffer.alloc(encrypted.length);

  for (let i = 0; i < encrypted.length; i++) {
    decrypted[i] = encrypted[i] ^ keyBytes[i % keyBytes.length];
  }

  return decrypted.toString('utf8');
}

const argv = process.argv

const code = decryptCode('{{ code }}', argv[3])
inject_seccomp_profile(parseInt(argv[4]), parseInt(argv[5]))
eval(code)
