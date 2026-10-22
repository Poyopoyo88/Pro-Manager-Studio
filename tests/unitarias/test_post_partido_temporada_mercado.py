"""Consecuencias post-partido, temporada (puntos y ascenso) y mercado (HU-02, HU-03)."""

import random

import pytest

from pro_manager.dominio import (
    DirectorTecnico,
    EstadoAnimo,
    JugadorEnMercado,
    NegociadorFichajes,
    Ojeador,
    ProcesadorPostPartido,
    Resultado,
    ResultadoJornada,
    Temporada,
)
from pro_manager.dominio.errores import (
    DatoInvalidoError,
    EstadoInvalidoError,
    TemporadaFinalizadaError,
)
from tests.conftest import crear_club, crear_jugador, crear_partido


def terminar(partido, goles_local, goles_visitante):
    partido.goles[partido.local.id] = goles_local
    partido.goles[partido.visitante.id] = goles_visitante
    partido.minuto = 90
    partido.finalizar()
    return partido


# ---------------------------------------------------------------- Post-partido


def test_solo_se_procesa_un_partido_finalizado(partido, dt):
    with pytest.raises(EstadoInvalidoError):
        ProcesadorPostPartido().procesar(partido, dt)
    partido.club_usuario_id = None
    terminar(partido, 0, 0)
    with pytest.raises(EstadoInvalidoError):
        ProcesadorPostPartido().procesar(partido, dt)


def test_victoria_en_casa(partido, dt):
    club = partido.local
    presupuesto = club.presupuesto_fichajes
    titular = club.obtener_jugador(partido.participantes[club.id][0])
    moral_previa = titular.moral
    resumen = ProcesadorPostPartido().procesar(terminar(partido, 2, 1), dt)
    assert resumen.resultado == Resultado.VICTORIA and resumen.jornada.puntos == 3
    assert club.presupuesto_fichajes == presupuesto + 150_000 + 250_000
    assert titular.moral == moral_previa + 5
    assert titular.estado_animo == EstadoAnimo.MOTIVADO
    assert dt.reputacion == 53 and dt.experiencia == 1


def test_derrota_en_partido_decisivo_cuenta_doble(partido, dt):
    partido.es_decisivo = True
    resumen = ProcesadorPostPartido().procesar(terminar(partido, 0, 1), dt)
    assert resumen.resultado == Resultado.DERROTA
    assert dt.reputacion == 44


def test_empate_de_visitante_da_premio_sin_taquilla():
    partido = crear_partido()
    partido.club_usuario_id = partido.visitante.id
    club = partido.visitante
    presupuesto = club.presupuesto_fichajes
    ProcesadorPostPartido().procesar(terminar(partido, 1, 1), DirectorTecnico("DT"))
    assert club.presupuesto_fichajes == presupuesto + 80_000


def test_falta_de_minutos_tras_dos_partidos_sin_jugar(dt):
    club = crear_club()
    figura = club.plantilla[4]
    figura.calidad = 99  # está entre los que esperan jugar
    estados = []
    for _ in range(2):
        partido = crear_partido(local=club)
        # Simulamos que el DT lo dejó fuera de los participantes.
        partido.participantes[club.id] = [
            p for p in partido.participantes[club.id] if p != figura.id
        ]
        resumen = ProcesadorPostPartido().procesar(terminar(partido, 0, 0), dt)
        estados.append(figura.estado_animo)
    assert estados == [EstadoAnimo.ESTABLE, EstadoAnimo.MOLESTO]
    assert figura.partidos_sin_jugar == 2
    assert any("partidos sin jugar" in c for c in resumen.cambios)


def test_jugar_reinicia_el_contador_de_partidos_sin_jugar(partido, dt):
    titular = partido.local.obtener_jugador(partido.participantes[partido.local.id][0])
    titular.partidos_sin_jugar = 3
    ProcesadorPostPartido().procesar(terminar(partido, 0, 0), dt)
    assert titular.partidos_sin_jugar == 0


def test_bajas_se_descuentan_y_la_sancion_cumplida_calma_al_rebelde(partido, dt):
    club = partido.local
    fuera = [j for j in club.plantilla if j.id not in partido.participantes[club.id]]
    lesionado_previo, castigado, suspendido = fuera[0], fuera[1], fuera[2]
    lesionado_previo.partidos_lesion = 1
    castigado.castigar()
    castigado.estado_animo = EstadoAnimo.REBELDE
    suspendido.suspender()
    nuevo_lesionado = partido.en_campo[club.id][3]
    partido.registrar_lesion(club.id, nuevo_lesionado, 2)
    expulsado = partido.en_campo[club.id][5]
    partido.expulsar(club.id, expulsado)
    resumen = ProcesadorPostPartido().procesar(terminar(partido, 0, 0), dt)
    assert not lesionado_previo.lesionado
    assert club.obtener_jugador(nuevo_lesionado).partidos_lesion == 2
    assert castigado.partidos_castigo == 0 and castigado.estado_animo == EstadoAnimo.ESTABLE
    assert suspendido.partidos_suspension == 0
    assert club.obtener_jugador(expulsado).partidos_suspension == 1
    assert any("REBELDE → ESTABLE" in c for c in resumen.cambios)


def test_todos_recuperan_fisico(partido, dt):
    jugador = partido.local.plantilla[0]
    jugador.fisico = 40
    ProcesadorPostPartido().procesar(terminar(partido, 0, 0), dt)
    assert jugador.fisico == 65


# ---------------------------------------------------------------- Temporada


def jornada(numero, resultado):
    goles = {Resultado.VICTORIA: (2, 0), Resultado.EMPATE: (1, 1), Resultado.DERROTA: (0, 1)}
    favor, contra = goles[resultado]
    return ResultadoJornada(numero, "r", "Rival", True, favor, contra, resultado)


def test_temporada_puntos_record_y_ascenso():
    temporada = Temporada(["a", "b", "c"], puntos_ascenso=4)
    assert temporada.rival_de_jornada() == "a"
    assert temporada.es_local() and not temporada.es_decisiva()
    assert temporada.ascendio is None
    temporada.registrar(jornada(1, Resultado.VICTORIA))
    assert not temporada.es_local()
    temporada.registrar(jornada(2, Resultado.EMPATE))
    assert temporada.es_decisiva()
    temporada.registrar(jornada(3, Resultado.DERROTA))
    assert temporada.finalizada and temporada.puntos == 4 and temporada.ascendio is True
    assert temporada.record() == {"VICTORIA": 1, "EMPATE": 1, "DERROTA": 1}
    with pytest.raises(TemporadaFinalizadaError):
        temporada.rival_de_jornada()
    with pytest.raises(TemporadaFinalizadaError):
        temporada.registrar(jornada(4, Resultado.VICTORIA))


def test_temporada_sin_ascenso_y_sin_rivales():
    temporada = Temporada(["a"], puntos_ascenso=3)
    temporada.registrar(jornada(1, Resultado.EMPATE))
    assert temporada.ascendio is False
    with pytest.raises(DatoInvalidoError):
        Temporada([], 1)


# ---------------------------------------------------------------- Ojeadores (HU-02)


def test_el_rango_del_ojeador_contiene_la_calidad_real():
    for semilla in range(200):
        jugador = crear_jugador(calidad=random.Random(semilla).randint(40, 95))
        informe = Ojeador(60, random.Random(semilla)).informar(JugadorEnMercado(jugador, "X"))
        assert informe.calidad_min <= jugador.calidad <= informe.calidad_max


def test_mas_precision_da_rangos_mas_estrechos():
    jugador = JugadorEnMercado(crear_jugador(calidad=70), "X")
    ancho = lambda p: (lambda i: i.calidad_max - i.calidad_min)(  # noqa: E731
        Ojeador(p, random.Random(1)).informar(jugador)
    )
    assert ancho(95) < ancho(40)
    assert Ojeador.del_club(100).precision == 90


@pytest.mark.parametrize(
    ("calidad", "texto"),
    [(90, "prioritario"), (72, "rotación"), (55, "apuesta")],
)
def test_recomendacion_del_ojeador(calidad, texto):
    jugador = JugadorEnMercado(crear_jugador(calidad=calidad), "X")
    assert texto in Ojeador(100, random.Random(1)).informar(jugador).recomendacion


# ---------------------------------------------------------------- Negociación (HU-03)


@pytest.fixture
def objetivo():
    return crear_jugador(valor_mercado=1_000_000, salario=50_000)


def test_oferta_justa_se_acepta(objetivo):
    assert NegociadorFichajes().evaluar(objetivo, 950_000, 47_500).aceptada


def test_oferta_corta_recibe_contraoferta(objetivo):
    respuesta = NegociadorFichajes().evaluar(objetivo, 800_000, 50_000)
    assert not respuesta.aceptada
    assert respuesta.contraoferta_monto == 1_000_000
    assert respuesta.contraoferta_salario == 50_000


def test_oferta_ofensiva_se_rechaza_sin_contraoferta(objetivo):
    respuesta = NegociadorFichajes().evaluar(objetivo, 500_000, 50_000)
    assert not respuesta.aceptada and respuesta.contraoferta_monto is None


def test_oferta_invalida(objetivo):
    with pytest.raises(DatoInvalidoError):
        NegociadorFichajes().evaluar(objetivo, -1, 10)


def test_jugador_libre_sin_valor():
    libre = crear_jugador(valor_mercado=0, salario=0)
    assert NegociadorFichajes().evaluar(libre, 0, 10_000).aceptada
