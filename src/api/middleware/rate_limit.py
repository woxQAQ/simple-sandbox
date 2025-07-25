import time
from typing import Dict, List

from fastapi import Request
from fastapi.responses import JSONResponse


class RateLimiter:
    """简单的速率限制器"""

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, client_ip: str) -> bool:
        """检查请求是否被允许"""
        now = time.time()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # 清理过期的请求
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < 60
        ]

        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False

        # 记录当前请求
        self.requests[client_ip].append(now)
        return True

    def get_wait_time(self, client_ip: str) -> float:
        """获取需要等待的时间"""
        if client_ip not in self.requests or not self.requests[client_ip]:
            return 0.0

        oldest_request = min(self.requests[client_ip])
        return max(0, 60 - (time.time() - oldest_request))


rate_limiter = RateLimiter(requests_per_minute=10)


async def rate_limit_middleware(request: Request, call_next):
    """速率限制中间件"""
    client_ip = request.client.host

    if not rate_limiter.is_allowed(client_ip):
        wait_time = int(rate_limiter.get_wait_time(client_ip))
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please wait {wait_time} seconds.",
                "retry_after": wait_time
            }
        )

    response = await call_next(request)
    return response
