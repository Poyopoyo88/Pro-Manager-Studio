"""Entidad Partido: marcador, estado de la simulación e incidencias.

Patrón GRASP *Creator*: ``Partido`` registra y por lo tanto crea las instancias de
``IncidenciaJuego`` que ocurren durante el encuentro.

Reglas que se validan aquí (CU-01):

* Solo se puede sustituir con el partido activo (en juego o pausado).
* 3a. El suplente debe estar habilitado (sin lesión, suspensión ni sanción interna).
* 5a. Máximo ``MAX_SUSTITUCIONES`` cambios por equipo.
"""

from __future__ import annotations

from dataclasses import dataclass

from .club import Club
from .enums import EstadoPartido, Mentalidad, Resultado, TipoIncidencia
from .errores import (
    ClubNoEncontradoError,
    EstadoInvalidoError,
    JugadorInhabilitadoError,
    PartidoNoActivoError,
    SustitucionesAgotadasError,
    SustitucionInvalidaError,
)
from .jugador import Jugador
from .tactica import Alineacion


@dataclass(frozen=True)
class IncidenciaJuego:
    minuto: int
    tipo: TipoIncidencia
    descripcion: str
    club_id: str | None = None
    jugador_id: str | None = None
    jugador_entra_id: str | None = None
    critica: bool = False


class Partido:
    DURACION = 90
    MINUTO_DESCANSO = 45
    MAX_SUSTITUCIONES = 5

    def __init__(
        self,
        id: str,
        local: Club,
        visitante: Club,
        alineacion_local: Alineacion,
        alineacion_visitante: Alineacion,
        club_usuario_id: str | None = None,
        jornada: int = 1,
        es_decisivo: bool = False,
    ) -> None:
        alineacion_local.validar(local)
        alineacion_visitante.validar(visitante)
        self.id = id
        self.local = local
        self.visitante = visitante
        self.club_usuario_id = club_usuario_id
        self.jornada = jornada
        self.es_decisivo = es_decisivo
        self.formaciones = {
            local.id: alineacion_local.formacion,
            visitante.id: alineacion_visitante.formacion,
        }
        self.estado = EstadoPartido.PROGRAMADO
        self.minuto = 0
        self.goles = {local.id: 0, visitante.id: 0}
        self.mentalidad = {
            local.id: alineacion_local.mentalidad,
            visitante.id: alineacion_visitante.mentalidad,
        }
        self.en_campo = {
            local.id: list(alineacion_local.titulares),
            visitante.id: list(alineacion_visitante.titulares),
        }
        self.banca = {
            local.id: list(alineacion_local.suplentes),
            visitante.id: list(alineacion_visitante.suplentes),
        }
        self.participantes = {
            local.id: list(alineacion_local.titulares),
            visitante.id: list(alineacion_visitante.titulares),
        }
        self.sustituciones = {local.id: 0, visitante.id: 0}
        self.amarillas: dict[str, int] = {}
        self.expulsados: list[str] = []
        self.lesionados_en_partido: list[str] = []
        self.incidencias: list[IncidenciaJuego] = []
        self.motivo_pausa: str | None = None
        self.descanso_realizado = False

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def club(self, club_id: str) -> Club:
        if club_id == self.local.id:
            return self.local
        if club_id == self.visitante.id:
            return self.visitante
        raise ClubNoEncontradoError(f"El club '{club_id}' no juega este partido.")

    def rival_de(self, club_id: str) -> Club:
        self.club(club_id)
        return self.visitante if club_id == self.local.id else self.local

    @property
    def esta_activo(self) -> bool:
        return self.estado in (EstadoPartido.EN_JUEGO, EstadoPartido.PAUSADO)

    @property
    def marcador(self) -> str:
        return f"{self.goles[self.local.id]} - {self.goles[self.visitante.id]}"

    def jugadores_en_campo(self, club_id: str) -> list[Jugador]:
        club = self.club(club_id)
        return [club.obtener_jugador(j) for j in self.en_campo[club_id]]

    def jugadores_en_banca(self, club_id: str) -> list[Jugador]:
        club = self.club(club_id)
        return [club.obtener_jugador(j) for j in self.banca[club_id]]

    def sustituciones_restantes(self, club_id: str) -> int:
        self.club(club_id)
        return self.MAX_SUSTITUCIONES - self.sustituciones[club_id]

    def resultado_para(self, club_id: str) -> Resultado:
        rival = self.rival_de(club_id)
        propios, ajenos = self.goles[club_id], self.goles[rival.id]
        if propios > ajenos:
            return Resultado.VICTORIA
        if propios < ajenos:
            return Resultado.DERROTA
        return Resultado.EMPATE

    # ------------------------------------------------------------------
    # Creator: incidencias
    # ------------------------------------------------------------------
    def registrar_incidencia(
        self,
        tipo: TipoIncidencia,
        descripcion: str,
        club_id: str | None = None,
        jugador_id: str | None = None,
        jugador_entra_id: str | None = None,
        critica: bool = False,
    ) -> IncidenciaJuego:
        incidencia = IncidenciaJuego(
            minuto=self.minuto,
            tipo=tipo,
            descripcion=descripcion,
            club_id=club_id,
            jugador_id=jugador_id,
            jugador_entra_id=jugador_entra_id,
            critica=critica,
        )
        self.incidencias.append(incidencia)
        return incidencia

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def iniciar(self) -> IncidenciaJuego:
        if self.estado != EstadoPartido.PROGRAMADO:
            raise EstadoInvalidoError("El partido ya fue iniciado.")
        self.estado = EstadoPartido.EN_JUEGO
        return self.registrar_incidencia(
            TipoIncidencia.INICIO,
            f"¡Rueda el balón! {self.local.nombre} vs {self.visitante.nombre}.",
        )

    def pausar(self, motivo: str = "Pausa solicitada por el DT.", critica: bool = False):
        if self.estado != EstadoPartido.EN_JUEGO:
            raise PartidoNoActivoError("Solo se puede pausar un partido en juego.")
        self.estado = EstadoPartido.PAUSADO
        self.motivo_pausa = motivo
        return self.registrar_incidencia(TipoIncidencia.PAUSA, motivo, critica=critica)

    def reanudar(self) -> IncidenciaJuego:
        if self.estado != EstadoPartido.PAUSADO:
            raise PartidoNoActivoError("Solo se puede reanudar un partido pausado.")
        self.estado = EstadoPartido.EN_JUEGO
        self.motivo_pausa = None
        return self.registrar_incidencia(TipoIncidencia.REANUDACION, "Se reanuda el encuentro.")

    def avanzar_minuto(self) -> int:
        if self.estado != EstadoPartido.EN_JUEGO:
            raise PartidoNoActivoError("La simulación solo avanza con el partido en juego.")
        if self.minuto >= self.DURACION:
            raise EstadoInvalidoError("El tiempo reglamentario ya terminó.")
        self.minuto += 1
        return self.minuto

    def finalizar(self) -> IncidenciaJuego:
        if self.estado != EstadoPartido.EN_JUEGO:
            raise PartidoNoActivoError("Solo se puede finalizar un partido en juego.")
        self.estado = EstadoPartido.FINALIZADO
        return self.registrar_incidencia(
            TipoIncidencia.FINAL,
            f"Final: {self.local.nombre} {self.marcador} {self.visitante.nombre}.",
        )

    # ------------------------------------------------------------------
    # Acciones de juego
    # ------------------------------------------------------------------
    def _exigir_activo(self) -> None:
        if not self.esta_activo:
            raise PartidoNoActivoError("La acción requiere un partido en curso.")

    def _exigir_en_campo(self, club_id: str, jugador_id: str) -> Jugador:
        if jugador_id not in self.en_campo[club_id]:
            raise SustitucionInvalidaError(f"El jugador '{jugador_id}' no está en el campo.")
        return self.club(club_id).obtener_jugador(jugador_id)

    def registrar_gol(self, club_id: str, jugador_id: str) -> IncidenciaJuego:
        self._exigir_activo()
        goleador = self._exigir_en_campo(club_id, jugador_id)
        self.goles[club_id] += 1
        goleador.actualizar_moral(3)
        return self.registrar_incidencia(
            TipoIncidencia.GOL,
            f"¡GOL de {self.club(club_id).nombre}! Anota {goleador.nombre}. ({self.marcador})",
            club_id=club_id,
            jugador_id=jugador_id,
        )

    def registrar_tarjeta_amarilla(self, club_id: str, jugador_id: str) -> list[IncidenciaJuego]:
        self._exigir_activo()
        jugador = self._exigir_en_campo(club_id, jugador_id)
        self.amarillas[jugador_id] = self.amarillas.get(jugador_id, 0) + 1
        incidencias = [
            self.registrar_incidencia(
                TipoIncidencia.TARJETA_AMARILLA,
                f"Tarjeta amarilla para {jugador.nombre}.",
                club_id=club_id,
                jugador_id=jugador_id,
            )
        ]
        if self.amarillas[jugador_id] >= 2:
            incidencias.append(self.expulsar(club_id, jugador_id, "doble amarilla"))
        return incidencias

    def expulsar(self, club_id: str, jugador_id: str, motivo: str = "roja directa"):
        self._exigir_activo()
        jugador = self._exigir_en_campo(club_id, jugador_id)
        self.en_campo[club_id].remove(jugador_id)
        self.expulsados.append(jugador_id)
        return self.registrar_incidencia(
            TipoIncidencia.EXPULSION,
            f"Expulsado {jugador.nombre} ({motivo}). {self.club(club_id).nombre} se queda con "
            f"{len(self.en_campo[club_id])}.",
            club_id=club_id,
            jugador_id=jugador_id,
            critica=club_id == self.club_usuario_id,
        )

    def registrar_lesion(self, club_id: str, jugador_id: str, partidos_baja: int):
        self._exigir_activo()
        jugador = self._exigir_en_campo(club_id, jugador_id)
        jugador.lesionar(partidos_baja)
        self.lesionados_en_partido.append(jugador_id)
        return self.registrar_incidencia(
            TipoIncidencia.LESION,
            f"Se lesiona {jugador.nombre} ({jugador.posicion.value}). Baja estimada: "
            f"{partidos_baja} partido(s).",
            club_id=club_id,
            jugador_id=jugador_id,
            critica=club_id == self.club_usuario_id,
        )

    def sustituir(self, club_id: str, id_sale: str, id_entra: str) -> IncidenciaJuego:
        """Ejecuta una sustitución validando las reglas del CU-01."""
        self._exigir_activo()
        self.club(club_id)
        if self.sustituciones[club_id] >= self.MAX_SUSTITUCIONES:
            raise SustitucionesAgotadasError(
                f"Ya se realizaron los {self.MAX_SUSTITUCIONES} cambios permitidos."
            )
        sale = self._exigir_en_campo(club_id, id_sale)
        if id_entra not in self.banca[club_id]:
            raise SustitucionInvalidaError(f"El jugador '{id_entra}' no está en la banca.")
        entra = self.club(club_id).obtener_jugador(id_entra)
        if not entra.habilitado:
            raise JugadorInhabilitadoError(f"{entra.motivo_inhabilitacion()} Elige otro suplente.")
        self.en_campo[club_id][self.en_campo[club_id].index(id_sale)] = id_entra
        self.banca[club_id].remove(id_entra)
        self.participantes[club_id].append(id_entra)
        self.sustituciones[club_id] += 1
        return self.registrar_incidencia(
            TipoIncidencia.SUSTITUCION,
            f"Cambio en {self.club(club_id).nombre}: sale {sale.nombre}, entra {entra.nombre}.",
            club_id=club_id,
            jugador_id=id_sale,
            jugador_entra_id=id_entra,
        )

    def cambiar_mentalidad(self, club_id: str, mentalidad: Mentalidad) -> IncidenciaJuego:
        self._exigir_activo()
        mentalidad = Mentalidad(mentalidad)
        self.club(club_id)
        self.mentalidad[club_id] = mentalidad
        return self.registrar_incidencia(
            TipoIncidencia.CAMBIO_MENTALIDAD,
            f"{self.club(club_id).nombre} cambia a mentalidad {mentalidad.value.lower()}.",
            club_id=club_id,
        )
