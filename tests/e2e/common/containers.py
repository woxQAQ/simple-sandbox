"""
容器管理模块 - 用于E2E测试的Docker容器生命周期管理
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

from docker.errors import DockerException, NotFound
from docker.models.containers import Container

import docker

logger = logging.getLogger(__name__)


class ContainerManager:
    """Docker容器管理器，用于E2E测试中的容器生命周期管理"""

    def __init__(
        self,
        image_name: str = "code-sandbox:latest",
        container_name: str = "code-sandbox-e2e-test",
        host_port: int = 8000,
        container_port: int = 8000,
        enabled: bool = True,
    ):
        self.image_name = image_name
        self.container_name = container_name
        self.host_port = host_port
        self.container_port = container_port
        self.enabled = enabled
        self.client = None
        self.container = None

        if enabled:
            try:
                self.client = docker.from_env()
                logger.info("Docker客户端初始化成功")
            except DockerException as e:
                logger.error(f"Docker客户端初始化失败: {e}")
                raise

    def _pull_image(self) -> None:
        """拉取Docker镜像"""
        if not self.enabled:
            return

        try:
            logger.info(f"正在拉取镜像: {self.image_name}")
            self.client.images.pull(self.image_name)
            logger.info(f"镜像拉取成功: {self.image_name}")
        except DockerException as e:
            logger.warning(f"镜像拉取失败: {e}，尝试使用本地镜像")

    def _remove_existing_container(self) -> None:
        """移除已存在的容器"""
        if not self.enabled:
            return

        try:
            existing_container = self.client.containers.get(self.container_name)
            if existing_container.status == "running":
                logger.info(f"停止运行中的容器: {self.container_name}")
                existing_container.stop()
            logger.info(f"移除现有容器: {self.container_name}")
            existing_container.remove(force=True)
        except NotFound:
            pass
        except DockerException as e:
            logger.warning(f"移除容器失败: {e}")

    def _wait_for_container_ready(self, timeout: int = 60) -> bool:
        """等待容器就绪"""
        if not self.enabled:
            return True

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.container:
                    self.container.reload()  # 刷新容器状态
                    logger.info(f"容器状态: {self.container.status}")
                    if self.container.status == "running":
                        # 简化检测逻辑：只要容器在运行就认为就绪
                        # HTTP客户端会进行真正的服务可用性检测
                        logger.info("容器已就绪")
                        return True
                time.sleep(2)
            except DockerException as e:
                logger.error(f"检查容器状态时出错: {e}")
                time.sleep(2)

        logger.error(f"等待容器就绪超时: {timeout}秒")
        return False

    def start_container(self) -> Optional[Container]:
        """启动容器"""
        if not self.enabled:
            logger.info("容器管理已禁用，跳过容器启动")
            return None

        try:
            self._pull_image()
            self._remove_existing_container()

            logger.info(f"启动容器: {self.container_name}")
            self.container = self.client.containers.run(
                self.image_name,
                name=self.container_name,
                ports={f"{self.container_port}/tcp": self.host_port},
                detach=True,
                environment={"PYTHONUNBUFFERED": "1", "LOG_LEVEL": "INFO"},
            )

            if self._wait_for_container_ready():
                logger.info(f"容器启动成功: {self.container_name}")
                return self.container
            else:
                logger.error("容器启动失败")
                self.stop_container()
                return None

        except DockerException as e:
            logger.error(f"容器启动失败: {e}")
            return None

    def stop_container(self) -> None:
        """停止容器"""
        if not self.enabled or not self.container:
            return

        try:
            logger.info(f"停止容器: {self.container_name}")
            self.container.stop()
            self.container.remove()
            self.container = None
            logger.info("容器已停止并移除")
        except DockerException as e:
            logger.warning(f"停止容器失败: {e}")

    def get_container_logs(self) -> str:
        """获取容器日志"""
        if not self.enabled or not self.container:
            return ""

        try:
            return self.container.logs().decode("utf-8")
        except DockerException as e:
            logger.error(f"获取容器日志失败: {e}")
            return ""

    def is_container_running(self) -> bool:
        """检查容器是否正在运行"""
        if not self.enabled or not self.container:
            return False

        try:
            self.container.reload()
            return self.container.status == "running"
        except DockerException:
            return False

    @contextmanager
    def container_context(self):
        """容器上下文管理器"""
        container = None
        try:
            container = self.start_container()
            yield container
        finally:
            self.stop_container()
