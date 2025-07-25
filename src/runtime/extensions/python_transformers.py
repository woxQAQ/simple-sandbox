import re
from typing import Dict, Any
from .base import CodeTransformer, TransformationContext


class PythonMatplotlibTransformer(CodeTransformer):
    """Python matplotlib图形输出转换器"""
    
    def __init__(self):
        super().__init__("matplotlib", priority=90)
    
    def detect(self, code: str, context: TransformationContext) -> bool:
        matplotlib_patterns = [
            r"import\s+matplotlib",
            r"from\s+matplotlib\s+import",
            r"import\s+matplotlib\.pyplot\s+as\s+plt",
            r"from\s+matplotlib\.pyplot\s+import"
        ]
        return any(re.search(pattern, code) for pattern in matplotlib_patterns)
    
    def transform(self, code: str, context: TransformationContext) -> str:
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
