"""Máquina de estados del jugador (sección 10) y regla RN-03."""

import pytest

from pro_manager.dominio import EstadoAnimo, EventoAnimo
from pro_manager.dominio.estado_animo import (
    TRANSICIONES,
    TRANSICIONES_ESPECIFICACION,
    siguiente_estado,
)
from tests.conftest import crear_jugador

E, Ev = EstadoAnimo, EventoAnimo


@pytest.mark.parametrize(
    ("origen", "evento", "destino"),
    [
        (E.ESTABLE, Ev.ELOGIO, E.MOTIVADO),
        (E.ESTABLE, Ev.VICTORIA, E.MOTIVADO),
        (E.ESTABLE, Ev.FALTA_DE_MINUTOS, E.MOLESTO),
        (E.MOLESTO, Ev.SANCION_SEVERA, E.REBELDE),
        (E.REBELDE, Ev.MEDIACION_COMPLETADA, E.ESTABLE),
    ],
)
def test_transiciones_de_la_especificacion(origen, evento, destino):
    assert TRANSICIONES_ESPECIFICACION[(origen, evento)] == destino
    jugador = crear_jugador(estado_animo=origen)
    assert jugador.aplicar_evento_animo(evento)
    assert jugador.estado_animo == destino


def test_rn03_la_sancion_cumplida_tambien_devuelve_a_estable():
    assert siguiente_estado(E.REBELDE, Ev.SANCION_CUMPLIDA) == E.ESTABLE


@pytest.mark.parametrize("evento", list(Ev))
def test_rn03_rebelde_solo_sale_por_mediacion_o_sancion(evento):
    resultado = siguiente_estado(E.REBELDE, evento)
    if evento in (Ev.MEDIACION_COMPLETADA, Ev.SANCION_CUMPLIDA):
        assert resultado == E.ESTABLE
    else:
        assert resultado == E.REBELDE


@pytest.mark.parametrize("estado", list(E))
@pytest.mark.parametrize("evento", list(Ev))
def test_pares_no_definidos_no_cambian_el_estado(estado, evento):
    esperado = TRANSICIONES.get((estado, evento), estado)
    assert siguiente_estado(estado, evento) == esperado


def test_ningun_evento_lleva_directo_de_estable_a_rebelde():
    assert all(siguiente_estado(E.ESTABLE, ev) != E.REBELDE for ev in Ev)
