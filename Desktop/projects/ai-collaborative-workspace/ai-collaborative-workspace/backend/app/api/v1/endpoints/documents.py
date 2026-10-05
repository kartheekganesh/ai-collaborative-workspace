import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache

from app.api.deps import check_workspace_permission, get_current_user
from app.core.database import get_db
from app.models.workspace import (
    Document,
    RoleEnum,
    User,
    WorkspaceMember,
)
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.tasks.ai_tasks import embed_and_store_document


router = APIRouter(
    prefix="/workspaces/{workspace_id}/documents",
    tags=["Documents"],
)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    workspace_id: uuid.UUID,
    doc_in: DocumentCreate,
    current_user: User = Depends(get_current_user),
    _member: WorkspaceMember = Depends(
        check_workspace_permission([RoleEnum.ADMIN, RoleEnum.EDITOR])
    ),
    db: AsyncSession = Depends(get_db),
):
    document = Document(
        workspace_id=workspace_id,
        title=doc_in.title,
        content=doc_in.content or "",
        created_by=current_user.id,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    if document.content:
        embed_and_store_document.delay(str(document.id), document.content)
    return document


@router.get("", response_model=List[DocumentResponse])
@cache(expire=60)
async def list_workspace_documents(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(
        check_workspace_permission(
            [RoleEnum.ADMIN, RoleEnum.EDITOR, RoleEnum.VIEWER]
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.workspace_id == workspace_id)
    )
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
@cache(expire=120)
async def get_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    _member: WorkspaceMember = Depends(
        check_workspace_permission(
            [RoleEnum.ADMIN, RoleEnum.EDITOR, RoleEnum.VIEWER]
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    doc_in: DocumentUpdate,
    _member: WorkspaceMember = Depends(
        check_workspace_permission([RoleEnum.ADMIN, RoleEnum.EDITOR])
    ),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc_in.title is not None:
        document.title = doc_in.title
    if doc_in.content is not None:
        document.content = doc_in.content

    await db.commit()
    await db.refresh(document)
    if doc_in.content is not None:
        embed_and_store_document.delay(str(document.id), document.content or "")
    return document