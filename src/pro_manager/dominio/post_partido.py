"""Consecuencias de un partido terminado sobre el club, el DT y los jugadores."""

from __future__ import annotations

from dataclasses import dataclass, field

from .director_tecnico import DirectorTecnico
from .enums import EstadoAnimo, EstadoPartido, EventoAnimo, Resultado
from .errores import EstadoInvalidoError
from .partido import Partido
from .temporada import ResultadoJornada


@dataclass
class ResumenPostPartido:
    resultado: Resultado
    marcador: str
    jornada: ResultadoJornada
    cambios: list[str] = field(default_factory=list)


class ProcesadorPostPartido:
    PREMIO_VICTORIA = 250_000
    PREMIO_EMPATE = 80_000
    TAQUILLA_LOCAL = 150_000
    RECUPERACION_FISICA = 25
    MORAL_VICTORIA = 5
    MORAL_DERROTA = -5
    MORAL_SIN_MINUTOS = -4
    REPUTACION_DT = {Resultado.VICTORIA: 3, Resultado.EMPATE: 0, Resultado.DERROTA: -3}
    # Los N jugadores de mayor calidad esperan jugar. Si se quedan sin minutos
    # PARTIDOS_PARA_MOLESTIA partidos seguidos, se dispara «falta de minutos».
    GRUPO_CON_EXPECTATIVA = 15
    PARTIDOS_PARA_MOLESTIA = 2

    def procesar(self, partido: Partido, dt: DirectorTecnico) -> ResumenPostPartido:
        if partido.estado != EstadoPartido.FINALIZADO:
            raise EstadoInvalidoError("Solo se procesa un partido finalizado.")
        if partido.club_usuario_id is None:
            raise EstadoInvalidoError("El partido no tiene un club controlado por el usuario.")
        club = partido.club(partido.club_usuario_id)
        rival = partido.rival_de(club.id)
        resultado = partido.resultado_para(club.id)
        cambios: list[str] = []

        # 1) Director Técnico y club
        multiplicador = 2 if partido.es_decisivo else 1
        dt.sumar_partido_dirigido()
        delta_rep = dt.ajustar_reputacion(self.REPUTACION_DT[resultado] * multiplicador)
        if delta_rep:
            cambios.append(f"Reputación del DT {delta_rep:+d}")
        if resultado != Resultado.EMPATE:
            club.ajustar_reputacion(1 if resultado == Resultado.VICTORIA else -1)

        # 2) Finanzas (HU-06)
        if partido.local.id == club.id:
            club.registrar_ingreso(
                f"Taquilla jornada {partido.jornada}", self.TAQUILLA_LOCAL, partido.jornada
            )
            cambios.append(f"Taquilla +${self.TAQUILLA_LOCAL:,}")
        premio = {Resultado.VICTORIA: self.PREMIO_VICTORIA, Resultado.EMPATE: self.PREMIO_EMPATE}
        if resultado in premio:
            club.registrar_ingreso(
                f"Premio por {resultado.value.lower()} (jornada {partido.jornada})",
                premio[resultado],
                partido.jornada,
            )
            cambios.append(f"Premio +${premio[resultado]:,}")

        # 3) Jugadores: moral, estado de ánimo y bajas
        participantes = set(partido.participantes[club.id])
        con_expectativa = {
            j.id
            for j in sorted(club.plantilla, key=lambda j: j.calidad, reverse=True)[
                : self.GRUPO_CON_EXPECTATIVA
            ]
        }
        for jugador in club.plantilla:
            if jugador.id in participantes:
                jugador.partidos_sin_jugar = 0
                if resultado == Resultado.VICTORIA:
                    jugador.actualizar_moral(self.MORAL_VICTORIA)
                    jugador.aplicar_evento_animo(EventoAnimo.VICTORIA)
                elif resultado == Resultado.DERROTA:
                    jugador.actualizar_moral(self.MORAL_DERROTA)
                    jugador.aplicar_evento_animo(EventoAnimo.DERROTA)
            elif jugador.id in con_expectativa and jugador.habilitado:
                jugador.partidos_sin_jugar += 1
                jugador.actualizar_moral(self.MORAL_SIN_MINUTOS)
                previo = jugador.estado_animo
                if (
                    jugador.partidos_sin_jugar >= self.PARTIDOS_PARA_MOLESTIA
                    and jugador.aplicar_evento_animo(EventoAnimo.FALTA_DE_MINUTOS)
                ):
                    cambios.append(
                        f"{jugador.nombre} lleva {jugador.partidos_sin_jugar} partidos sin jugar: "
                        f"{previo.value} → {jugador.estado_animo.value}"
                    )

            jugador.recuperar(self.RECUPERACION_FISICA)

            if jugador.partidos_lesion and jugador.id not in partido.lesionados_en_partido:
                jugador.partidos_lesion -= 1
                if not jugador.lesionado:
                    cambios.append(f"{jugador.nombre} se recuperó de su lesión")
            if jugador.id in partido.expulsados:
                jugador.suspender(1)
                cambios.append(f"{jugador.nombre} suspendido un partido por expulsión")
            elif jugador.partidos_suspension:
                jugador.partidos_suspension -= 1
            if jugador.partidos_castigo:
                jugador.partidos_castigo -= 1
                if jugador.partidos_castigo == 0:
                    cambios.append(f"{jugador.nombre} cumplió su sanción interna")
                    if jugador.estado_animo == EstadoAnimo.REBELDE:
                        jugador.aplicar_evento_animo(EventoAnimo.SANCION_CUMPLIDA)
                        cambios.append(f"{jugador.nombre}: REBELDE → ESTABLE")

        es_local = partido.local.id == club.id
        resumen_jornada = ResultadoJornada(
            jornada=partido.jornada,
            rival_id=rival.id,
            rival_nombre=rival.nombre,
            local=es_local,
            goles_favor=partido.goles[club.id],
            goles_contra=partido.goles[rival.id],
            resultado=resultado,
        )
        return ResumenPostPartido(resultado, partido.marcador, resumen_jornada, cambios)
