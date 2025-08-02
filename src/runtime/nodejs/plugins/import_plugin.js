/**
 * JavaScript导入增强插件
 * 独立的功能模块，只包含扩展逻辑
 */

class ImportPlugin {
    constructor() {
        this.name = 'import_plugin';
        this.priority = 85;
    }

    /**
     * 检测是否应该应用此插件
     * @param {Object} ast - 解析后的AST
     * @returns {boolean} - 是否应用插件
     */
    shouldTransform(ast) {
        let hasImport = false;

        const traverse = (node) => {
            if (!node || typeof node !== 'object') return;

            if (node.type === 'ImportDeclaration' ||
                (node.type === 'CallExpression' &&
                    node.callee?.name === 'require')) {
                hasImport = true;
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
        return hasImport;
    }

    /**
     * 生成增强代码
     * @returns {string} - 增强代码
     */
    generateEnhancementCode() {
        return `// === 增强的模块加载日志和安全检查 ===
const originalRequire = typeof require !== 'undefined' ? require : null;
if (originalRequire) {
    require = function(id) {
        const start = Date.now();
        const module = originalRequire(id);
        const duration = Date.now() - start;
        console.log(\`[\${new Date().toISOString()}] Loaded module: \${id} (\${duration}ms)\`);

        // 危险模块警告
        const dangerousModules = ["fs", "child_process", "cluster", "worker_threads"];
        if (dangerousModules.includes(id)) {
            console.warn(\`Warning: Module '\${id}' is restricted in sandbox environment\`);
        }

        return module;
    };
}
`;
    }
}

export default ImportPlugin;
