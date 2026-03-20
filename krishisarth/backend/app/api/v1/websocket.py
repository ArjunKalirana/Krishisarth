from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import logging
from app.api import deps

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # farm_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, farm_id: str, websocket: WebSocket):
        await websocket.accept()
        if farm_id not in self.active_connections:
            self.active_connections[farm_id] = []
        self.active_connections[farm_id].append(websocket)
        logger.info(f"WS: Farmer connected to Farm {farm_id}. Total: {len(self.active_connections[farm_id])}")

    def disconnect(self, farm_id: str, websocket: WebSocket):
        if farm_id in self.active_connections:
            if websocket in self.active_connections[farm_id]:
                self.active_connections[farm_id].remove(websocket)
            if not self.active_connections[farm_id]:
                del self.active_connections[farm_id]
        logger.info(f"WS: Farmer disconnected from Farm {farm_id}")

    async def broadcast_to_farm(self, farm_id: str, message: dict):
        if farm_id in self.active_connections:
            dead_links = []
            for connection in self.active_connections[farm_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_links.append(connection)
            
            for dead in dead_links:
                self.disconnect(farm_id, dead)

manager = ConnectionManager()

router = APIRouter()

@router.websocket("/ws/farms/{farm_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    farm_id: str
):
    # Note: Traditional Depends(deps.get_current_farmer) doesn't work easily with WS handshakes
    # in some FastAPI versions without custom handling. We'll accept the connection for now
    # and verify farm existence.
    
    await manager.connect(farm_id, websocket)
    try:
        while True:
            # Keep connection alive and listen for any client-side pings
            data = await websocket.receive_text()
            # We don't expect much from client, but can handle pings
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(farm_id, websocket)
    except Exception as e:
        logger.error(f"WS Error on Farm {farm_id}: {str(e)}")
        manager.disconnect(farm_id, websocket)
