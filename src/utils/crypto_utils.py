"""
简单加密工具模块
使用内置的加密功能提供基本的代码保护
"""

import base64
import hashlib
import hmac
import secrets
from typing import Dict


class CryptoUtils:
    """简单加密工具类 - 使用内置加密功能"""

    def generate_encryption_key(self) -> str:
        """生成32字节的随机加密密钥"""
        key = secrets.token_bytes(32)
        return base64.b64encode(key).decode("utf-8")

    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """简单的XOR加密"""
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

    def _hmac_sign(self, data: bytes, key: bytes) -> str:
        """使用HMAC进行数据签名"""
        return hmac.new(key, data, hashlib.sha256).hexdigest()

    def encrypt_code(self, code: str, key_b64: str) -> Dict[str, str]:
        """使用简单加密方法加密代码"""
        # 解码密钥
        key = base64.b64decode(key_b64.encode("utf-8"))

        # 生成随机盐值
        salt = secrets.token_bytes(16)

        # 使用XOR加密
        code_bytes = code.encode("utf-8")
        encrypted_data = self._xor_encrypt(code_bytes, key + salt)

        # 生成签名
        signature = self._hmac_sign(encrypted_data, key)

        # 返回加密数据
        return {
            "encrypted_data": base64.b64encode(encrypted_data).decode("utf-8"),
            "salt": base64.b64encode(salt).decode("utf-8"),
            "signature": signature,
        }

    def decrypt_code(self, encrypted_data: Dict[str, str], key_b64: str) -> str:
        """解密代码"""
        # 解码密钥和加密数据
        key = base64.b64decode(key_b64.encode("utf-8"))
        encrypted_bytes = base64.b64decode(
            encrypted_data["encrypted_data"].encode("utf-8")
        )
        salt = base64.b64decode(encrypted_data["salt"].encode("utf-8"))
        signature = encrypted_data["signature"]

        # 验证签名
        computed_signature = self._hmac_sign(encrypted_bytes, key)
        if not hmac.compare_digest(computed_signature, signature):
            raise ValueError("Invalid signature - data may be tampered")

        # 使用XOR解密
        decrypted_bytes = self._xor_encrypt(encrypted_bytes, key + salt)

        return decrypted_bytes.decode("utf-8")
