"""Controladores de la capa de aplicación (patrón GRASP *Controller*).

Cada controlador recibe una petición de la interfaz, carga la partida, delega en el
dominio y guarda el resultado. **No contienen reglas de negocio**: solo coordinan
(sección 9 de la especificación). Las reglas viven en ``pro_manager.dominio``.

* ``ControladorCarrera``   → crear, cargar y eliminar partidas.
* ``ControladorPlantilla`` → HU-01 alineación y configuración táctica.
* ``ControladorVestuario`` → HU-04 conflictos de vestuario.
* ``ControladorPartido``   → HU-05 / CU-01 partido en tiempo real.
* ``ControladorClub``      → HU-02 ojeadores, HU-03 fichajes, HU-06 finanzas.
"""

from __future__ import annotations

import random
import uuid
import zlib
from datetime import UTC, datetime

from ..dominio import (
    FORMACIONES,
    AccionDT,
    Alineacion,
    DirectorTecnico,
    EventoVestuario,
    GestorVestuario,
    IncidenciaJuego,
    InformeOjeo,
    JugadorEnMercado,
    Mentalidad,
    NegociadorFichajes,
    Ojeador,
    Partido,
    Posicion,
    ProcesadorPostPartido,
    ResultadoResolucion,
    SimuladorPartido,
    Temporada,
    sugerir_alineacion,
)
from ..dominio.errores import (
    AlineacionInvalidaError,
    EstadoInvalidoError,
    EventosPendientesError,
)
from ..dominio.mercado import RespuestaNegociacion
from .errores import SinPartidoError
from .partida import Partida
from .puertos import ProveedorDatosIniciales, RepositorioPartidas


class _ControladorBase:
    def __init__(self, repositorio: RepositorioPartidas) -> None:
        self.repositorio = repositorio

    def _cargar(self, partida_id: str) -> Partida:
        return self.repositorio.obtener(partida_id)

    def _guardar(self, partida: Partida) -> None:
        self.repositorio.guardar(partida)


# ---------------------------------------------------------------------------
class ControladorCarrera(_ControladorBase):
    def __init__(self, repositorio: RepositorioPartidas, datos: ProveedorDatosIniciales) -> None:
        super().__init__(repositorio)
        self.datos = datos

        def crear_partida(
        self, nombre_dt: str, semilla: int | None = None, nombre_club: str | None = None
    ) -> Partida:
        semilla = semilla if semilla is not None else random.SystemRandom().randint(1, 10**9)
        rng = random.Random(semilla)
        club = self.datos.crear_club_usuario()
        rivales = self.datos.crear_rivales(rng)
        if nombre_club is not None:
            club.renombrar(nombre_club, [r.nombre for r in rivales])
        rivales = self.datos.crear_rivales(rng)
        partida = Partida(
            id=uuid.uuid4().hex[:12],
            semilla=semilla,
            dt=DirectorTecnico(nombre_dt),
            club=club,
            rivales=rivales,
            temporada=Temporada([r.id for r in rivales], self.datos.puntos_ascenso),
            eventos=self.datos.eventos_iniciales(club),
            mercado=self.datos.crear_mercado(rng),
            creada_en=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        partida.noticias = [
            f"Bienvenido, {partida.dt.nombre}. La directiva de {club.nombre} te encarga "
            f"el ascenso: necesitas {partida.temporada.puntos_ascenso} puntos en "
            f"{partida.temporada.total_jornadas} jornadas."
        ]
        self._guardar(partida)
        return partida

    def obtener(self, partida_id: str) -> Partida:
        return self._cargar(partida_id)

    def listar(self) -> list[Partida]:
        return [self._cargar(pid) for pid in self.repositorio.listar()]

    def eliminar(self, partida_id: str) -> None:
        self._cargar(partida_id)
        self.repositorio.eliminar(partida_id)


# ---------------------------------------------------------------------------
class ControladorPlantilla(_ControladorBase):
    """HU-01: configuración táctica y alineación pre-partido."""

    def obtener_partida(self, partida_id: str) -> Partida:
        return self._cargar(partida_id)

    def formaciones(self) -> list[str]:
        return list(FORMACIONES)

    def sugerir_alineacion(
        self, partida_id: str, formacion: str, mentalidad: Mentalidad = Mentalidad.EQUILIBRADA
    ) -> tuple[Alineacion, list[str]]:
        partida = self._cargar(partida_id)
        alineacion = sugerir_alineacion(partida.club, formacion, mentalidad)
        return alineacion, alineacion.advertencias(partida.club)

    def definir_alineacion(
        self,
        partida_id: str,
        formacion: str,
        titulares: list[str],
        suplentes: list[str],
        mentalidad: Mentalidad = Mentalidad.EQUILIBRADA,
    ) -> tuple[Alineacion, list[str]]:
        partida = self._cargar(partida_id)
        if partida.hay_partido_en_curso:
            raise EstadoInvalidoError(
                "Durante el partido los ajustes se hacen con sustituciones y mentalidad."
            )
        alineacion = Alineacion(formacion, titulares, suplentes, Mentalidad(mentalidad))
        alineacion.validar(partida.club)
        partida.alineacion = alineacion
        self._guardar(partida)
        return alineacion, alineacion.advertencias(partida.club)

    def elogiar_jugador(self, partida_id: str, jugador_id: str) -> tuple[Partida, bool]:
        partida = self._cargar(partida_id)
        jugador = partida.club.obtener_jugador(jugador_id)
        cambio = partida.dt.elogiar(jugador, partida.temporada.jornada_actual)
        self._guardar(partida)
        return partida, cambio


# ---------------------------------------------------------------------------
class ControladorVestuario(_ControladorBase):
    """HU-04: resolución de conflictos de vestuario (diagrama de secuencia, sección 10)."""

    def eventos(
        self, partida_id: str, solo_pendientes: bool = False
    ) -> tuple[Partida, list[EventoVestuario]]:
        partida = self._cargar(partida_id)
        eventos = partida.eventos_pendientes() if solo_pendientes else list(partida.eventos)
        return partida, eventos

    def revisar_crisis(self, partida_id: str, evento_id: str) -> tuple[Partida, EventoVestuario]:
        partida = self._cargar(partida_id)
        return partida, partida.evento(evento_id)

    def resolver_evento(
        self, partida_id: str, evento_id: str, accion: AccionDT
    ) -> ResultadoResolucion:
        partida = self._cargar(partida_id)
        evento = partida.evento(evento_id)
        gestor = GestorVestuario(partida.nuevo_rng())
        resultado = gestor.resolver(evento, AccionDT(accion), partida.club, partida.dt)
        partida.noticias = [resultado.desenlace, *resultado.cambios]
        self._guardar(partida)
        return resultado


# ---------------------------------------------------------------------------
class ControladorPartido(_ControladorBase):
    """HU-05 / CU-01: decisiones tácticas en tiempo real y gestión de crisis en partido."""

    def _partido(self, partida: Partida) -> Partido:
        if partida.partido is None:
            raise SinPartidoError("No hay un partido creado. Inicia el partido de la jornada.")
        return partida.partido

    def iniciar_partido(self, partida_id: str) -> Partida:
        partida = self._cargar(partida_id)
        if partida.hay_partido_en_curso:
            raise EstadoInvalidoError("Ya hay un partido en curso.")
        temporada = partida.temporada
        rival = partida.rival(temporada.rival_de_jornada())
        pendientes = partida.eventos_pendientes()
        if pendientes:
            raise EventosPendientesError(
                f"Hay {len(pendientes)} situación(es) de vestuario sin resolver. "
                "El DT debe intervenir antes del partido."
            )
        if partida.alineacion is None:
            raise AlineacionInvalidaError(["Define la alineación antes de iniciar el partido."])

        rng = partida.nuevo_rng()
        alineacion_rival = sugerir_alineacion(rival, rng.choice(list(FORMACIONES)))
        es_local = temporada.es_local()
        partido = Partido(
            id=f"{partida.id}-J{temporada.jornada_actual}",
            local=partida.club if es_local else rival,
            visitante=rival if es_local else partida.club,
            alineacion_local=partida.alineacion if es_local else alineacion_rival,
            alineacion_visitante=alineacion_rival if es_local else partida.alineacion,
            club_usuario_id=partida.club.id,
            jornada=temporada.jornada_actual,
            es_decisivo=temporada.es_decisiva(),
        )
        partido.iniciar()
        partida.partido = partido
        self._guardar(partida)
        return partida

    def estado(self, partida_id: str) -> Partida:
        partida = self._cargar(partida_id)
        self._partido(partida)
        return partida

    def simular(self, partida_id: str, minutos: int) -> tuple[Partida, list[IncidenciaJuego]]:
        partida = self._cargar(partida_id)
        partido = self._partido(partida)
        nuevas = SimuladorPartido(rng=partida.nuevo_rng()).simular(partido, minutos)
        if not partido.esta_activo:
            self._cerrar_jornada(partida)
        self._guardar(partida)
        return partida, nuevas

    def pausar_partido(self, partida_id: str) -> Partida:
        partida = self._cargar(partida_id)
        self._partido(partida).pausar()
        self._guardar(partida)
        return partida

    def reanudar_partido(self, partida_id: str) -> Partida:
        partida = self._cargar(partida_id)
        self._partido(partida).reanudar()
        self._guardar(partida)
        return partida

    def ejecutar_sustitucion(self, partida_id: str, id_sale: str, id_entra: str) -> bool:
        partida = self._cargar(partida_id)
        self._partido(partida).sustituir(partida.club.id, id_sale, id_entra)
        self._guardar(partida)
        return True

    def cambiar_mentalidad(self, partida_id: str, mentalidad: Mentalidad) -> Partida:
        partida = self._cargar(partida_id)
        self._partido(partida).cambiar_mentalidad(partida.club.id, Mentalidad(mentalidad))
        self._guardar(partida)
        return partida

    def _cerrar_jornada(self, partida: Partida) -> None:
        partido = self._partido(partida)
        resumen = ProcesadorPostPartido().procesar(partido, partida.dt)
        partida.temporada.registrar(resumen.jornada)
        noticias = [
            f"Jornada {resumen.jornada.jornada}: {partido.local.nombre} {resumen.marcador} "
            f"{partido.visitante.nombre} ({resumen.resultado.value}).",
            *resumen.cambios,
        ]
        if partida.temporada.finalizada:
            if partida.temporada.ascendio:
                noticias.insert(0, "¡ASCENSO CONSEGUIDO! La afición invade la cancha.")
            else:
                noticias.insert(0, "La temporada terminó sin alcanzar el ascenso.")
        else:
            evento = GestorVestuario(partida.nuevo_rng()).generar_evento(
                partida.club,
                partida.temporada.jornada_actual,
                partida.siguiente_id_evento(),
                partida.eventos,
            )
            if evento:
                partida.eventos.append(evento)
                noticias.append(f"Nuevo asunto en el vestuario: {evento.titulo}.")
        partida.noticias = noticias


# ---------------------------------------------------------------------------
class ControladorClub(_ControladorBase):
    """HU-02 búsqueda de talento, HU-03 negociación de fichajes, HU-06 finanzas."""

    def finanzas(self, partida_id: str) -> Partida:
        return self._cargar(partida_id)

    def mercado(self, partida_id: str) -> list[JugadorEnMercado]:
        return list(self._cargar(partida_id).mercado)

    def ojear(self, partida_id: str, posicion: Posicion | None = None) -> list[InformeOjeo]:
        partida = self._cargar(partida_id)
        informes = []
        for entrada in partida.mercado:
            if posicion and entrada.jugador.posicion != Posicion(posicion):
                continue
            # Semilla por jugador: repetir el ojeo no da información nueva.
            rng = random.Random(partida.semilla + zlib.crc32(entrada.jugador.id.encode()))
            informes.append(Ojeador.del_club(partida.club.reputacion, rng).informar(entrada))
        return informes

    def ofertar(
        self, partida_id: str, jugador_id: str, monto: int, salario: int
    ) -> RespuestaNegociacion:
        partida = self._cargar(partida_id)
        if partida.hay_partido_en_curso:
            raise EstadoInvalidoError("No se negocian fichajes con un partido en curso.")
        entrada = partida.entrada_mercado(jugador_id)
        partida.club.validar_fichaje(monto, salario)  # RN-02 antes de negociar
        respuesta = NegociadorFichajes().evaluar(entrada.jugador, monto, salario)
        if respuesta.aceptada:
            jugador = entrada.jugador
            jugador.salario = salario
            partida.club.fichar(jugador, monto, partida.temporada.jornada_actual)
            jugador.registrar_historia(
                f"Jornada {partida.temporada.jornada_actual}: fichado desde {entrada.club_origen}."
            )
            partida.mercado.remove(entrada)
            partida.noticias = [respuesta.mensaje]
            self._guardar(partida)
        return respuesta
