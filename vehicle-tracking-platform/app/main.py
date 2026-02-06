from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app import models
from app.database import engine
from app.routes import vehicles, positions, websocket
from app.config import settings
import os

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas da API
app.include_router(vehicles.router)
app.include_router(positions.router)
app.include_router(websocket.router)

# Servir frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

    index_path = os.path.join(frontend_dir, "templates", "index.html")
    monitor_path = os.path.join(frontend_dir, "templates", "monitor.html")

    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        if not os.path.exists(index_path):
            return HTMLResponse("<h1>Front-end não encontrado</h1>", status_code=404)
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
            return HTMLResponse(content, media_type="text/html; charset=utf-8")

    @app.get("/monitor", response_class=HTMLResponse)
    async def read_monitor():
        if not os.path.exists(monitor_path):
            # Se não existir, informar usuário em vez de lançar erro
            return HTMLResponse("<h1>Página de monitoramento não disponível</h1>", status_code=404)
        with open(monitor_path, "r", encoding="utf-8") as f:
            content = f.read()
            return HTMLResponse(content, media_type="text/html; charset=utf-8")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)