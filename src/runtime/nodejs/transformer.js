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
    // 检查是否有测试参数
    const isTestMode = process.argv.includes('--test') || process.argv.includes('-t');

    if (isTestMode) {
        // 测试模式 - 运行一个简单的测试
        const testCode = 'console.log("Hello from Node.js transformer!");';
        const result = transformCode(testCode, {});

        console.log(JSON.stringify({
            success: true,
            transformed: result,
            original: testCode
        }));
        process.exit(0);
    }

    // 管道输入模式 - 默认行为
    try {
        const input = JSON.parse(await new Promise((resolve, reject) => {
            let data = '';
            let timeout = setTimeout(() => {
                reject(new Error('输入超时 - 请通过管道提供JSON数据'));
            }, 100); // 100ms超时检测是否有输入

            process.stdin.on('data', (chunk) => {
                clearTimeout(timeout);
                data += chunk;
            });

            process.stdin.on('end', () => {
                clearTimeout(timeout);
                resolve(data);
            });

            // 如果是TTY且没有数据，立即拒绝
            if (process.stdin.isTTY) {
                clearTimeout(timeout);
                reject(new Error('交互式模式 - 请使用 --test 参数运行测试或通过管道提供输入'));
            }
        }));

        const result = transformCode(input.code, input.options || {});

        console.log(JSON.stringify({
            success: true,
            transformed: result,
            original: input.code
        }));
    } catch (error) {
        console.error(JSON.stringify({
            success: false,
            error: error.message,
            usage: '使用方法: 1. 通过管道输入: echo \'{"code": "console.log(\\"Hello\\");"}\' | node transformer.js'
                + ' 2. 测试模式: node transformer.js --test'
        }));
        process.exit(1);
    }
}

export default { transformCode };
