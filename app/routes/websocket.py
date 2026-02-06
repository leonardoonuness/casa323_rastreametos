from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import websocket_manager
import json

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
                print(f"Message from vehicle {vehicle_id}: {message}")
            except json.JSONDecodeError:
                pass
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