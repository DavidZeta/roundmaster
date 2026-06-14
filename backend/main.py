from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine, Base
import models  # noqa: F401 — necesario para que SQLAlchemy registre los modelos
from routers import torneos, jugadores

# ── Crear tablas automáticamente al iniciar ───────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SwissDesk API",
    description="Sistema de torneos formato suizo para TCG",
    version="1.0.0",
)

# ── CORS — permite que el frontend (mismo servidor o localhost) consuma la API ─
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # En producción puedes restringir al dominio de Railway
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(torneos.router, prefix="/api")
app.include_router(jugadores.router, prefix="/api")

# ── Servir frontend estático ──────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/torneo/{torneo_id}", include_in_schema=False)
    def torneo_view(torneo_id: int):
        return FileResponse(os.path.join(FRONTEND_DIR, "torneo.html"))

    @app.get("/emparejamientos", include_in_schema=False)
    def emparejamientos_view():
        return FileResponse(os.path.join(FRONTEND_DIR, "emparejamientos.html"))

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "app": "RoundMaster"}
