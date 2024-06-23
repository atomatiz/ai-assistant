import logging
from fastapi import WebSocket
from typing import Dict
from redis.asyncio import Redis
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("     :")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

    async def check_redis_connection(self):
        try:
            await self.redis.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")

    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_connections[device_id] = websocket

    def disconnect(self, device_id: str):
        self.active_connections.pop(device_id, None)

    async def send_json(self, device_id: str, message: dict):
        connection = self.active_connections.get(device_id)
        if connection:
            await connection.send_json(message)

    def get_redis(self) -> Redis:
        return self.redis
    
manager = ConnectionManager()