import asyncio
import random
import time
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
VEHICLES = []


async def create_vehicles():
    """Cria veículos de exemplo"""
    vehicles_data = [
        {
            "license_plate": "ABC1D23",
            "vehicle_type": "car",
            "brand": "Toyota",
            "model": "Corolla",
            "color": "Prata"
        },
        {
            "license_plate": "MOT0R01",
            "vehicle_type": "motorcycle",
            "brand": "Honda",
            "model": "CB 500",
            "color": "Vermelha"
        },
        {
            "license_plate": "XYZ9A87",
            "vehicle_type": "car",
            "brand": "Volkswagen",
            "model": "Golf",
            "color": "Azul"
        },
        {
            "license_plate": "MOT0R02",
            "vehicle_type": "motorcycle",
            "brand": "Yamaha",
            "model": "MT-07",
            "color": "Preta"
        },
        {
            "license_plate": "DEF4G56",
            "vehicle_type": "car",
            "brand": "Ford",
            "model": "Focus",
            "color": "Branca"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for vehicle in vehicles_data:
            try:
                response = await client.post(f"{BASE_URL}/vehicles/", json=vehicle)
                if response.status_code == 200:
                    created = response.json()
                    VEHICLES.append(created)
                    print(f"Veículo criado: {created['license_plate']}")
            except Exception as e:
                print(f"Erro ao criar veículo: {e}")


async def simulate_position(vehicle):
    """Simula movimento do veículo"""
    # Posição inicial (São Paulo)
    lat = -23.5505 + random.uniform(-0.05, 0.05)
    lng = -46.6333 + random.uniform(-0.05, 0.05)
    
    while True:
        # Mover aleatoriamente
        lat += random.uniform(-0.001, 0.001)
        lng += random.uniform(-0.001, 0.001)
        
        # Manter dentro de limites
        lat = max(-23.6, min(-23.5, lat))
        lng = max(-46.7, min(-46.6, lng))
        
        position = {
            "vehicle_id": vehicle["id"],
            "latitude": lat,
            "longitude": lng,
            "speed": random.uniform(0, 80),
            "heading": random.uniform(0, 360),
            "accuracy": random.uniform(1, 10)
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{BASE_URL}/positions/", json=position)
                if response.status_code == 200:
                    print(f"Posição atualizada: {vehicle['license_plate']} "
                          f"({lat:.4f}, {lng:.4f})")
            except Exception as e:
                print(f"Erro ao atualizar posição: {e}")
        
        await asyncio.sleep(random.uniform(5, 15))  # Intervalo entre 5-15 segundos


async def main():
    print("Criando veículos...")
    await create_vehicles()
    
    print(f"{len(VEHICLES)} veículos criados")
    print("Iniciando simulação de movimento...")
    
    # Iniciar simulação para cada veículo
    tasks = [simulate_position(vehicle) for vehicle in VEHICLES]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())