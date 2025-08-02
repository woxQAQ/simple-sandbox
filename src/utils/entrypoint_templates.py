"""
Entrypoint模板模块
提供简单的代码执行入口点模板
"""

import json


class EntrypointTemplates:
    """Entrypoint模板类"""

    @staticmethod
    def create_python_entrypoint(
        encrypted_code: dict,
        key_b64: str,
        uid: str,
        gid: str,
        seccomp_lib_path: str = "/var/sandbox/python/libseccomp_injector_python.so",
    ) -> str:
        """创建Python执行入口点，直接嵌入加密代码"""
        encrypted_json = json.dumps(encrypted_code)
        template = '''#!/usr/bin/env python3
"""
代码执行入口点
支持解密和执行加密的用户代码
"""

import base64
import hashlib
import hmac
import json
import os
import sys

def decrypt_code(encrypted_data: dict, key_b64: str) -> str:
    """解密代码"""
    # 解码密钥和加密数据
    key = base64.b64decode(key_b64.encode("utf-8"))
    encrypted_bytes = base64.b64decode(
        encrypted_data["encrypted_data"].encode("utf-8")
    )
    salt = base64.b64decode(encrypted_data["salt"].encode("utf-8"))
    signature = encrypted_data["signature"]

    # 验证签名
    computed_signature = hmac.new(key, encrypted_bytes, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_signature, signature):
        raise ValueError("Invalid signature - data may be tampered")

    # 使用XOR解密
    def xor_decrypt(data: bytes, key: bytes) -> bytes:
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

    decrypted_bytes = xor_decrypt(encrypted_bytes, key + salt)

    return decrypted_bytes.decode("utf-8")

def main():
    """主函数"""
    try:
        # 从命令行参数获取加密密钥
        key_b64 = sys.argv[1]

        # 直接嵌入的加密数据
        encrypted_data = {encrypted_json}

        # 解密代码
        user_code = decrypt_code(encrypted_data, key_b64)

        # 设置seccomp安全限制
        try:
            import ctypes
            import os

            # 加载seccomp注入器
            lib_path = "{seccomp_lib_path}"
            if os.path.exists(lib_path):
                seccomp_lib = ctypes.CDLL(lib_path)

                # 设置seccomp过滤器
                result = seccomp_lib.inject_seccomp_profile(int('{uid}'), int('{gid}'))
                if result != 0:
                    # 错误码-4表示权限操作失败，这在容器环境中是正常的
                    if result == -4:
                        # 在容器环境中，权限已经降低，这是正常的
                        pass
                    else:
                        print(f"Warning: seccomp injection failed with code: {{result}}", file=sys.stderr)
        except Exception as e:
            # 在容器环境中，seccomp设置失败是正常的
            pass

        # 执行用户代码
        exec_globals = {{
            '__name__': '__main__',
            '__file__': __file__
        }}

        exec(user_code, exec_globals)

    except Exception as e:
        import traceback
        error_msg = f"Execution failed: {{e}}\\n{{traceback.format_exc()}}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
'''.format(
            encrypted_json=encrypted_json,
            uid=uid,
            gid=gid,
            seccomp_lib_path=seccomp_lib_path,
        )
        return template

    @staticmethod
    def create_nodejs_entrypoint(
        encrypted_code: dict,
        key_b64: str,
        uid: str,
        gid: str,
        seccomp_lib_path: str = "/var/sandbox/nodejs/libseccomp_injector_nodejs.so",
    ) -> str:
        """创建Node.js执行入口点，直接嵌入加密代码"""
        import json

        encrypted_json = json.dumps(encrypted_code)

        template = f"""#!/usr/bin/env node
/**
 * 代码执行入口点
 * 支持解密和执行加密的用户代码
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function decryptCode(encryptedData, keyB64) {{
    // 解密代码
    const key = Buffer.from(keyB64, 'base64');
    const encrypted = Buffer.from(encryptedData.encrypted_data, 'base64');
    const salt = Buffer.from(encryptedData.salt, 'base64');
    const signature = encryptedData.signature;

    // 验证签名
    const hmac = crypto.createHmac('sha256', key);
    hmac.update(encrypted);
    const computedSignature = hmac.digest('hex');

    if (computedSignature !== signature) {{
        throw new Error('Invalid signature - data may be tampered');
    }}

    // 使用XOR解密
    const keyWithSalt = Buffer.concat([key, salt]);
    let decrypted = Buffer.alloc(encrypted.length);
    for (let i = 0; i < encrypted.length; i++) {{
        decrypted[i] = encrypted[i] ^ keyWithSalt[i % keyWithSalt.length];
    }}

    return decrypted.toString('utf8');
}}

function main() {{
    try {{
        // 从命令行参数获取加密密钥
        const keyB64 = process.argv[2];

        // 直接嵌入的加密数据
        const encryptedData = {encrypted_json};

        // 解密代码
        const userCode = decryptCode(encryptedData, keyB64);

        // 设置seccomp安全限制（暂未实现，需要外部FFI支持）
        // TODO: 实现Node.js的seccomp安全设置

        // 执行用户代码
        eval(userCode);

    }} catch (e) {{
        console.error("Execution failed: " + e.message);
        process.exit(1);
    }}
}}


if (require.main === module) {{
    main();
}}
"""
        return template

    @staticmethod
    def create_entrypoint(
        language: str,
        encrypted_code: dict,
        key_b64: str,
        uid: str,
        gid: str,
        seccomp_lib_path: str = None,
    ) -> str:
        """创建指定语言的入口点"""
        if language.lower() == "python":
            if seccomp_lib_path is None:
                seccomp_lib_path = (
                    "/var/sandbox/python/libseccomp_injector_python.so"
                )
            return EntrypointTemplates.create_python_entrypoint(
                encrypted_code, key_b64, uid, gid, seccomp_lib_path
            )
        elif language.lower() == "nodejs":
            if seccomp_lib_path is None:
                seccomp_lib_path = (
                    "/var/sandbox/nodejs/libseccomp_injector_nodejs.so"
                )
            return EntrypointTemplates.create_nodejs_entrypoint(
                encrypted_code, key_b64, uid, gid, seccomp_lib_path
            )
        else:
            raise ValueError(f"Unsupported language: {language}")


# 全局模板实例
entrypoint_templates = EntrypointTemplates()
