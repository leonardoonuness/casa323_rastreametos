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
uvicorn app.main:app --host 0.0.0.0 --port 8000
# em outro terminal
python simulate_vehicles.py
```

## Checklist rápido de deploy

- [ ] Variáveis de ambiente definidas (`.env`) e segredos trocados.
- [ ] Banco configurado para ambiente alvo (SQLite para dev, PostgreSQL para produção).
- [ ] Redis disponível no ambiente de produção.
- [ ] API sobe sem erro com `uvicorn app.main:app`.
- [ ] Endpoint de saúde retorna status `healthy` (`GET /api/health`).
- [ ] CORS restrito para os domínios reais de frontend.
- [ ] Logs/monitoramento habilitados no ambiente alvo.
