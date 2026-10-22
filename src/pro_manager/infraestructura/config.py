"""Configuración por variables de entorno.

* ``PM_REPOSITORIO``: ``json`` (por defecto) o ``memoria``.
* ``PM_DIRECTORIO_PARTIDAS``: carpeta de partidas guardadas (por defecto ``partidas_guardadas``).
"""

from __future__ import annotations

import os

from .repositorios import RepositorioEnMemoria, RepositorioJSON


def crear_repositorio_desde_entorno():
    tipo = os.getenv("PM_REPOSITORIO", "json").strip().lower()
    if tipo == "memoria":
        return RepositorioEnMemoria()
    if tipo == "json":
        return RepositorioJSON(os.getenv("PM_DIRECTORIO_PARTIDAS", "partidas_guardadas"))
    raise ValueError(f"PM_REPOSITORIO no reconocido: {tipo!r} (usa 'json' o 'memoria').")
