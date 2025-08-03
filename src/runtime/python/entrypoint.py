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
gid = sys.argv[3]
if not uid and not gid:
    exit(-1)


def decrypt_code(code, key):
    key_len = len(key)
    code_len = len(code)
    code = bytearray(code)
    for i in range(code_len):
        code[i] ^= key[i % key_len]
    return bytes(code)


user_code = decrypt_code({{code}}, key_b64)  # noqa

libseccomp = ctypes.CDLL("./libseccomp_injector_python.so")
result = libseccomp.inject_seccomp_profile(uid, gid)
if not result:
    exit(-1)

exec(user_code)
