from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine, Base
import models  # noqa
from routers import torneos, jugadores

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RoundMaster API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(torneos.router, prefix="/api")
app.include_router(jugadores.router, prefix="/api")

# Buscar frontend relativo al backend, funciona tanto local como en Railway
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

if not os.path.exists(FRONTEND_DIR):
    # En Railway el repo completo está en /app/../ 
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    static_dir = os.path.join(FRONTEND_DIR, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/torneo/{torneo_id}", include_in_schema=False)
    def torneo_view(torneo_id: int):
        return FileResponse(os.path.join(FRONTEND_DIR, "torneo.html"))

    @app.get("/emparejamientos", include_in_schema=False)
    def emparejamientos_view():
        return FileResponse(os.path.join(FRONTEND_DIR, "emparejamientos.html"))

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "RoundMaster"}
