import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from app.models.workspace import RoleEnum


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    role: RoleEnum
    joined_at: datetime


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str]
    owner_id: uuid.UUID
    created_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
