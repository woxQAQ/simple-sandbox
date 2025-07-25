from .execute import router as execute_router
from .health import router as health_router
from .plugins import router as plugins_router

__all__ = ["execute_router", "health_router", "plugins_router"]