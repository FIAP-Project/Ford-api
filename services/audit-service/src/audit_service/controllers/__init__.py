from audit_service.controllers.audit_controller import router as audit_router
from audit_service.controllers.health_controller import router as health_router

__all__ = ["audit_router", "health_router"]
