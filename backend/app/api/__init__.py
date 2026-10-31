from fastapi import APIRouter

from app.api import ai, analytics, auth, cv, ml, network, notifications, profile, projects

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(projects.router)
api_router.include_router(network.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(ai.router)
api_router.include_router(cv.router)
api_router.include_router(ml.router)
