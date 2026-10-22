"""Rutas de partidas guardadas y plantilla (HU-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from ...aplicacion import ControladorCarrera, ControladorPlantilla
from ...dominio.enums import Mentalidad
from . import dependencias as dep
from . import esquemas as e
from . import mapeo

ERRORES = {
    404: {"model": e.ErrorSalida, "description": "Recurso no encontrado"},
    409: {"model": e.ErrorSalida, "description": "Estado inválido para la acción"},
    422: {"model": e.ErrorSalida, "description": "Regla de negocio incumplida"},
}

router = APIRouter(prefix="/partidas", responses=ERRORES)


@router.post("", status_code=201, response_model=e.PartidaSalida, tags=["Partidas"])
def crear_partida(entrada: e.CrearPartidaEntrada, ctrl: ControladorCarrera = Depends(dep.carrera)):
    """Crea una nueva carrera: club, rivales, mercado y la primera crisis de vestuario."""
    return mapeo.partida(ctrl.crear_partida(entrada.nombre_dt, entrada.semilla))


@router.get("", response_model=list[e.PartidaResumenSalida], tags=["Partidas"])
def listar_partidas(ctrl: ControladorCarrera = Depends(dep.carrera)):
    return [mapeo.partida_resumen(p) for p in ctrl.listar()]


@router.get("/{partida_id}", response_model=e.PartidaSalida, tags=["Partidas"])
def obtener_partida(partida_id: str, ctrl: ControladorCarrera = Depends(dep.carrera)):
    return mapeo.partida(ctrl.obtener(partida_id))


@router.delete("/{partida_id}", status_code=204, tags=["Partidas"])
def eliminar_partida(partida_id: str, ctrl: ControladorCarrera = Depends(dep.carrera)):
    ctrl.eliminar(partida_id)
    return Response(status_code=204)


# ------------------------------------------------------------------ HU-01


@router.get(
    "/{partida_id}/plantilla", response_model=list[e.JugadorSalida], tags=["Plantilla (HU-01)"]
)
def plantilla(partida_id: str, ctrl: ControladorPlantilla = Depends(dep.plantilla)):
    partida = ctrl.obtener_partida(partida_id)
    return [mapeo.jugador(j) for j in partida.club.plantilla]


@router.get(
    "/{partida_id}/plantilla/{jugador_id}",
    response_model=e.JugadorSalida,
    tags=["Plantilla (HU-01)"],
)
def jugador(partida_id: str, jugador_id: str, ctrl: ControladorPlantilla = Depends(dep.plantilla)):
    partida = ctrl.obtener_partida(partida_id)
    return mapeo.jugador(partida.club.obtener_jugador(jugador_id))


@router.post(
    "/{partida_id}/plantilla/{jugador_id}/elogio",
    response_model=e.ElogioSalida,
    tags=["Plantilla (HU-01)"],
)
def elogiar(partida_id: str, jugador_id: str, ctrl: ControladorPlantilla = Depends(dep.plantilla)):
    """Elogio público (una vez por jornada). Puede llevar a un jugador de Estable a Motivado."""
    partida, cambio = ctrl.elogiar_jugador(partida_id, jugador_id)
    return e.ElogioSalida(
        jugador=mapeo.jugador(partida.club.obtener_jugador(jugador_id)), cambio_estado=cambio
    )


@router.get("/{partida_id}/formaciones", response_model=list[str], tags=["Plantilla (HU-01)"])
def formaciones(partida_id: str, ctrl: ControladorPlantilla = Depends(dep.plantilla)):
    ctrl.obtener_partida(partida_id)
    return ctrl.formaciones()


@router.get(
    "/{partida_id}/alineacion/sugerida",
    response_model=e.AlineacionSalida,
    tags=["Plantilla (HU-01)"],
)
def alineacion_sugerida(
    partida_id: str,
    formacion: str = Query("4-4-2"),
    mentalidad: Mentalidad = Query(Mentalidad.EQUILIBRADA),
    ctrl: ControladorPlantilla = Depends(dep.plantilla),
):
    """El cuerpo técnico propone a los mejores disponibles por rendimiento actual."""
    alineacion, advertencias = ctrl.sugerir_alineacion(partida_id, formacion, mentalidad)
    return e.AlineacionSalida(**alineacion.__dict__, advertencias=advertencias)


@router.get(
    "/{partida_id}/alineacion",
    response_model=e.AlineacionSalida | None,
    tags=["Plantilla (HU-01)"],
)
def alineacion_actual(partida_id: str, ctrl: ControladorPlantilla = Depends(dep.plantilla)):
    partida = ctrl.obtener_partida(partida_id)
    if partida.alineacion is None:
        return None
    return e.AlineacionSalida(
        **partida.alineacion.__dict__, advertencias=partida.alineacion.advertencias(partida.club)
    )


@router.put(
    "/{partida_id}/alineacion",
    response_model=e.AlineacionSalida,
    tags=["Plantilla (HU-01)"],
)
def definir_alineacion(
    partida_id: str,
    entrada: e.AlineacionEntrada,
    ctrl: ControladorPlantilla = Depends(dep.plantilla),
):
    """Valida y guarda la alineación pre-partido (11 titulares, 1 portero, hasta 9 suplentes)."""
    alineacion, advertencias = ctrl.definir_alineacion(
        partida_id, entrada.formacion, entrada.titulares, entrada.suplentes, entrada.mentalidad
    )
    return e.AlineacionSalida(**alineacion.__dict__, advertencias=advertencias)
