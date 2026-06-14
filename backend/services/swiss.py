"""
swiss.py — Lógica de torneos formato suizo
Portado desde torneo.py (SwissDesk desktop) de DavidZ v2.0
Lógica corregida con backtracking real para emparejamientos.
"""
import random
from sqlalchemy.orm import Session
from models import Torneo, Jugador, Inscripcion, Partida


# ── Rondas ────────────────────────────────────────────────────────────────────

def calcular_rondas(n: int) -> int:
    if n <= 3:   return 2
    if n <= 8:   return 3
    if n <= 16:  return 4
    if n <= 32:  return 5
    if n <= 64:  return 6
    if n <= 128: return 7
    if n <= 226: return 8
    if n <= 409: return 9
    return 9


# ── Puntaje individual ────────────────────────────────────────────────────────

def get_puntaje(db: Session, torneo_id: int, jugador_id: int) -> tuple:
    """Retorna (puntos, wins, draws, losses) de un jugador en el torneo."""
    partidas = db.query(Partida).filter(
        Partida.torneo_id == torneo_id,
        Partida.resultado.isnot(None)
    ).all()

    puntos = wins = draws = losses = 0
    for p in partidas:
        if p.jugador1_id != jugador_id and p.jugador2_id != jugador_id:
            continue
        if p.resultado == "bye":
            puntos += 3; wins += 1
        elif p.resultado == "empate":
            puntos += 1; draws += 1
        elif p.resultado == "gana1":
            if p.jugador1_id == jugador_id: puntos += 3; wins += 1
            else: losses += 1
        elif p.resultado == "gana2":
            if p.jugador2_id == jugador_id: puntos += 3; wins += 1
            else: losses += 1

    return puntos, wins, draws, losses


# ── Match Win Rate ────────────────────────────────────────────────────────────

def get_match_win_rate(db: Session, torneo_id: int, jugador_id: int) -> float:
    """Win rate individual. Mínimo 33% según reglamento oficial Pokémon TCG."""
    partidas = db.query(Partida).filter(
        Partida.torneo_id == torneo_id,
        Partida.resultado.isnot(None)
    ).all()

    game_pts = max_pts = 0
    for p in partidas:
        if p.jugador1_id != jugador_id and p.jugador2_id != jugador_id:
            continue
        if p.resultado == "bye":
            game_pts += 3; max_pts += 3
        elif p.resultado == "empate":
            game_pts += 1; max_pts += 3
        elif p.resultado == "gana1":
            if p.jugador1_id == jugador_id: game_pts += 3
            max_pts += 3
        elif p.resultado == "gana2":
            if p.jugador2_id == jugador_id: game_pts += 3
            max_pts += 3

    if max_pts == 0:
        return 0.333
    return max(game_pts / max_pts, 0.333)


# ── Rivales enfrentados ───────────────────────────────────────────────────────

def get_opponents(db: Session, torneo_id: int, jugador_id: int) -> list:
    """IDs de rivales reales enfrentados (sin BYEs)."""
    partidas = db.query(Partida).filter(
        Partida.torneo_id == torneo_id,
        Partida.resultado.isnot(None),
        Partida.jugador2_id.isnot(None),
        Partida.resultado != "bye"
    ).all()

    opponents = []
    for p in partidas:
        if p.jugador1_id == jugador_id:
            opponents.append(p.jugador2_id)
        elif p.jugador2_id == jugador_id:
            opponents.append(p.jugador1_id)
    return opponents


# ── OMW% ──────────────────────────────────────────────────────────────────────

def get_omw(db: Session, torneo_id: int, jugador_id: int) -> float:
    """Opponent Match Win Rate: promedio del MWR de cada rival."""
    opponents = get_opponents(db, torneo_id, jugador_id)
    if not opponents:
        return 0.0
    total = sum(get_match_win_rate(db, torneo_id, opp) for opp in opponents)
    return total / len(opponents)


# ── Ranking ───────────────────────────────────────────────────────────────────

def get_ranking(db: Session, torneo_id: int) -> list:
    """Ranking con desempate oficial Pokémon TCG: Puntos → OMW% → Victorias."""
    inscripciones = db.query(Inscripcion).filter(
        Inscripcion.torneo_id == torneo_id,
        Inscripcion.activo == True
    ).all()

    rows = []
    for ins in inscripciones:
        jid = ins.jugador_id
        puntos, wins, draws, losses = get_puntaje(db, torneo_id, jid)
        omw = get_omw(db, torneo_id, jid)
        rows.append({
            "jugador_id": jid,
            "nombre":     ins.jugador.nombre,
            "player_id":  ins.jugador.player_id,
            "puntos":     puntos,
            "wins":       wins,
            "draws":      draws,
            "losses":     losses,
            "omw":        round(omw * 100, 2),
        })

    rows.sort(key=lambda r: (-r["puntos"], -r["omw"], -r["wins"]))
    for i, r in enumerate(rows):
        r["posicion"] = i + 1
    return rows


# ── Enfrentamientos previos ───────────────────────────────────────────────────

def get_enfrentamientos_previos(db: Session, torneo_id: int) -> set:
    """Set de tuplas (minId, maxId) de todos los pares ya enfrentados."""
    partidas = db.query(Partida).filter(
        Partida.torneo_id == torneo_id,
        Partida.jugador2_id.isnot(None),
        Partida.resultado != "bye"
    ).all()
    return {(min(p.jugador1_id, p.jugador2_id), max(p.jugador1_id, p.jugador2_id)) for p in partidas}


# ── Backtracking ──────────────────────────────────────────────────────────────

def _backtrack_emparejar(jugadores: list, previos: set):
    """Backtracking real: empareja respetando el orden de ranking.
    Evita rematches desplazando al siguiente rival disponible.
    Retorna (pares, bye) o None si no encontró solución."""
    if not jugadores:
        return [], None
    if len(jugadores) == 1:
        return [], jugadores[0]   # BYE

    j1 = jugadores[0]
    resto = jugadores[1:]

    # Intentar emparejar j1 con el más cercano en ranking sin rematch
    for i, j2 in enumerate(resto):
        par = (min(j1, j2), max(j1, j2))
        if par not in previos:
            nuevos = resto[:i] + resto[i+1:]
            resultado = _backtrack_emparejar(nuevos, previos)
            if resultado is not None:
                pares, bye = resultado
                return [(j1, j2)] + pares, bye

    # Si todos son rematches, forzar con el más cercano
    j2 = resto[0]
    nuevos = resto[1:]
    resultado = _backtrack_emparejar(nuevos, previos)
    if resultado is not None:
        pares, bye = resultado
        return [(j1, j2)] + pares, bye

    return None


# ── Emparejamiento suizo ──────────────────────────────────────────────────────

def crear_emparejamiento(db: Session, torneo_id: int, ronda: int) -> list:
    """
    Emparejamiento suizo correcto:
    - Ronda 1: aleatorio puro (todos con 0 puntos).
    - Rondas siguientes: ranking ordenado por puntos+OMW%, backtracking para
      evitar rematches SIN romper el orden. El 1° siempre juega vs el 2° posible,
      el 3° vs el 4° posible, etc. Shuffle dentro de cada grupo de puntos para variedad.
    """
    ranking = get_ranking(db, torneo_id)
    previos = get_enfrentamientos_previos(db, torneo_id)

    if ronda == 1:
        # Ronda 1: completamente aleatorio
        jugadores = [r["jugador_id"] for r in ranking]
        random.shuffle(jugadores)
        pares = []
        while len(jugadores) >= 2:
            pares.append((jugadores.pop(0), jugadores.pop(0)))
        bye = jugadores[0] if jugadores else None
    else:
        # Rondas 2+: agrupar por puntos, shuffle dentro de cada grupo
        grupos: dict = {}
        for r in ranking:
            grupos.setdefault(r["puntos"], []).append(r["jugador_id"])

        ordenados = []
        for pts in sorted(grupos.keys(), reverse=True):
            grupo = grupos[pts]
            random.shuffle(grupo)   # variedad DENTRO del mismo grupo de puntos
            ordenados.extend(grupo)

        # Backtracking respetando orden
        resultado = _backtrack_emparejar(ordenados, previos)
        if resultado is None:
            # Fallback extremo (no debería ocurrir)
            pares = [(ordenados[i], ordenados[i+1]) for i in range(0, len(ordenados)-1, 2)]
            bye = ordenados[-1] if len(ordenados) % 2 else None
        else:
            pares, bye = resultado

    # Insertar partidas en la DB
    partidas_nuevas = []
    mesa = 1

    for j1_id, j2_id in pares:
        nueva = Partida(
            torneo_id=torneo_id,
            ronda=ronda,
            mesa=mesa,
            jugador1_id=j1_id,
            jugador2_id=j2_id,
            resultado=None,
            ganador_id=None,
        )
        db.add(nueva)
        partidas_nuevas.append(nueva)
        mesa += 1

    if bye is not None:
        nueva = Partida(
            torneo_id=torneo_id,
            ronda=ronda,
            mesa=mesa,
            jugador1_id=bye,
            jugador2_id=None,
            resultado="bye",
            ganador_id=bye,
        )
        db.add(nueva)
        partidas_nuevas.append(nueva)

    db.commit()
    for p in partidas_nuevas:
        db.refresh(p)
    return partidas_nuevas
