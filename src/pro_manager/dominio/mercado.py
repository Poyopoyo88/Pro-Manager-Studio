"""Búsqueda de talento (HU-02) y negociación de fichajes (HU-03)."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .atributos import acotar, validar_atributo
from .errores import DatoInvalidoError
from .jugador import Jugador


@dataclass
class JugadorEnMercado:
    jugador: Jugador
    club_origen: str


@dataclass(frozen=True)
class InformeOjeo:
    jugador_id: str
    nombre: str
    posicion: str
    edad: int
    club_origen: str
    calidad_min: int
    calidad_max: int
    valor_mercado: int
    salario_pretendido: int
    recomendacion: str


class Ojeador:
    """Observa jugadores y estima su calidad con un margen de error.

    A mayor ``precision`` (1-100), más estrecho es el rango estimado.
    """

    def __init__(self, precision: int = 60, rng: random.Random | None = None) -> None:
        self.precision = validar_atributo("precision", precision)
        self.rng = rng or random.Random()

    @classmethod
    def del_club(cls, reputacion_club: int, rng: random.Random | None = None) -> Ojeador:
        """Un club con más reputación tiene mejores ojeadores (precisión 40-90)."""
        return cls(40 + reputacion_club // 2, rng)

    def informar(self, entrada: JugadorEnMercado) -> InformeOjeo:
        jugador = entrada.jugador
        margen = max(2, (100 - self.precision) // 4)
        centro = jugador.calidad + self.rng.randint(-margen // 2, margen // 2)
        minimo, maximo = acotar(centro - margen), acotar(centro + margen)
        estimada = (minimo + maximo) / 2
        if estimada >= 78:
            recomendacion = "Fichaje prioritario: mejoraría al once titular."
        elif estimada >= 68:
            recomendacion = "Buen complemento para la rotación."
        else:
            recomendacion = "Solo como apuesta a futuro o por precio."
        return InformeOjeo(
            jugador_id=jugador.id,
            nombre=jugador.nombre,
            posicion=jugador.posicion.value,
            edad=jugador.edad,
            club_origen=entrada.club_origen,
            calidad_min=minimo,
            calidad_max=maximo,
            valor_mercado=jugador.valor_mercado,
            salario_pretendido=jugador.salario,
            recomendacion=recomendacion,
        )


@dataclass(frozen=True)
class RespuestaNegociacion:
    aceptada: bool
    mensaje: str
    contraoferta_monto: int | None = None
    contraoferta_salario: int | None = None


class NegociadorFichajes:
    """Evalúa una oferta contra el valor de mercado y el salario pretendido."""

    UMBRAL_ACEPTACION = 0.95
    UMBRAL_RECHAZO_ROTUNDO = 0.6

    def evaluar(self, jugador: Jugador, monto: int, salario: int) -> RespuestaNegociacion:
        if monto < 0 or salario <= 0:
            raise DatoInvalidoError(
                "La oferta necesita un monto no negativo y un salario positivo."
            )
        ratio_monto = monto / jugador.valor_mercado if jugador.valor_mercado else 1.0
        ratio_salario = salario / jugador.salario if jugador.salario else 1.0
        if ratio_monto >= self.UMBRAL_ACEPTACION and ratio_salario >= self.UMBRAL_ACEPTACION:
            return RespuestaNegociacion(True, f"¡Trato hecho! {jugador.nombre} firma con tu club.")
        if min(ratio_monto, ratio_salario) < self.UMBRAL_RECHAZO_ROTUNDO:
            return RespuestaNegociacion(
                False, f"La oferta por {jugador.nombre} se considera ofensiva. Rechazada."
            )
        return RespuestaNegociacion(
            False,
            f"El representante de {jugador.nombre} pide mejorar la oferta.",
            contraoferta_monto=max(monto, jugador.valor_mercado),
            contraoferta_salario=max(salario, jugador.salario),
        )
