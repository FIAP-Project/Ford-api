from auth_service.controllers.auth_controller import router as auth_router
from auth_service.controllers.health_controller import router as health_router

__all__ = ["auth_router", "health_router"]
