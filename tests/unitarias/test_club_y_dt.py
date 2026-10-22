"""RN-02 (presupuesto y masa salarial), visibilidad de la plantilla y Director Técnico."""

import pytest

from pro_manager.dominio import DirectorTecnico, EstadoAnimo
from pro_manager.dominio.errores import (
    AtributoFueraDeRangoError,
    DatoInvalidoError,
    EstadoInvalidoError,
    JugadorNoEncontradoError,
    MasaSalarialExcedidaError,
    PresupuestoExcedidoError,
)
from tests.conftest import crear_club, crear_jugador

# ---------------------------------------------------------------- RN-02


def test_fichaje_dentro_de_los_limites(club):
    nuevo = crear_jugador("nuevo", salario=50_000)
    club.fichar(nuevo, 400_000, jornada=2)
    assert club.tiene_jugador("nuevo")
    assert club.presupuesto_fichajes == 600_000
    assert club.movimientos[-1].monto == -400_000


def test_valor_limite_presupuesto_exacto_se_permite(club):
    club.fichar(crear_jugador("nuevo"), club.presupuesto_fichajes)
    assert club.presupuesto_fichajes == 0


def test_un_peso_por_encima_del_presupuesto_se_rechaza(club):
    with pytest.raises(PresupuestoExcedidoError):
        club.fichar(crear_jugador("nuevo"), club.presupuesto_fichajes + 1)
    assert not club.tiene_jugador("nuevo")


def test_valor_limite_de_masa_salarial(club):
    margen = club.margen_salarial()
    assert club.puede_fichar(0, margen)
    assert not club.puede_fichar(0, margen + 1)
    with pytest.raises(MasaSalarialExcedidaError):
        club.validar_fichaje(0, margen + 1)


def test_montos_negativos_no_son_validos(club):
    assert not club.puede_fichar(-1, 10)
    with pytest.raises(DatoInvalidoError):
        club.validar_fichaje(0, -5)


def test_plantilla_inicial_no_puede_exceder_el_limite():
    with pytest.raises(MasaSalarialExcedidaError):
        crear_club(limite_masa_salarial=1)


def test_ingresos_y_gastos(club):
    club.registrar_ingreso("Taquilla", 100_000, 1)
    club.registrar_gasto("Viaje", 50_000, 1)
    assert club.presupuesto_fichajes == 1_050_000
    with pytest.raises(PresupuestoExcedidoError):
        club.registrar_gasto("Estadio nuevo", 10_000_000)
    with pytest.raises(DatoInvalidoError):
        club.registrar_ingreso("Nada", 0)
    with pytest.raises(DatoInvalidoError):
        club.registrar_gasto("Nada", -1)


# ---------------------------------------------------------------- Plantilla


def test_la_plantilla_expuesta_es_una_copia(club):
    copia = club.plantilla
    copia.clear()
    assert len(club.plantilla) == 18


def test_jugador_duplicado_o_inexistente(club):
    with pytest.raises(DatoInvalidoError):
        club.agregar_jugador(crear_jugador(club.plantilla[0].id))
    with pytest.raises(JugadorNoEncontradoError):
        club.obtener_jugador("no-existe")


def test_capitan(club):
    assert club.capitan() is None
    club.plantilla[3].es_capitan = True
    assert club.capitan() is club.plantilla[3]


def test_club_con_datos_invalidos():
    with pytest.raises(DatoInvalidoError):
        crear_club(presupuesto_fichajes=-1)
    with pytest.raises(AtributoFueraDeRangoError):
        crear_club(reputacion=0)


def test_reputacion_del_club_satura(club):
    club.ajustar_reputacion(500)
    assert club.reputacion == 100


# ---------------------------------------------------------------- Aval de la directiva


@pytest.mark.parametrize(
    ("calidad", "capitan", "reputacion_dt", "aval"),
    [
        (70, False, 30, True),  # jugador normal, umbral 30 exacto
        (70, False, 29, False),
        (85, False, 50, True),  # figura, umbral 50 exacto
        (85, False, 49, False),
        (60, True, 49, False),  # el capitán cuenta como figura
    ],
)
def test_aval_de_la_directiva(club, calidad, capitan, reputacion_dt, aval):
    jugador = crear_jugador(calidad=calidad, es_capitan=capitan)
    assert club.avalar_sancion(jugador, DirectorTecnico("DT", reputacion=reputacion_dt)) is aval


# ---------------------------------------------------------------- Director Técnico


def test_dt_valida_sus_datos():
    with pytest.raises(DatoInvalidoError):
        DirectorTecnico("  ")
    with pytest.raises(DatoInvalidoError):
        DirectorTecnico("DT", experiencia=-1)
    with pytest.raises(AtributoFueraDeRangoError):
        DirectorTecnico("DT", reputacion=101)


def test_reputacion_del_dt_satura(dt):
    assert dt.ajustar_reputacion(-80) == -49
    assert dt.reputacion == 1


def test_elogio_motiva_y_solo_una_vez_por_jornada(dt):
    jugador = crear_jugador(moral=50)
    assert dt.elogiar(jugador, jornada=1) is True
    assert jugador.estado_animo == EstadoAnimo.MOTIVADO
    assert jugador.moral == 56
    with pytest.raises(EstadoInvalidoError):
        dt.elogiar(crear_jugador("otro"), jornada=1)
    assert dt.elogiar(crear_jugador("otro"), jornada=2) is True


def test_partidos_dirigidos(dt):
    dt.sumar_partido_dirigido()
    assert dt.experiencia == 1
