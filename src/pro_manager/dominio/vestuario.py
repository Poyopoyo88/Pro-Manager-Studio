"""Sistema de vestuario: eventos y su resolución (HU-04).

Diagrama de secuencia de la sección 10 (gestión de crisis)::

    DT ─▶ ControladorVestuario ─▶ GestorVestuario
    alt  sanciona → reduce moral del Jugador y solicita aval al Club
    else dialoga  → equilibra la moral de los involucrados
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .atributos import acotar
from .club import Club
from .director_tecnico import DirectorTecnico
from .enums import AccionDT, EstadoAnimo, EventoAnimo, Personalidad, TipoEventoVestuario
from .errores import EventoYaResueltoError
from .jugador import Jugador


@dataclass
class EventoVestuario:
    id: str
    tipo: TipoEventoVestuario
    titulo: str
    descripcion: str
    protagonista_id: str
    afectado_id: str | None = None
    jornada: int = 1
    severidad: int = 10
    resuelto: bool = False
    accion_tomada: AccionDT | None = None
    desenlace: str | None = None

    def __post_init__(self) -> None:
        self.tipo = TipoEventoVestuario(self.tipo)
        if self.accion_tomada is not None:
            self.accion_tomada = AccionDT(self.accion_tomada)

    def marcar_resuelto(self, accion: AccionDT, desenlace: str) -> None:
        if self.resuelto:
            raise EventoYaResueltoError(f"El evento '{self.titulo}' ya fue resuelto.")
        self.resuelto = True
        self.accion_tomada = AccionDT(accion)
        self.desenlace = desenlace


@dataclass(frozen=True)
class ResultadoResolucion:
    evento_id: str
    accion: AccionDT
    resuelto: bool
    aval_directiva: bool | None
    desenlace: str
    cambios: list[str] = field(default_factory=list)


class GestorVestuario:
    REPUTACION_SANCION_AVALADA = 2
    REPUTACION_SANCION_RECHAZADA = -3
    REPUTACION_DIALOGO = -2
    BONO_DIALOGO = 4
    BONO_DIALOGO_INDIVIDUAL = 8
    PROB_QUEJA_SI_MOLESTO = 0.6
    PROB_CONFLICTO = 0.2
    PROB_RUMOR = 0.15
    CALIDAD_MINIMA_RUMOR = 75

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    # ------------------------------------------------------------------
    # Resolución (HU-04, flujo alternativo de la sección 10)
    # ------------------------------------------------------------------
    def resolver(
        self, evento: EventoVestuario, accion: AccionDT, club: Club, dt: DirectorTecnico
    ) -> ResultadoResolucion:
        if evento.resuelto:
            raise EventoYaResueltoError(f"El evento '{evento.titulo}' ya fue resuelto.")
        accion = AccionDT(accion)
        protagonista = club.obtener_jugador(evento.protagonista_id)
        afectado = club.obtener_jugador(evento.afectado_id) if evento.afectado_id else None
        if accion == AccionDT.SANCIONAR:
            return self._sancionar(evento, club, dt, protagonista, afectado)
        return self._dialogar(evento, dt, protagonista, afectado)

    def _sancionar(
        self,
        evento: EventoVestuario,
        club: Club,
        dt: DirectorTecnico,
        protagonista: Jugador,
        afectado: Jugador | None,
    ) -> ResultadoResolucion:
        if not club.avalar_sancion(protagonista, dt):
            dt.ajustar_reputacion(self.REPUTACION_SANCION_RECHAZADA)
            return ResultadoResolucion(
                evento_id=evento.id,
                accion=AccionDT.SANCIONAR,
                resuelto=False,
                aval_directiva=False,
                desenlace=(
                    f"La directiva no respalda la sanción contra {protagonista.nombre}. "
                    "Tu autoridad queda en entredicho; prueba con el diálogo."
                ),
                cambios=[f"Reputación del DT {self.REPUTACION_SANCION_RECHAZADA}"],
            )

        cambios: list[str] = []
        delta = protagonista.actualizar_moral(-evento.severidad)
        cambios.append(f"Moral de {protagonista.nombre} {delta:+d}")
        protagonista.castigar(1)
        cambios.append(f"{protagonista.nombre} va a la banca: no podrá jugar el próximo partido")
        estado_previo = protagonista.estado_animo
        if protagonista.aplicar_evento_animo(EventoAnimo.SANCION_SEVERA):
            cambios.append(
                f"{protagonista.nombre}: {estado_previo.value} → {protagonista.estado_animo.value}"
            )
        if afectado:
            delta_afectado = afectado.actualizar_moral(evento.severidad // 2)
            cambios.append(f"Moral de {afectado.nombre} {delta_afectado:+d} (se siente respaldado)")
        dt.ajustar_reputacion(self.REPUTACION_SANCION_AVALADA)
        cambios.append(f"Reputación del DT +{self.REPUTACION_SANCION_AVALADA}")

        if protagonista.estado_animo == EstadoAnimo.REBELDE:
            desenlace = (
                f"Sancionaste a {protagonista.nombre}. Acepta la banca a regañadientes: seguirá "
                "Rebelde hasta cumplir la sanción o hasta que medies con él."
            )
        else:
            desenlace = f"Sancionaste a {protagonista.nombre}. El vestuario entiende el mensaje."
        protagonista.registrar_historia(
            f"Jornada {evento.jornada}: sancionado y enviado a la banca ({evento.titulo})."
        )
        evento.marcar_resuelto(AccionDT.SANCIONAR, desenlace)
        return ResultadoResolucion(evento.id, AccionDT.SANCIONAR, True, True, desenlace, cambios)

    def _dialogar(
        self,
        evento: EventoVestuario,
        dt: DirectorTecnico,
        protagonista: Jugador,
        afectado: Jugador | None,
    ) -> ResultadoResolucion:
        cambios: list[str] = []
        if afectado:
            promedio = (protagonista.moral + afectado.moral) // 2
            for jugador in (protagonista, afectado):
                anterior = jugador.moral
                jugador.moral = acotar(promedio + self.BONO_DIALOGO)
                cambios.append(f"Moral de {jugador.nombre} {jugador.moral - anterior:+d}")
        else:
            delta = protagonista.actualizar_moral(self.BONO_DIALOGO_INDIVIDUAL)
            cambios.append(f"Moral de {protagonista.nombre} {delta:+d}")
        estado_previo = protagonista.estado_animo
        if protagonista.aplicar_evento_animo(EventoAnimo.MEDIACION_COMPLETADA):
            cambios.append(
                f"{protagonista.nombre}: {estado_previo.value} → {protagonista.estado_animo.value}"
            )
        dt.ajustar_reputacion(self.REPUTACION_DIALOGO)
        cambios.append(
            f"Reputación del DT {self.REPUTACION_DIALOGO} (algunos lo ven como debilidad)"
        )
        desenlace = f"Mediaste con {protagonista.nombre}" + (
            f" y {afectado.nombre}. Se dan la mano frente al grupo." if afectado else "."
        )
        protagonista.registrar_historia(
            f"Jornada {evento.jornada}: el DT medió tras «{evento.titulo}»."
        )
        evento.marcar_resuelto(AccionDT.DIALOGAR, desenlace)
        return ResultadoResolucion(evento.id, AccionDT.DIALOGAR, True, None, desenlace, cambios)

    # ------------------------------------------------------------------
    # Narrativa dinámica: generación de eventos tras cada jornada
    # ------------------------------------------------------------------
    def generar_evento(
        self, club: Club, jornada: int, evento_id: str, eventos_existentes: list[EventoVestuario]
    ) -> EventoVestuario | None:
        ocupados = {e.protagonista_id for e in eventos_existentes if not e.resuelto}
        libres = [j for j in club.plantilla if j.id not in ocupados]

        rebeldes = [j for j in libres if j.estado_animo == EstadoAnimo.REBELDE]
        rebeldes_libres = [j for j in rebeldes if j.partidos_castigo == 0]
        if rebeldes_libres:
            return self._indisciplina(rebeldes_libres[0], jornada, evento_id)

        molestos = [j for j in libres if j.estado_animo == EstadoAnimo.MOLESTO]
        if molestos and self.rng.random() < self.PROB_QUEJA_SI_MOLESTO:
            return self._queja(self.rng.choice(molestos), jornada, evento_id)

        tirada = self.rng.random()
        if tirada < self.PROB_CONFLICTO:
            return self._conflicto(club, libres, jornada, evento_id)
        if tirada < self.PROB_CONFLICTO + self.PROB_RUMOR:
            figuras = [j for j in libres if j.calidad >= self.CALIDAD_MINIMA_RUMOR]
            if figuras:
                return self._rumor(self.rng.choice(figuras), jornada, evento_id)
        return None

    def _indisciplina(self, jugador: Jugador, jornada: int, evento_id: str) -> EventoVestuario:
        return EventoVestuario(
            id=evento_id,
            tipo=TipoEventoVestuario.INDISCIPLINA,
            titulo=f"{jugador.nombre} desafía al cuerpo técnico",
            descripcion=(
                f"{jugador.nombre} llegó tarde al entrenamiento y respondió de mala manera al "
                "auxiliar. Mientras siga Rebelde necesita una mediación o una sanción."
            ),
            protagonista_id=jugador.id,
            jornada=jornada,
            severidad=12,
        )

    def _queja(self, jugador: Jugador, jornada: int, evento_id: str) -> EventoVestuario:
        motivo = self.rng.choice(
            [
                "pide explicaciones en tu oficina por su falta de minutos",
                "dio una entrevista diciendo que no entiende por qué no juega",
                "publicó un mensaje ambiguo en redes tras quedarse en la banca",
            ]
        )
        return EventoVestuario(
            id=evento_id,
            tipo=TipoEventoVestuario.QUEJA_POR_MINUTOS,
            titulo=f"{jugador.nombre} se queja por sus minutos",
            descripcion=f"{jugador.nombre} {motivo}.",
            protagonista_id=jugador.id,
            jornada=jornada,
            severidad=8,
        )

    def _conflicto(
        self, club: Club, libres: list[Jugador], jornada: int, evento_id: str
    ) -> EventoVestuario | None:
        if len(libres) < 2:
            return None
        pesos = [
            3.0 if j.personalidad in (Personalidad.TEMPERAMENTAL, Personalidad.AMBICIOSO) else 1.0
            for j in libres
        ]
        protagonista = self.rng.choices(libres, weights=pesos, k=1)[0]
        capitan = club.capitan()
        if capitan and capitan.id != protagonista.id and capitan in libres:
            afectado = capitan
        else:
            afectado = self.rng.choice([j for j in libres if j.id != protagonista.id])
        escena = self.rng.choice(
            [
                "discuten a gritos tras una entrada fuerte en el entrenamiento",
                "se enfrentan en el vestuario por quién cobra los penales",
                "tienen un roce en el comedor que termina con empujones",
            ]
        )
        return EventoVestuario(
            id=evento_id,
            tipo=TipoEventoVestuario.CONFLICTO_ENTRE_JUGADORES,
            titulo=f"Roce entre {protagonista.nombre} y {afectado.nombre}",
            descripcion=f"{protagonista.nombre} y {afectado.nombre} {escena}.",
            protagonista_id=protagonista.id,
            afectado_id=afectado.id,
            jornada=jornada,
            severidad=10,
        )

    def _rumor(self, jugador: Jugador, jornada: int, evento_id: str) -> EventoVestuario:
        return EventoVestuario(
            id=evento_id,
            tipo=TipoEventoVestuario.RUMOR_TRANSFERENCIA,
            titulo=f"Rumores de salida de {jugador.nombre}",
            descripcion=(
                f"La prensa asegura que un club de Primera División quiere a {jugador.nombre}. "
                "Se le nota distraído en los entrenamientos."
            ),
            protagonista_id=jugador.id,
            jornada=jornada,
            severidad=8,
        )
