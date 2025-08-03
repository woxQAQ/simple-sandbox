const koffi = require("koffi")
const lib = koffi.load("./libseccomp_injector_python.so")
const libseccomp = lib.func("int inject_seccomp_profile(int, int)")

const decryptCode = (code, key) => {
  {
    let decrypted = Buffer.alloc(code.length);
    let keylen = len(key)
    for (let i = 0; i < code.length; i++) {
      {
        code[i] = code[i] ^ key[i % keylen];
      }
    }

    return decrypted.toString('utf8');
  }
}

const argv = process.argv

const code = decryptCode({{ code }}, argv[3])
libseccomp(argv[4], argv[5])
eval(code)
