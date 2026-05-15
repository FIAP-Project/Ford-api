from user_service.controllers.profile_controller import router as profile_router
from user_service.controllers.health_controller import router as health_router

__all__ = ["health_router", "profile_router"]
