"""
测试报告生成模块 - 专门用于生成E2E测试报告
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# 常量定义
ALLURE_LABELS = [
    {"name": "suite", "value": "E2E Tests"},
    {"name": "testClass", "value": "E2ETests"},
    {"name": "package", "value": "e2e_tests"},
    {"name": "host", "value": "localhost"},
    {"name": "thread", "value": "main"},
    {"name": "framework", "value": "custom"},
    {"name": "language", "value": "python"},
]


def _write_json_file(path: Path, data: Dict[str, Any]) -> None:
    """写入JSON文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_text_file(path: Path, content: str) -> None:
    """写入文本文件"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _create_attachment_step(
    name: str, file_name: str, content: str, test_uuid: str
) -> Dict[str, Any]:
    """创建附件步骤"""
    timestamp = int(datetime.now().timestamp() * 1000)
    return {
        "name": name,
        "status": "passed",
        "stage": "finished",
        "start": timestamp,
        "stop": timestamp,
        "attachments": [
            {
                "name": name.lower().replace(" ", ""),
                "source": file_name,
                "type": "text/plain",
            }
        ],
    }


def _generate_test_result(
    test_uuid: str, result: Dict[str, Any]
) -> Dict[str, Any]:
    """生成单个测试结果"""
    test_name = result.get("test_name", "未知测试")
    status = "passed" if result.get("status") == "passed" else "failed"
    error = result.get("error", "")
    duration_ms = int(result.get("execution_time", 0) * 1000)

    start_time = int(datetime.now().timestamp() * 1000)
    end_time = start_time + duration_ms

    return {
        "name": test_name,
        "fullName": f"e2e_tests.{test_name}",
        "historyId": test_uuid,
        "time": {
            "start": start_time,
            "stop": end_time,
            "duration": duration_ms,
        },
        "status": status,
        "statusDetails": {
            "known": False,
            "muted": False,
            "flaky": False,
            "message": error if error else "",
            "trace": "",
        },
        "stage": "finished",
        "steps": [],
        "parameters": [],
        "labels": ALLURE_LABELS,
        "links": [],
    }


def _process_test_details(
    test_result: Dict[str, Any],
    details: Dict[str, Any],
    test_uuid: str,
    allure_dir: Path,
) -> None:
    """处理测试详情和附件"""
    if not details:
        return

    stdout = details.get("stdout", "")
    stderr = details.get("stderr", "")

    if stdout:
        file_name = f"stdout-{test_uuid}.txt"
        _write_text_file(allure_dir / file_name, stdout)
        test_result["steps"].append(
            _create_attachment_step("标准输出", file_name, stdout, test_uuid)
        )

    if stderr:
        file_name = f"stderr-{test_uuid}.txt"
        _write_text_file(allure_dir / file_name, stderr)
        test_result["steps"].append(
            _create_attachment_step("错误输出", file_name, stderr, test_uuid)
        )


def generate_allure_results(
    results: List[Dict[str, Any]], output_dir: str
) -> Path:
    """生成Allure格式的测试结果文件"""
    allure_dir = Path(output_dir) / "allure-results"
    allure_dir.mkdir(parents=True, exist_ok=True)

    # 清理旧的结果
    for file in allure_dir.glob("*"):
        file.unlink()

    for result in results:
        test_uuid = str(uuid.uuid4())

        # 生成测试结果
        test_result = _generate_test_result(test_uuid, result)
        _process_test_details(
            test_result, result.get("details", {}), test_uuid, allure_dir
        )

        # 保存结果文件
        _write_json_file(allure_dir / f"{test_uuid}-result.json", test_result)

        # 创建容器文件
        container = {
            "uuid": test_uuid,
            "name": result.get("test_name", "未知测试"),
            "children": [f"{test_uuid}-result.json"],
            "befores": [],
            "afters": [],
            "start": test_result["time"]["start"],
            "stop": test_result["time"]["stop"],
        }
        _write_json_file(allure_dir / f"{test_uuid}-container.json", container)

    logger.info(f"生成了 {len(results)} 个Allure测试结果文件")
    return allure_dir


def generate_test_report(
    results: List[Dict[str, Any]],
    output_dir: str,
) -> str:
    """生成Allure格式的测试报告"""
    allure_dir = generate_allure_results(results, output_dir)
    logger.info(f"Allure结果数据已保存到: {allure_dir}")
    logger.info("使用 'make serve-allure' 启动Allure服务查看详细报告")
    return str(allure_dir)
