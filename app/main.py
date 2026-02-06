from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
import json
import os
import redis
from typing import Optional
import asyncio
from contextlib import asynccontextmanager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Banco de dados SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./vehicles.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis (opcional - se não tiver, usamos dict em memória)
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis conectado com sucesso")
except:
    REDIS_AVAILABLE = False
    logger.warning("Redis não disponível, usando cache em memória")
    in_memory_cache = {}

# Enums
class VehicleType(str, enum.Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"

class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

# Modelos
class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), unique=True, index=True, nullable=False)
    vehicle_type = Column(String(20), nullable=False)
    brand = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
    color = Column(String(50))
    status = Column(String(20), default=VehicleStatus.ACTIVE.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class VehiclePosition(Base):
    __tablename__ = "vehicle_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float)
    heading = Column(Float)
    accuracy = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Gerenciador de WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# Lifespan da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando aplicação CASA323 Rastreamentos")
    yield
    # Shutdown
    logger.info("Encerrando aplicação")

# Criar aplicação FastAPI
app = FastAPI(
    title="CASA323 Rastreamentos",
    description="Plataforma de rastreamento de veículos em tempo real",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper para obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Página principal
@app.get("/", response_class=HTMLResponse)
async def get_home():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Retornar HTML básico se o arquivo não existir
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CASA323 Rastreamentos</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .status { padding: 20px; background: #f0f0f0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>CASA323 Rastreamentos</h1>
                <p>Sistema de rastreamento de veículos em tempo real</p>
                <div class="status">
                    <p>Backend está funcionando!</p>
                    <p>API disponível em: <a href="/docs">/docs</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

# API Routes
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "CASA323 Rastreamentos",
        "timestamp": datetime.now().isoformat(),
        "redis": REDIS_AVAILABLE
    }

@app.get("/api/vehicles")
async def get_vehicles(db: Session = Depends(get_db)):
    try:
        vehicles = db.query(Vehicle).all()
        return {
            "success": True,
            "count": len(vehicles),
            "vehicles": [
                {
                    "id": v.id,
                    "license_plate": v.license_plate,
                    "vehicle_type": v.vehicle_type,
                    "brand": v.brand,
                    "model": v.model,
                    "year": v.year,
                    "color": v.color,
                    "status": v.status,
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in vehicles
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao buscar veículos: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/vehicles")
async def create_vehicle(data: dict, db: Session = Depends(get_db)):
    try:
        # Validar dados básicos
        if not data.get("license_plate"):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Placa é obrigatória"}
            )
        
        # Verificar se veículo já existe
        existing = db.query(Vehicle).filter(
            Vehicle.license_plate == data["license_plate"]
        ).first()
        
        if existing:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Veículo já cadastrado"}
            )
        
        # Criar veículo
        vehicle = Vehicle(
            license_plate=data["license_plate"],
            vehicle_type=data.get("vehicle_type", "car"),
            brand=data.get("brand"),
            model=data.get("model"),
            year=data.get("year"),
            color=data.get("color"),
            status=data.get("status", "active")
        )
        
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        
        # Notificar via WebSocket
        await manager.broadcast({
            "type": "vehicle_added",
            "data": {
                "id": vehicle.id,
                "license_plate": vehicle.license_plate,
                "vehicle_type": vehicle.vehicle_type
            }
        })
        
        return {
            "success": True,
            "vehicle": {
                "id": vehicle.id,
                "license_plate": vehicle.license_plate,
                "vehicle_type": vehicle.vehicle_type,
                "brand": vehicle.brand,
                "model": vehicle.model,
                "status": vehicle.status
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar veículo: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/positions")
async def create_position(data: dict, db: Session = Depends(get_db)):
    try:
        # Validar dados
        required_fields = ["vehicle_id", "latitude", "longitude"]
        for field in required_fields:
            if field not in data:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": f"Campo {field} é obrigatório"}
                )
        
        # Verificar se veículo existe
        vehicle = db.query(Vehicle).filter(Vehicle.id == data["vehicle_id"]).first()
        if not vehicle:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Veículo não encontrado"}
            )
        
        # Criar posição
        position = VehiclePosition(
            vehicle_id=data["vehicle_id"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            speed=data.get("speed"),
            heading=data.get("heading"),
            accuracy=data.get("accuracy")
        )
        
        db.add(position)
        db.commit()
        db.refresh(position)
        
        # Armazenar em cache
        cache_data = {
            "vehicle_id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "vehicle_type": vehicle.vehicle_type,
            "latitude": position.latitude,
            "longitude": position.longitude,
            "speed": position.speed,
            "heading": position.heading,
            "timestamp": position.timestamp.isoformat() if position.timestamp else None
        }
        
        if REDIS_AVAILABLE:
            redis_client.setex(
                f"vehicle:{vehicle.id}:position",
                300,  # 5 minutos
                json.dumps(cache_data)
            )
        else:
            in_memory_cache[f"vehicle:{vehicle.id}:position"] = cache_data
        
        # Notificar via WebSocket
        await manager.broadcast({
            "type": "position_update",
            "data": cache_data
        })
        
        return {
            "success": True,
            "position": {
                "id": position.id,
                "vehicle_id": position.vehicle_id,
                "latitude": position.latitude,
                "longitude": position.longitude,
                "speed": position.speed,
                "timestamp": position.timestamp.isoformat() if position.timestamp else None
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar posição: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/vehicles/{vehicle_id}/positions")
async def get_vehicle_positions(vehicle_id: int, limit: int = 50, db: Session = Depends(get_db)):
    try:
        positions = db.query(VehiclePosition).filter(
            VehiclePosition.vehicle_id == vehicle_id
        ).order_by(VehiclePosition.timestamp.desc()).limit(limit).all()
        
        return {
            "success": True,
            "count": len(positions),
            "positions": [
                {
                    "id": p.id,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "speed": p.speed,
                    "heading": p.heading,
                    "timestamp": p.timestamp.isoformat() if p.timestamp else None
                }
                for p in positions
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao buscar posições: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Manter conexão aberta
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Endpoint para dados de teste
@app.post("/api/test/setup")
async def setup_test_data(db: Session = Depends(get_db)):
    """Criar dados de teste para demonstração"""
    try:
        # Criar veículos de teste
        test_vehicles = [
            Vehicle(
                license_plate="ABC1D23",
                vehicle_type="car",
                brand="Toyota",
                model="Corolla",
                year=2022,
                color="Prata",
                status="active"
            ),
            Vehicle(
                license_plate="MOT0R01",
                vehicle_type="motorcycle",
                brand="Honda",
                model="CB 500",
                year=2021,
                color="Vermelha",
                status="active"
            ),
            Vehicle(
                license_plate="XYZ9A87",
                vehicle_type="car",
                brand="Volkswagen",
                model="Golf",
                year=2020,
                color="Azul",
                status="active"
            ),
        ]
        
        for vehicle in test_vehicles:
            db.add(vehicle)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Dados de teste criados com sucesso",
            "vehicles_created": len(test_vehicles)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar dados de teste: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Importar Depends aqui para evitar erro
from fastapi import Depends

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )