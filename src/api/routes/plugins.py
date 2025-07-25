from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ...runtime.plugins.manager import plugin_manager
from ...runtime.plugins.base import LibraryHandler

router = APIRouter(prefix="/api/v1", tags=["plugins"])


@router.get("/plugins")
async def get_plugins():
    """获取所有可用的插件处理器"""
    return {
        "plugins": plugin_manager.get_available_handlers()
    }


@router.post("/plugins/register")
async def register_plugin(plugin_info: Dict[str, Any]):
    """注册自定义插件处理器（仅支持内置处理器）"""
    # 这里可以扩展支持动态加载处理器
    return {
        "message": "Plugin registration endpoint available for future extension",
        "current_plugins": plugin_manager.get_available_handlers()
    }


@router.delete("/plugins/{plugin_name}")
async def disable_plugin(plugin_name: str):
    """禁用指定插件处理器"""
    try:
        plugin_manager.unregister_handler(plugin_name)
        return {
            "message": f"Plugin {plugin_name} disabled",
            "plugins": plugin_manager.get_available_handlers()
        }
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Plugin {plugin_name} not found"
        )


@router.post("/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """启用指定插件处理器"""
    # 这里可以扩展支持重新启用处理器
    return {
        "message": f"Plugin {plugin_name} enable endpoint available",
        "plugins": plugin_manager.get_available_handlers()
    }