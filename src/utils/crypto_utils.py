"""
简单加密工具模块
使用内置的加密功能提供基本的代码保护
"""

import base64
import secrets


class CryptoUtils:
    """简单加密工具类 - 使用内置加密功能"""

    @staticmethod
    def generate_encryption_key(_len: int) -> str:
        """生成32字节的随机加密密钥"""
        key = secrets.token_bytes(_len)
        return base64.b64encode(key).decode("utf-8")

    @staticmethod
    def _xor_encrypt(data: bytes, key: bytes) -> bytes:
        """简单的XOR加密"""
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

    @staticmethod
    def encrypt_code(code: str):
        """使用简单加密方法加密代码"""
        # 生成密钥
        key_b64 = CryptoUtils.generate_encryption_key(32)
        # 解码密钥为字节
        key_bytes = base64.b64decode(key_b64)
        # 使用XOR加密
        code_bytes = code.encode("utf-8")
        encrypted_data = CryptoUtils._xor_encrypt(code_bytes, key_bytes)
        # 使用base64编码以便安全嵌入Python代码
        encrypted_b64 = base64.b64encode(encrypted_data).decode("utf-8")

        return (encrypted_b64, key_b64)
