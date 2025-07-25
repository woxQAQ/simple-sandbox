import os
import tempfile
from typing import List, Dict

from .base import LanguageRuntime
from .models import ExecutionResult
from .manager import ProcessManager


class PythonRuntime(LanguageRuntime):
    """Python运行时实现"""
    
    def __init__(self):
        super().__init__("python")
        self.process_manager = ProcessManager()
    
    def get_supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]
    
    def get_default_filename(self) -> str:
        return "main.py"
    
    def preprocess_code(self, code: str) -> str:
        """预处理Python代码，处理matplotlib等特殊情况"""
        processed_code = code
        
        # 处理matplotlib的show()调用
        if "import matplotlib" in code or "from matplotlib" in code:
            processed_code = self._handle_matplotlib(processed_code)
        
        # 处理input()函数
        if "input(" in code:
            processed_code = self._handle_input(processed_code)
        
        return processed_code
    
    def _handle_matplotlib(self, code: str) -> str:
        """处理matplotlib的show()调用"""
        matplotlib_wrapper = '''
import matplotlib.pyplot as plt
import io
import base64

# 保存原始的show函数
_original_show = plt.show if hasattr(plt, 'show') else None

def _capture_plot():
    """捕获图形为base64字符串"""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return f"![plot](data:image/png;base64,{img_base64})"

# 替换show函数
if _original_show:
    def new_show(*args, **kwargs):
        try:
            plot_data = _capture_plot()
            print(plot_data)
        except Exception as e:
            print(f"Error displaying plot: {e}")
            if _original_show:
                _original_show(*args, **kwargs)
    
    plt.show = new_show

'''
        
        # 在代码开头插入matplotlib处理
        if "import matplotlib" in code or "from matplotlib" in code:
            lines = code.split('\n')
            import_index = -1
            
            # 找到matplotlib导入的位置
            for i, line in enumerate(lines):
                if "import matplotlib" in line or "from matplotlib" in line:
                    import_index = i + 1
                    break
            
            if import_index > 0:
                lines.insert(import_index, matplotlib_wrapper.strip())
                return '\n'.join(lines)
        
        return code
    
    def _handle_input(self, code: str) -> str:
        """处理input()函数调用"""
        input_replacement = '''
# 重定向input函数
import sys
from io import StringIO

class MockInput:
    def __init__(self):
        self.input_data = sys.argv[1] if len(sys.argv) > 1 else ""
        self.input_lines = self.input_data.split('\n') if self.input_data else []
        self.current_line = 0
    
    def __call__(self, prompt=""):
        if self.current_line < len(self.input_lines):
            line = self.input_lines[self.current_line]
            self.current_line += 1
            return line
        return ""

# 替换input函数
sys.modules['builtins'].input = MockInput()

'''
        
        if "input(" in code:
            lines = code.split('\n')
            lines.insert(0, input_replacement.strip())
            return '\n'.join(lines)
        
        return code
    
    def get_command(self, filename: str) -> List[str]:
        """获取Python执行命令"""
        return ["python3", filename]
    
    def execute(self, code: str, timeout: int, memory_limit: int,
                input_data: str = "", env_vars: Dict[str, str] = None) -> ExecutionResult:
        """执行Python代码"""
        
        # 预处理代码
        processed_code = self.preprocess_code(code)
        
        # 创建临时Python文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            dir=self.process_manager.work_dir,
            delete=False
        ) as f:
            f.write(processed_code)
            temp_filename = f.name
        
        try:
            # 设置环境变量
            if env_vars is None:
                env_vars = {}
            
            # 添加输入数据作为命令行参数
            if input_data:
                env_vars['PYTHON_INPUT'] = input_data
            
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