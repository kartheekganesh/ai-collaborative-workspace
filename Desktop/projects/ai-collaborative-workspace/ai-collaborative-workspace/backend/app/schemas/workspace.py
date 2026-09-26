import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.workspace import RoleEnum

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class WorkspaceMemberResponse(BaseModel):
    user_id: uuid.UUID
    role: RoleEnum
    joined_at: datetime

    class Config:
        from_attributes = True

class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    owner_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True