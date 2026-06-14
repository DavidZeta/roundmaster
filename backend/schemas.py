from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


# ── Jugador ──────────────────────────────────────────────────────────────────

class JugadorCreate(BaseModel):
    nombre: str
    player_id: str

class JugadorOut(BaseModel):
    id: int
    nombre: str
    player_id: str
    model_config = {"from_attributes": True}


# ── Torneo ───────────────────────────────────────────────────────────────────

class TorneoCreate(BaseModel):
    nombre: str
    fecha: str
    tienda: str
    lugar: str

    @field_validator("nombre", "tienda", "lugar")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío")
        return v.strip()

class TorneoOut(BaseModel):
    id: int
    nombre: str
    fecha: str
    tienda: str
    lugar: str
    num_participantes: int
    total_rondas: int
    ronda_actual: int
    finalizado: bool
    created_at: Optional[datetime]
    model_config = {"from_attributes": True}


# ── Inscripción ───────────────────────────────────────────────────────────────

class InscripcionCreate(BaseModel):
    jugador_id: int


# ── Partida / Resultado ───────────────────────────────────────────────────────

class ResultadoUpdate(BaseModel):
    resultado: str   # gana1 | gana2 | empate

    @field_validator("resultado")
    @classmethod
    def resultado_valido(cls, v: str) -> str:
        if v not in ("gana1", "gana2", "empate"):
            raise ValueError("Resultado debe ser: gana1, gana2 o empate")
        return v

class PartidaOut(BaseModel):
    id: int
    mesa: int
    ronda: int
    jugador1: JugadorOut
    jugador2: Optional[JugadorOut]
    resultado: Optional[str]
    ganador_id: Optional[int]
    model_config = {"from_attributes": True}


# ── Ranking ───────────────────────────────────────────────────────────────────

class RankingRow(BaseModel):
    posicion: int
    jugador_id: int
    nombre: str
    player_id: str
    puntos: int
    wins: int
    draws: int
    losses: int
    omw: float        # Opponent Match Win Rate (%)
