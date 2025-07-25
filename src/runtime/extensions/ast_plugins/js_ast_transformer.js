/**
 * Node.js AST转换器 - 使用acorn解析
 * 分离AST解析和插件扩展逻辑
 */

const acorn = require('acorn');
const { getPlugins, applyPlugins } = require('./js_plugins');

/**
 * 主转换函数
 * @param {string} sourceCode - 源代码
 * @param {Object} options - 转换选项
 * @returns {string} - 转换后的代码
 */
function transformCode(sourceCode, options = {}) {
    try {
        // 解析AST
        const ast = acorn.parse(sourceCode, {
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
if (require.main === module) {
    const fs = require('fs');
    const input = JSON.parse(fs.readFileSync(0, 'utf8'));

    const result = transformCode(input.code, input.options || {});

    console.log(JSON.stringify({
        success: true,
        transformed: result,
        original: input.code
    }));
}

module.exports = { transformCode };