"""Repositorios de partidas guardadas (implementan ``RepositorioPartidas``)."""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path

from ..aplicacion.errores import PartidaNoEncontradaError
from ..aplicacion.partida import Partida
from .serializacion import partida_a_dict, partida_desde_dict

_ID_VALIDO = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _validar_id(partida_id: str) -> str:
    # Evita que un identificador manipulado escape del directorio (path traversal).
    if not _ID_VALIDO.match(partida_id or ""):
        raise PartidaNoEncontradaError(f"No existe la partida '{partida_id}'.")
    return partida_id


class RepositorioEnMemoria:
    """Guarda las partidas serializadas en memoria.

    Serializar en cada guardado hace que el repositorio se comporte igual que el de
    archivos (cada lectura devuelve una copia independiente) y ejercita el mapeador.
    """

    def __init__(self) -> None:
        self._datos: dict[str, str] = {}
        self._candado = threading.Lock()

    def guardar(self, partida: Partida) -> None:
        with self._candado:
            self._datos[partida.id] = json.dumps(partida_a_dict(partida), ensure_ascii=False)

    def obtener(self, partida_id: str) -> Partida:
        with self._candado:
            contenido = self._datos.get(partida_id)
        if contenido is None:
            raise PartidaNoEncontradaError(f"No existe la partida '{partida_id}'.")
        return partida_desde_dict(json.loads(contenido))

    def listar(self) -> list[str]:
        with self._candado:
            return sorted(self._datos)

    def eliminar(self, partida_id: str) -> None:
        with self._candado:
            if self._datos.pop(partida_id, None) is None:
                raise PartidaNoEncontradaError(f"No existe la partida '{partida_id}'.")


class RepositorioJSON:
    """Guarda cada partida en ``<directorio>/<id>.json`` con escritura atómica."""

    def __init__(self, directorio: Path | str) -> None:
        self.directorio = Path(directorio)
        self.directorio.mkdir(parents=True, exist_ok=True)
        self._candado = threading.Lock()

    def _ruta(self, partida_id: str) -> Path:
        return self.directorio / f"{_validar_id(partida_id)}.json"

    def guardar(self, partida: Partida) -> None:
        ruta = self._ruta(partida.id)
        temporal = ruta.with_suffix(".json.tmp")
        contenido = json.dumps(partida_a_dict(partida), ensure_ascii=False, indent=2)
        with self._candado:
            temporal.write_text(contenido, encoding="utf-8")
            os.replace(temporal, ruta)

    def obtener(self, partida_id: str) -> Partida:
        ruta = self._ruta(partida_id)
        if not ruta.exists():
            raise PartidaNoEncontradaError(f"No existe la partida '{partida_id}'.")
        return partida_desde_dict(json.loads(ruta.read_text(encoding="utf-8")))

    def listar(self) -> list[str]:
        return sorted(r.stem for r in self.directorio.glob("*.json"))

    def eliminar(self, partida_id: str) -> None:
        ruta = self._ruta(partida_id)
        if not ruta.exists():
            raise PartidaNoEncontradaError(f"No existe la partida '{partida_id}'.")
        ruta.unlink()
