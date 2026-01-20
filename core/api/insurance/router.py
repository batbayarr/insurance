"""
Insurance module API router
This will contain policy, claim, and other insurance-related endpoints
"""
from ninja import Router
from .policy import router as policy_router
from .template import router as template_router

# Create main router for insurance endpoints
router = Router(tags=["Insurance"])

# Include sub-routers
router.add_router("/policy", policy_router)
router.add_router("/template", template_router)

