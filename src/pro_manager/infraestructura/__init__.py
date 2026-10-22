"""Capa de Infraestructura: persistencia de partidas y lectura de archivos de datos."""

from .config import crear_repositorio_desde_entorno
from .datos_iniciales import ProveedorDatosJSON
from .repositorios import RepositorioEnMemoria, RepositorioJSON

__all__ = [
    "ProveedorDatosJSON",
    "RepositorioEnMemoria",
    "RepositorioJSON",
    "crear_repositorio_desde_entorno",
]
