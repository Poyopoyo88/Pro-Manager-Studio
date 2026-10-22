"""Partido y CU-01: ciclo de vida, sustituciones y excepciones 3a / 5a."""

import pytest

from pro_manager.dominio import EstadoPartido, Mentalidad, Resultado, TipoIncidencia
from pro_manager.dominio.errores import (
    AlineacionInvalidaError,
    ClubNoEncontradoError,
    EstadoInvalidoError,
    JugadorInhabilitadoError,
    PartidoNoActivoError,
    SustitucionesAgotadasError,
    SustitucionInvalidaError,
)
from pro_manager.dominio.partido import Partido
from pro_manager.dominio.tactica import Alineacion
from tests.conftest import crear_club, crear_partido


def test_no_se_crea_con_alineacion_invalida():
    local, visitante = crear_club("a"), crear_club("b")
    with pytest.raises(AlineacionInvalidaError):
        Partido("p", local, visitante, Alineacion("4-4-2", []), Alineacion("4-4-2", []))


def test_ciclo_de_vida_completo():
    partido = crear_partido(iniciar=False)
    assert partido.estado == EstadoPartido.PROGRAMADO and not partido.esta_activo
    with pytest.raises(PartidoNoActivoError):
        partido.avanzar_minuto()
    assert partido.iniciar().tipo == TipoIncidencia.INICIO
    with pytest.raises(EstadoInvalidoError):
        partido.iniciar()
    assert partido.avanzar_minuto() == 1
    partido.pausar()
    assert partido.estado == EstadoPartido.PAUSADO and partido.motivo_pausa
    with pytest.raises(PartidoNoActivoError):
        partido.pausar()
    with pytest.raises(PartidoNoActivoError):
        partido.finalizar()
    partido.reanudar()
    with pytest.raises(PartidoNoActivoError):
        partido.reanudar()
    partido.minuto = Partido.DURACION
    with pytest.raises(EstadoInvalidoError):
        partido.avanzar_minuto()
    assert partido.finalizar().tipo == TipoIncidencia.FINAL
    assert partido.estado == EstadoPartido.FINALIZADO


def test_sustitucion_valida(partido):
    club = partido.local.id
    sale, entra = partido.en_campo[club][5], partido.banca[club][1]
    incidencia = partido.sustituir(club, sale, entra)
    assert incidencia.tipo == TipoIncidencia.SUSTITUCION
    assert entra in partido.en_campo[club] and sale not in partido.en_campo[club]
    assert entra not in partido.banca[club]
    assert entra in partido.participantes[club]
    assert partido.sustituciones_restantes(club) == 4


def test_se_puede_sustituir_con_el_partido_pausado(partido):
    partido.pausar()
    club = partido.local.id
    partido.sustituir(club, partido.en_campo[club][0], partido.banca[club][0])


def test_excepcion_3a_jugador_inhabilitado(partido):
    club = partido.local.id
    castigado = partido.local.obtener_jugador(partido.banca[club][2])
    castigado.castigar()
    with pytest.raises(JugadorInhabilitadoError, match="Elige otro suplente"):
        partido.sustituir(club, partido.en_campo[club][3], castigado.id)
    assert partido.sustituciones[club] == 0


def test_excepcion_5a_limite_de_cambios(partido):
    club = partido.local.id
    for i in range(Partido.MAX_SUSTITUCIONES):
        partido.sustituir(club, partido.en_campo[club][i + 1], partido.banca[club][0])
    assert partido.sustituciones_restantes(club) == 0
    with pytest.raises(SustitucionesAgotadasError):
        partido.sustituir(club, partido.en_campo[club][8], partido.banca[club][0])


def test_un_jugador_sustituido_no_vuelve_a_entrar(partido):
    club = partido.local.id
    sale = partido.en_campo[club][4]
    partido.sustituir(club, sale, partido.banca[club][0])
    with pytest.raises(SustitucionInvalidaError, match="banca"):
        partido.sustituir(club, partido.en_campo[club][6], sale)


def test_sale_debe_estar_en_el_campo(partido):
    club = partido.local.id
    with pytest.raises(SustitucionInvalidaError, match="campo"):
        partido.sustituir(club, partido.banca[club][0], partido.banca[club][1])


def test_no_se_sustituye_sin_partido_activo():
    partido = crear_partido(iniciar=False)
    club = partido.local.id
    with pytest.raises(PartidoNoActivoError):
        partido.sustituir(club, partido.en_campo[club][0], partido.banca[club][0])


def test_club_ajeno_al_partido(partido):
    with pytest.raises(ClubNoEncontradoError):
        partido.cambiar_mentalidad("otro", Mentalidad.OFENSIVA)
    with pytest.raises(ClubNoEncontradoError):
        partido.rival_de("otro")


def test_cambio_de_mentalidad(partido):
    incidencia = partido.cambiar_mentalidad(partido.local.id, "OFENSIVA")
    assert partido.mentalidad[partido.local.id] == Mentalidad.OFENSIVA
    assert incidencia.tipo == TipoIncidencia.CAMBIO_MENTALIDAD


def test_goles_y_resultado(partido):
    local, visitante = partido.local.id, partido.visitante.id
    assert partido.resultado_para(local) == Resultado.EMPATE
    partido.registrar_gol(local, partido.en_campo[local][10])
    assert partido.marcador == "1 - 0"
    assert partido.resultado_para(local) == Resultado.VICTORIA
    assert partido.resultado_para(visitante) == Resultado.DERROTA


def test_doble_amarilla_es_expulsion_y_critica_para_el_usuario(partido):
    club = partido.local.id
    jugador = partido.en_campo[club][2]
    assert len(partido.registrar_tarjeta_amarilla(club, jugador)) == 1
    incidencias = partido.registrar_tarjeta_amarilla(club, jugador)
    assert incidencias[-1].tipo == TipoIncidencia.EXPULSION
    assert incidencias[-1].critica is True
    assert jugador in partido.expulsados and len(partido.en_campo[club]) == 10


def test_expulsion_del_rival_no_es_critica(partido):
    club = partido.visitante.id
    incidencia = partido.expulsar(club, partido.en_campo[club][1])
    assert incidencia.critica is False


def test_lesion_marca_al_jugador(partido):
    club = partido.local.id
    jugador_id = partido.en_campo[club][0]
    incidencia = partido.registrar_lesion(club, jugador_id, 2)
    assert incidencia.critica
    assert partido.local.obtener_jugador(jugador_id).lesionado
    assert jugador_id in partido.lesionados_en_partido
