"""
API客户端模块
提供与sandbox API交互的功能
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class Language(Enum):
    """支持的语言枚举"""

    PYTHON = "python"
    NODEJS = "nodejs"


@dataclass
class ExecuteRequest:
    """执行请求数据结构"""

    code: str
    language: Language
    timeout: Optional[int] = None


@dataclass
class ExecuteResponse:
    """执行响应数据结构"""

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    status_code: Optional[int] = None


@dataclass
class HealthResponse:
    """健康检查响应数据结构"""

    status: str
    timestamp: Optional[str] = None
    uptime: Optional[float] = None
    languages: Optional[List[str]] = None


class SandboxClient:
    """Sandbox API客户端"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "Sandbox-E2E-Test/1.0",
            }
        )

    def check_health(self) -> HealthResponse:
        """检查服务健康状态"""
        try:
            url = f"{self.base_url}/api/v1/health"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return HealthResponse(
                    status=data.get("status", "healthy"),
                    timestamp=data.get("timestamp"),
                    uptime=data.get("uptime"),
                    languages=data.get("languages", []),
                )
            else:
                return HealthResponse(
                    status="unhealthy",
                    timestamp=None,
                    uptime=None,
                    languages=None,
                )

        except requests.RequestException as e:
            logger.error(f"健康检查失败: {e}")
            return HealthResponse(
                status="error", timestamp=None, uptime=None, languages=None
            )

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        try:
            url = f"{self.base_url}/api/v1/languages"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return data.get("languages", [])
            else:
                logger.error(f"获取语言列表失败: HTTP {response.status_code}")
                return []

        except requests.RequestException as e:
            logger.error(f"获取语言列表失败: {e}")
            return []

    def execute_code(self, request: ExecuteRequest) -> ExecuteResponse:
        """执行代码"""
        try:
            url = f"{self.base_url}/api/v1/execute"

            payload = {"code": request.code, "language": request.language.value}

            if request.timeout:
                payload["timeout"] = request.timeout

            start_time = __import__("time").time()
            response = self.session.post(
                url, json=payload, timeout=self.timeout + 10
            )
            execution_time = __import__("time").time() - start_time

            if response.status_code == 200:
                data = response.json()
                # API返回的是stdout而不是output
                output = data.get("stdout") or data.get("output", "")
                success = data.get("status") == "success"

                return ExecuteResponse(
                    success=success,
                    output=output,
                    error=data.get("stderr") or data.get("error"),
                    execution_time=data.get("execution_time", execution_time),
                    status_code=response.status_code,
                )
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get(
                        "error", f"HTTP {response.status_code}"
                    )
                except json.JSONDecodeError:
                    error_message = (
                        f"HTTP {response.status_code}: {response.text}"
                    )

                return ExecuteResponse(
                    success=False,
                    error=error_message,
                    execution_time=execution_time,
                    status_code=response.status_code,
                )

        except requests.Timeout:
            logger.error("执行代码超时")
            return ExecuteResponse(
                success=False, error="请求超时", execution_time=self.timeout
            )
        except requests.RequestException as e:
            logger.error(f"执行代码失败: {e}")
            return ExecuteResponse(success=False, error=str(e))

    def execute_python_code(
        self, code: str, timeout: Optional[int] = None
    ) -> ExecuteResponse:
        """执行Python代码"""
        request = ExecuteRequest(
            code=code, language=Language.PYTHON, timeout=timeout
        )
        return self.execute_code(request)

    def execute_nodejs_code(
        self, code: str, timeout: Optional[int] = None
    ) -> ExecuteResponse:
        """执行Node.js代码"""
        request = ExecuteRequest(
            code=code, language=Language.NODEJS, timeout=timeout
        )
        return self.execute_code(request)

    def test_basic_functionality(self) -> Dict[str, Any]:
        """测试基本功能"""
        results = {
            "health_check": False,
            "languages": [],
            "python_execution": False,
            "nodejs_execution": False,
        }

        try:
            health = self.check_health()
            results["health_check"] = health.status == "healthy"

            languages = self.get_supported_languages()
            results["languages"] = languages

            if Language.PYTHON.value in languages:
                python_result = self.execute_python_code(
                    'print("Hello, Python!")'
                )
                results["python_execution"] = python_result.success

            if Language.NODEJS.value in languages:
                nodejs_result = self.execute_nodejs_code(
                    'console.log("Hello, Node.js!")'
                )
                results["nodejs_execution"] = nodejs_result.success

        except Exception as e:
            logger.error(f"基本功能测试失败: {e}")
            results["error"] = str(e)

        return results

    def close(self):
        """关闭客户端"""
        self.session.close()
