from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.models import VehicleType, VehicleStatus


class VehicleBase(BaseModel):
    license_plate: str = Field(..., min_length=1, max_length=20)
    vehicle_type: VehicleType
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=datetime.now().year)
    color: Optional[str] = None
    status: VehicleStatus = VehicleStatus.ACTIVE


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    status: Optional[VehicleStatus] = None


class Vehicle(VehicleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PositionBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = Field(None, ge=0)
    heading: Optional[float] = Field(None, ge=0, le=360)
    accuracy: Optional[float] = Field(None, ge=0)


class PositionCreate(PositionBase):
    vehicle_id: int


class Position(PositionBase):
    id: int
    vehicle_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class VehicleWithPositions(Vehicle):
    positions: List[Position] = []


class WebSocketMessage(BaseModel):
    type: str  # "position_update", "vehicle_status", "new_vehicle"
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)


class RedisPosition(BaseModel):
    vehicle_id: int
    license_plate: str
    vehicle_type: VehicleType
    latitude: float
    longitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True