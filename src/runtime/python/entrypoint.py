import base64
import ctypes
import os
import sys

key_b64 = sys.argv[1]
if not key_b64:
    exit(-1)

lib_path = sys.argv[2]
if not lib_path:
    exit(-1)
os.chdir(lib_path)
uid = sys.argv[3]
gid = sys.argv[4]
if not uid and not gid:
    exit(-1)


def decrypt_code(code_b64, key):
    # 解码base64
    encrypted_data = base64.b64decode(code_b64)
    # 解码密钥
    key_bytes = base64.b64decode(key)
    # XOR解密
    key_len = len(key_bytes)
    code_len = len(encrypted_data)
    code = bytearray(encrypted_data)
    for i in range(code_len):
        code[i] ^= key_bytes[i % key_len]
    return bytes(code)


user_code = decrypt_code("{{code}}", key_b64)  # noqa

libseccomp = ctypes.CDLL("./libseccomp_injector_python.so")
result = libseccomp.inject_seccomp_profile(uid, gid)
if not result:
    exit(-1)

exec(user_code)
