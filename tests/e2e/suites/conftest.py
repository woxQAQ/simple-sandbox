"""
e2e测试的conftest.py文件
提供测试所需的fixture和配置
"""

import logging
import sys
from pathlib import Path

import pytest

# 添加父目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.client import SandboxClient
from common.config import Config

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def config():
    """配置fixture"""
    return Config()


@pytest.fixture(scope="session")
def client(config):
    """API客户端fixture"""
    api_base_url = config.get("api_base_url")
    test_timeout = config.get("test_timeout", 30)

    client = SandboxClient(api_base_url, test_timeout)

    try:
        # 测试基本连接
        health_response = client.check_health()
        if health_response.status != "healthy":
            pytest.skip("服务不可用")

        yield client

    finally:
        client.close()


@pytest.fixture(autouse=True)
def setup_test_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
