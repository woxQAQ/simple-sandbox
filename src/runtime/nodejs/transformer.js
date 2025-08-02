/**
 * Node.js AST转换器 - 使用acorn解析
 * 分离AST解析和插件扩展逻辑
 */

import { parse } from 'acorn';
import ConsolePlugin from './plugins/console_plugin.js';
import ImportPlugin from './plugins/import_plugin.js';
import ProcessPlugin from './plugins/process_plugin.js';
/**
 * 获取所有可用的插件
 * @returns {Array} - 插件列表
 */
function getPlugins() {
    return [
        new ConsolePlugin(),
        new ImportPlugin(),
        new ProcessPlugin()
    ];
}
/**
 * 应用插件到AST
 * @param {Object} ast - 解析后的AST
 * @param {Array} plugins - 插件列表
 * @returns {string} - 生成的增强代码
 */
function applyPlugins(ast, plugins) {
    let enhancementCode = '';

    // 按优先级排序
    const sortedPlugins = plugins.sort((a, b) => b.priority - a.priority);

    for (const plugin of sortedPlugins) {
        if (plugin.shouldTransform && plugin.shouldTransform(ast)) {
            enhancementCode += plugin.generateEnhancementCode();
        }
    }

    return enhancementCode;
}
/**
 * 主转换函数
 * @param {string} sourceCode - 源代码
 * @param {Object} options - 转换选项
 * @returns {string} - 转换后的代码
 */
function transformCode(sourceCode, options = {}) {
    try {
        // 解析AST
        const ast = parse(sourceCode, {
            ecmaVersion: 2022,
            sourceType: 'module',
            allowImportExportEverywhere: true,
            allowReturnOutsideFunction: true
        });

        // 获取所有插件
        const plugins = getPlugins();

        // 应用插件生成增强代码
        const enhancementCode = applyPlugins(ast, plugins);

        return enhancementCode + sourceCode;
    } catch (error) {
        console.error('AST转换错误:', error.message);
        return sourceCode;
    }
}

/**
 * 命令行接口
 */
if (import.meta.url === `file://${process.argv[1]}`) {
    const input = JSON.parse(await new Promise((resolve) => {
        let data = '';
        process.stdin.on('data', (chunk) => {
            data += chunk;
        });
        process.stdin.on('end', () => {
            resolve(data);
        });
    }));

    const result = transformCode(input.code, input.options || {});

    console.log(JSON.stringify({
        success: true,
        transformed: result,
        original: input.code
    }));
}

export default { transformCode };
