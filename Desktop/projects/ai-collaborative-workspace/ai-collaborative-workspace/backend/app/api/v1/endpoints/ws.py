import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.websocket import manager
from app.core.security import decode_access_token
from app.models.workspace import Document, WorkspaceMember

router = APIRouter()


@router.websocket("/ws/documents/{document_id}")
async def websocket_document_endpoint(
    websocket: WebSocket, document_id: uuid.UUID, token: str = Query(...)
):
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, TypeError, ValueError):
        await websocket.close(code=4001)
        return

    async with SessionLocal() as db:
        result = await db.execute(
            select(WorkspaceMember.id)
            .join(Document, Document.workspace_id == WorkspaceMember.workspace_id)
            .where(
                Document.id == document_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            await websocket.close(code=4003)
            return

    # Assign a unique internal ID to this connection
    websocket.socket_id = str(uuid.uuid4())
    user_email = payload.get("email", "Collaborator")
    document_room = str(document_id)

    await manager.connect(document_room, websocket)

    try:
        await manager.publish_to_channel(
            document_room,
            {
                "type": "user_joined",
                "user_id": user_id,
                "email": user_email,
                "socket_id": websocket.socket_id,
            },
        )

        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict) or data.get("type") not in {
                "content_change",
                "cursor_move",
            }:
                await websocket.send_json({"type": "error", "message": "Invalid message"})
                continue
            data["user_id"] = user_id
            data["socket_id"] = websocket.socket_id

            # Route all incoming socket messages to Redis Pub/Sub
            await manager.publish_to_channel(document_room, data)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(document_room, websocket)
        await manager.publish_to_channel(
            document_room,
            {
                "type": "user_left",
                "user_id": user_id,
                "email": user_email,
                "socket_id": websocket.socket_id,
            },
        )
