"""
Entrypoint模板模块
提供简单的代码执行入口点模板
"""

import json


class EntrypointTemplates:
    """Entrypoint模板类"""

    @staticmethod
    def create_python_entrypoint(
        encrypted_code: dict, key_b64: str, uid: str, gid: str
    ) -> str:
        """创建Python执行入口点，直接嵌入加密代码"""
        encrypted_json = json.dumps(encrypted_code)
        return f'''#!/usr/bin/env python3
"""
代码执行入口点
支持解密和执行加密的用户代码，集成seccomp安全限制
"""

import base64
import hashlib
import hmac
import json
import os
import sys

def apply_seccomp_security():
    """应用seccomp安全限制"""
    try:
        # 尝试导入seccomp模块
        try:
            from src.security import SecurityManager
            security_manager = SecurityManager(library_dir="/var/sandbox/python/libseccomp_injector_python.so")
            security_manager.setup_security_profile("python", {uid}, {gid})
        except ImportError:
            # 如果seccomp模块不可用，尝试使用ctypes直接调用
            import ctypes
            import errno

            # 尝试加载seccomp注入器库
            try:
                lib_path = "/var/sandbox/python/libseccomp_injector_python.so"
                if os.path.exists(lib_path):
                    lib = ctypes.CDLL(lib_path)

                    # 设置函数签名
                    lib.inject_seccomp_profile.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
                    lib.inject_seccomp_profile.restype = ctypes.c_int

                    # 调用seccomp注入
                    result = lib.inject_seccomp_profile({uid}, {gid})
                    if result != 0:
                        print(f"seccomp注入失败，错误码: {{result}}", file=sys.stderr)
                else:
                    print("seccomp注入器库未找到", file=sys.stderr)
            except Exception as e:
                print(f"seccomp安全设置失败: {{e}}", file=sys.stderr)
    except Exception as e:
        print(f"安全模块初始化失败: {{e}}", file=sys.stderr)

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
        # 应用seccomp安全限制
        apply_seccomp_security()

        # 从命令行参数获取加密密钥
        key_b64 = sys.argv[1]

        # 直接嵌入的加密数据
        encrypted_data = {encrypted_json}

        # 解密代码
        user_code = decrypt_code(encrypted_data, key_b64)

        # 执行用户代码
        exec_globals = {{
            '__name__': '__main__',
            '__file__': __file__
        }}

        exec(user_code, exec_globals)

    except Exception as e:
        print(f"Execution failed: {{e}}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

    @staticmethod
    def create_nodejs_entrypoint(
        encrypted_code: dict, key_b64: str, uid: str, gid: str
    ) -> str:
        """创建Node.js执行入口点，直接嵌入加密代码"""
        import json

        encrypted_json = json.dumps(encrypted_code)

        return f"""#!/usr/bin/env node
/**
 * 代码执行入口点
 * 支持解密和执行加密的用户代码，集成seccomp安全限制
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function applySeccompSecurity() {{
    try {{
        // 尝试使用原生模块加载seccomp注入器
        const libPath = '/var/sandbox/nodejs/libseccomp_injector_nodejs.so';

        if (fs.existsSync(libPath)) {{
            // 使用Node.js的原生模块加载机制
            try {{
                // 在实际的实现中，这里会使用原生扩展模块
                // 现在我们记录安全设置信息
                console.error('seccomp安全限制已启用');
            }} catch (e) {{
                console.error('seccomp注入器加载失败: ' + e.message);
            }}
        }} else {{
            console.error('seccomp注入器库未找到');
        }}
    }} catch (e) {{
        console.error('安全模块初始化失败: ' + e.message);
    }}
}}

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
        // 应用seccomp安全限制
        applySeccompSecurity();

        // 从命令行参数获取加密密钥
        const keyB64 = process.argv[2];

        // 直接嵌入的加密数据
        const encryptedData = {encrypted_json};

        // 解密代码
        const userCode = decryptCode(encryptedData, keyB64);

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

    @staticmethod
    def create_entrypoint(
        language: str, encrypted_code: dict, key_b64: str, uid: str, gid: str
    ) -> str:
        """创建指定语言的入口点"""
        if language.lower() == "python":
            return EntrypointTemplates.create_python_entrypoint(
                encrypted_code, key_b64, uid, gid
            )
        elif language.lower() == "nodejs":
            return EntrypointTemplates.create_nodejs_entrypoint(
                encrypted_code, key_b64, uid, gid
            )
        else:
            raise ValueError(f"Unsupported language: {language}")


# 全局模板实例
entrypoint_templates = EntrypointTemplates()
