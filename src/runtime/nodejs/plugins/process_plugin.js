/**
 * JavaScript进程控制插件
 * 处理process.exit等进程控制调用
 */

class ProcessPlugin {
    constructor() {
        this.name = 'process_plugin';
        this.priority = 80;
    }

    /**
     * 检测是否应该应用此插件
     * @param {Object} ast - 解析后的AST
     * @returns {boolean} - 是否应用插件
     */
    shouldTransform(ast) {
        let hasProcessExit = false;

        const traverse = (node) => {
            if (!node || typeof node !== 'object') return;

            if (node.type === 'CallExpression' &&
                node.callee?.type === 'MemberExpression' &&
                node.callee.object?.name === 'process' &&
                node.callee.property?.name === 'exit') {
                hasProcessExit = true;
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
        return hasProcessExit;
    }

    /**
     * 生成增强代码
     * @returns {string} - 增强代码
     */
    generateEnhancementCode() {
        return `// === 安全的进程退出处理 ===
const originalExit = process.exit;
process.exit = function(code = 0) {
    console.log(\`Process exit with code: \${code}\`);
    originalExit(code);
};
`;
    }
}

export default ProcessPlugin;
