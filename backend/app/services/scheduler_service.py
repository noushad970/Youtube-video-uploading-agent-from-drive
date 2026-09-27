import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logging_config import logger
from app.database.database import SessionLocal
from app.database.repository import Repository
from app.services.agent_service import AgentService

# Global scheduler instance and execution lock
_scheduler: Optional[BackgroundScheduler] = None
_job_lock = threading.Lock()
_is_job_active = False


def _scheduled_agent_task():
    """Wrapper invoked on recurring intervals by APScheduler."""
    global _is_job_active
    if not _job_lock.acquire(blocking=False):
        logger.warning("Another upload job is already actively running. Skipping this scheduled tick.")
        return

    _is_job_active = True
    try:
        with SessionLocal() as db:
            agent = AgentService(db)
            agent.run_upload_agent(force_run=False)
    except Exception as e:
        logger.error(f"Error in scheduled agent task: {e}")
    finally:
        _is_job_active = False
        _job_lock.release()


class SchedulerService:
    @classmethod
    def get_scheduler(cls) -> BackgroundScheduler:
        global _scheduler
        if _scheduler is None:
            _scheduler = BackgroundScheduler(daemon=True)
        return _scheduler

    @classmethod
    def start(cls) -> None:
        scheduler = cls.get_scheduler()
        if not scheduler.running:
            scheduler.start()
            logger.info("APScheduler background service started.")

        # Check DB settings to see if agent job should be enabled
        with SessionLocal() as db:
            repo = Repository(db)
            app_settings = repo.get_settings()
            if app_settings.enabled:
                cls.reschedule(app_settings.interval_minutes)

    @classmethod
    def stop(cls) -> None:
        scheduler = cls.get_scheduler()
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("APScheduler background service stopped.")

    @classmethod
    def reschedule(cls, interval_minutes: int) -> None:
        """Update or add the recurring agent job with new interval in minutes."""
        scheduler = cls.get_scheduler()
        if not scheduler.running:
            scheduler.start()

        # Remove existing agent job if present
        if scheduler.get_job("youtube_agent_run"):
            scheduler.remove_job("youtube_agent_run")

        trigger = IntervalTrigger(minutes=max(5, interval_minutes))
        scheduler.add_job(
            _scheduled_agent_task,
            trigger=trigger,
            id="youtube_agent_run",
            name="YouTube AI Agent Automatic Upload",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        logger.info(f"Agent scheduled to run every {interval_minutes} minutes.")

    @classmethod
    def pause_job(cls) -> None:
        scheduler = cls.get_scheduler()
        if scheduler.get_job("youtube_agent_run"):
            scheduler.remove_job("youtube_agent_run")
            logger.info("Agent scheduled job paused/removed.")

    @classmethod
    def trigger_manual_upload(cls) -> Dict[str, Any]:
        """Trigger an immediate agent run synchronously or with lock."""
        global _is_job_active
        if not _job_lock.acquire(blocking=False):
            return {
                "success": False,
                "message": "An upload operation is already actively running. Please wait for it to complete.",
            }

        _is_job_active = True
        try:
            with SessionLocal() as db:
                agent = AgentService(db)
                return agent.run_upload_agent(force_run=True)
        finally:
            _is_job_active = False
            _job_lock.release()

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        global _is_job_active
        scheduler = cls.get_scheduler()
        job = scheduler.get_job("youtube_agent_run") if scheduler.running else None

        next_run = None
        if job and job.next_run_time:
            next_run = job.next_run_time

        return {
            "scheduler_running": scheduler.running if scheduler else False,
            "has_active_job": job is not None,
            "is_job_currently_executing": _is_job_active,
            "next_scheduled_run": next_run,
        }
