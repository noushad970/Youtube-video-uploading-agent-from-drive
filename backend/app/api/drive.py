from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repository import Repository
from app.services.drive_service import DriveService
from app.schemas.video import DriveFolderSchema, SelectFolderRequest

router = APIRouter(prefix="/api/drive", tags=["Google Drive"])


@router.get("/folders", response_model=List[DriveFolderSchema])
def list_drive_folders(db: Session = Depends(get_db)):
    """List accessible folders in connected Google Drive."""
    try:
        service = DriveService(db)
        folders = service.list_drive_folders()
        repo = Repository(db)
        selected = repo.get_selected_folder()
        selected_id = selected.folder_id if selected else None

        result = []
        for f in folders:
            result.append(
                DriveFolderSchema(
                    folder_id=f["folder_id"],
                    folder_name=f["folder_name"],
                    is_selected=(f["folder_id"] == selected_id),
                )
            )
        return result
    except PermissionError as pe:
        raise HTTPException(status_code=401, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list Drive folders: {e}")


@router.get("/videos")
def list_drive_videos(
    folder_id: Optional[str] = Query(default=None, description="Drive folder ID to inspect"),
    db: Session = Depends(get_db),
):
    """List video files located directly in the specified or selected Drive folder."""
    try:
        repo = Repository(db)
        if not folder_id:
            selected = repo.get_selected_folder()
            if not selected:
                return {"videos": [], "total": 0, "message": "No folder selected."}
            folder_id = selected.folder_id

        service = DriveService(db)
        videos = service.list_videos(folder_id)
        return {"folder_id": folder_id, "total": len(videos), "videos": videos}
    except PermissionError as pe:
        raise HTTPException(status_code=401, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list Drive videos: {e}")


@router.post("/select-folder", response_model=DriveFolderSchema)
def select_drive_folder(
    req: SelectFolderRequest,
    db: Session = Depends(get_db),
):
    """Select a Drive folder for the agent to monitor and sync its video catalog."""
    try:
        service = DriveService(db)
        service.sync_folder_videos(req.folder_id, req.folder_name)
        repo = Repository(db)
        selected = repo.get_selected_folder()
        if not selected:
            raise HTTPException(status_code=404, detail="Folder selection failed")
        return selected
    except PermissionError as pe:
        raise HTTPException(status_code=401, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to select folder: {e}")
