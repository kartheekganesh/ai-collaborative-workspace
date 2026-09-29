from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.websocket import manager
from app.core.database import get_db
from app.core.security import decode_access_token

router = APIRouter()

@router.websocket("/ws/documents/{document_id}")
async def websocket_document_endpoint(
    websocket: WebSocket,
    document_id: str,
    token: str = Query(...)
):
    # 1. Authenticate JWT token passed in query parameters
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001)  # Unauthorized
        return

    user_id = payload.get("sub")
    
    # 2. Accept connection & join room
    await manager.connect(document_id, websocket)
    
    # Notify room members that a user joined
    await manager.broadcast(
        document_id, 
        {"type": "user_joined", "user_id": user_id}, 
        sender=websocket
    )

    try:
        while True:
            # Receive incoming text/JSON frames from client
            data = await websocket.receive_json()
            event_type = data.get("type")

            if event_type == "content_change":
                # Broadcast delta/content updates to all room subscribers
                await manager.broadcast(
                    document_id,
                    {
                        "type": "content_change",
                        "content": data.get("content"),
                        "user_id": user_id
                    },
                    sender=websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(document_id, websocket)
        await manager.broadcast(
            document_id, 
            {"type": "user_left", "user_id": user_id}
        )