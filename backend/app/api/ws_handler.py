"""
WebSocket handler for real-time updates.
Clients connect to receive push notifications about:
  - Schedule changes
  - Machine status changes
  - Task completion events
"""

import json
import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages active WebSocket connections.
    Provides broadcast capability for real-time updates.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, event_type: str, data: dict):
        """Broadcast a JSON message to all connected clients."""
        message = json.dumps({"type": event_type, "data": data}, default=str)
        disconnected = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)

        # Clean up broken connections
        for ws in disconnected:
            self.active_connections.discard(ws)

    async def send_to(self, websocket: WebSocket, event_type: str, data: dict):
        """Send a message to a specific client."""
        message = json.dumps({"type": event_type, "data": data}, default=str)
        await websocket.send_text(message)


# Singleton connection manager
ws_manager = ConnectionManager()


@router.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """
    Main WebSocket endpoint for all real-time updates.
    Client connects and receives push events for schedule, machine status, etc.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, optionally handle client messages
            data = await websocket.receive_text()
            # Client can send ping or subscribe messages
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws_manager.send_to(websocket, "pong", {})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


async def broadcast_schedule_update(schedule_data: dict):
    """Helper to broadcast schedule changes from API endpoints."""
    await ws_manager.broadcast("schedule_update", schedule_data)


async def broadcast_machine_status(machine_id: str, status: str):
    """Helper to broadcast machine status changes."""
    await ws_manager.broadcast("machine_status", {
        "machine_id": machine_id,
        "status": status,
    })


async def broadcast_task_complete(task_token: str, task_type: str):
    """Helper to broadcast task completion."""
    await ws_manager.broadcast("task_complete", {
        "task_token": task_token,
        "task_type": task_type,
    })
