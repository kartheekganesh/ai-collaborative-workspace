import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.websocket import manager
from app.core.security import decode_access_token

router = APIRouter()

@router.websocket("/ws/documents/{document_id}")
async def websocket_document_endpoint(
    websocket: WebSocket,
    document_id: str,
    token: str = Query(...)
):
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    # Assign a unique internal ID to this connection
    websocket.socket_id = str(uuid.uuid4())
    user_id = payload.get("sub")
    user_email = payload.get("email", "Collaborator")

    await manager.connect(document_id, websocket)

    # Publish join event to Redis
    await manager.publish_to_channel(document_id, {
        "type": "user_joined",
        "user_id": user_id,
        "email": user_email,
        "socket_id": websocket.socket_id
    })

    try:
        while True:
            data = await websocket.receive_json()
            data["user_id"] = user_id
            data["socket_id"] = websocket.socket_id
            
            # Route all incoming socket messages to Redis Pub/Sub
            await manager.publish_to_channel(document_id, data)

    except WebSocketDisconnect:
        manager.disconnect(document_id, websocket)
        await manager.publish_to_channel(document_id, {
            "type": "user_left",
            "user_id": user_id,
            "email": user_email,
            "socket_id": websocket.socket_id
        })