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
        health_status = client.health_check()
        if not health_status:
            pytest.skip("服务不可用")

        yield client

    finally:
        client.close()


@pytest.fixture(scope="session")
def python_client(client):
    """Python执行客户端"""
    return client


@pytest.fixture(scope="session")
def nodejs_client(client):
    """Node.js执行客户端"""
    return client


@pytest.fixture(autouse=True)
def setup_test_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


# 全局测试结果变量
_test_results = {"passed": 0, "failed": 0, "errors": []}


@pytest.fixture(scope="session")
def test_results():
    """测试结果收集器"""
    return _test_results


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """收集测试结果"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        if rep.passed:
            _test_results["passed"] += 1
        elif rep.failed:
            _test_results["failed"] += 1
            _test_results["errors"].append(f"{item.name}: {rep.longrepr}")


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的处理"""
    logger.info(
        f"测试完成: 通过 {_test_results['passed']}, 失败 {_test_results['failed']}"
    )

    if _test_results["errors"]:
        logger.error("失败的测试:")
        for error in _test_results["errors"][:5]:  # 只显示前5个错误
            logger.error(f"  - {error}")
