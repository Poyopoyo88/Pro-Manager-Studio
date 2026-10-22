"""HU-04: resolución de conflictos de vestuario y narrativa dinámica."""

import random

import pytest

from pro_manager.dominio import (
    AccionDT,
    DirectorTecnico,
    EstadoAnimo,
    EventoVestuario,
    GestorVestuario,
    TipoEventoVestuario,
)
from pro_manager.dominio.errores import EventoYaResueltoError
from tests.conftest import crear_club


@pytest.fixture
def escenario():
    """Escenario crítico de la especificación: el goleador discute con el capitán."""
    club = crear_club()
    goleador, capitan = club.plantilla[-1], club.plantilla[3]
    goleador.calidad, goleador.moral, goleador.estado_animo = 86, 55, EstadoAnimo.MOLESTO
    goleador.personalidad = "TEMPERAMENTAL"
    capitan.es_capitan, capitan.moral = True, 72
    evento = EventoVestuario(
        id="EV-001",
        tipo=TipoEventoVestuario.CONFLICTO_ENTRE_JUGADORES,
        titulo="Pelea en el entrenamiento",
        descripcion="Discuten por rumores de transferencia.",
        protagonista_id=goleador.id,
        afectado_id=capitan.id,
        severidad=12,
    )
    return club, goleador, capitan, evento


def test_sancionar_con_aval_de_la_directiva(escenario):
    club, goleador, capitan, evento = escenario
    dt = DirectorTecnico("DT", reputacion=50)
    resultado = GestorVestuario(random.Random(1)).resolver(evento, AccionDT.SANCIONAR, club, dt)
    assert resultado.resuelto and resultado.aval_directiva is True
    assert goleador.estado_animo == EstadoAnimo.REBELDE  # Molesto → Rebelde
    assert goleador.moral == 55 - 18  # -12 amplificado ×1.5 por temperamental
    assert goleador.partidos_castigo == 1 and not goleador.habilitado and goleador.convocable
    assert capitan.moral == 78
    assert dt.reputacion == 52
    assert evento.resuelto and evento.accion_tomada == AccionDT.SANCIONAR
    assert "Rebelde" in resultado.desenlace
    assert goleador.historia


def test_sancion_sin_aval_no_resuelve_el_conflicto(escenario):
    club, goleador, _, evento = escenario
    dt = DirectorTecnico("DT", reputacion=49)  # figura: requiere 50
    resultado = GestorVestuario().resolver(evento, AccionDT.SANCIONAR, club, dt)
    assert resultado.resuelto is False and resultado.aval_directiva is False
    assert not evento.resuelto
    assert goleador.partidos_castigo == 0 and goleador.estado_animo == EstadoAnimo.MOLESTO
    assert dt.reputacion == 46


def test_dialogar_equilibra_la_moral_y_cuesta_autoridad(escenario):
    club, goleador, capitan, evento = escenario
    dt = DirectorTecnico("DT", reputacion=50)
    resultado = GestorVestuario().resolver(evento, AccionDT.DIALOGAR, club, dt)
    assert resultado.resuelto and resultado.aval_directiva is None
    assert goleador.moral == capitan.moral == (55 + 72) // 2 + 4
    assert goleador.estado_animo == EstadoAnimo.ESTABLE  # mediación: Molesto → Estable
    assert dt.reputacion == 48


def test_dialogar_con_un_rebelde_lo_devuelve_a_estable(escenario):
    club, goleador, _, evento = escenario
    goleador.estado_animo = EstadoAnimo.REBELDE
    evento.afectado_id = None
    GestorVestuario().resolver(evento, AccionDT.DIALOGAR, club, DirectorTecnico("DT"))
    assert goleador.estado_animo == EstadoAnimo.ESTABLE
    assert goleador.moral == 63


def test_sancionar_a_un_estable_no_cambia_su_estado(escenario):
    club, goleador, _, evento = escenario
    goleador.estado_animo = EstadoAnimo.ESTABLE
    evento.afectado_id = None
    resultado = GestorVestuario().resolver(
        evento, AccionDT.SANCIONAR, club, DirectorTecnico("DT", reputacion=80)
    )
    assert goleador.estado_animo == EstadoAnimo.ESTABLE
    assert "entiende el mensaje" in resultado.desenlace


def test_un_evento_resuelto_no_se_vuelve_a_resolver(escenario):
    club, _, _, evento = escenario
    gestor = GestorVestuario()
    gestor.resolver(evento, AccionDT.DIALOGAR, club, DirectorTecnico("DT"))
    with pytest.raises(EventoYaResueltoError):
        gestor.resolver(evento, AccionDT.SANCIONAR, club, DirectorTecnico("DT"))
    with pytest.raises(EventoYaResueltoError):
        evento.marcar_resuelto(AccionDT.DIALOGAR, "otra vez")


# ---------------------------------------------------------------- Narrativa dinámica


def test_un_rebelde_sin_castigo_genera_indisciplina():
    club = crear_club()
    rebelde = club.plantilla[5]
    rebelde.estado_animo = EstadoAnimo.REBELDE
    evento = GestorVestuario(random.Random(1)).generar_evento(club, 2, "EV-002", [])
    assert evento.tipo == TipoEventoVestuario.INDISCIPLINA
    assert evento.protagonista_id == rebelde.id


def test_no_se_duplica_un_evento_para_quien_ya_tiene_uno_pendiente():
    club = crear_club()
    rebelde = club.plantilla[5]
    rebelde.estado_animo = EstadoAnimo.REBELDE
    pendiente = EventoVestuario("EV-1", "INDISCIPLINA", "t", "d", rebelde.id)
    gestor = GestorVestuario(random.Random(4))
    for _ in range(20):
        evento = gestor.generar_evento(club, 2, "EV-2", [pendiente])
        assert evento is None or evento.protagonista_id != rebelde.id


def test_los_molestos_se_quejan_con_frecuencia():
    club = crear_club()
    molesto = club.plantilla[7]
    molesto.estado_animo = EstadoAnimo.MOLESTO
    gestor = GestorVestuario(random.Random(10))
    tipos = [gestor.generar_evento(club, 2, "EV", []) for _ in range(50)]
    quejas = [e for e in tipos if e and e.tipo == TipoEventoVestuario.QUEJA_POR_MINUTOS]
    assert len(quejas) > 20
    assert all(q.protagonista_id == molesto.id for q in quejas)


def test_conflictos_y_rumores_aparecen_en_un_vestuario_tranquilo():
    club = crear_club(nivel=80)
    club.plantilla[0].es_capitan = True
    gestor = GestorVestuario(random.Random(3))
    tipos = {
        e.tipo
        for e in (gestor.generar_evento(club, 2, "EV", []) for _ in range(200))
        if e is not None
    }
    assert TipoEventoVestuario.CONFLICTO_ENTRE_JUGADORES in tipos
    assert TipoEventoVestuario.RUMOR_TRANSFERENCIA in tipos


def test_conflicto_con_menos_de_dos_jugadores_libres():
    club = crear_club()
    gestor = GestorVestuario(random.Random(0))
    assert gestor._conflicto(club, club.plantilla[:1], 1, "EV") is None
