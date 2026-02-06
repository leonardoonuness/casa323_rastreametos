from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db
from app.websocket_manager import websocket_manager

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.post("/", response_model=schemas.Position)
async def create_position(position: schemas.PositionCreate, db: Session = Depends(get_db)):
    # Verifica se o veículo existe
    vehicle = crud.VehicleCRUD.get_vehicle(db, position.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Cria a posição
    db_position = crud.PositionCRUD.create_position(db, position)
    
    # Prepara dados para WebSocket
    position_data = {
        "vehicle_id": vehicle.id,
        "license_plate": vehicle.license_plate,
        "vehicle_type": vehicle.vehicle_type,
        "latitude": position.latitude,
        "longitude": position.longitude,
        "speed": position.speed,
        "heading": position.heading,
        "timestamp": db_position.timestamp.isoformat()
    }
    
    # Envia atualização via WebSocket
    await websocket_manager.send_position_update(position_data)
    
    return db_position


@router.get("/nearby")
def get_nearby_vehicles(
    lat: float,
    lng: float,
    radius_km: float = 5.0
):
    """Busca veículos próximos usando Redis Geo"""
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates")
    
    vehicles = crud.PositionCRUD.get_positions_in_area(lat, lng, radius_km)
    return {
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "count": len(vehicles),
        "vehicles": vehicles
    }