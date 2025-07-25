from src.runtime.plugins.base import LibraryHandler, ProcessingContext
from src.runtime.plugins.manager import PluginManager
from src.runtime.plugins.handlers import (
    MatplotlibHandler, 
    InputHandler, 
    PandasHandler
)


class TestPluginSystem:
    """测试插件系统"""
    
    def setup_method(self):
        self.manager = PluginManager()
    
    def test_matplotlib_handler_detection(self):
        """测试Matplotlib处理器检测"""
        handler = MatplotlibHandler()
        
        # 应该检测到的代码
        assert handler.detect("import matplotlib.pyplot as plt")
        assert handler.detect("from matplotlib import pyplot")
        assert handler.detect("import matplotlib.pyplot")
        
        # 不应该检测到的代码
        assert not handler.detect("import numpy as np")
        assert not handler.detect("print('hello')")
    
    def test_input_handler_detection(self):
        """测试Input处理器检测"""
        handler = InputHandler()
        
        # 应该检测到的代码
        assert handler.detect("name = input('Enter name: ')")
        assert handler.detect("age = int(input('Age: '))")
        
        # 不应该检测到的代码
        assert not handler.detect("print('hello')")
        assert not handler.detect("import input")
    
    def test_pandas_handler_detection(self):
        """测试Pandas处理器检测"""
        handler = PandasHandler()
        
        # 应该检测到的代码
        assert handler.detect("import pandas as pd")
        assert handler.detect("from pandas import DataFrame")
        
        # 不应该检测到的代码
        assert not handler.detect("import numpy as np")
    
    def test_processor_ordering(self):
        """测试处理器优先级排序"""
        processor = self.manager.processor
        
        # 注册不同优先级的处理器
        low_priority = LibraryHandler("low", priority=50)
        high_priority = LibraryHandler("high", priority=90)
        medium_priority = LibraryHandler("medium", priority=70)
        
        processor.register_handler(low_priority)
        processor.register_handler(high_priority)
        processor.register_handler(medium_priority)
        
        # 检查排序结果
        handlers = processor._sorted_handlers
        assert handlers[0].name == "high"
        assert handlers[1].name == "medium"
        assert handlers[2].name == "low"
    
    def test_code_processing(self):
        """测试代码处理"""
        code = '''
import matplotlib.pyplot as plt
import numpy as np

x = np.array([1, 2, 3, 4, 5])
y = x ** 2

plt.plot(x, y)
plt.show()
print("Plot generated")
'''
        
        context = ProcessingContext("python")
        processed_code = self.manager.processor.process_code(code, context)
        
        # 检查是否包含处理后的代码
        assert "_capture_plot" in processed_code
        assert "plt.show = new_show" in processed_code
        assert "import matplotlib.pyplot as plt" in processed_code
    
    def test_custom_handler_registration(self):
        """测试自定义处理器注册"""
        
        class CustomHandler(LibraryHandler):
            def __init__(self):
                super().__init__("custom", priority=75)
            
            def detect(self, code: str) -> bool:
                return "custom_lib" in code
            
            def process(self, code: str, context: ProcessingContext) -> str:
                return f"# Custom processing\n{code}"
        
        custom_handler = CustomHandler()
        self.manager.register_custom_handler(custom_handler)
        
        code = "import custom_lib\nprint('test')"
        processed_code = self.manager.processor.process_code(code, ProcessingContext("python"))
        
        assert "# Custom processing" in processed_code
    
    def test_handler_config(self):
        """测试处理器配置"""
        handler = MatplotlibHandler()
        config = handler.get_config()
        
        assert config["name"] == "matplotlib"
        assert config["priority"] == 90
    
    def test_multiple_handlers(self):
        """测试多个处理器同时工作"""
        code = '''
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

name = input("Enter name: ")
df = pd.DataFrame({'x': [1,2,3], 'y': [4,5,6]})
plt.plot(df['x'], df['y'])
plt.show()
print(name)
'''
        
        context = ProcessingContext("python", input_data="Alice")
        processed_code = self.manager.processor.process_code(code, context)
        
        # 检查所有处理器都生效了
        assert "MockInput" in processed_code  # InputHandler
        assert "_capture_plot" in processed_code  # MatplotlibHandler
        assert "enhanced_display" in processed_code  # PandasHandler
    
    def test_handler_deregistration(self):
        """测试处理器注销"""
        initial_count = len(self.manager.processor.handlers)
        
        # 注销处理器
        self.manager.unregister_handler("matplotlib")
        
        # 检查处理器是否被移除
        assert "matplotlib" not in self.manager.processor.handlers
        assert len(self.manager.processor.handlers) == initial_count - 1
    
    def test_empty_code(self):
        """测试空代码处理"""
        code = ""
        context = ProcessingContext("python")
        processed_code = self.manager.processor.process_code(code, context)
        
        assert processed_code == ""
    
    def test_no_matching_handlers(self):
        """测试没有匹配处理器的情况"""
        code = "print('hello world')"
        context = ProcessingContext("python")
        processed_code = self.manager.processor.process_code(code, context)
        
        assert processed_code == "print('hello world')"