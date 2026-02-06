import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime
from app.schemas import WebSocketMessage


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "vehicles": set(),
            "monitoring": set()
        }
    
    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        self.active_connections[client_type].add(websocket)
    
    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections[client_type].discard(websocket)
    
    async def broadcast(self, message: WebSocketMessage, client_type: str = "monitoring"):
        disconnected = set()
        for connection in self.active_connections[client_type]:
            try:
                await connection.send_json(message.model_dump())
            except Exception:
                disconnected.add(connection)
        
        # Limpar conexões desconectadas
        for connection in disconnected:
            self.disconnect(connection, client_type)
    
    async def send_to_vehicle(self, vehicle_id: int, message: WebSocketMessage):
        # Enviar mensagem específica para um veículo
        message.data["target_vehicle"] = vehicle_id
        await self.broadcast(message, "vehicles")
    
    async def send_position_update(self, position_data: dict):
        message = WebSocketMessage(
            type="position_update",
            data=position_data,
            timestamp=datetime.now()
        )
        await self.broadcast(message, "monitoring")


websocket_manager = WebSocketManager()