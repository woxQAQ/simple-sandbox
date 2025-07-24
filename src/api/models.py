from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class Language(str, Enum):
    PYTHON = "python"
    NODEJS = "nodejs"


class ExecuteRequest(BaseModel):
    language: Language = Field(..., description="编程语言")
    code: str = Field(..., description="要执行的代码")
    timeout: int = Field(default=30, ge=1, le=300, description="超时时间(秒)")
    memory_limit: int = Field(default=128, ge=16, le=1024, description="内存限制(MB)")
    input_data: str = Field(default="", description="标准输入数据")
    environment_variables: Optional[Dict[str, str]] = Field(
        default=None, description="环境变量"
    )


class ExecuteResponse(BaseModel):
    status: str = Field(..., description="执行状态")
    stdout: str = Field(..., description="标准输出")
    stderr: str = Field(..., description="标准错误")
    execution_time: float = Field(..., description="执行时间(秒)")
    memory_used: float = Field(..., description="内存使用(MB)")
    exit_code: Optional[int] = Field(None, description="退出码")
    error: Optional[str] = Field(None, description="错误信息")


class LanguageInfo(BaseModel):
    name: str = Field(..., description="语言名称")
    version: str = Field(..., description="版本")
    extensions: list[str] = Field(..., description="支持的扩展名")


class HealthResponse(BaseModel):
    status: str = Field(..., description="服务状态")
    timestamp: str = Field(..., description="时间戳")
    supported_languages: list[LanguageInfo] = Field(..., description="支持的语言")