from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class VehicleType(str, enum.Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"


class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ACCIDENT = "accident"


class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), unique=True, index=True, nullable=False)
    vehicle_type = Column(Enum(VehicleType), nullable=False)
    brand = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
    color = Column(String(50))
    status = Column(Enum(VehicleStatus), default=VehicleStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    positions = relationship("VehiclePosition", back_populates="vehicle", cascade="all, delete-orphan")


class VehiclePosition(Base):
    __tablename__ = "vehicle_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float)  # em km/h
    heading = Column(Float)  # em graus (0-360)
    accuracy = Column(Float)  # precisão em metros
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    vehicle = relationship("Vehicle", back_populates="positions")


class Driver(Base):
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    license_number = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VehicleAssignment(Base):
    __tablename__ = "vehicle_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    unassigned_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)