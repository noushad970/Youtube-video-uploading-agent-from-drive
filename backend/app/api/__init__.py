from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.drive import router as drive_router
from app.api.youtube import router as youtube_router
from app.api.videos import router as videos_router
from app.api.agent import router as agent_router
from app.api.settings import router as settings_router
from app.api.uploads import router as uploads_router
from app.api.logs import router as logs_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(drive_router)
api_router.include_router(youtube_router)
api_router.include_router(videos_router)
api_router.include_router(agent_router)
api_router.include_router(settings_router)
api_router.include_router(uploads_router)
api_router.include_router(logs_router)
