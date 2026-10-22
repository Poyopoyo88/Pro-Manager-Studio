"""Inyección de dependencias: construye los controladores a partir del estado de la app."""

from __future__ import annotations

from fastapi import Request

from ...aplicacion import (
    ControladorCarrera,
    ControladorClub,
    ControladorPartido,
    ControladorPlantilla,
    ControladorVestuario,
)


def carrera(request: Request) -> ControladorCarrera:
    return ControladorCarrera(request.app.state.repositorio, request.app.state.datos)


def plantilla(request: Request) -> ControladorPlantilla:
    return ControladorPlantilla(request.app.state.repositorio)


def vestuario(request: Request) -> ControladorVestuario:
    return ControladorVestuario(request.app.state.repositorio)


def partido(request: Request) -> ControladorPartido:
    return ControladorPartido(request.app.state.repositorio)


def club(request: Request) -> ControladorClub:
    return ControladorClub(request.app.state.repositorio)
