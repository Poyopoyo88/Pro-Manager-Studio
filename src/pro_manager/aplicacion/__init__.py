"""Capa de Aplicación / Control: coordina los casos de uso sin lógica de negocio."""

from .controladores import (
    ControladorCarrera,
    ControladorClub,
    ControladorPartido,
    ControladorPlantilla,
    ControladorVestuario,
)
from .errores import PartidaNoEncontradaError, SinPartidoError
from .partida import Partida
from .puertos import ProveedorDatosIniciales, RepositorioPartidas

__all__ = [
    "ControladorCarrera",
    "ControladorClub",
    "ControladorPartido",
    "ControladorPlantilla",
    "ControladorVestuario",
    "Partida",
    "PartidaNoEncontradaError",
    "ProveedorDatosIniciales",
    "RepositorioPartidas",
    "SinPartidoError",
]
