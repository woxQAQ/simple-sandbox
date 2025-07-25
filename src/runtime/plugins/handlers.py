import re
from typing import List
from .base import LibraryHandler, ProcessingContext


class MatplotlibHandler(LibraryHandler):
    """Matplotlib图形输出处理器"""
    
    def __init__(self):
        super().__init__("matplotlib", priority=90)
    
    def detect(self, code: str) -> bool:
        """检测是否包含matplotlib"""
        matplotlib_patterns = [
            r"import\s+matplotlib",
            r"from\s+matplotlib\s+import",
            r"import\s+matplotlib\.pyplot\s+as\s+plt",
            r"from\s+matplotlib\.pyplot\s+import"
        ]
        return any(re.search(pattern, code) for pattern in matplotlib_patterns)
    
    def process(self, code: str, context: ProcessingContext) -> str:
        """处理matplotlib图形输出"""
        wrapper = '''
import matplotlib.pyplot as plt
import io
import base64

# 保存原始的show函数
_original_show = plt.show if hasattr(plt, 'show') else None

def _capture_plot():
    """捕获图形为base64字符串"""
    try:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
        return f"![plot](data:image/png;base64,{img_base64})"
    except Exception as e:
        return f"Error capturing plot: {e}"

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
        return wrapper + code


class InputHandler(LibraryHandler):
    """输入处理处理器"""
    
    def __init__(self):
        super().__init__("input", priority=100)
    
    def detect(self, code: str) -> bool:
        """检测是否包含input()调用"""
        return "input(" in code
    
    def process(self, code: str, context: ProcessingContext) -> str:
        """处理input()函数调用"""
        wrapper = f'''
import sys
from io import StringIO

class MockInput:
    def __init__(self):
        self.input_data = """{context.input_data}"""
        self.input_lines = self.input_data.splitlines() if self.input_data else []
        self.current_line = 0
    
    def __call__(self, prompt=""):
        if self.current_line < len(self.input_lines):
            line = self.input_lines[self.current_line]
            self.current_line += 1
            return line
        return ""

# 替换input函数
import builtins
builtins.input = MockInput()

'''
        return wrapper + code


class PandasHandler(LibraryHandler):
    """Pandas DataFrame显示处理器"""
    
    def __init__(self):
        super().__init__("pandas", priority=80)
    
    def detect(self, code: str) -> bool:
        """检测是否包含pandas"""
        pandas_patterns = [
            r"import\s+pandas",
            r"from\s+pandas\s+import",
            r"import\s+pandas\s+as\s+pd",
            r"from\s+pandas\s+import.*DataFrame"
        ]
        return any(re.search(pattern, code) for pattern in pandas_patterns)
    
    def process(self, code: str, context: ProcessingContext) -> str:
        """处理pandas DataFrame显示"""
        wrapper = '''
import pandas as pd

# 保存原始的display函数
_original_display = None
if hasattr(pd, 'DataFrame'):
    _original_display = pd.DataFrame.to_string if hasattr(pd.DataFrame, 'to_string') else None

def _enhanced_display(self, *args, **kwargs):
    """增强的DataFrame显示"""
    try:
        result = _original_display(self, *args, **kwargs) if _original_display else str(self)
        print(result)
        return result
    except Exception as e:
        print(f"Error displaying DataFrame: {e}")
        return str(self)

# 应用到DataFrame
if hasattr(pd, 'DataFrame'):
    pd.DataFrame.__str__ = _enhanced_display
    pd.DataFrame.__repr__ = _enhanced_display

'''
        return wrapper + code


class SeabornHandler(LibraryHandler):
    """Seaborn图形处理器"""
    
    def __init__(self):
        super().__init__("seaborn", priority=85)
    
    def detect(self, code: str) -> bool:
        """检测是否包含seaborn"""
        seaborn_patterns = [
            r"import\s+seaborn",
            r"from\s+seaborn\s+import",
            r"import\s+seaborn\s+as\s+sns"
        ]
        return any(re.search(pattern, code) for pattern in seaborn_patterns)
    
    def process(self, code: str, context: ProcessingContext) -> str:
        """处理seaborn图形输出"""
        wrapper = '''
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64

# 保存原始绘图函数
_original_show = plt.show if hasattr(plt, 'show') else None

def _capture_seaborn_plot():
    """捕获seaborn图形"""
    try:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
        return f"![seaborn_plot](data:image/png;base64,{img_base64})"
    except Exception as e:
        return f"Error capturing seaborn plot: {e}"

# 替换show函数
if _original_show:
    def new_show(*args, **kwargs):
        try:
            plot_data = _capture_seaborn_plot()
            print(plot_data)
        except Exception as e:
            print(f"Error displaying plot: {e}")
            if _original_show:
                _original_show(*args, **kwargs)
    
    plt.show = new_show

'''
        return wrapper + code


class NumpyHandler(LibraryHandler):
    """Numpy数组显示处理器"""
    
    def __init__(self):
        super().__init__("numpy", priority=70)
    
    def detect(self, code: str) -> bool:
        """检测是否包含numpy"""
        numpy_patterns = [
            r"import\s+numpy",
            r"from\s+numpy\s+import",
            r"import\s+numpy\s+as\s+np"
        ]
        return any(re.search(pattern, code) for pattern in numpy_patterns)
    
    def process(self, code: str, context: ProcessingContext) -> str:
        """处理numpy数组显示"""
        wrapper = '''
import numpy as np

# 增强数组显示
_original_array_str = np.array_str if hasattr(np, 'array_str') else None

def _enhanced_array_display(arr):
    """增强的数组显示"""
    try:
        if arr.ndim == 2 and arr.shape[0] <= 10 and arr.shape[1] <= 10:
            return str(arr)
        elif arr.ndim == 1 and len(arr) <= 20:
            return str(arr)
        else:
            return f"Array(shape={arr.shape}, dtype={arr.dtype})"
    except Exception:
        return str(arr)

# 应用到数组显示
if hasattr(np, 'ndarray'):
    np.set_printoptions(edgeitems=3, infstr='inf', linewidth=75, nanstr='nan', precision=8, suppress=False, threshold=1000, formatter=None)

'''
        return wrapper + code