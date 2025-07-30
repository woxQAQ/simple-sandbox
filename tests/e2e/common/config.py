"""
配置管理模块
读取和管理e2e测试的配置信息
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / ".env"
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                load_dotenv(self.config_path)
                logger.info(f"加载配置文件: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                self._create_default_config()

            self._load_environment_variables()
            self._validate_config()

        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise

    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        default_config = """# Docker配置
DOCKER_IMAGE_NAME=code-sandbox
DOCKER_CONTAINER_NAME=sandbox-test
DOCKER_PORT_MAPPING=8000:8000

# 测试配置
CONTAINER_STARTUP_TIMEOUT=60
HEALTH_CHECK_INTERVAL=5
TEST_TIMEOUT=30

# API配置
API_BASE_URL=http://localhost:8000
API_HEALTH_ENDPOINT=/api/v1/health
API_EXECUTE_ENDPOINT=/api/v1/execute

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# 测试报告配置
REPORT_OUTPUT_DIR=reports
REPORT_FORMAT=html
"""

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(default_config)
            logger.info(f"创建默认配置文件: {self.config_path}")
            load_dotenv(self.config_path)
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
            raise

    def _load_environment_variables(self) -> None:
        """加载环境变量"""
        config_mapping = {
            "DOCKER_IMAGE_NAME": "docker_image_name",
            "DOCKER_CONTAINER_NAME": "docker_container_name",
            "DOCKER_PORT_MAPPING": "docker_port_mapping",
            "CONTAINER_STARTUP_TIMEOUT": "container_startup_timeout",
            "HEALTH_CHECK_INTERVAL": "health_check_interval",
            "TEST_TIMEOUT": "test_timeout",
            "API_BASE_URL": "api_base_url",
            "API_HEALTH_ENDPOINT": "api_health_endpoint",
            "API_EXECUTE_ENDPOINT": "api_execute_endpoint",
            "LOG_LEVEL": "log_level",
            "LOG_FORMAT": "log_format",
            "REPORT_OUTPUT_DIR": "report_output_dir",
            "REPORT_FORMAT": "report_format",
        }

        for env_var, config_key in config_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                self.config[config_key] = value

    def _validate_config(self) -> None:
        """验证配置"""
        required_configs = [
            "docker_image_name",
            "docker_container_name",
            "docker_port_mapping",
            "api_base_url",
            "api_health_endpoint",
            "api_execute_endpoint",
        ]

        missing_configs = []
        for config_key in required_configs:
            if config_key not in self.config:
                missing_configs.append(config_key)

        if missing_configs:
            logger.error(f"缺少必需的配置项: {missing_configs}")
            raise ValueError(f"缺少必需的配置项: {missing_configs}")

        self._parse_port_mapping()
        self._convert_numeric_configs()

    def _parse_port_mapping(self) -> None:
        """解析端口映射"""
        if "docker_port_mapping" in self.config:
            mapping_str = self.config["docker_port_mapping"]
            try:
                host_port, container_port = mapping_str.split(":")
                self.config["port_mapping"] = {
                    int(container_port): int(host_port)
                }
            except ValueError as e:
                logger.error(f"端口映射格式错误: {mapping_str}")
                raise ValueError(
                    f"端口映射格式错误，应为 'host:container': {e}"
                )

    def _convert_numeric_configs(self) -> None:
        """转换数值型配置"""
        numeric_configs = [
            ("container_startup_timeout", 60),
            ("health_check_interval", 5),
            ("test_timeout", 30),
        ]

        for config_key, default_value in numeric_configs:
            if config_key in self.config:
                try:
                    self.config[config_key] = int(self.config[config_key])
                except ValueError:
                    logger.warning(
                        f"配置项 {config_key} 不是有效数字，使用默认值: {default_value}"
                    )
                    self.config[config_key] = default_value
            else:
                self.config[config_key] = default_value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def get_health_check_url(self) -> str:
        """获取健康检查URL"""
        base_url = self.get("api_base_url")
        endpoint = self.get("api_health_endpoint")
        return f"{base_url}{endpoint}"

    def get_execute_url(self) -> str:
        """获取执行API URL"""
        base_url = self.get("api_base_url")
        endpoint = self.get("api_execute_endpoint")
        return f"{base_url}{endpoint}"

    def get_report_output_path(self) -> Path:
        """获取报告输出路径"""
        output_dir = self.get("report_output_dir", "reports")
        return Path(__file__).parent.parent / output_dir

    def __str__(self) -> str:
        """字符串表示"""
        return f"Config(config_path={self.config_path}, config_keys={list(self.config.keys())})"
