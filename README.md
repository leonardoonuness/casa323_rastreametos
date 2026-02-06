# Plataforma de Rastreamento de Veículos

Plataforma em tempo real para rastreamento de veículos (carros e motos) com FastAPI, WebSockets e Redis.

## Arquitetura

## Características

- Rastreamento em tempo real com WebSockets
- Cache Redis para posições (sub-milissegundo)
- Mapas interativos com Mapbox GL JS
- Atualizações parciais com htmx
- API RESTful completa
- Suporte a múltiplos tipos de veículos
- Busca por proximidade usando Redis Geo
- Simulação de dados incluída

## Instalação

### 1. Pré-requisitos
- Python 3.8+
- Redis
- PostgreSQL (opcional)

### 2. Instalar dependências
```bash
pip install -r requirements.txt
cp .env.example .env
# Edite .env com suas configurações
docker-compose up -d redis postgres
python -m app.main
http://localhost:8000
python simulate_vehicles.py