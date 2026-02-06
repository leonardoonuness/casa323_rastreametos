import asyncio
import random
import logging
import httpx

BASE_URL = "http://localhost:8000/api"
VEHICLES = []


async def create_vehicles(client: httpx.AsyncClient):
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
    
    for vehicle in vehicles_data:
        try:
            response = await client.post(f"{BASE_URL}/vehicles/", json=vehicle, timeout=10.0)
            if response.status_code in (200, 201):
                created = response.json()
                VEHICLES.append(created)
                logging.info("Veículo criado: %s", created.get("license_plate"))
            else:
                logging.warning("Failed creating vehicle %s: %s", vehicle.get("license_plate"), response.status_code)
        except Exception as e:
            logging.exception("Erro ao criar veículo")


async def simulate_position(vehicle, client: httpx.AsyncClient):
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
        
        try:
            response = await client.post(f"{BASE_URL}/positions/", json=position, timeout=10.0)
            if response.status_code in (200, 201):
                logging.debug("Posição atualizada: %s (%0.4f, %0.4f)", vehicle.get("license_plate"), lat, lng)
            else:
                logging.warning("Failed updating position for %s: %s", vehicle.get("license_plate"), response.status_code)
        except Exception:
            logging.exception("Erro ao atualizar posição para %s", vehicle.get("license_plate"))
        
        await asyncio.sleep(random.uniform(5, 15))  # Intervalo entre 5-15 segundos


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("Criando veículos...")
    async with httpx.AsyncClient() as client:
        await create_vehicles(client)

        logging.info("%d veículos criados", len(VEHICLES))
        if not VEHICLES:
            logging.error("Nenhum veículo criado — abortando simulação")
            return

        logging.info("Iniciando simulação de movimento...")

        # Iniciar simulação para cada veículo
        tasks = [simulate_position(vehicle, client) for vehicle in VEHICLES]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())