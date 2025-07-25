/**
 * JavaScript插件注册和导出
 */

import ConsoleEnhancer from './console_plugin';
import ImportEnhancer from './import_plugin';

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

export default {
    getPlugins,
    applyPlugins,
    ConsoleEnhancer,
    ImportEnhancer
};