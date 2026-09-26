import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user, check_workspace_permission
from app.models.workspace import User, Workspace, WorkspaceMember, RoleEnum
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Create Workspace
    new_workspace = Workspace(
        name=workspace_in.name,
        description=workspace_in.description,
        owner_id=current_user.id
    )
    db.add(new_workspace)
    await db.flush()  # Flush to populate new_workspace.id

    # 2. Automatically assign creator as ADMIN member
    membership = WorkspaceMember(
        workspace_id=new_workspace.id,
        user_id=current_user.id,
        role=RoleEnum.ADMIN
    )
    db.add(membership)
    await db.commit()
    await db.refresh(new_workspace)
    return new_workspace

@router.get("", response_model=List[WorkspaceResponse])
async def list_my_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve all workspaces where user is a member
    stmt = (
        select(Workspace)
        .join(WorkspaceMember)
        .where(WorkspaceMember.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(
        check_workspace_permission([RoleEnum.ADMIN, RoleEnum.EDITOR, RoleEnum.VIEWER])
    ),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    result = await db.execute(stmt)
    return result.scalar_one()

@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    workspace_in: WorkspaceUpdate,
    _member: WorkspaceMember = Depends(
        check_workspace_permission([RoleEnum.ADMIN])
    ),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    result = await db.execute(stmt)
    workspace = result.scalar_one()

    if workspace_in.name is not None:
        workspace.name = workspace_in.name
    if workspace_in.description is not None:
        workspace.description = workspace_in.description

    await db.commit()
    await db.refresh(workspace)
    return workspace