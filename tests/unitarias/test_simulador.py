"""Motor de simulación (HU-05) y requisito de calidad de rendimiento."""

import random
import time

import pytest

from pro_manager.dominio import (
    EstadoPartido,
    Mentalidad,
    Posicion,
    SimuladorPartido,
    TipoIncidencia,
)
from pro_manager.dominio.errores import PartidoNoActivoError
from pro_manager.dominio.ia_rival import IAEntrenadorRival
from tests.conftest import crear_club, crear_partido


def jugar_completo(partido, simulador):
    while partido.estado != EstadoPartido.FINALIZADO:
        if partido.estado == EstadoPartido.PAUSADO:
            partido.reanudar()
        simulador.simular(partido, 90)
    return partido


def test_simular_requiere_partido_en_juego():
    partido = crear_partido(iniciar=False)
    with pytest.raises(PartidoNoActivoError):
        SimuladorPartido(random.Random(1)).simular(partido, 5)


def test_avanza_los_minutos_pedidos(partido):
    simulador = SimuladorPartido(random.Random(1), pausar_en_descanso=False)
    simulador.PROB_LESION = 0  # sin interrupciones
    simulador.PROB_AMARILLA = simulador.PROB_ROJA = 0
    simulador.simular(partido, 10)
    assert partido.minuto == 10


def test_se_detiene_en_el_descanso(partido):
    simulador = SimuladorPartido(random.Random(3))
    simulador.PROB_LESION = simulador.PROB_AMARILLA = simulador.PROB_ROJA = 0
    simulador.simular(partido, 90)
    assert partido.estado == EstadoPartido.PAUSADO
    assert partido.minuto == 45 and "Descanso" in partido.motivo_pausa


def test_termina_a_los_noventa_minutos(partido):
    jugar_completo(partido, SimuladorPartido(random.Random(5)))
    assert partido.minuto == 90
    assert partido.incidencias[-1].tipo == TipoIncidencia.FINAL


def test_es_determinista_con_la_misma_semilla():
    marcadores = []
    for _ in range(2):
        partido = crear_partido()
        jugar_completo(partido, SimuladorPartido(random.Random(42)))
        marcadores.append((partido.marcador, [i.descripcion for i in partido.incidencias]))
    assert marcadores[0] == marcadores[1]


def test_lesion_del_usuario_detiene_la_simulacion(partido):
    simulador = SimuladorPartido(random.Random(7))
    simulador.PROB_LESION = 1.0
    nuevas = simulador.simular(partido, 30)
    assert partido.estado == EstadoPartido.PAUSADO
    assert partido.minuto == 1
    assert any(i.tipo == TipoIncidencia.LESION and i.critica for i in nuevas)
    assert "Incidencia crítica" in partido.motivo_pausa


def test_la_ia_rival_sustituye_a_sus_lesionados(partido):
    rival = partido.visitante.id
    lesionado = partido.en_campo[rival][4]
    partido.visitante.obtener_jugador(lesionado).lesionar(2)
    IAEntrenadorRival().actuar(partido, rival)
    assert lesionado not in partido.en_campo[rival]
    assert partido.sustituciones[rival] == 1


def test_la_ia_rival_cambia_agotados_y_ajusta_mentalidad(partido):
    rival = partido.visitante.id
    cansado = partido.en_campo[rival][6]
    partido.visitante.obtener_jugador(cansado).fisico = 20
    partido.goles[partido.local.id] = 2
    partido.minuto = 60
    IAEntrenadorRival().actuar(partido, rival)
    assert cansado not in partido.en_campo[rival]
    assert partido.mentalidad[rival] == Mentalidad.OFENSIVA
    partido.goles[rival] = 5
    partido.minuto = 75
    IAEntrenadorRival().actuar(partido, rival)
    assert partido.mentalidad[rival] == Mentalidad.DEFENSIVA


def test_la_ia_rival_no_actua_sin_cambios_ni_partido_activo(partido):
    rival = partido.visitante.id
    partido.sustituciones[rival] = 5
    partido.visitante.obtener_jugador(partido.en_campo[rival][2]).lesionar(1)
    IAEntrenadorRival().actuar(partido, rival)
    assert partido.sustituciones[rival] == 5
    partido.pausar()
    partido.estado = EstadoPartido.FINALIZADO
    IAEntrenadorRival().actuar(partido, rival)


# ---------------------------------------------------------------- Fuerza de los equipos


def test_mentalidad_ofensiva_sube_ataque_y_baja_defensa(partido):
    simulador = SimuladorPartido(random.Random(1))
    club = partido.local.id
    ataque_eq, defensa_eq = simulador.fuerza(partido, club)
    partido.cambiar_mentalidad(club, Mentalidad.OFENSIVA)
    ataque_of, defensa_of = simulador.fuerza(partido, club)
    assert ataque_of > ataque_eq and defensa_of < defensa_eq


def test_inferioridad_numerica_reduce_la_fuerza(partido):
    simulador = SimuladorPartido(random.Random(1))
    club = partido.local.id
    antes = simulador.fuerza(partido, club)
    partido.expulsar(club, partido.en_campo[club][5])
    despues = simulador.fuerza(partido, club)
    assert despues[0] < antes[0] and despues[1] < antes[1]


def test_sin_portero_la_defensa_se_desploma(partido):
    simulador = SimuladorPartido(random.Random(1))
    club = partido.local.id
    defensa_con_portero = simulador.fuerza(partido, club)[1]
    portero = next(j.id for j in partido.jugadores_en_campo(club) if j.posicion == Posicion.PORTERO)
    delantero_banca = next(
        j.id for j in partido.jugadores_en_banca(club) if j.posicion != Posicion.PORTERO
    )
    partido.sustituir(club, portero, delantero_banca)
    assert simulador.fuerza(partido, club)[1] < defensa_con_portero


def test_equipo_superior_marca_mas_en_promedio():
    goles_fuerte = goles_debil = 0
    for semilla in range(60):
        fuerte, debil = crear_club("fuerte", nivel=85), crear_club("debil", nivel=55)
        partido = crear_partido(fuerte, debil)
        jugar_completo(partido, SimuladorPartido(random.Random(semilla)))
        goles_fuerte += partido.goles["fuerte"]
        goles_debil += partido.goles["debil"]
    assert goles_fuerte > goles_debil * 1.5


def test_promedio_de_goles_realista():
    total = 0
    partidos = 150
    for semilla in range(partidos):
        partido = crear_partido()
        jugar_completo(partido, SimuladorPartido(random.Random(semilla)))
        total += sum(partido.goles.values())
    assert 1.5 <= total / partidos <= 4.0


def test_la_fatiga_reduce_el_fisico(partido):
    simulador = SimuladorPartido(random.Random(9))
    simulador.PROB_LESION = simulador.PROB_AMARILLA = simulador.PROB_ROJA = 0
    club = partido.local.id
    jugador = partido.jugadores_en_campo(club)[3]
    inicial = jugador.fisico
    simulador.simular(partido, 30)
    assert jugador.fisico < inicial


@pytest.mark.rendimiento
def test_requisito_de_calidad_un_partido_completo_en_menos_de_150_ms():
    """La simulación no debe degradar la interfaz.

    Se mide la mediana de 30 partidos completos (90 minutos). Sin instrumentación tarda
    unos 7 ms; el margen absorbe la sobrecarga de la medición de cobertura en CI.
    """
    tiempos = []
    for semilla in range(30):
        partido = crear_partido()
        inicio = time.perf_counter()
        jugar_completo(partido, SimuladorPartido(random.Random(semilla)))
        tiempos.append(time.perf_counter() - inicio)
    assert sorted(tiempos)[len(tiempos) // 2] < 0.150
