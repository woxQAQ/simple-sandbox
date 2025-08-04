"""
E2E测试入口文件
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.e2e.common.client import SandboxClient
from tests.e2e.common.config import E2ETestConfig
from tests.e2e.common.containers import ContainerManager
from tests.e2e.common.report import generate_test_report
from tests.e2e.common.utils import (
    create_output_directory,
    setup_logging,
)
from tests.e2e.suites.test_nodejs_codes import NodeJSE2ETests
from tests.e2e.suites.test_python_codes import PythonE2ETests


def main():
    """E2E测试主函数"""
    # 加载配置
    config = E2ETestConfig.load_from_env()

    # 设置日志
    setup_logging(config.test.verbose)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Code Sandbox E2E测试开始")
    logger.info("=" * 60)

    # 创建输出目录
    output_dir = create_output_directory(config.test.output_dir)

    # 初始化容器管理器
    container_manager = ContainerManager(
        image_name=config.container.image_name,
        container_name=config.container.container_name,
        host_port=config.container.host_port,
        container_port=config.container.container_port,
        enabled=config.container.enabled,
    )

    container = None
    all_results: List[Dict[str, Any]] = []

    try:
        # 启动容器
        if config.container.enabled:
            logger.info("启动Docker容器...")
            container = container_manager.start_container()
            if not container:
                logger.error("容器启动失败")
                return 1
        else:
            logger.info("容器管理已禁用，假设服务已在运行")

        # 等待服务就绪
        client = SandboxClient(config)

        logger.info("等待服务就绪...")
        if not client.wait_for_server(config.test.max_wait_time):
            logger.error("服务未在规定时间内就绪")
            if config.container.enabled:
                logger.error("容器日志:")
                logger.error(container_manager.get_container_logs())
            return 1

        # 运行Python测试
        logger.info("运行Python E2E测试...")
        python_tests = PythonE2ETests(client)
        python_results = python_tests.run_all_tests()
        all_results.extend(python_results)

        # 运行Node.js测试
        logger.info("运行Node.js E2E测试...")
        nodejs_tests = NodeJSE2ETests(client)
        nodejs_results = nodejs_tests.run_all_tests()
        all_results.extend(nodejs_results)

        # 生成报告
        logger.info("生成测试报告...")
        report_path = generate_test_report(all_results, output_dir)

        # 输出总结
        total_tests = len(all_results)
        passed_tests = sum(
            1 for r in all_results if r.get("status") == "passed"
        )
        failed_tests = sum(
            1 for r in all_results if r.get("status") == "failed"
        )
        success_rate = (
            passed_tests / total_tests * 100 if total_tests > 0 else 0
        )

        logger.info("=" * 60)
        logger.info("E2E测试总结")
        logger.info("=" * 60)
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过: {passed_tests}")
        logger.info(f"失败: {failed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"报告路径: {report_path}")

        # 如果有失败的测试，输出详细信息
        if failed_tests > 0:
            logger.warning("失败的测试:")
            for result in all_results:
                if result.get("status") == "failed":
                    logger.warning(
                        f"  - {result.get('test_name')}: "
                        f"{result.get('error')}"
                    )

        # 返回适当的退出码
        return 0 if failed_tests == 0 else 1

    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        return 1
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        logger.exception("完整错误信息:")
        return 1
    finally:
        # 清理资源
        if "client" in locals():
            try:
                client.close()
            except Exception:
                pass

        if config.container.enabled:
            try:
                container_manager.stop_container()
            except Exception:
                pass

        logger.info("E2E测试完成")


if __name__ == "__main__":
    sys.exit(main())
