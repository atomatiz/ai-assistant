from fastapi import WebSocket
from typing import Dict
from utils.logger import logger


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_connections[device_id] = websocket
        logger.info("Websocket connection established: %s", device_id)

    def disconnect(self, device_id: str):
        self.active_connections.pop(device_id, None)

    async def send_json(self, device_id: str, message: dict):
        connection = self.active_connections.get(device_id)
        if connection:
            await connection.send_json(message)


webSocketManager = WebSocketManager()
