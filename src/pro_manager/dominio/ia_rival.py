"""Comportamiento del entrenador rival controlado por la computadora."""

from __future__ import annotations

from .enums import Mentalidad, Resultado
from .errores import ErrorDominio
from .jugador import Jugador
from .partido import Partido


class IAEntrenadorRival:
    MINUTOS_REVISION_TACTICA = (60, 75)
    MINUTOS_CAMBIO_POR_FATIGA = (60, 70, 80)
    FISICO_AGOTADO = 55

    def actuar(self, partido: Partido, club_id: str) -> None:
        if not partido.esta_activo:
            return
        self._sustituir_lesionados(partido, club_id)
        if partido.minuto in self.MINUTOS_CAMBIO_POR_FATIGA:
            self._sustituir_agotado(partido, club_id)
        if partido.minuto in self.MINUTOS_REVISION_TACTICA:
            self._ajustar_mentalidad(partido, club_id)

    def _mejor_reemplazo(self, partido: Partido, club_id: str, sale: Jugador) -> Jugador | None:
        habilitados = [j for j in partido.jugadores_en_banca(club_id) if j.habilitado]
        if not habilitados:
            return None
        misma_posicion = [j for j in habilitados if j.posicion == sale.posicion]
        candidatos = misma_posicion or habilitados
        return max(candidatos, key=lambda j: j.calcular_rendimiento_actual())

    def _intentar_cambio(self, partido: Partido, club_id: str, sale: Jugador) -> None:
        if partido.sustituciones_restantes(club_id) <= 0:
            return
        entra = self._mejor_reemplazo(partido, club_id, sale)
        if entra is None:
            return
        try:
            partido.sustituir(club_id, sale.id, entra.id)
        except ErrorDominio:  # pragma: no cover - defensa ante estados raros
            return

    def _sustituir_lesionados(self, partido: Partido, club_id: str) -> None:
        for jugador in partido.jugadores_en_campo(club_id):
            if jugador.lesionado:
                self._intentar_cambio(partido, club_id, jugador)

    def _sustituir_agotado(self, partido: Partido, club_id: str) -> None:
        en_campo = partido.jugadores_en_campo(club_id)
        mas_cansado = min(en_campo, key=lambda j: j.fisico, default=None)
        if mas_cansado and mas_cansado.fisico < self.FISICO_AGOTADO:
            self._intentar_cambio(partido, club_id, mas_cansado)

    def _ajustar_mentalidad(self, partido: Partido, club_id: str) -> None:
        resultado = partido.resultado_para(club_id)
        rival = partido.rival_de(club_id).id
        diferencia = partido.goles[club_id] - partido.goles[rival]
        if resultado == Resultado.DERROTA:
            deseada = Mentalidad.OFENSIVA
        elif diferencia >= 2:
            deseada = Mentalidad.DEFENSIVA
        else:
            deseada = Mentalidad.EQUILIBRADA
        if partido.mentalidad[club_id] != deseada:
            partido.cambiar_mentalidad(club_id, deseada)
