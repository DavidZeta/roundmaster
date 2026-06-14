from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Jugador(Base):
    __tablename__ = "jugadores"

    id        = Column(Integer, primary_key=True, index=True)
    nombre    = Column(String, nullable=False)
    player_id = Column(String, unique=True, nullable=False)

    inscripciones = relationship("Inscripcion", back_populates="jugador")


class Torneo(Base):
    __tablename__ = "torneos"

    id                 = Column(Integer, primary_key=True, index=True)
    nombre             = Column(String, nullable=False)
    fecha              = Column(String, nullable=False)
    tienda             = Column(String, nullable=False)
    lugar              = Column(String, nullable=False)
    num_participantes  = Column(Integer, nullable=False)
    total_rondas       = Column(Integer, nullable=False)
    ronda_actual       = Column(Integer, default=0)
    finalizado         = Column(Boolean, default=False)
    created_at         = Column(DateTime, default=datetime.utcnow)

    inscripciones = relationship("Inscripcion", back_populates="torneo")
    partidas      = relationship("Partida", back_populates="torneo")


class Inscripcion(Base):
    __tablename__ = "inscripciones"

    id         = Column(Integer, primary_key=True, index=True)
    torneo_id  = Column(Integer, ForeignKey("torneos.id"), nullable=False)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"), nullable=False)
    activo     = Column(Boolean, default=True)

    torneo  = relationship("Torneo",  back_populates="inscripciones")
    jugador = relationship("Jugador", back_populates="inscripciones")


class Partida(Base):
    __tablename__ = "partidas"

    id           = Column(Integer, primary_key=True, index=True)
    torneo_id    = Column(Integer, ForeignKey("torneos.id"), nullable=False)
    ronda        = Column(Integer, nullable=False)
    mesa         = Column(Integer, nullable=False)
    jugador1_id  = Column(Integer, ForeignKey("jugadores.id"), nullable=False)
    jugador2_id  = Column(Integer, ForeignKey("jugadores.id"), nullable=True)
    resultado    = Column(String, nullable=True)   # gana1 | gana2 | empate | bye
    ganador_id   = Column(Integer, ForeignKey("jugadores.id"), nullable=True)

    torneo   = relationship("Torneo",  back_populates="partidas")
    jugador1 = relationship("Jugador", foreign_keys=[jugador1_id])
    jugador2 = relationship("Jugador", foreign_keys=[jugador2_id])
    ganador  = relationship("Jugador", foreign_keys=[ganador_id])
