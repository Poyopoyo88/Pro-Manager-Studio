"""HU-01: configuración táctica y alineación pre-partido."""

import pytest

from pro_manager.dominio import FORMACIONES, Alineacion, Mentalidad, Posicion, sugerir_alineacion
from pro_manager.dominio.errores import AlineacionInvalidaError
from tests.conftest import crear_club, crear_jugador


def ids(club, posicion):
    return [j.id for j in club.plantilla if j.posicion == posicion]


def once_valido(club):
    """1 POR + 4 DEF + 4 MED + 2 DEL, suplentes: el resto hasta 7."""
    titulares = ids(club, Posicion.PORTERO)[:1] + ids(club, Posicion.DEFENSA)[:4]
    titulares += ids(club, Posicion.MEDIOCAMPISTA)[:4] + ids(club, Posicion.DELANTERO)[:2]
    suplentes = [j.id for j in club.plantilla if j.id not in titulares][:7]
    return Alineacion("4-4-2", titulares, suplentes)


def test_alineacion_valida_sin_errores_ni_advertencias(club):
    alineacion = once_valido(club)
    alineacion.validar(club)
    assert alineacion.errores(club) == []
    assert alineacion.advertencias(club) == []


def test_formacion_inexistente(club):
    alineacion = once_valido(club)
    alineacion.formacion = "2-2-6"
    assert any("no existe" in e for e in alineacion.errores(club))
    assert alineacion.advertencias(club) == []


@pytest.mark.parametrize("cantidad", [10, 12])
def test_debe_haber_exactamente_once_titulares(club, cantidad):
    todos = [j.id for j in club.plantilla]
    alineacion = Alineacion("4-4-2", todos[:cantidad])
    assert any("exactamente 11 titulares" in e for e in alineacion.errores(club))


def test_sin_portero_o_con_dos_porteros(club):
    sin_portero = [j.id for j in club.plantilla if j.posicion != Posicion.PORTERO][:11]
    assert any("un portero" in e for e in Alineacion("4-4-2", sin_portero).errores(club))
    dos_porteros = (
        ids(club, Posicion.PORTERO)
        + [j.id for j in club.plantilla if j.posicion != Posicion.PORTERO][:9]
    )
    assert any("un portero" in e for e in Alineacion("4-4-2", dos_porteros).errores(club))


def test_duplicados_jugadores_ajenos_y_limite_de_suplentes(club):
    alineacion = once_valido(club)
    alineacion.suplentes = [alineacion.titulares[0], "ajeno", *[j.id for j in club.plantilla][11:]]
    assert len(alineacion.suplentes) == 9  # todavía dentro del límite
    alineacion.suplentes.append(club.plantilla[0].id)
    errores = alineacion.errores(club)
    assert any("más de una vez" in e for e in errores)
    assert any("no pertenece" in e for e in errores)
    assert any("como máximo 9" in e for e in errores)


def test_titular_ajeno(club):
    alineacion = once_valido(club)
    alineacion.titulares[-1] = "ajeno"
    with pytest.raises(AlineacionInvalidaError) as error:
        alineacion.validar(club)
    assert any("no pertenece" in e for e in error.value.errores)


def test_castigado_puede_ir_a_la_banca_pero_no_ser_titular(club):
    alineacion = once_valido(club)
    castigado = club.obtener_jugador(alineacion.titulares[-1])
    castigado.castigar()
    assert any("No puede ser titular" in e for e in alineacion.errores(club))
    indice = next(
        i
        for i, s in enumerate(alineacion.suplentes)
        if club.obtener_jugador(s).posicion != Posicion.PORTERO
    )
    promovido = alineacion.suplentes[indice]
    alineacion.titulares[-1], alineacion.suplentes[indice] = promovido, castigado.id
    # El suplente promovido puede ser de otra posición: eso es advertencia, no error.
    assert alineacion.errores(club) == []


def test_suspendido_o_lesionado_no_puede_ser_convocado(club):
    alineacion = once_valido(club)
    club.obtener_jugador(alineacion.suplentes[0]).suspender()
    club.obtener_jugador(alineacion.suplentes[1]).lesionar(2)
    errores = alineacion.errores(club)
    assert sum("No puede ser convocado" in e for e in errores) == 2


def test_advertencia_por_jugadores_fuera_de_posicion(club):
    alineacion = once_valido(club)
    alineacion.formacion = "4-3-3"
    advertencias = alineacion.advertencias(club)
    assert any("pide 3 MED y alineaste 4" in a for a in advertencias)
    assert any("pide 3 DEL y alineaste 2" in a for a in advertencias)


# ---------------------------------------------------------------- Sugerencia del cuerpo técnico


@pytest.mark.parametrize("formacion", list(FORMACIONES))
def test_sugerencia_valida_para_cada_formacion(club, formacion):
    alineacion = sugerir_alineacion(club, formacion, Mentalidad.OFENSIVA)
    alineacion.validar(club)
    assert alineacion.mentalidad == Mentalidad.OFENSIVA
    assert alineacion.advertencias(club) == []


def test_sugerencia_elige_a_los_mejores_y_lleva_portero_suplente():
    club = crear_club()
    estrella = club.obtener_jugador(ids(club, Posicion.DELANTERO)[-1])
    estrella.calidad = 99
    alineacion = sugerir_alineacion(club, "4-4-2")
    assert estrella.id in alineacion.titulares
    porteros_banca = [s for s in alineacion.suplentes if s in ids(club, Posicion.PORTERO)]
    assert len(porteros_banca) == 1


def test_sugerencia_excluye_inhabilitados(club):
    lesionado, castigado = club.plantilla[2], club.plantilla[3]
    lesionado.lesionar(1)
    castigado.castigar()
    alineacion = sugerir_alineacion(club)
    convocados = alineacion.titulares + alineacion.suplentes
    assert lesionado.id not in convocados and castigado.id not in convocados


def test_sugerencia_completa_con_jugadores_fuera_de_posicion():
    club = crear_club()
    for jugador_id in ids(club, Posicion.DELANTERO):
        club.obtener_jugador(jugador_id).lesionar(1)
    alineacion = sugerir_alineacion(club, "4-4-2")
    assert len(alineacion.titulares) == 11
    assert any("DEL" in a for a in alineacion.advertencias(club))


def test_sugerencia_con_formacion_inexistente(club):
    with pytest.raises(AlineacionInvalidaError):
        sugerir_alineacion(club, "1-1-8")


def test_mentalidad_se_normaliza_desde_texto():
    alineacion = Alineacion("4-4-2", [], [], "DEFENSIVA")
    assert alineacion.mentalidad is Mentalidad.DEFENSIVA
    assert crear_jugador().posicion is Posicion.MEDIOCAMPISTA
