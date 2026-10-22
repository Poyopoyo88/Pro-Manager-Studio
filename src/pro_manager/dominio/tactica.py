"""Configuración táctica y alineación (HU-01)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .club import Club
from .enums import Mentalidad, Posicion
from .errores import AlineacionInvalidaError, JugadorNoEncontradoError

TITULARES = 11
MAX_SUPLENTES = 9

# Jugadores de campo por línea (defensas, mediocampistas, delanteros).
FORMACIONES: dict[str, dict[Posicion, int]] = {
    "4-4-2": {Posicion.DEFENSA: 4, Posicion.MEDIOCAMPISTA: 4, Posicion.DELANTERO: 2},
    "4-3-3": {Posicion.DEFENSA: 4, Posicion.MEDIOCAMPISTA: 3, Posicion.DELANTERO: 3},
    "4-2-3-1": {Posicion.DEFENSA: 4, Posicion.MEDIOCAMPISTA: 5, Posicion.DELANTERO: 1},
    "3-5-2": {Posicion.DEFENSA: 3, Posicion.MEDIOCAMPISTA: 5, Posicion.DELANTERO: 2},
    "5-3-2": {Posicion.DEFENSA: 5, Posicion.MEDIOCAMPISTA: 3, Posicion.DELANTERO: 2},
}


@dataclass
class Alineacion:
    formacion: str
    titulares: list[str]
    suplentes: list[str] = field(default_factory=list)
    mentalidad: Mentalidad = Mentalidad.EQUILIBRADA

    def __post_init__(self) -> None:
        self.mentalidad = Mentalidad(self.mentalidad)
        self.titulares = list(self.titulares)
        self.suplentes = list(self.suplentes)

    def errores(self, club: Club) -> list[str]:
        """Reglas duras: si devuelve algo, la alineación no puede usarse."""
        errores: list[str] = []
        if self.formacion not in FORMACIONES:
            errores.append(
                f"La formación '{self.formacion}' no existe. Opciones: {', '.join(FORMACIONES)}."
            )
        if len(self.titulares) != TITULARES:
            errores.append(f"Debe haber exactamente {TITULARES} titulares ({len(self.titulares)}).")
        if len(self.suplentes) > MAX_SUPLENTES:
            errores.append(f"Se permiten como máximo {MAX_SUPLENTES} suplentes.")
        todos = self.titulares + self.suplentes
        if len(set(todos)) != len(todos):
            errores.append("Un jugador aparece más de una vez en la convocatoria.")

        porteros = 0
        for jugador_id in self.titulares:
            try:
                jugador = club.obtener_jugador(jugador_id)
            except JugadorNoEncontradoError:
                errores.append(f"El jugador '{jugador_id}' no pertenece a {club.nombre}.")
                continue
            if jugador.posicion == Posicion.PORTERO:
                porteros += 1
            if not jugador.habilitado:
                errores.append(f"No puede ser titular: {jugador.motivo_inhabilitacion()}")
        for jugador_id in self.suplentes:
            try:
                jugador = club.obtener_jugador(jugador_id)
            except JugadorNoEncontradoError:
                errores.append(f"El jugador '{jugador_id}' no pertenece a {club.nombre}.")
                continue
            if not jugador.convocable:
                errores.append(f"No puede ser convocado: {jugador.motivo_inhabilitacion()}")
        if len(self.titulares) == TITULARES and porteros != 1:
            errores.append(f"Debe haber exactamente un portero titular ({porteros}).")
        return errores

    def validar(self, club: Club) -> None:
        errores = self.errores(club)
        if errores:
            raise AlineacionInvalidaError(errores)

    def advertencias(self, club: Club) -> list[str]:
        """Reglas blandas: avisos que no impiden jugar (jugadores fuera de posición)."""
        if self.formacion not in FORMACIONES:
            return []
        conteo = {p: 0 for p in FORMACIONES[self.formacion]}
        for jugador_id in self.titulares:
            if club.tiene_jugador(jugador_id):
                posicion = club.obtener_jugador(jugador_id).posicion
                if posicion in conteo:
                    conteo[posicion] += 1
        avisos = []
        for posicion, requeridos in FORMACIONES[self.formacion].items():
            if conteo[posicion] != requeridos:
                avisos.append(
                    f"La {self.formacion} pide {requeridos} {posicion.value} "
                    f"y alineaste {conteo[posicion]}."
                )
        return avisos


def sugerir_alineacion(
    club: Club, formacion: str = "4-4-2", mentalidad: Mentalidad = Mentalidad.EQUILIBRADA
) -> Alineacion:
    """Elige a los mejores disponibles por rendimiento para cada línea.

    Si una línea no tiene suficientes jugadores, se completa con los mejores
    jugadores de campo restantes (fuera de posición).
    """
    if formacion not in FORMACIONES:
        raise AlineacionInvalidaError([f"La formación '{formacion}' no existe."])

    def ordenar(jugadores):
        return sorted(jugadores, key=lambda j: j.calcular_rendimiento_actual(), reverse=True)

    disponibles = ordenar([j for j in club.plantilla if j.habilitado])
    elegidos: list = []

    porteros = [j for j in disponibles if j.posicion == Posicion.PORTERO]
    if porteros:
        elegidos.append(porteros[0])
    for posicion, cantidad in FORMACIONES[formacion].items():
        de_linea = [j for j in disponibles if j.posicion == posicion and j not in elegidos]
        elegidos.extend(de_linea[:cantidad])
    restantes = [j for j in disponibles if j not in elegidos and j.posicion != Posicion.PORTERO]
    while len(elegidos) < TITULARES and restantes:
        elegidos.append(restantes.pop(0))

    banca_candidatos = [j for j in disponibles if j not in elegidos]
    suplentes = []
    portero_suplente = next((j for j in banca_candidatos if j.posicion == Posicion.PORTERO), None)
    if portero_suplente:
        suplentes.append(portero_suplente)
    for jugador in banca_candidatos:
        if len(suplentes) >= MAX_SUPLENTES:
            break
        if jugador not in suplentes and jugador.posicion != Posicion.PORTERO:
            suplentes.append(jugador)

    return Alineacion(
        formacion=formacion,
        titulares=[j.id for j in elegidos],
        suplentes=[j.id for j in suplentes],
        mentalidad=mentalidad,
    )
