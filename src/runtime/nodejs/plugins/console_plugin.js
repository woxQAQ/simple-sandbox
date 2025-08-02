/**
 * JavaScript控制台增强插件
 * 独立的功能模块，只包含扩展逻辑
 */

class ConsolePlugin {
    constructor() {
        this.name = 'console_plugin';
        this.priority = 90;
    }

    /**
     * 检测是否应该应用此插件
     * @param {Object} ast - 解析后的AST
     * @returns {boolean} - 是否应用插件
     */
    shouldTransform(ast) {
        let hasConsole = false;

        const traverse = (node) => {
            if (!node || typeof node !== 'object') return;

            if (node.type === 'CallExpression' &&
                node.callee?.type === 'MemberExpression' &&
                node.callee.object?.name === 'console') {
                hasConsole = true;
            }

            Object.keys(node).forEach(key => {
                const value = node[key];
                if (Array.isArray(value)) {
                    value.forEach(item => traverse(item));
                } else if (value && typeof value === 'object') {
                    traverse(value);
                }
            });
        };

        traverse(ast);
        return hasConsole;
    }

    /**
     * 生成增强代码
     * @returns {string} - 增强代码
     */
    generateEnhancementCode() {
        return `// === 增强的console输出 ===
(function() {
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    const originalInfo = console.info;
    const originalDebug = console.debug;

    const timestamp = () => new Date().toISOString();

    function enhanceConsole(name, originalFn) {
        return function(...args) {
            const enhancedArgs = [\`[\${timestamp()}] [\${name.toUpperCase()}]\`, ...args];
            originalFn.call(console, ...enhancedArgs);
        };
    }

    console.log = enhanceConsole('log', originalLog);
    console.error = enhanceConsole('error', originalError);
    console.warn = enhanceConsole('warn', originalWarn);
    console.info = enhanceConsole('info', originalInfo);
    console.debug = enhanceConsole('debug', originalDebug);
})();
`;
    }
}

export default ConsolePlugin;
