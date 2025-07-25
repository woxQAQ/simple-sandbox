import re
from typing import Dict, Any
from .base import CodeTransformer, TransformationContext


class NodeJSConsoleTransformer(CodeTransformer):
    """Node.js console输出转换器"""
    
    def __init__(self):
        super().__init__("console", priority=90)
    
    def detect(self, code: str, context: TransformationContext) -> bool:
        console_patterns = [
            r"console\.log",
            r"console\.error",
            r"console\.warn",
            r"console\.info",
            r"console\.debug"
        ]
        return any(re.search(pattern, code) for pattern in console_patterns)
    
    def transform(self, code: str, context: TransformationContext) -> str:
        wrapper = '''
// 增强的console输出
const originalLog = console.log;
const originalError = console.error;
const originalWarn = console.warn;
const originalInfo = console.info;
const originalDebug = console.debug;

// 格式化输出
console.log = function(...args) {
    const formatted = args.map(arg => {
        if (typeof arg === 'object') {
            try {
                return JSON.stringify(arg, null, 2);
            } catch (e) {
                return String(arg);
            }
        }
        return String(arg);
    }).join(' ');
    originalLog.call(console, formatted);
};

console.error = function(...args) {
    const formatted = args.map(arg => {
        if (typeof arg === 'object') {
            try {
                return JSON.stringify(arg, null, 2);
            } catch (e) {
                return String(arg);
            }
        }
        return String(arg);
    }).join(' ');
    originalError.call(console, formatted);
};

'''
        return wrapper + code

