"""Partida guardada: el contenedor de todo el estado de una carrera del DT.

No contiene reglas de negocio; solo agrupa las entidades del dominio y ofrece
búsquedas por identificador. Es la unidad que se guarda y carga.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from ..dominio import (
    Alineacion,
    Club,
    DirectorTecnico,
    EventoVestuario,
    JugadorEnMercado,
    Partido,
    Temporada,
)
from ..dominio.errores import (
    ClubNoEncontradoError,
    EventoNoEncontradoError,
    JugadorNoEncontradoError,
)


@dataclass
class Partida:
    id: str
    semilla: int
    dt: DirectorTecnico
    club: Club
    rivales: list[Club]
    temporada: Temporada
    eventos: list[EventoVestuario] = field(default_factory=list)
    mercado: list[JugadorEnMercado] = field(default_factory=list)
    alineacion: Alineacion | None = None
    partido: Partido | None = None
    noticias: list[str] = field(default_factory=list)
    contador_acciones: int = 0
    creada_en: str = ""

    def nuevo_rng(self) -> random.Random:
        """Generador aleatorio reproducible: misma semilla + mismas acciones = mismo juego."""
        self.contador_acciones += 1
        return random.Random(self.semilla * 1_000_003 + self.contador_acciones)

    def rival(self, rival_id: str) -> Club:
        for club in self.rivales:
            if club.id == rival_id:
                return club
        raise ClubNoEncontradoError(f"No existe el rival '{rival_id}'.")

    def evento(self, evento_id: str) -> EventoVestuario:
        for evento in self.eventos:
            if evento.id == evento_id:
                return evento
        raise EventoNoEncontradoError(f"No existe el evento de vestuario '{evento_id}'.")

    def eventos_pendientes(self) -> list[EventoVestuario]:
        return [e for e in self.eventos if not e.resuelto]

    def entrada_mercado(self, jugador_id: str) -> JugadorEnMercado:
        for entrada in self.mercado:
            if entrada.jugador.id == jugador_id:
                return entrada
        raise JugadorNoEncontradoError(f"El jugador '{jugador_id}' no está en el mercado.")

    def siguiente_id_evento(self) -> str:
        return f"EV-{len(self.eventos) + 1:03d}"

    @property
    def hay_partido_en_curso(self) -> bool:
        return self.partido is not None and self.partido.esta_activo
