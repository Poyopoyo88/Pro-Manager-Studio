"""Entidad DirectorTecnico: el avatar del usuario."""

from __future__ import annotations

from .atributos import acotar, validar_atributo
from .enums import EventoAnimo
from .errores import DatoInvalidoError, EstadoInvalidoError
from .jugador import Jugador


class DirectorTecnico:
    IMPACTO_ELOGIO = 6

    def __init__(
        self,
        nombre: str,
        experiencia: int = 0,
        reputacion: int = 50,
        ultima_jornada_elogio: int | None = None,
    ) -> None:
        if not nombre or not nombre.strip():
            raise DatoInvalidoError("El Director Técnico necesita un nombre.")
        if experiencia < 0:
            raise DatoInvalidoError("La experiencia no puede ser negativa.")
        self.nombre = nombre.strip()
        self.experiencia = experiencia  # partidos dirigidos
        self.reputacion = reputacion
        self.ultima_jornada_elogio = ultima_jornada_elogio

    def elogiar(self, jugador: Jugador, jornada: int) -> bool:
        """Elogio público: un uso por jornada para que conserve su valor.

        Sube la moral y dispara la transición Estable → Motivado. Devuelve si
        cambió el estado de ánimo.
        """
        if self.ultima_jornada_elogio == jornada:
            raise EstadoInvalidoError(
                "Ya elogiaste a un jugador en esta jornada; un elogio repetido pierde valor."
            )
        self.ultima_jornada_elogio = jornada
        jugador.actualizar_moral(self.IMPACTO_ELOGIO)
        jugador.registrar_historia(f"Jornada {jornada}: recibió un elogio público del DT.")
        return jugador.aplicar_evento_animo(EventoAnimo.ELOGIO)

    @property
    def reputacion(self) -> int:
        return self._reputacion

    @reputacion.setter
    def reputacion(self, valor: int) -> None:
        self._reputacion = validar_atributo("reputacion", valor)

    def ajustar_reputacion(self, delta: int) -> int:
        """Suma ``delta`` saturando en [1, 100]; devuelve el cambio real."""
        anterior = self._reputacion
        self._reputacion = acotar(self._reputacion + delta)
        return self._reputacion - anterior

    def sumar_partido_dirigido(self) -> None:
        self.experiencia += 1
