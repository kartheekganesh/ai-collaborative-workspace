import json
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        # Maps document_id (str) -> List of active WebSocket connections
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, document_id: str, websocket: WebSocket):
        await websocket.accept()
        if document_id not in self.active_rooms:
            self.active_rooms[document_id] = []
        self.active_rooms[document_id].append(websocket)

    def disconnect(self, document_id: str, websocket: WebSocket):
        if document_id in self.active_rooms:
            if websocket in self.active_rooms[document_id]:
                self.active_rooms[document_id].remove(websocket)
            if not self.active_rooms[document_id]:
                del self.active_rooms[document_id]

    async def broadcast(self, document_id: str, message: dict, sender: WebSocket = None):
        """Broadcast a JSON message to all clients in a document room except the sender."""
        if document_id in self.active_rooms:
            for connection in self.active_rooms[document_id]:
                if connection != sender:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        # Clean up stale connections
                        self.disconnect(document_id, connection)

# Global Manager Instance
manager = ConnectionManager()