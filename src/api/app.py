import json
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.config import config
from src.runtime import NodeJSRuntime, PythonRuntime


class Language(str, Enum):
    PYTHON = "python"
    NODEJS = "nodejs"


# 运行时映射
RUNTIMES = {Language.PYTHON: PythonRuntime(), Language.NODEJS: NodeJSRuntime()}

logger = logging.getLogger(__name__)

# 并发控制
request_semaphore = threading.Semaphore(config.MAX_CONCURRENT_REQUESTS)

# 请求速率限制
request_timestamps = defaultdict(deque)
request_lock = threading.Lock()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()

    def check_rate_limit(self, client_ip: str) -> bool:
        """检查请求速率限制"""
        if not config.ENABLE_RATE_LIMITING:
            return True

        with request_lock:
            now = datetime.now()
            timestamps = request_timestamps[client_ip]

            # 清理1分钟前的请求记录
            while timestamps and timestamps[0] < now - timedelta(minutes=1):
                timestamps.popleft()

            # 检查是否超过限制
            if len(timestamps) >= config.MAX_REQUESTS_PER_MINUTE:
                return False

            # 记录当前请求
            timestamps.append(now)
            return True

    def get_client_ip(self) -> str:
        """获取客户端IP"""
        return self.client_address[0] if self.client_address else "unknown"

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """处理GET请求"""
        if self.path == "/":
            self._handle_root()
        elif self.path == "/api/v1/health":
            self._handle_health()
        else:
            self._handle_404()

    def do_POST(self):
        """处理POST请求"""
        if self.path == "/api/v1/execute":
            self._handle_execute()
        else:
            self._handle_404()

    def _send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(response)

    def _send_error(self, message, status_code=400):
        """发送错误响应"""
        self._send_json_response({"error": message}, status_code)

    def _handle_root(self):
        """处理根路径"""
        self._send_json_response(
            {"message": "Code Sandbox API", "version": "1.0.0"}
        )

    def _handle_health(self):
        """处理健康检查"""
        response = {
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._send_json_response(response)

    def _handle_execute(self):
        """处理代码执行"""
        client_ip = self.get_client_ip()

        # 检查速率限制
        if not self.check_rate_limit(client_ip):
            self._send_error("Rate limit exceeded. Too many requests.", 429)
            return

        # 检查并发限制
        if not request_semaphore.acquire(blocking=False):
            self._send_error("Server busy. Too many concurrent requests.", 503)
            return

        try:
            # 读取请求体
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_error("Missing request body", 400)
                return

            request_body = self.rfile.read(content_length)
            request_data = json.loads(request_body.decode("utf-8"))

            # 验证必需字段
            if "language" not in request_data or "code" not in request_data:
                self._send_error(
                    "Missing required fields: language and code", 400
                )
                return

            language = request_data["language"]
            code = request_data["code"]
            input_data = request_data.get("input_data", "")
            env_vars = request_data.get("environment_variables")

            # 获取运行时
            runtime = RUNTIMES.get(language)
            if not runtime:
                self._send_error(f"Unsupported language: {language}", 400)
                return

            # 执行代码
            result = runtime.execute(
                code=code,
                input_data=input_data,
                env_vars=env_vars,
            )

            # 返回响应
            response = {
                "status": result.status.value,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": result.execution_time,
                "exit_code": result.exit_code,
                "error": result.error_message,
            }
            self._send_json_response(response)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            if request_body:
                logger.error(f"Request body: {request_body}")
            self._send_error("Invalid JSON", 400)
        except Exception as e:
            logger.error(f"Execution error: {e}")
            self._send_error(f"Internal server error: {str(e)}", 500)
        finally:
            # 释放信号量
            request_semaphore.release()

    def _handle_404(self):
        """处理404错误"""
        self._send_json_response({"error": "Not found"}, 404)


def run_server(host=None, port=None):
    """启动HTTP服务器"""
    if host is None:
        host = "0.0.0.0"
    if port is None:
        port = 8000

    server = HTTPServer((host, port), SimpleHTTPRequestHandler)
    logger = logging.getLogger(__name__)

    logger.info(f"Code Sandbox API started on http://{host}:{port}")
    logger.info(f"Configuration: {config.to_dict()}")

    def signal_handler(signum, frame):
        """信号处理函数"""
        logger.info(f"收到信号 {signum}，正在优雅关闭服务器...")
        server.shutdown()
        server.server_close()

    import signal

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号，正在关闭服务器...")
        server.server_close()
    except Exception as e:
        logger.error(f"服务器运行时错误: {e}")
        raise
    finally:
        logger.info("服务器已关闭")


if __name__ == "__main__":
    run_server()
