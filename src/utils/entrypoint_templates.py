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
