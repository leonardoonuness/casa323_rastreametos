from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
import redis
import json
from app import models, schemas
from app.config import settings


# Redis client
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class VehicleCRUD:
    @staticmethod
    def get_vehicle(db: Session, vehicle_id: int):
        return db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    
    @staticmethod
    def get_vehicle_by_plate(db: Session, license_plate: str):
        return db.query(models.Vehicle).filter(models.Vehicle.license_plate == license_plate).first()
    
    @staticmethod
    def get_vehicles(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Vehicle).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_vehicle(db: Session, vehicle: schemas.VehicleCreate):
        db_vehicle = models.Vehicle(**vehicle.model_dump())
        db.add(db_vehicle)
        db.commit()
        db.refresh(db_vehicle)
        return db_vehicle
    
    @staticmethod
    def update_vehicle(db: Session, vehicle_id: int, vehicle_update: schemas.VehicleUpdate):
        db_vehicle = VehicleCRUD.get_vehicle(db, vehicle_id)
        if db_vehicle:
            update_data = vehicle_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_vehicle, field, value)
            db.commit()
            db.refresh(db_vehicle)
        return db_vehicle
    
    @staticmethod
    def delete_vehicle(db: Session, vehicle_id: int):
        db_vehicle = VehicleCRUD.get_vehicle(db, vehicle_id)
        if db_vehicle:
            db.delete(db_vehicle)
            db.commit()
        return db_vehicle


class PositionCRUD:
    @staticmethod
    def create_position(db: Session, position: schemas.PositionCreate):
        db_position = models.VehiclePosition(**position.model_dump())
        db.add(db_position)
        db.commit()
        db.refresh(db_position)
        
        # Cache no Redis
        vehicle = VehicleCRUD.get_vehicle(db, position.vehicle_id)
        if vehicle:
            redis_position = schemas.RedisPosition(
                vehicle_id=vehicle.id,
                license_plate=vehicle.license_plate,
                vehicle_type=vehicle.vehicle_type,
                latitude=position.latitude,
                longitude=position.longitude,
                speed=position.speed,
                heading=position.heading,
                timestamp=db_position.timestamp
            )
            redis_key = f"vehicle:{vehicle.id}:position"
            redis_client.setex(
                redis_key,
                timedelta(minutes=5),
                json.dumps(redis_position.model_dump(), default=str)
            )
            
            # Adicionar ao GeoRedis para consultas espaciais
            redis_client.geoadd(
                "vehicles:locations",
                (position.longitude, position.latitude, vehicle.id)
            )
        
        return db_position
    
    @staticmethod
    def get_latest_position(db: Session, vehicle_id: int):
        return db.query(models.VehiclePosition).filter(
            models.VehiclePosition.vehicle_id == vehicle_id
        ).order_by(desc(models.VehiclePosition.timestamp)).first()
    
    @staticmethod
    def get_vehicle_positions(db: Session, vehicle_id: int, limit: int = 100):
        return db.query(models.VehiclePosition).filter(
            models.VehiclePosition.vehicle_id == vehicle_id
        ).order_by(desc(models.VehiclePosition.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_positions_in_area(lat: float, lng: float, radius_km: float = 5):
        """Busca veículos em um raio usando Redis Geo"""
        results = redis_client.georadius(
            "vehicles:locations",
            lng,
            lat,
            radius_km,
            "km",
            withdist=True,
            withcoord=True
        )
        
        vehicles_in_area = []
        for result in results:
            vehicle_id = int(result[0])
            distance = result[1]
            coordinates = result[2]
            
            # Buscar dados completos do Redis
            redis_data = redis_client.get(f"vehicle:{vehicle_id}:position")
            if redis_data:
                vehicle_data = json.loads(redis_data)
                vehicle_data["distance"] = distance
                vehicle_data["coordinates"] = coordinates
                vehicles_in_area.append(vehicle_data)
        
        return vehicles_in_area
    
    @staticmethod
    def get_cached_position(vehicle_id: int):
        """Busca posição do cache Redis"""
        redis_data = redis_client.get(f"vehicle:{vehicle_id}:position")
        if redis_data:
            return json.loads(redis_data)
        return None