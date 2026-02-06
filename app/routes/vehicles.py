from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.post("/", response_model=schemas.Vehicle)
def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = crud.VehicleCRUD.get_vehicle_by_plate(db, vehicle.license_plate)
    if db_vehicle:
        raise HTTPException(status_code=400, detail="License plate already registered")
    return crud.VehicleCRUD.create_vehicle(db, vehicle)


@router.get("/", response_model=List[schemas.Vehicle])
def read_vehicles(
    skip: int = 0,
    limit: int = 100,
    vehicle_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    vehicles = crud.VehicleCRUD.get_vehicles(db, skip=skip, limit=limit)
    if vehicle_type:
        vehicles = [v for v in vehicles if v.vehicle_type.value == vehicle_type]
    return vehicles


@router.get("/{vehicle_id}", response_model=schemas.VehicleWithPositions)
def read_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    db_vehicle = crud.VehicleCRUD.get_vehicle(db, vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return db_vehicle


@router.put("/{vehicle_id}", response_model=schemas.Vehicle)
def update_vehicle(
    vehicle_id: int,
    vehicle_update: schemas.VehicleUpdate,
    db: Session = Depends(get_db)
):
    db_vehicle = crud.VehicleCRUD.update_vehicle(db, vehicle_id, vehicle_update)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return db_vehicle


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    db_vehicle = crud.VehicleCRUD.delete_vehicle(db, vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"message": "Vehicle deleted successfully"}


@router.get("/{vehicle_id}/positions", response_model=List[schemas.Position])
def get_vehicle_positions(
    vehicle_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    return crud.PositionCRUD.get_vehicle_positions(db, vehicle_id, limit)


@router.get("/{vehicle_id}/position/latest")
def get_latest_position(vehicle_id: int, db: Session = Depends(get_db)):
    # Tenta buscar do cache primeiro
    cached = crud.PositionCRUD.get_cached_position(vehicle_id)
    if cached:
        return cached
    
    # Se não tem cache, busca do banco
    position = crud.PositionCRUD.get_latest_position(db, vehicle_id)
    if position is None:
        raise HTTPException(status_code=404, detail="No position data found")
    
    return position