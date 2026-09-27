from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.database.database import init_db
from app.services.scheduler_service import SchedulerService
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Initializing database schema...")
    init_db()
    logger.info("Starting background scheduler...")
    SchedulerService.start()
    logger.info(f"YouTube AI Agent ready on {settings.HOST}:{settings.PORT}")
    yield
    # Shutdown
    logger.info("Shutting down background scheduler...")
    SchedulerService.stop()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="YouTube AI Upload Agent API",
    description="Automated AI-powered pipeline from Google Drive to YouTube with Ollama metadata generation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "service": "YouTube AI Upload Agent",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
