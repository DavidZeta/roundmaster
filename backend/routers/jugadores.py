from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Jugador
from schemas import JugadorCreate, JugadorOut

router = APIRouter(prefix="/jugadores", tags=["jugadores"])


@router.get("/", response_model=list[JugadorOut])
def listar_jugadores(db: Session = Depends(get_db)):
    return db.query(Jugador).order_by(Jugador.nombre).all()


@router.post("/", response_model=JugadorOut, status_code=201)
def crear_jugador(data: JugadorCreate, db: Session = Depends(get_db)):
    existente = db.query(Jugador).filter(Jugador.player_id == data.player_id).first()
    if existente:
        raise HTTPException(400, f"Ya existe un jugador con player_id '{data.player_id}'")
    jugador = Jugador(nombre=data.nombre.strip(), player_id=data.player_id.strip())
    db.add(jugador)
    db.commit()
    db.refresh(jugador)
    return jugador


@router.get("/{jugador_id}", response_model=JugadorOut)
def obtener_jugador(jugador_id: int, db: Session = Depends(get_db)):
    j = db.query(Jugador).filter(Jugador.id == jugador_id).first()
    if not j:
        raise HTTPException(404, "Jugador no encontrado")
    return j
