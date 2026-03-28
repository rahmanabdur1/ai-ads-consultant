# backend/api/workspace.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.database import get_db, Workspace, Campaign, User
from core.dependencies import get_current_user

router = APIRouter()

class WorkspaceUpdate(BaseModel):
    name: str

@router.get("/")
def get_my_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspaces = db.query(Workspace).filter(Workspace.owner_id == current_user.id).all()
    return [
        {
            "id": str(w.id),
            "name": w.name,
            "campaign_count": db.query(Campaign).filter(Campaign.workspace_id == w.id).count()
        }
        for w in workspaces
    ]

@router.get("/{workspace_id}")
def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ws = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"id": str(ws.id), "name": ws.name}

@router.patch("/{workspace_id}")
def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ws = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    ws.name = data.name
    db.commit()
    return {"id": str(ws.id), "name": ws.name}

# Add to main.py:
# from api.workspace import router as workspace_router
# app.include_router(workspace_router, prefix="/workspace", tags=["Workspace"])