"""
工具函数模块 - E2E测试所需的通用工具函数
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """设置日志配置"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("e2e_test.log")],
    )


def create_output_directory(output_dir: str) -> Path:
    """创建输出目录"""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出目录已创建: {path}")
    return path


# 测试报告生成功能已移至 report.py 模块


def wait_for_condition(
    condition_func,
    timeout: int = 60,
    interval: int = 2,
    description: str = "条件",
) -> bool:
    """等待条件满足"""
    logger.info(f"等待条件: {description}，超时时间: {timeout}秒")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            logger.info(f"条件满足: {description}")
            return True
        time.sleep(interval)

    logger.error(f"等待条件超时: {description}")
    return False


def safe_execute_code(
    client, language: str, code: str, input_data: str = ""
) -> Dict[str, Any]:
    """安全执行代码的包装函数"""
    try:
        result = client.execute_code(language, code, input_data)
        return result
    except Exception as e:
        logger.error(f"执行代码失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "execution_time": 0,
        }


def validate_execution_result(result: Dict[str, Any]) -> bool:
    """验证执行结果格式"""
    required_fields = ["status", "stdout", "stderr", "execution_time"]
    return all(field in result for field in required_fields)


def extract_test_result(
    result: Dict[str, Any],
    test_name: str,
    description: str,
    expected_status: str = "success",
) -> Dict[str, Any]:
    """提取测试结果"""
    actual_status = result.get("status", "error")
    is_passed = actual_status == expected_status

    return {
        "test_name": test_name,
        "description": description,
        "status": "passed" if is_passed else "failed",
        "error": result.get("error") if not is_passed else "",
        "execution_time": result.get("execution_time", 0),
        "details": {
            "expected_status": expected_status,
            "actual_status": actual_status,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
        },
    }
