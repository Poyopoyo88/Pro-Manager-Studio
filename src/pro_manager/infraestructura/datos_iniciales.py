"""Lectura de archivos de datos y generación procedural de rivales y mercado."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from ..dominio import (
    Club,
    EventoVestuario,
    Jugador,
    JugadorEnMercado,
    Personalidad,
    Posicion,
)
from ..dominio.atributos import acotar

RUTA_DATOS = Path(__file__).parent / "datos" / "club_inicial.json"

# Composición de la plantilla de un rival generado.
COMPOSICION_RIVAL = {
    Posicion.PORTERO: 2,
    Posicion.DEFENSA: 6,
    Posicion.MEDIOCAMPISTA: 6,
    Posicion.DELANTERO: 4,
}


def valor_estimado(calidad: int, edad: int) -> int:
    """Valor de mercado aproximado (MXN) según calidad y edad."""
    base = max(0, calidad - 50) ** 2 * 4000 + 150_000
    if edad <= 22:
        base *= 1.3
    elif edad >= 31:
        base *= 0.6
    return int(round(base, -4))


def salario_estimado(calidad: int) -> int:
    """Salario mensual pretendido (MXN) según calidad."""
    return int(round(max(15_000, (calidad - 45) * 2500), -3))


class ProveedorDatosJSON:
    """Implementa ``ProveedorDatosIniciales`` a partir de un archivo JSON."""

    def __init__(self, ruta: Path | str = RUTA_DATOS) -> None:
        self.ruta = Path(ruta)
        self._datos: dict[str, Any] = json.loads(self.ruta.read_text(encoding="utf-8"))
        self.puntos_ascenso: int = self._datos["puntos_ascenso"]

    # -- Club del usuario ------------------------------------------------
    def crear_club_usuario(self) -> Club:
        datos_club = self._datos["club"]
        plantilla = [Jugador(**j) for j in self._datos["plantilla"]]
        return Club(plantilla=plantilla, **datos_club)

    def eventos_iniciales(self, club: Club) -> list[EventoVestuario]:
        eventos = []
        for i, datos in enumerate(self._datos.get("eventos_iniciales", []), start=1):
            if not club.tiene_jugador(datos["protagonista_id"]):
                continue
            eventos.append(EventoVestuario(id=f"EV-{i:03d}", jornada=1, **datos))
        return eventos

    # -- Generación procedural -------------------------------------------
    def _nombre(self, rng: random.Random) -> str:
        return f"{rng.choice(self._datos['nombres'])} {rng.choice(self._datos['apellidos'])}"

    def _jugador_generado(
        self, rng: random.Random, jugador_id: str, posicion: Posicion, nivel: int
    ) -> Jugador:
        calidad = acotar(rng.gauss(nivel, 5))
        edad = rng.randint(18, 34)
        return Jugador(
            id=jugador_id,
            nombre=self._nombre(rng),
            posicion=posicion,
            calidad=calidad,
            fisico=rng.randint(78, 92),
            moral=rng.randint(55, 75),
            personalidad=rng.choice(list(Personalidad)),
            edad=edad,
            salario=salario_estimado(calidad),
            valor_mercado=valor_estimado(calidad, edad),
        )

    def crear_rivales(self, rng: random.Random) -> list[Club]:
        rivales = []
        for datos in self._datos["rivales"]:
            plantilla = []
            numero = 1
            for posicion, cantidad in COMPOSICION_RIVAL.items():
                for _ in range(cantidad):
                    plantilla.append(
                        self._jugador_generado(
                            rng, f"{datos['id']}-{numero:02d}", posicion, datos["nivel"]
                        )
                    )
                    numero += 1
            masa = sum(j.salario for j in plantilla)
            rivales.append(
                Club(
                    id=datos["id"],
                    nombre=datos["nombre"],
                    ciudad=datos["ciudad"],
                    presupuesto_fichajes=0,
                    limite_masa_salarial=masa,
                    reputacion=datos["nivel"] - 20,
                    plantilla=plantilla,
                )
            )
        return rivales

    def crear_mercado(self, rng: random.Random, cantidad: int = 10) -> list[JugadorEnMercado]:
        posiciones = [
            Posicion.PORTERO,
            Posicion.DEFENSA,
            Posicion.DEFENSA,
            Posicion.DEFENSA,
            Posicion.MEDIOCAMPISTA,
            Posicion.MEDIOCAMPISTA,
            Posicion.MEDIOCAMPISTA,
            Posicion.DELANTERO,
            Posicion.DELANTERO,
            Posicion.DELANTERO,
        ]
        mercado = []
        for i in range(cantidad):
            posicion = posiciones[i % len(posiciones)]
            jugador = self._jugador_generado(rng, f"mer-{i + 1:02d}", posicion, rng.randint(64, 80))
            jugador.historia.append("Disponible en el mercado de transferencias.")
            mercado.append(JugadorEnMercado(jugador, rng.choice(self._datos["clubes_mercado"])))
        return mercado
