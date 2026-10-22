"""Temporada: calendario de jornadas, puntos y objetivo de ascenso."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import Resultado
from .errores import DatoInvalidoError, TemporadaFinalizadaError

PUNTOS_POR_RESULTADO = {Resultado.VICTORIA: 3, Resultado.EMPATE: 1, Resultado.DERROTA: 0}


@dataclass(frozen=True)
class ResultadoJornada:
    jornada: int
    rival_id: str
    rival_nombre: str
    local: bool
    goles_favor: int
    goles_contra: int
    resultado: Resultado

    @property
    def puntos(self) -> int:
        return PUNTOS_POR_RESULTADO[Resultado(self.resultado)]


class Temporada:
    def __init__(
        self,
        rivales_ids: list[str],
        puntos_ascenso: int,
        jornada_actual: int = 1,
        historial: list[ResultadoJornada] | None = None,
    ) -> None:
        if not rivales_ids:
            raise DatoInvalidoError("La temporada necesita al menos un rival.")
        self.rivales_ids = list(rivales_ids)
        self.puntos_ascenso = puntos_ascenso
        self.jornada_actual = jornada_actual
        self.historial: list[ResultadoJornada] = list(historial or [])

    @property
    def total_jornadas(self) -> int:
        return len(self.rivales_ids)

    @property
    def finalizada(self) -> bool:
        return self.jornada_actual > self.total_jornadas

    def rival_de_jornada(self) -> str:
        if self.finalizada:
            raise TemporadaFinalizadaError("La temporada ya terminó.")
        return self.rivales_ids[self.jornada_actual - 1]

    def es_local(self, jornada: int | None = None) -> bool:
        """Jornadas impares en casa, pares de visitante."""
        return (jornada or self.jornada_actual) % 2 == 1

    def es_decisiva(self, jornada: int | None = None) -> bool:
        return (jornada or self.jornada_actual) == self.total_jornadas

    def registrar(self, resultado: ResultadoJornada) -> None:
        if self.finalizada:
            raise TemporadaFinalizadaError("La temporada ya terminó.")
        self.historial.append(resultado)
        self.jornada_actual += 1

    @property
    def puntos(self) -> int:
        return sum(r.puntos for r in self.historial)

    def record(self) -> dict[str, int]:
        conteo = {r.value: 0 for r in Resultado}
        for r in self.historial:
            conteo[Resultado(r.resultado).value] += 1
        return conteo

    @property
    def ascendio(self) -> bool | None:
        """``None`` mientras la temporada sigue; luego si se alcanzó la meta de puntos."""
        if not self.finalizada:
            return None
        return self.puntos >= self.puntos_ascenso
