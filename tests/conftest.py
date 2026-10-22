"""Fixtures y fábricas compartidas por las pruebas."""

from __future__ import annotations

import random

import pytest
from fastapi.testclient import TestClient

from pro_manager.dominio import (
    Club,
    DirectorTecnico,
    Jugador,
    Partido,
    sugerir_alineacion,
)
from pro_manager.infraestructura import ProveedorDatosJSON, RepositorioEnMemoria
from pro_manager.presentacion.app import crear_app

COMPOSICION = ["POR"] * 2 + ["DEF"] * 6 + ["MED"] * 6 + ["DEL"] * 4


def crear_jugador(id: str = "j1", **cambios) -> Jugador:
    datos = {
        "id": id,
        "nombre": f"Jugador {id}",
        "posicion": "MED",
        "calidad": 70,
        "fisico": 80,
        "moral": 60,
        "personalidad": "PROFESIONAL",
        "salario": 10_000,
    }
    datos.update(cambios)
    return Jugador(**datos)


def crear_club(id: str = "club", nivel: int = 70, **cambios) -> Club:
    """Club con 18 jugadores (2 POR, 6 DEF, 6 MED, 4 DEL) de calidad decreciente."""
    plantilla = [
        crear_jugador(f"{id}-{i:02d}", posicion=pos, calidad=max(1, nivel - (i % 6)))
        for i, pos in enumerate(COMPOSICION, start=1)
    ]
    datos = {
        "id": id,
        "nombre": f"Club {id}",
        "ciudad": "Hermosillo",
        "presupuesto_fichajes": 1_000_000,
        "limite_masa_salarial": 500_000,
        "plantilla": plantilla,
    }
    datos.update(cambios)
    return Club(**datos)


def crear_partido(
    local: Club | None = None, visitante: Club | None = None, iniciar=True
) -> Partido:
    local = local or crear_club("loc")
    visitante = visitante or crear_club("vis")
    partido = Partido(
        "p1",
        local,
        visitante,
        sugerir_alineacion(local),
        sugerir_alineacion(visitante),
        club_usuario_id=local.id,
    )
    if iniciar:
        partido.iniciar()
    return partido


@pytest.fixture
def jugador() -> Jugador:
    return crear_jugador()


@pytest.fixture
def club() -> Club:
    return crear_club()


@pytest.fixture
def dt() -> DirectorTecnico:
    return DirectorTecnico("Profe Prueba")


@pytest.fixture
def partido() -> Partido:
    return crear_partido()


@pytest.fixture
def rng() -> random.Random:
    return random.Random(2026)


@pytest.fixture
def repositorio() -> RepositorioEnMemoria:
    return RepositorioEnMemoria()


@pytest.fixture
def datos() -> ProveedorDatosJSON:
    return ProveedorDatosJSON()


@pytest.fixture
def cliente(repositorio) -> TestClient:
    return TestClient(crear_app(repositorio=repositorio))
