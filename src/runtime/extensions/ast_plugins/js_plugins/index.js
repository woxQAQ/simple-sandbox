/**
 * JavaScript插件注册和导出
 */

const ConsoleEnhancer = require('./console_plugin');
const ImportEnhancer = require('./import_plugin');

/**
 * 获取所有可用的插件
 * @returns {Array} - 插件列表
 */
function getPlugins() {
    return [
        new ConsoleEnhancer(),
        new ImportEnhancer()
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

module.exports = {
    getPlugins,
    applyPlugins,
    ConsoleEnhancer,
    ImportEnhancer
};