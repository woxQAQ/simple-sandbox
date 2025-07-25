import subprocess
import time

from fastapi import APIRouter

from ..models import HealthResponse, LanguageInfo

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    
    # 获取Python版本
    python_version = subprocess.run(
        ["python3", "--version"], 
        capture_output=True, 
        text=True
    ).stdout.strip().replace("Python ", "")
    
    # 获取Node.js版本
    node_version_result = subprocess.run(
        ["node", "--version"], 
        capture_output=True, 
        text=True
    )
    node_version = "unknown"
    if node_version_result.returncode == 0:
        node_version = node_version_result.stdout.strip().replace("v", "")
    
    return HealthResponse(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        supported_languages=[
            LanguageInfo(
                name="python",
                version=python_version,
                extensions=[".py", ".pyw"]
            ),
            LanguageInfo(
                name="nodejs",
                version=node_version,
                extensions=[".js", ".mjs", ".cjs"]
            )
        ]
    )