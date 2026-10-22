"""Capa de aplicación: casos de uso completos con el repositorio en memoria."""

import pytest

from pro_manager.aplicacion import (
    ControladorCarrera,
    ControladorClub,
    ControladorPartido,
    ControladorPlantilla,
    ControladorVestuario,
    SinPartidoError,
)
from pro_manager.dominio import AccionDT, EstadoPartido, Mentalidad, Posicion
from pro_manager.dominio.errores import (
    AlineacionInvalidaError,
    EstadoInvalidoError,
    EventoNoEncontradoError,
    EventosPendientesError,
    JugadorNoEncontradoError,
    MasaSalarialExcedidaError,
    PresupuestoExcedidoError,
    TemporadaFinalizadaError,
)


@pytest.fixture
def ctrl(repositorio, datos):
    class Controladores:
        carrera = ControladorCarrera(repositorio, datos)
        plantilla = ControladorPlantilla(repositorio)
        vestuario = ControladorVestuario(repositorio)
        partido = ControladorPartido(repositorio)
        club = ControladorClub(repositorio)

    return Controladores


def preparar_jornada(ctrl, partida_id, formacion="4-4-2"):
    _, pendientes = ctrl.vestuario.eventos(partida_id, solo_pendientes=True)
    for evento in pendientes:
        ctrl.vestuario.resolver_evento(partida_id, evento.id, AccionDT.DIALOGAR)
    alineacion, _ = ctrl.plantilla.sugerir_alineacion(partida_id, formacion)
    ctrl.plantilla.definir_alineacion(
        partida_id, formacion, alineacion.titulares, alineacion.suplentes
    )


def jugar_partido(ctrl, partida_id):
    ctrl.partido.iniciar_partido(partida_id)
    while True:
        partida, _ = ctrl.partido.simular(partida_id, 90)
        if partida.partido.estado == EstadoPartido.FINALIZADO:
            return partida
        ctrl.partido.reanudar_partido(partida_id)


def test_temporada_completa(ctrl):
    partida = ctrl.carrera.crear_partida("DT Temporada", semilla=99)
    for _ in range(partida.temporada.total_jornadas):
        preparar_jornada(ctrl, partida.id)
        partida = jugar_partido(ctrl, partida.id)
    assert partida.temporada.finalizada
    assert len(partida.temporada.historial) == 5
    assert partida.dt.experiencia == 5
    assert partida.temporada.ascendio in (True, False)
    assert "ascenso" in partida.noticias[0].lower()
    with pytest.raises(TemporadaFinalizadaError):
        ctrl.partido.iniciar_partido(partida.id)


def test_la_misma_semilla_reproduce_la_temporada(ctrl):
    resultados = []
    for _ in range(2):
        partida = ctrl.carrera.crear_partida("DT", semilla=1234)
        preparar_jornada(ctrl, partida.id)
        resultados.append(jugar_partido(ctrl, partida.id).partido.marcador)
    assert resultados[0] == resultados[1]


def test_precondiciones_para_iniciar_un_partido(ctrl):
    partida = ctrl.carrera.crear_partida("DT", semilla=5)
    with pytest.raises(EventosPendientesError):
        ctrl.partido.iniciar_partido(partida.id)
    ctrl.vestuario.resolver_evento(partida.id, partida.eventos[0].id, AccionDT.DIALOGAR)
    with pytest.raises(AlineacionInvalidaError):
        ctrl.partido.iniciar_partido(partida.id)
    with pytest.raises(SinPartidoError):
        ctrl.partido.estado(partida.id)
    preparar_jornada(ctrl, partida.id)
    ctrl.partido.iniciar_partido(partida.id)
    with pytest.raises(EstadoInvalidoError):
        ctrl.partido.iniciar_partido(partida.id)
    with pytest.raises(EstadoInvalidoError):
        ctrl.plantilla.definir_alineacion(partida.id, "4-4-2", [], [])


def test_cu01_gestion_de_crisis_en_partido(ctrl):
    partida = ctrl.carrera.crear_partida("DT", semilla=8)
    preparar_jornada(ctrl, partida.id)
    ctrl.partido.iniciar_partido(partida.id)
    ctrl.partido.simular(partida.id, 10)
    partida = ctrl.partido.pausar_partido(partida.id)  # paso 1
    club = partida.club.id
    sale, entra = partida.partido.en_campo[club][2], partida.partido.banca[club][1]
    assert ctrl.partido.ejecutar_sustitucion(partida.id, sale, entra) is True  # pasos 3 y 5
    partida = ctrl.partido.cambiar_mentalidad(partida.id, Mentalidad.OFENSIVA)  # paso 4
    assert partida.partido.mentalidad[club] == Mentalidad.OFENSIVA
    partida = ctrl.partido.reanudar_partido(partida.id)  # paso 6
    assert partida.partido.estado == EstadoPartido.EN_JUEGO
    assert entra in ctrl.partido.estado(partida.id).partido.en_campo[club]


def test_sancion_del_escenario_critico_y_elogio(ctrl):
    partida = ctrl.carrera.crear_partida("DT", semilla=3)
    resultado = ctrl.vestuario.resolver_evento(partida.id, "EV-001", AccionDT.SANCIONAR)
    assert resultado.resuelto and resultado.aval_directiva
    partida, evento = ctrl.vestuario.revisar_crisis(partida.id, "EV-001")
    assert evento.resuelto
    with pytest.raises(EventoNoEncontradoError):
        ctrl.vestuario.revisar_crisis(partida.id, "EV-999")
    partida, cambio = ctrl.plantilla.elogiar_jugador(partida.id, "hal-04")
    assert cambio is True
    with pytest.raises(EstadoInvalidoError):
        ctrl.plantilla.elogiar_jugador(partida.id, "hal-02")
    assert ctrl.plantilla.formaciones()[0] == "4-4-2"


def test_ojeo_y_fichaje(ctrl):
    partida = ctrl.carrera.crear_partida("DT", semilla=21)
    informes = ctrl.club.ojear(partida.id)
    assert len(informes) == 10
    assert ctrl.club.ojear(partida.id) == informes  # repetir no da información nueva
    porteros = ctrl.club.ojear(partida.id, Posicion.PORTERO)
    assert all(i.posicion == "POR" for i in porteros)

    barato = min(ctrl.club.mercado(partida.id), key=lambda m: m.jugador.valor_mercado)
    jugador = barato.jugador
    respuesta = ctrl.club.ofertar(partida.id, jugador.id, jugador.valor_mercado, jugador.salario)
    assert respuesta.aceptada
    partida = ctrl.carrera.obtener(partida.id)
    assert partida.club.tiene_jugador(jugador.id)
    assert all(m.jugador.id != jugador.id for m in partida.mercado)
    with pytest.raises(JugadorNoEncontradoError):
        ctrl.club.ofertar(partida.id, jugador.id, 1, 1)


def test_fichaje_que_rompe_las_reglas_financieras(ctrl):
    partida = ctrl.carrera.crear_partida("DT", semilla=21)
    objetivo = ctrl.club.mercado(partida.id)[0].jugador
    with pytest.raises(PresupuestoExcedidoError):
        ctrl.club.ofertar(partida.id, objetivo.id, 999_999_999, objetivo.salario)
    with pytest.raises(MasaSalarialExcedidaError):
        ctrl.club.ofertar(partida.id, objetivo.id, 0, 10_000_000)


def test_no_se_ficha_con_partido_en_curso(ctrl):
    partida = ctrl.carrera.crear_partida("DT", semilla=2)
    preparar_jornada(ctrl, partida.id)
    ctrl.partido.iniciar_partido(partida.id)
    objetivo = ctrl.club.mercado(partida.id)[0].jugador
    with pytest.raises(EstadoInvalidoError):
        ctrl.club.ofertar(partida.id, objetivo.id, objetivo.valor_mercado, objetivo.salario)
    assert ctrl.club.finanzas(partida.id).club.presupuesto_fichajes == 3_500_000
