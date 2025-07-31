"""
Docker容器操作模块
提供容器创建、启动、停止、删除等操作
"""

import logging
import time
from pathlib import Path
from typing import Dict

from docker.models.containers import Container

import docker

logger = logging.getLogger(__name__)


class ContainerManager:
    """Docker容器管理器"""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"无法连接到Docker: {e}")
            raise

    def check_image_exists(self, image_name: str) -> bool:
        """检查镜像是否存在"""
        try:
            logger.info(f"检查镜像是否存在: {image_name}")
            self.client.images.get(image_name)
            logger.info(f"镜像存在: {image_name}")
            return True
        except docker.errors.ImageNotFound:
            logger.warning(f"镜像不存在: {image_name}")
            return False
        except Exception as e:
            logger.error(f"检查镜像失败: {e}")
            return False

    def build_image(
        self,
        build_context: Path,
        image_name: str,
        dockerfile: str = "Dockerfile",
    ) -> str:
        """构建Docker镜像"""
        try:
            logger.info(f"构建镜像: {image_name}")
            image, build_logs = self.client.images.build(
                path=str(build_context),
                dockerfile=dockerfile,
                tag=image_name,
                rm=True,
            )

            logger.info(f"开始构建镜像，构建上下文: {build_context}")
            logger.info(f"Dockerfile路径: {dockerfile}")

            # 打印构建日志
            for log in build_logs:
                if "stream" in log:
                    logger.info(log["stream"].strip())
                elif "error" in log:
                    logger.error(log["error"].strip())
                elif "status" in log:
                    logger.info(log["status"].strip())
                elif "aux" in log:
                    logger.info(f"构建信息: {log['aux']}")
                else:
                    logger.info(str(log))

            logger.info(f"镜像构建完成: {image.id}")
            return image.id
        except Exception as e:
            logger.error(f"构建镜像失败: {e}")
            raise

    def create_container(
        self,
        image_name: str,
        container_name: str,
        port_mapping: Dict[int, int] = None,
        environment: Dict[str, str] = None,
        volumes: Dict[str, Dict[str, str]] = None,
    ) -> Container:
        """创建容器"""
        try:
            logger.info(f"创建容器: {container_name}")

            container = self.client.containers.create(
                image=image_name,
                name=container_name,
                ports=port_mapping,
                environment=environment,
                volumes=volumes,
                detach=True,
            )

            logger.info(f"容器创建成功: {container.id}")
            return container
        except Exception as e:
            logger.error(f"创建容器失败: {e}")
            raise

    def start_container(self, container: Container) -> None:
        """启动容器"""
        try:
            logger.info(f"启动容器: {container.name}")
            container.start()
            logger.info("容器启动成功")
        except Exception as e:
            logger.error(f"启动容器失败: {e}")
            raise

    def stop_container(self, container: Container, timeout: int = 10) -> None:
        """停止容器"""
        try:
            logger.info(f"停止容器: {container.name}")
            container.stop(timeout=timeout)
            logger.info("容器停止成功")
        except Exception as e:
            logger.error(f"停止容器失败: {e}")
            raise

    def remove_container(
        self, container: Container, force: bool = True
    ) -> None:
        """删除容器"""
        try:
            logger.info(f"删除容器: {container.name}")
            container.remove(force=force)
            logger.info("容器删除成功")
        except Exception as e:
            logger.error(f"删除容器失败: {e}")
            raise

    def get_container_status(self, container: Container) -> str:
        """获取容器状态"""
        try:
            container.reload()
            return container.status
        except Exception as e:
            logger.error(f"获取容器状态失败: {e}")
            return "unknown"

    def wait_for_container_ready(
        self,
        container: Container,
        health_check_url: str,
        timeout: int = 60,
        check_interval: int = 5,
    ) -> bool:
        """等待容器准备就绪"""
        import requests

        logger.info(f"等待容器准备就绪: {container.name}")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                status = self.get_container_status(container)
                if status != "running":
                    logger.warning(f"容器状态异常: {status}")
                    time.sleep(check_interval)
                    continue

                response = requests.get(health_check_url, timeout=5)
                if response.status_code == 200:
                    logger.info("容器准备就绪")
                    return True

            except requests.RequestException:
                pass
            except Exception as e:
                logger.warning(f"健康检查失败: {e}")

            time.sleep(check_interval)

        logger.error(f"等待容器准备就绪超时: {timeout}秒")
        return False

    def get_container_logs(self, container: Container, tail: int = 100) -> str:
        """获取容器日志"""
        try:
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8")
            return logs
        except Exception as e:
            logger.error(f"获取容器日志失败: {e}")
            return ""

    def cleanup(self):
        """清理资源"""
        try:
            self.client.close()
        except Exception as e:
            logger.error(f"清理Docker客户端失败: {e}")
