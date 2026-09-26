import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user, check_workspace_permission
from app.models.workspace import User, Document, RoleEnum, WorkspaceMember
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["Documents"])

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    workspace_id: uuid.UUID,
    doc_in: DocumentCreate,
    current_user: User = Depends(get_current_user),
    _member: WorkspaceMember = Depends(
        check_workspace_permission([RoleEnum.ADMIN, RoleEnum.EDITOR])
    ),
    db: AsyncSession = Depends(get_db)
):
    new_doc = Document(
        workspace_id=workspace_id,
        title=doc_in.title,
        content=doc_in.content or "",
        created_by=current_user.id
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    return new_doc

@router.get("", response_model=List[DocumentResponse])
async def list_workspace_documents(
    workspace_id: uuid.UUID,
    _member: WorkspaceMember = Depends(
        check_workspace_permission([RoleEnum.ADMIN, RoleEnum.EDITOR, RoleEnum.VIEWER])
    ),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document).where(Document.workspace_id == workspace_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    _member: WorkspaceMember = Depends(
        check_workspace_permission([RoleEnum.ADMIN, RoleEnum.EDITOR, RoleEnum.VIEWER])
    ),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document).where(
        Document.id == document_id,
        Document.workspace_id == workspace_id
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    doc_in: DocumentUpdate,
    _member: WorkspaceMember = Depends(
        check_workspace_permission([RoleEnum.ADMIN, RoleEnum.EDITOR])
    ),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document).where(
        Document.id == document_id,
        Document.workspace_id == workspace_id
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc_in.title is not None:
        doc.title = doc_in.title
    if doc_in.content is not None:
        doc.content = doc_in.content

    await db.commit()
    await db.refresh(doc)
    return doc