from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import websocket_manager
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/vehicle/{vehicle_id}")
async def vehicle_websocket(websocket: WebSocket, vehicle_id: int):
    await websocket_manager.connect(websocket, "vehicles")
    try:
        while True:
            data = await websocket.receive_text()
            # Processar dados do veículo
            try:
                message = json.loads(data)
                # Aqui você pode processar comandos para o veículo
                # como desligar motor, travar portas, etc.
                logger.debug("Message from vehicle %s: %s", vehicle_id, message)
            except json.JSONDecodeError:
                logger.debug("Received non-JSON message from vehicle %s", vehicle_id)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, "vehicles")


@router.websocket("/ws/monitoring")
async def monitoring_websocket(websocket: WebSocket):
    await websocket_manager.connect(websocket, "monitoring")
    try:
        while True:
            # Manter conexão aberta
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, "monitoring")