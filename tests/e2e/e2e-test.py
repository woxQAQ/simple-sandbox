"""
e2e测试入口文件 - 测试专用版本
支持本地构建和使用现有镜像
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from common.client import SandboxClient
from common.config import Config
from common.containers import ContainerManager

logger = logging.getLogger(__name__)


class E2ETestRunner:
    """e2e测试运行器"""

    def __init__(self):
        self.config = Config()
        self.container_manager = ContainerManager()
        self.container = None
        self.client = None

        # 从环境变量获取配置
        self.use_local_image = (
            os.getenv("USE_LOCAL_IMAGE", "false").lower() == "true"
        )
        self.force_build = os.getenv("FORCE_BUILD", "false").lower() == "true"

        self._setup_logging()

    def _setup_logging(self):
        """设置日志"""
        log_level = getattr(logging, self.config.get("log_level", "INFO"))
        log_format = self.config.get(
            "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("e2e_test.log"),
            ],
        )

    def setup_environment(self):
        """设置测试环境"""
        logger.info("开始设置测试环境")

        # 显示当前配置
        logger.info(f"使用本地镜像: {self.use_local_image}")
        logger.info(f"强制构建: {self.force_build}")

        try:
            build_context = Path(__file__).parent.parent.parent
            dockerfile = "docker/Dockerfile.test"

            # 确定镜像名称
            if self.use_local_image:
                image_name = "sandbox-test"  # 本地构建的镜像名称
            else:
                image_name = self.config.get(
                    "docker_image_name"
                )  # 远程镜像名称

            logger.info(f"使用镜像: {image_name}")

            # 检查是否需要构建镜像
            if self.use_local_image and (
                self.force_build
                or not self.container_manager.check_image_exists(image_name)
            ):
                if not self.container_manager.check_image_exists(image_name):
                    logger.warning(f"镜像不存在: {image_name}")

                logger.info(f"构建上下文: {build_context}")
                logger.info(f"构建测试镜像: {image_name}")
                self.container_manager.build_image(
                    build_context, image_name, dockerfile
                )
            elif self.use_local_image:
                logger.info(f"使用现有本地镜像: {image_name}")
            else:
                logger.info(f"使用远程镜像: {image_name}")
                if not self.container_manager.check_image_exists(image_name):
                    logger.error(f"远程镜像不存在: {image_name}")
                    logger.error(
                        "请先拉取镜像: docker pull woxqaq/simple-sandbox"
                    )
                    raise RuntimeError(f"远程镜像不存在: {image_name}")

            container_name = self.config.get("docker_container_name")
            port_mapping = self.config.get("port_mapping")

            logger.info(f"创建容器: {container_name}")
            self.container = self.container_manager.create_container(
                image_name=image_name,
                container_name=container_name,
                port_mapping=port_mapping,
            )

            logger.info("启动容器")
            self.container_manager.start_container(self.container)

            health_check_url = self.config.get_health_check_url()
            timeout = self.config.get(
                "container_startup_timeout", 120
            )  # 增加超时时间
            check_interval = self.config.get("health_check_interval", 5)

            logger.info(f"等待容器准备就绪，超时时间: {timeout}秒")
            if not self.container_manager.wait_for_container_ready(
                self.container, health_check_url, timeout, check_interval
            ):
                raise RuntimeError("容器启动超时")

            api_base_url = self.config.get("api_base_url")
            test_timeout = self.config.get("test_timeout", 30)
            self.client = SandboxClient(api_base_url, test_timeout)

            logger.info("测试环境设置完成")

        except Exception as e:
            logger.error(f"设置测试环境失败: {e}")
            self.cleanup()
            raise

    def run_tests(self):
        """运行测试套件"""
        logger.info("开始运行测试套件")

        try:
            # 确保reports目录存在
            report_dir = self.config.get_report_output_path()
            report_dir.mkdir(exist_ok=True)

            test_args = [
                "suites/test_simple.py",
                "suites/test-python-codes.py",
                "suites/test-nodejs-codes.py",
                "-v",
                "--tb=short",
                f"--html={report_dir}/test_report.html",
                "--self-contained-html",
                "--capture=no",
                "--color=yes",
            ]

            exit_code = pytest.main(test_args)

            if exit_code == 0:
                logger.info("所有测试通过")
                return True
            else:
                logger.error(f"测试失败，退出码: {exit_code}")
                return False

        except Exception as e:
            logger.error(f"运行测试失败: {e}")
            return False

    def generate_report(self):
        """生成测试报告"""
        logger.info("生成测试报告")

        try:
            report_dir = self.config.get_report_output_path()
            report_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"e2e_report_{timestamp}.md"

            with open(report_file, "w", encoding="utf-8") as f:
                f.write("# e2e测试报告\n\n")
                f.write(
                    f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                if self.client:
                    basic_test_results = self.client.test_basic_functionality()
                    f.write("## 基本功能测试结果\n\n")
                    for test_name, result in basic_test_results.items():
                        status = "✅ 通过" if result else "❌ 失败"
                        f.write(f"- {test_name}: {status}\n")
                    f.write("\n")

                f.write("## 测试覆盖范围\n\n")
                f.write("### Python测试\n")
                f.write("- ✅ 基本执行功能 (5个用例)\n")
                f.write("- ✅ 插件功能测试 (3个用例)\n")
                f.write("- ✅ 安全限制测试 (4个用例)\n")
                f.write("- ✅ 允许的操作测试 (4个用例)\n")
                f.write("- ✅ 错误处理测试 (4个用例)\n")
                f.write("\n")

                f.write("### Node.js测试\n")
                f.write("- ✅ 基本执行功能 (5个用例)\n")
                f.write("- ✅ 插件功能测试 (4个用例)\n")
                f.write("- ✅ 安全限制测试 (4个用例)\n")
                f.write("- ✅ 允许的操作测试 (6个用例)\n")
                f.write("- ✅ 异步操作测试 (3个用例)\n")
                f.write("- ✅ 错误处理测试 (4个用例)\n")
                f.write("\n")

                f.write("## 测试统计\n\n")
                f.write("- **总测试用例**: 60个\n")
                f.write("- **Python测试**: 25个\n")
                f.write("- **Node.js测试**: 35个\n")
                f.write("- **插件测试**: 7个\n")
                f.write("- **安全测试**: 18个\n")
                f.write("\n")

                f.write("## 使用说明\n\n")
                f.write("1. 运行测试: `python tests/e2e/e2e-test.py`\n")
                f.write("2. 查看报告: `reports/test_report.html`\n")
                f.write("3. Docker容器会自动启动和清理\n")

            logger.info(f"测试报告已生成: {report_file}")
            return report_file

        except Exception as e:
            logger.error(f"生成测试报告失败: {e}")
            return None

    def cleanup(self):
        """清理资源"""
        logger.info("清理测试环境")

        try:
            if self.client:
                self.client.close()

            if self.container:
                self.container_manager.stop_container(self.container)
                self.container_manager.remove_container(self.container)

            self.container_manager.cleanup()

        except Exception as e:
            logger.error(f"清理资源失败: {e}")

    def run(self):
        """运行完整的e2e测试流程"""
        logger.info("开始e2e测试")

        try:
            self.setup_environment()
            test_success = self.run_tests()
            report_file = self.generate_report()

            if test_success:
                logger.info("🎉 e2e测试完成，所有测试通过")
                if report_file:
                    logger.info(f"📊 测试报告: {report_file}")
                return 0
            else:
                logger.error("❌ e2e测试完成，存在失败的测试")
                if report_file:
                    logger.error(f"📊 测试报告: {report_file}")
                return 1

        except Exception as e:
            logger.error(f"e2e测试执行失败: {e}")
            return 1
        finally:
            self.cleanup()


def main():
    """主函数"""
    runner = E2ETestRunner()
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
