from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Torneo, Jugador, Inscripcion, Partida
from schemas import TorneoCreate, TorneoOut, InscripcionCreate, PartidaOut, ResultadoUpdate, RankingRow
from services.swiss import calcular_rondas, crear_emparejamiento, get_ranking

router = APIRouter(prefix="/torneos", tags=["torneos"])


# ── CRUD Torneo ───────────────────────────────────────────────────────────────

@router.get("/", response_model=list[TorneoOut])
def listar_torneos(db: Session = Depends(get_db)):
    return db.query(Torneo).order_by(Torneo.created_at.desc()).all()


@router.post("/", response_model=TorneoOut, status_code=201)
def crear_torneo(data: TorneoCreate, db: Session = Depends(get_db)):
    torneo = Torneo(
        nombre=data.nombre,
        fecha=data.fecha,
        tienda=data.tienda,
        lugar=data.lugar,
        num_participantes=0,
        total_rondas=0,
        ronda_actual=0,
        finalizado=False,
    )
    db.add(torneo)
    db.commit()
    db.refresh(torneo)
    return torneo


@router.get("/{torneo_id}", response_model=TorneoOut)
def obtener_torneo(torneo_id: int, db: Session = Depends(get_db)):
    t = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if not t:
        raise HTTPException(404, "Torneo no encontrado")
    return t


# ── Inscripciones ─────────────────────────────────────────────────────────────

@router.get("/{torneo_id}/jugadores", response_model=list)
def listar_inscritos(torneo_id: int, db: Session = Depends(get_db)):
    _get_torneo_o_404(torneo_id, db)
    ins = db.query(Inscripcion).filter(
        Inscripcion.torneo_id == torneo_id,
        Inscripcion.activo == True
    ).all()
    return [{"id": i.jugador.id, "nombre": i.jugador.nombre, "player_id": i.jugador.player_id} for i in ins]


@router.post("/{torneo_id}/jugadores", status_code=201)
def inscribir_jugador(torneo_id: int, data: InscripcionCreate, db: Session = Depends(get_db)):
    torneo = _get_torneo_o_404(torneo_id, db)
    if torneo.ronda_actual > 0:
        raise HTTPException(400, "No se puede inscribir jugadores una vez iniciado el torneo")

    jugador = db.query(Jugador).filter(Jugador.id == data.jugador_id).first()
    if not jugador:
        raise HTTPException(404, "Jugador no encontrado")

    ya_inscrito = db.query(Inscripcion).filter(
        Inscripcion.torneo_id == torneo_id,
        Inscripcion.jugador_id == data.jugador_id,
        Inscripcion.activo == True
    ).first()
    if ya_inscrito:
        raise HTTPException(400, "El jugador ya está inscrito en este torneo")

    ins = Inscripcion(torneo_id=torneo_id, jugador_id=data.jugador_id)
    db.add(ins)

    # Actualizar conteo y recalcular rondas
    total = db.query(Inscripcion).filter(
        Inscripcion.torneo_id == torneo_id, Inscripcion.activo == True
    ).count() + 1
    torneo.num_participantes = total
    torneo.total_rondas = calcular_rondas(total)
    db.commit()
    return {"mensaje": f"{jugador.nombre} inscrito correctamente", "total": total}


@router.delete("/{torneo_id}/jugadores/{jugador_id}")
def dar_baja(torneo_id: int, jugador_id: int, db: Session = Depends(get_db)):
    torneo = _get_torneo_o_404(torneo_id, db)
    ins = db.query(Inscripcion).filter(
        Inscripcion.torneo_id == torneo_id,
        Inscripcion.jugador_id == jugador_id,
        Inscripcion.activo == True
    ).first()
    if not ins:
        raise HTTPException(404, "El jugador no está inscrito activamente")

    ins.activo = False

    # Si tiene partida activa en la ronda actual, registrar derrota
    if torneo.ronda_actual > 0:
        partida_activa = db.query(Partida).filter(
            Partida.torneo_id == torneo_id,
            Partida.ronda == torneo.ronda_actual,
            Partida.resultado.is_(None),
            ((Partida.jugador1_id == jugador_id) | (Partida.jugador2_id == jugador_id))
        ).first()
        if partida_activa:
            if partida_activa.jugador1_id == jugador_id:
                partida_activa.resultado = "gana2"
                partida_activa.ganador_id = partida_activa.jugador2_id
            else:
                partida_activa.resultado = "gana1"
                partida_activa.ganador_id = partida_activa.jugador1_id

    # Recalcular rondas
    total_activos = db.query(Inscripcion).filter(
        Inscripcion.torneo_id == torneo_id, Inscripcion.activo == True
    ).count() - 1
    torneo.num_participantes = total_activos
    torneo.total_rondas = calcular_rondas(total_activos)
    db.commit()
    return {"mensaje": "Jugador dado de baja"}


# ── Rondas ────────────────────────────────────────────────────────────────────

@router.post("/{torneo_id}/iniciar")
def iniciar_torneo(torneo_id: int, db: Session = Depends(get_db)):
    torneo = _get_torneo_o_404(torneo_id, db)
    if torneo.ronda_actual > 0:
        raise HTTPException(400, "El torneo ya fue iniciado")
    if torneo.num_participantes < 2:
        raise HTTPException(400, "Se necesitan al menos 2 jugadores para iniciar")

    torneo.ronda_actual = 1
    db.commit()
    partidas = crear_emparejamiento(db, torneo_id, 1)
    return {"mensaje": "Torneo iniciado", "ronda": 1, "partidas": len(partidas)}


@router.post("/{torneo_id}/siguiente-ronda")
def siguiente_ronda(torneo_id: int, db: Session = Depends(get_db)):
    torneo = _get_torneo_o_404(torneo_id, db)
    if torneo.finalizado:
        raise HTTPException(400, "El torneo ya está finalizado")
    if torneo.ronda_actual == 0:
        raise HTTPException(400, "El torneo aún no ha iniciado")

    # Verificar pendientes
    pendientes = db.query(Partida).filter(
        Partida.torneo_id == torneo_id,
        Partida.ronda == torneo.ronda_actual,
        Partida.resultado.is_(None)
    ).count()
    if pendientes > 0:
        raise HTTPException(400, f"Hay {pendientes} partida(s) sin resultado en la ronda actual")

    if torneo.ronda_actual >= torneo.total_rondas:
        torneo.finalizado = True
        db.commit()
        return {"mensaje": "Torneo finalizado", "finalizado": True}

    nueva_ronda = torneo.ronda_actual + 1
    torneo.ronda_actual = nueva_ronda
    db.commit()
    partidas = crear_emparejamiento(db, torneo_id, nueva_ronda)
    return {"mensaje": f"Ronda {nueva_ronda} iniciada", "ronda": nueva_ronda, "partidas": len(partidas)}


# ── Partidas y resultados ─────────────────────────────────────────────────────

@router.get("/{torneo_id}/partidas", response_model=list[PartidaOut])
def listar_partidas(torneo_id: int, ronda: int = None, db: Session = Depends(get_db)):
    _get_torneo_o_404(torneo_id, db)
    q = db.query(Partida).filter(Partida.torneo_id == torneo_id)
    if ronda:
        q = q.filter(Partida.ronda == ronda)
    return q.order_by(Partida.ronda, Partida.mesa).all()


@router.put("/{torneo_id}/partidas/{partida_id}/resultado")
def registrar_resultado(torneo_id: int, partida_id: int, data: ResultadoUpdate, db: Session = Depends(get_db)):
    partida = db.query(Partida).filter(
        Partida.id == partida_id,
        Partida.torneo_id == torneo_id
    ).first()
    if not partida:
        raise HTTPException(404, "Partida no encontrada")
    if partida.resultado == "bye":
        raise HTTPException(400, "No se puede modificar un BYE")

    partida.resultado = data.resultado
    if data.resultado == "gana1":
        partida.ganador_id = partida.jugador1_id
    elif data.resultado == "gana2":
        partida.ganador_id = partida.jugador2_id
    else:
        partida.ganador_id = None
    db.commit()
    return {"mensaje": "Resultado registrado"}


@router.delete("/{torneo_id}/partidas/{partida_id}/resultado")
def borrar_resultado(torneo_id: int, partida_id: int, db: Session = Depends(get_db)):
    partida = db.query(Partida).filter(
        Partida.id == partida_id,
        Partida.torneo_id == torneo_id
    ).first()
    if not partida:
        raise HTTPException(404, "Partida no encontrada")
    if partida.resultado == "bye":
        raise HTTPException(400, "No se puede modificar un BYE")
    partida.resultado = None
    partida.ganador_id = None
    db.commit()
    return {"mensaje": "Resultado borrado"}


# ── Ranking ───────────────────────────────────────────────────────────────────

@router.get("/{torneo_id}/ranking", response_model=list[RankingRow])
def ranking(torneo_id: int, db: Session = Depends(get_db)):
    _get_torneo_o_404(torneo_id, db)
    return get_ranking(db, torneo_id)


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_torneo_o_404(torneo_id: int, db: Session) -> Torneo:
    t = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if not t:
        raise HTTPException(404, "Torneo no encontrado")
    return t
