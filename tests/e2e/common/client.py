"""
HTTP客户端模块 - 与沙盒服务器交互的HTTP客户端
"""

import logging
from typing import Any, Dict, Optional

import requests
from requests.exceptions import RequestException, Timeout

from .config import E2ETestConfig

logger = logging.getLogger(__name__)


class SandboxClient:
    """沙盒服务器HTTP客户端"""

    def __init__(self, config: E2ETestConfig):
        self.config = config
        self.base_url = config.get_api_base_url()
        self.timeout = config.api.timeout
        self.session = requests.Session()

        # 设置默认请求头
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "Code-Sandbox-E2E-Test/1.0",
            }
        )

    def check_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            url = self.config.get_health_url()
            logger.debug(f"检查健康状态: {url}")

            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"健康检查响应: {data}")
                return data.get("status") == "healthy"
            else:
                logger.warning(f"健康检查失败: HTTP {response.status_code}")
                return False

        except Timeout:
            logger.error("健康检查超时")
            return False
        except RequestException as e:
            logger.error(f"健康检查请求失败: {e}")
            return False
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False

    def execute_code(
        self,
        language: str,
        code: str,
        input_data: str = "",
        environment_variables: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """执行代码"""
        try:
            url = self.config.get_execute_url()
            logger.debug(f"执行代码: {language} - {len(code)} 字符")

            payload = {
                "language": language,
                "code": code,
                "input_data": input_data,
            }

            if environment_variables:
                payload["environment_variables"] = environment_variables

            response = self.session.post(
                url, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                logger.debug(f"代码执行结果: {result.get('status')}")
                return result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"代码执行失败: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "stdout": "",
                    "stderr": "",
                    "execution_time": 0,
                }

        except Timeout:
            error_msg = "请求超时"
            logger.error(f"代码执行超时: {error_msg}")
            return {
                "status": "timeout",
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "execution_time": 0,
            }
        except RequestException as e:
            error_msg = f"请求失败: {e}"
            logger.error(f"代码执行请求失败: {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "execution_time": 0,
            }
        except Exception as e:
            error_msg = f"未知错误: {e}"
            logger.error(f"代码执行未知错误: {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "execution_time": 0,
            }

    def wait_for_server(self, max_wait_time: int = 60) -> bool:
        """等待服务器就绪"""
        logger.info(f"等待服务器就绪，最大等待时间: {max_wait_time}秒")

        import time

        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            if self.check_health():
                logger.info("服务器已就绪")
                return True
            time.sleep(2)

        logger.error(f"等待服务器就绪超时: {max_wait_time}秒")
        return False

    def close(self) -> None:
        """关闭客户端"""
        self.session.close()
        logger.info("HTTP客户端已关闭")
