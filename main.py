#!/usr/bin/env python3
"""
代码沙箱主入口文件
"""

import os
import sys
from pathlib import Path

import uvicorn

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
