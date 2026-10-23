"""Entidad Club: presupuesto, reputación y plantilla.

Visibilidad por atributo (sección 8): el club conserva la lista interna de sus
jugadores; hacia fuera solo expone copias de esa lista.

Regla de negocio RN-02: ningún club puede exceder el presupuesto de fichajes ni
el límite de masa salarial.
"""

from __future__ import annotations

from dataclasses import dataclass

from .atributos import acotar, validar_atributo
from .director_tecnico import DirectorTecnico
from .errores import (
    DatoInvalidoError,
    JugadorNoEncontradoError,
    MasaSalarialExcedidaError,
    PresupuestoExcedidoError,
)
from .jugador import Jugador


@dataclass(frozen=True)
class MovimientoFinanciero:
    concepto: str
    monto: int  # positivo = ingreso, negativo = gasto
    jornada: int | None = None


class Club:
    # Reputación mínima del DT para que la directiva avale una sanción.
    UMBRAL_AVAL_GENERAL = 30
    UMBRAL_AVAL_FIGURA = 50
    CALIDAD_FIGURA = 85

    def __init__(
        self,
        id: str,
        nombre: str,
        ciudad: str,
        presupuesto_fichajes: int,
        limite_masa_salarial: int,
        reputacion: int = 50,
        plantilla: list[Jugador] | None = None,
        movimientos: list[MovimientoFinanciero] | None = None,
    ) -> None:
        if not id or not nombre:
            raise DatoInvalidoError("El club necesita identificador y nombre.")
        if presupuesto_fichajes < 0 or limite_masa_salarial < 0:
            raise DatoInvalidoError("El presupuesto y el límite salarial no pueden ser negativos.")
        self.id = id
        self.nombre = nombre
        self.ciudad = ciudad
        self.presupuesto_fichajes = presupuesto_fichajes
        self.limite_masa_salarial = limite_masa_salarial
        self.reputacion = validar_atributo("reputacion", reputacion)
        self._plantilla: list[Jugador] = []
        self.movimientos: list[MovimientoFinanciero] = list(movimientos or [])
        for jugador in plantilla or []:
            self.agregar_jugador(jugador)
        if self.masa_salarial() > self.limite_masa_salarial:
            raise MasaSalarialExcedidaError(
                f"La plantilla inicial de {nombre} excede su límite de masa salarial."
            )

    # ------------------------------------------------------------------
    # Plantilla
    # ------------------------------------------------------------------
    @property
    def plantilla(self) -> list[Jugador]:
        return list(self._plantilla)

    def agregar_jugador(self, jugador: Jugador) -> None:
        if self.tiene_jugador(jugador.id):
            raise DatoInvalidoError(f"{jugador.nombre} ya pertenece a {self.nombre}.")
        self._plantilla.append(jugador)

    def tiene_jugador(self, jugador_id: str) -> bool:
        return any(j.id == jugador_id for j in self._plantilla)

    def obtener_jugador(self, jugador_id: str) -> Jugador:
        for jugador in self._plantilla:
            if jugador.id == jugador_id:
                return jugador
        raise JugadorNoEncontradoError(f"No existe el jugador '{jugador_id}' en {self.nombre}.")

    def capitan(self) -> Jugador | None:
        return next((j for j in self._plantilla if j.es_capitan), None)

    # ------------------------------------------------------------------
    # Finanzas (RN-02)
    # ------------------------------------------------------------------
    def masa_salarial(self) -> int:
        return sum(j.salario for j in self._plantilla)

    def margen_salarial(self) -> int:
        return self.limite_masa_salarial - self.masa_salarial()

    def validar_fichaje(self, costo_transferencia: int, salario: int) -> None:
        if costo_transferencia < 0 or salario < 0:
            raise DatoInvalidoError("El costo y el salario no pueden ser negativos.")
        if costo_transferencia > self.presupuesto_fichajes:
            raise PresupuestoExcedidoError(
                f"El fichaje cuesta ${costo_transferencia:,} y el presupuesto disponible es "
                f"${self.presupuesto_fichajes:,}."
            )
        if self.masa_salarial() + salario > self.limite_masa_salarial:
            raise MasaSalarialExcedidaError(
                f"El salario de ${salario:,} supera el margen salarial libre "
                f"(${self.margen_salarial():,})."
            )

    def puede_fichar(self, costo_transferencia: int, salario: int) -> bool:
        try:
            self.validar_fichaje(costo_transferencia, salario)
        except (PresupuestoExcedidoError, MasaSalarialExcedidaError, DatoInvalidoError):
            return False
        return True

    def fichar(
        self, jugador: Jugador, costo_transferencia: int, jornada: int | None = None
    ) -> None:
        self.validar_fichaje(costo_transferencia, jugador.salario)
        self.agregar_jugador(jugador)
        self.presupuesto_fichajes -= costo_transferencia
        self.movimientos.append(
            MovimientoFinanciero(f"Fichaje de {jugador.nombre}", -costo_transferencia, jornada)
        )

    def registrar_ingreso(self, concepto: str, monto: int, jornada: int | None = None) -> None:
        if monto <= 0:
            raise DatoInvalidoError("Un ingreso debe ser positivo.")
        self.presupuesto_fichajes += monto
        self.movimientos.append(MovimientoFinanciero(concepto, monto, jornada))

    def registrar_gasto(self, concepto: str, monto: int, jornada: int | None = None) -> None:
        if monto <= 0:
            raise DatoInvalidoError("Un gasto debe ser positivo.")
        if monto > self.presupuesto_fichajes:
            raise PresupuestoExcedidoError(
                f"El gasto '{concepto}' (${monto:,}) excede el presupuesto disponible."
            )
        self.presupuesto_fichajes -= monto
        self.movimientos.append(MovimientoFinanciero(concepto, -monto, jornada))

    # ------------------------------------------------------------------
    # Identidad (RN-13)
    # ------------------------------------------------------------------
    LONGITUD_NOMBRE_MIN = 3
    LONGITUD_NOMBRE_MAX = 40

    def renombrar(self, nombre: str, nombres_ocupados: list[str] | tuple = ()) -> None:
        """Cambia el nombre del club (RN-13).

        Se normalizan los espacios; debe medir entre 3 y 40 caracteres y no puede
        coincidir (sin distinguir mayúsculas) con el de otro club de la liga.
        """
        limpio = " ".join((nombre or "").split())
        if not self.LONGITUD_NOMBRE_MIN <= len(limpio) <= self.LONGITUD_NOMBRE_MAX:
            raise DatoInvalidoError(
                f"El nombre del club debe tener entre {self.LONGITUD_NOMBRE_MIN} y "
                f"{self.LONGITUD_NOMBRE_MAX} caracteres."
            )
        ocupados = {" ".join(n.split()).casefold() for n in nombres_ocupados}
        if limpio.casefold() in ocupados:
            raise DatoInvalidoError(f"«{limpio}» ya lo usa otro club de la liga. Elige otro.")
        self.nombre = limpio
    
    def ajustar_reputacion(self, delta: int) -> None:
        self.reputacion = acotar(self.reputacion + delta)

    # ------------------------------------------------------------------
    # Gobierno: aval de la directiva a una sanción del DT
    # ------------------------------------------------------------------
    def avalar_sancion(self, jugador: Jugador, dt: DirectorTecnico) -> bool:
        """La directiva respalda la sanción si el DT tiene suficiente reputación.

        Sancionar a una figura (calidad ≥ 85) o al capitán exige más respaldo.
        """
        es_figura = jugador.calidad >= self.CALIDAD_FIGURA or jugador.es_capitan
        umbral = self.UMBRAL_AVAL_FIGURA if es_figura else self.UMBRAL_AVAL_GENERAL
        return dt.reputacion >= umbral
