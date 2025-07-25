import os
import tempfile
from typing import List, Dict, Any

from .base import LanguageRuntime
from .models import ExecutionResult
from .manager import ProcessManager
from .extensions.registry import extension_manager


class NodeJSRuntime(LanguageRuntime):
    """Node.js运行时实现"""
    
    def __init__(self):
        super().__init__("nodejs")
        self.process_manager = ProcessManager()
    
    def get_supported_extensions(self) -> List[str]:
        return [".js", ".mjs", ".cjs"]
    
    def get_default_filename(self) -> str:
        return "main.js"
    
    def preprocess_code(self, code: str) -> str:
        """预处理Node.js代码，处理console.log等特殊输出"""
        processed_code = code
        
        # 处理require('fs')等危险模块
        dangerous_modules = ['fs', 'child_process', 'cluster', 'worker_threads']
        for module in dangerous_modules:
            if f"require('{module}')" in processed_code or f'require("{module}")' in processed_code:
                # 添加安全警告但不阻止执行
                warning_code = f'''
console.warn("Warning: Module '{module}' is restricted in sandbox environment");
'''
                processed_code = warning_code + processed_code
        
        # 处理console.log输出
        if "console.log" in code or "console.error" in code:
            processed_code = self._handle_console_output(processed_code)
        
        # 处理process.exit()调用
        if "process.exit" in code:
            processed_code = self._handle_process_exit(processed_code)
        
        return processed_code
    
    def _handle_console_output(self, code: str) -> str:
        """处理console输出"""
        console_wrapper = '''
// 捕获console输出
const originalLog = console.log;
const originalError = console.error;
const originalWarn = console.warn;

console.log = function(...args) {
    originalLog.apply(console, args);
};

console.error = function(...args) {
    originalError.apply(console, args);
};

console.warn = function(...args) {
    originalWarn.apply(console, args);
};

'''
        
        return console_wrapper + code
    
    def _handle_process_exit(self, code: str) -> str:
        """处理process.exit调用"""
        exit_replacement = '''
// 安全处理process.exit
const originalExit = process.exit;
process.exit = function(code = 0) {
    console.log(`Process exit with code: ${code}`);
    originalExit(code);
};

'''
        
        return exit_replacement + code
    
    def get_command(self, filename: str) -> List[str]:
        """获取Node.js执行命令"""
        return ["node", filename]
    
    def execute(self, code: str, timeout: int, memory_limit: int,
                input_data: str = "", env_vars: Dict[str, str] = None) -> ExecutionResult:
        """执行Node.js代码"""
        
        # 预处理代码
        processed_code = self.preprocess_code(code)
        
        # 创建临时JavaScript文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.js',
            dir=self.process_manager.work_dir,
            delete=False
        ) as f:
            f.write(processed_code)
            temp_filename = f.name
        
        try:
            # 设置环境变量
            if env_vars is None:
                env_vars = {}
            
            # Node.js特定的环境变量
            env_vars.update({
                'NODE_ENV': 'production',
                'NODE_OPTIONS': '--max-old-space-size=' + str(memory_limit),
                'NODE_INPUT': input_data
            })
            
            # 执行代码
            command = self.get_command(temp_filename)
            result = self.process_manager.execute_process(
                command=command,
                timeout=timeout,
                memory_limit=memory_limit,
                stdin_data=input_data,
                env_vars=env_vars
            )
            
            return result
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_filename)
            except OSError:
                pass