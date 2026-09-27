import webbrowser
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.database.database import init_db, SessionLocal
from app.database.repository import Repository
from app.services.google_auth_service import GoogleAuthService
from app.services.drive_service import DriveService
from app.services.youtube_service import YouTubeService
from app.services.ai_service import AIService
from app.services.agent_service import AgentService
from app.services.scheduler_service import SchedulerService

app = typer.Typer(
    help="YouTube AI Upload Agent CLI - Autonomous Google Drive to YouTube Pipeline",
    no_args_is_help=True,
)
import sys
console = Console(safe_box=True)


def _ensure_initialized():
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    setup_logging()
    init_db()


@app.command("status")
def status_command():
    """Display real-time connection status, catalog statistics, and agent state."""
    _ensure_initialized()
    with SessionLocal() as db:
        repo = Repository(db)
        auth_service = GoogleAuthService(db)
        ai_service = AIService(db)
        
        auth_status = auth_service.get_auth_status()
        ai_health = ai_service.check_health()
        settings_record = repo.get_settings()
        selected_folder = repo.get_selected_folder()

        google_text = (
            f"[bold green]CONNECTED[/bold green] ({auth_status['email']})"
            if auth_status["is_authenticated"]
            else "[bold red]NOT CONNECTED[/bold red]"
        )

        drive_text = (
            f"[bold green]CONNECTED[/bold green] (Folder: '{selected_folder.folder_name}')"
            if selected_folder and auth_status["has_drive_scope"]
            else "[bold yellow]NOT CONFIGURED[/bold yellow]"
        )

        yt_title = None
        if auth_status["has_youtube_scope"]:
            try:
                yt_service = YouTubeService(db)
                yt_info = yt_service.get_channel_info()
                yt_title = yt_info.get("title")
            except Exception:
                yt_title = "Connected"

        youtube_text = (
            f"[bold green]CONNECTED[/bold green] ({yt_title})"
            if yt_title
            else "[bold red]NOT CONNECTED[/bold red]"
        )

        ollama_text = (
            f"[bold green]CONNECTED[/bold green] (Model: {ai_health['current_model']})"
            if ai_health["connected"]
            else f"[bold yellow]DISCONNECTED[/bold yellow] ({ai_health['base_url']})"
        )

        agent_text = (
            f"[bold green]RUNNING[/bold green] (Every {settings_record.interval_minutes}m)"
            if settings_record.enabled
            else "[bold red]STOPPED / PAUSED[/bold red]"
        )

        stats = repo.get_video_stats(selected_folder.folder_id if selected_folder else None)

        content = (
            f"[bold cyan]YouTube AI Agent[/bold cyan]\n"
            f"====================================\n"
            f"Google:    {google_text}\n"
            f"Drive:     {drive_text}\n"
            f"YouTube:   {youtube_text}\n"
            f"Ollama:    {ollama_text}\n"
            f"Agent:     {agent_text}\n"
            f"------------------------------------\n"
            f"Total Videos:     [bold]{stats['total']}[/bold]\n"
            f"Uploaded Videos:  [bold green]{stats['uploaded']}[/bold green]\n"
            f"Remaining Videos: [bold yellow]{stats['remaining']}[/bold yellow]\n"
            f"Failed:           [bold red]{stats['failed']}[/bold red]\n"
        )
        console.print(Panel(content, title="YouTube AI Upload Agent Status", border_style="cyan"))


@app.command("authenticate")
def authenticate_command():
    """Initiate Google OAuth 2.0 flow to link Google Drive & YouTube accounts."""
    _ensure_initialized()
    with SessionLocal() as db:
        service = GoogleAuthService(db)
        try:
            auth_url = service.get_authorization_url()
            console.print("[bold yellow]Opening browser for Google OAuth 2.0 authentication...[/bold yellow]")
            console.print(f"URL: {auth_url}\n")
            webbrowser.open(auth_url)

            code = typer.prompt("Paste the authorization code from the callback URL (or run via dashboard)")
            if code:
                user, _ = service.handle_auth_callback(code.strip())
                console.print(f"[bold green]Successfully authenticated user: {user.email}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Authentication failed: {e}[/bold red]")


@app.command("list-videos")
def list_videos_command(limit: int = 50):
    """List videos in database catalog and their current status."""
    _ensure_initialized()
    with SessionLocal() as db:
        repo = Repository(db)
        total, videos = repo.list_videos(limit=limit)

        table = Table(title=f"Video Catalog (Total: {total})", border_style="blue")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Filename", style="bold")
        table.add_column("Size", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Drive File ID", style="dim")

        for v in videos:
            status_style = "green" if v.status == "uploaded" else "yellow" if v.status == "available" else "red"
            size_mb = f"{v.size / (1024*1024):.1f} MB" if v.size else "0 MB"
            table.add_row(
                str(v.id),
                v.file_name,
                size_mb,
                f"[{status_style}]{v.status}[/{status_style}]",
                v.drive_file_id,
            )

        console.print(table)


@app.command("upload-now")
def upload_now_command():
    """Trigger an immediate autonomous upload run."""
    _ensure_initialized()
    console.print("[bold cyan]Triggering immediate YouTube upload agent run...[/bold cyan]")
    with SessionLocal() as db:
        agent = AgentService(db)
        result = agent.run_upload_agent(force_run=True)

        if result.get("success"):
            console.print(f"[bold green]SUCCESS![/bold green] {result.get('message')}")
            console.print(f"YouTube Video ID: [bold underline blue]{result.get('youtube_video_id')}[/bold underline blue]")
            console.print(f"Title: {result.get('title')}")
            console.print(f"Privacy: {result.get('status')}")
        else:
            console.print(f"[bold red]FAILED:[/bold red] {result.get('message')}")
            if result.get("error"):
                console.print(f"Error detail: {result.get('error')}")


@app.command("start-agent")
def start_agent_command():
    """Activate automatic scheduled background uploads."""
    _ensure_initialized()
    with SessionLocal() as db:
        repo = Repository(db)
        settings_record = repo.update_settings(enabled=True)
        console.print(
            f"[bold green]Agent scheduled activated! Upload interval: every {settings_record.interval_minutes} minutes.[/bold green]"
        )


@app.command("stop-agent")
def stop_agent_command():
    """Pause automatic scheduled uploads."""
    _ensure_initialized()
    with SessionLocal() as db:
        repo = Repository(db)
        repo.update_settings(enabled=False)
        console.print("[bold yellow]Agent scheduled runs paused.[/bold yellow]")


@app.command("history")
def history_command(limit: int = 50):
    """View upload history with YouTube video links and timestamps."""
    _ensure_initialized()
    with SessionLocal() as db:
        repo = Repository(db)
        total, uploads = repo.list_uploads(limit=limit)

        table = Table(title=f"Upload History (Total: {total})", border_style="green")
        table.add_column("ID", width=5)
        table.add_column("YouTube Video ID", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Uploaded At", style="dim")

        for u in uploads:
            status_style = "green" if u.status == "uploaded" else "red"
            time_str = u.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if u.uploaded_at else str(u.created_at)
            table.add_row(
                str(u.id),
                u.youtube_video_id or "N/A",
                u.title[:45] + ("..." if len(u.title) > 45 else ""),
                f"[{status_style}]{u.status}[/{status_style}]",
                time_str,
            )

        console.print(table)


if __name__ == "__main__":
    app()
