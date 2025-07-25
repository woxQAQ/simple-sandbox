from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from .routes import execute_router, health_router, plugins_router

# 创建FastAPI应用
app = FastAPI(
    title="Code Sandbox API",
    description="安全的代码执行沙箱服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        from .middleware.rate_limit import rate_limit_middleware
        return await rate_limit_middleware(request, call_next)

app.add_middleware(RateLimitMiddleware)

# 注册路由
app.include_router(execute_router)
app.include_router(health_router)
app.include_router(plugins_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Code Sandbox API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("Code Sandbox API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    print("Code Sandbox API shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
