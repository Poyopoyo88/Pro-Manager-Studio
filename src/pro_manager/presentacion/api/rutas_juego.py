"""Rutas de vestuario (HU-04), partido (HU-05 / CU-01) y club (HU-02, HU-03, HU-06)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...aplicacion import (
    ControladorClub,
    ControladorPartido,
    ControladorVestuario,
)
from ...dominio.enums import Posicion
from . import dependencias as dep
from . import esquemas as e
from . import mapeo
from .rutas_partidas import ERRORES

router = APIRouter(prefix="/partidas/{partida_id}", responses=ERRORES)

# ------------------------------------------------------------------ HU-04 Vestuario


@router.get("/vestuario/eventos", response_model=list[e.EventoSalida], tags=["Vestuario (HU-04)"])
def eventos_vestuario(
    partida_id: str,
    pendientes: bool = Query(False, description="Solo los que esperan decisión del DT."),
    ctrl: ControladorVestuario = Depends(dep.vestuario),
):
    partida, eventos = ctrl.eventos(partida_id, pendientes)
    return [mapeo.evento(ev, partida.club) for ev in eventos]


@router.get(
    "/vestuario/eventos/{evento_id}", response_model=e.EventoSalida, tags=["Vestuario (HU-04)"]
)
def revisar_crisis(
    partida_id: str, evento_id: str, ctrl: ControladorVestuario = Depends(dep.vestuario)
):
    partida, evento = ctrl.revisar_crisis(partida_id, evento_id)
    return mapeo.evento(evento, partida.club)


@router.post(
    "/vestuario/eventos/{evento_id}/resolucion",
    response_model=e.ResolucionSalida,
    tags=["Vestuario (HU-04)"],
)
def resolver_crisis(
    partida_id: str,
    evento_id: str,
    entrada: e.ResolucionEntrada,
    ctrl: ControladorVestuario = Depends(dep.vestuario),
):
    """SANCIONAR pide aval a la directiva y manda al jugador a la banca.

    DIALOGAR equilibra la moral de los involucrados, a costa de autoridad.
    """
    resultado = ctrl.resolver_evento(partida_id, evento_id, entrada.accion)
    return e.ResolucionSalida(**resultado.__dict__)


# ------------------------------------------------------------------ HU-05 / CU-01 Partido


@router.post("/partido", status_code=201, response_model=e.PartidoSalida, tags=["Partido (HU-05)"])
def iniciar_partido(partida_id: str, ctrl: ControladorPartido = Depends(dep.partido)):
    """Inicia el partido de la jornada. Requiere alineación y vestuario sin crisis pendientes."""
    return mapeo.partido(ctrl.iniciar_partido(partida_id).partido)


@router.get("/partido", response_model=e.PartidoSalida, tags=["Partido (HU-05)"])
def estado_partido(partida_id: str, ctrl: ControladorPartido = Depends(dep.partido)):
    return mapeo.partido(ctrl.estado(partida_id).partido)


@router.post("/partido/simulacion", response_model=e.SimularSalida, tags=["Partido (HU-05)"])
def simular(
    partida_id: str, entrada: e.SimularEntrada, ctrl: ControladorPartido = Depends(dep.partido)
):
    """Avanza la simulación. Se detiene sola en el descanso y ante incidencias críticas."""
    partida, nuevas = ctrl.simular(partida_id, entrada.minutos)
    partido = partida.partido
    return e.SimularSalida(
        partido=mapeo.partido(partido),
        nuevas_incidencias=[mapeo.incidencia(i) for i in nuevas],
        noticias=partida.noticias if not partido.esta_activo else [],
    )


@router.post("/partido/pausa", response_model=e.PartidoSalida, tags=["Partido (HU-05)"])
def pausar(partida_id: str, ctrl: ControladorPartido = Depends(dep.partido)):
    """CU-01 paso 1: el DT pausa la simulación y ve el panel de control."""
    return mapeo.partido(ctrl.pausar_partido(partida_id).partido)


@router.post("/partido/reanudacion", response_model=e.PartidoSalida, tags=["Partido (HU-05)"])
def reanudar(partida_id: str, ctrl: ControladorPartido = Depends(dep.partido)):
    """CU-01 paso 6: confirma los ajustes y reanuda el encuentro."""
    return mapeo.partido(ctrl.reanudar_partido(partida_id).partido)


@router.post("/partido/sustituciones", response_model=e.SustitucionSalida, tags=["Partido (HU-05)"])
def sustituir(
    partida_id: str,
    entrada: e.SustitucionEntrada,
    ctrl: ControladorPartido = Depends(dep.partido),
):
    """CU-01 pasos 3 y 5. Excepciones: 3a jugador inhabilitado (422), 5a límite de cambios (422)."""
    aplicada = ctrl.ejecutar_sustitucion(partida_id, entrada.id_sale, entrada.id_entra)
    return e.SustitucionSalida(
        aplicada=aplicada, partido=mapeo.partido(ctrl.estado(partida_id).partido)
    )


@router.put("/partido/mentalidad", response_model=e.PartidoSalida, tags=["Partido (HU-05)"])
def mentalidad(
    partida_id: str,
    entrada: e.MentalidadEntrada,
    ctrl: ControladorPartido = Depends(dep.partido),
):
    """CU-01 paso 4: ajustar la mentalidad táctica desde la banda."""
    return mapeo.partido(ctrl.cambiar_mentalidad(partida_id, entrada.mentalidad).partido)


# ------------------------------------------------------------------ HU-06 / HU-02 / HU-03 Club


@router.get("/finanzas", response_model=e.FinanzasSalida, tags=["Club (HU-02, HU-03, HU-06)"])
def finanzas(partida_id: str, ctrl: ControladorClub = Depends(dep.club)):
    return mapeo.finanzas(ctrl.finanzas(partida_id).club)


@router.get(
    "/mercado",
    response_model=list[e.JugadorMercadoSalida],
    tags=["Club (HU-02, HU-03, HU-06)"],
)
def mercado(partida_id: str, ctrl: ControladorClub = Depends(dep.club)):
    """Jugadores transferibles. La calidad real no se conoce: hay que enviar ojeadores."""
    return [mapeo.jugador_mercado(m) for m in ctrl.mercado(partida_id)]


@router.get(
    "/mercado/informes",
    response_model=list[e.InformeOjeoSalida],
    tags=["Club (HU-02, HU-03, HU-06)"],
)
def informes_ojeo(
    partida_id: str,
    posicion: Posicion | None = Query(None),
    ctrl: ControladorClub = Depends(dep.club),
):
    """HU-02: los ojeadores estiman la calidad con un rango (según la reputación del club)."""
    return [mapeo.informe(i) for i in ctrl.ojear(partida_id, posicion)]


@router.post(
    "/mercado/{jugador_id}/ofertas",
    response_model=e.OfertaSalida,
    tags=["Club (HU-02, HU-03, HU-06)"],
)
def ofertar(
    partida_id: str,
    jugador_id: str,
    entrada: e.OfertaEntrada,
    ctrl: ControladorClub = Depends(dep.club),
):
    """HU-03: negociación. Antes de negociar se valida presupuesto y masa salarial (RN-02)."""
    respuesta = ctrl.ofertar(partida_id, jugador_id, entrada.monto_transferencia, entrada.salario)
    return e.OfertaSalida(**respuesta.__dict__)
