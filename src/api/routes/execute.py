from fastapi import APIRouter, HTTPException, Request

from ..models import ExecuteRequest, ExecuteResponse, Language
from ...runtime import PythonRuntime, NodeJSRuntime

router = APIRouter(prefix="/api/v1", tags=["execute"])

# 运行时映射
RUNTIMES = {
    Language.PYTHON: PythonRuntime(),
    Language.NODEJS: NodeJSRuntime()
}


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest, client_request: Request):
    """执行代码"""
    
    # 验证代码长度
    if len(request.code) > 1024 * 1024:  # 1MB限制
        raise HTTPException(
            status_code=413,
            detail="Code size exceeds 1MB limit"
        )
    
    # 获取运行时
    runtime = RUNTIMES.get(request.language)
    if not runtime:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {request.language}"
        )
    
    try:
        # 执行代码
        result = runtime.execute(
            code=request.code,
            timeout=request.timeout,
            memory_limit=request.memory_limit,
            input_data=request.input_data,
            env_vars=request.environment_variables
        )
        
        # 返回响应
        return ExecuteResponse(
            status=result.status.value,
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time=result.execution_time,
            memory_used=result.memory_used_mb,
            exit_code=result.exit_code,
            error=result.error_message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/languages")
async def get_supported_languages():
    """获取支持的语言列表"""
    return {
        "languages": [
            {
                "name": "python",
                "display_name": "Python",
                "extensions": [".py", ".pyw"]
            },
            {
                "name": "nodejs", 
                "display_name": "Node.js",
                "extensions": [".js", ".mjs", ".cjs"]
            }
        ]
    }