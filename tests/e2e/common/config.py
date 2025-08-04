"""
配置管理模块 - 基于Pydantic的E2E测试配置
"""

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class ContainerConfig(BaseModel):
    """容器配置"""

    image_name: str = Field(
        default="woxqaq/simple-sandbox", description="Docker镜像名称"
    )
    container_name: str = Field(
        default="code-sandbox-e2e-test", description="容器名称"
    )
    host_port: int = Field(default=8000, description="主机端口")
    container_port: int = Field(default=8000, description="容器端口")
    enabled: bool = Field(default=True, description="是否启用容器管理")

    @field_validator("host_port", "container_port")
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("端口号必须在1-65535范围内")
        return v


class ApiConfig(BaseModel):
    """API配置"""

    base_url: str = Field(
        default="http://localhost:8000", description="API基础URL"
    )
    health_endpoint: str = Field(
        default="/api/v1/health", description="健康检查端点"
    )
    execute_endpoint: str = Field(
        default="/api/v1/execute", description="代码执行端点"
    )
    timeout: int = Field(default=30, description="请求超时时间（秒）")

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("超时时间必须大于0")
        return v


class TestConfig(BaseModel):
    """测试配置"""

    max_wait_time: int = Field(default=60, description="最大等待时间（秒）")
    wait_interval: int = Field(default=2, description="等待间隔（秒）")
    output_dir: str = Field(default="reports", description="输出目录")
    verbose: bool = Field(default=False, description="是否输出详细日志")

    @field_validator("max_wait_time", "wait_interval")
    @classmethod
    def validate_time(cls, v):
        if v <= 0:
            raise ValueError("时间值必须大于0")
        return v


class E2ETestConfig(BaseSettings):
    """E2E测试配置"""

    container: ContainerConfig = Field(default_factory=ContainerConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    test: TestConfig = Field(default_factory=TestConfig)

    class Config:
        env_file = ".env"
        env_prefix = "E2E_"
        env_nested_delimiter = "__"
        case_sensitive = False
        extra = "ignore"

    @classmethod
    def load_from_env(cls) -> "E2ETestConfig":
        """从环境变量加载配置"""
        return cls()

    def get_api_base_url(self) -> str:
        """获取API基础URL"""
        return self.api.base_url

    def get_health_url(self) -> str:
        """获取健康检查URL"""
        return f"{self.api.base_url}{self.api.health_endpoint}"

    def get_execute_url(self) -> str:
        """获取代码执行URL"""
        return f"{self.api.base_url}{self.api.execute_endpoint}"
