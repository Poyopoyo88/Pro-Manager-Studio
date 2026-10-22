"""Puertos (interfaces) que la capa de aplicación necesita del exterior.

La infraestructura los implementa. Así las dependencias apuntan hacia adentro:
la aplicación no sabe si las partidas se guardan en memoria, en JSON o en una base
de datos (principio de inversión de dependencias / *Protected Variations*).
"""

from __future__ import annotations

import random
from typing import Protocol

from ..dominio import Club, EventoVestuario, JugadorEnMercado
from .partida import Partida


class RepositorioPartidas(Protocol):
    def guardar(self, partida: Partida) -> None: ...

    def obtener(self, partida_id: str) -> Partida: ...

    def listar(self) -> list[str]: ...

    def eliminar(self, partida_id: str) -> None: ...


class ProveedorDatosIniciales(Protocol):
    puntos_ascenso: int

    def crear_club_usuario(self) -> Club: ...

    def crear_rivales(self, rng: random.Random) -> list[Club]: ...

    def crear_mercado(self, rng: random.Random) -> list[JugadorEnMercado]: ...

    def eventos_iniciales(self, club: Club) -> list[EventoVestuario]: ...
