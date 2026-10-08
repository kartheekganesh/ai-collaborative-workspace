import json
import asyncio
import logging
from typing import Dict, List
from fastapi import WebSocket
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Maps document_id -> List of local WebSocket connections on this container instance
        self.active_rooms: Dict[str, List[WebSocket]] = {}
        # Tracks active Redis listener tasks per room
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}
        self.pubsub_ready: Dict[str, asyncio.Event] = {}

    async def connect(self, document_id: str, websocket: WebSocket):
        await websocket.accept()
        if document_id not in self.active_rooms:
            self.active_rooms[document_id] = []
            ready = asyncio.Event()
            self.pubsub_ready[document_id] = ready
            # Start listening to Redis channel for this document if room is newly created locally
            self.pubsub_tasks[document_id] = asyncio.create_task(self._listen_to_redis(document_id))
            await ready.wait()

        self.active_rooms[document_id].append(websocket)

    def disconnect(self, document_id: str, websocket: WebSocket):
        if document_id in self.active_rooms:
            if websocket in self.active_rooms[document_id]:
                self.active_rooms[document_id].remove(websocket)

            # Clean up Redis listener if no local connections remain for this room
            if not self.active_rooms[document_id]:
                del self.active_rooms[document_id]
                if document_id in self.pubsub_tasks:
                    self.pubsub_tasks[document_id].cancel()
                    del self.pubsub_tasks[document_id]

    async def publish_to_channel(self, document_id: str, message: dict):
        """Publish message to Redis Pub/Sub channel so all app replicas receive it."""
        channel = f"doc_room:{document_id}"
        await redis_client.publish(channel, json.dumps(message, default=str))

    async def _listen_to_redis(self, document_id: str):
        """Listen to Redis channel and forward messages to local WebSocket clients."""
        pubsub = redis_client.pubsub()
        channel = f"doc_room:{document_id}"
        ready = self.pubsub_ready[document_id]
        try:
            await pubsub.subscribe(channel)
            ready.set()
            async for message in pubsub.listen():
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await self._broadcast_local(
                        document_id, data, sender_socket_id=data.get("socket_id")
                    )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Redis listener failed for document room %s", document_id)
        finally:
            ready.set()
            await pubsub.aclose()
            self.pubsub_ready.pop(document_id, None)

    async def _broadcast_local(self, document_id: str, message: dict, sender_socket_id: str = None):
        """Broadcast message to all WebSocket connections hosted on THIS container."""
        if document_id in self.active_rooms:
            for connection in list(self.active_rooms[document_id]):
                # Avoid echoing message back to the originating socket
                if getattr(connection, "socket_id", None) != sender_socket_id:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        logger.warning(
                            "Removing disconnected WebSocket from room %s",
                            document_id,
                            exc_info=True,
                        )
                        self.disconnect(document_id, connection)


manager = ConnectionManager()
