"""RN-01: atributos en [1, 100] — particiones de equivalencia y valores límite.

Particiones para ``validar_atributo``:
    P1 (inválida)  valor < 1          → representantes: -1, 0
    P2 (válida)    1 <= valor <= 100  → representantes: 1, 2, 50, 99, 100
    P3 (inválida)  valor > 100        → representantes: 101, 1000
    P4 (inválida)  no entero          → 50.5, "50", True
"""

import pytest

from pro_manager.dominio import EstadoAnimo, EventoAnimo, Jugador
from pro_manager.dominio.atributos import acotar, validar_atributo
from pro_manager.dominio.errores import AtributoFueraDeRangoError, DatoInvalidoError
from tests.conftest import crear_jugador

# ---------------------------------------------------------------- validar_atributo


@pytest.mark.parametrize("valor", [1, 2, 50, 99, 100])
def test_valores_validos_en_el_rango_cerrado(valor):
    assert validar_atributo("moral", valor) == valor


@pytest.mark.parametrize("valor", [-1, 0, 101, 1000])
def test_valores_fuera_de_rango_se_rechazan(valor):
    with pytest.raises(AtributoFueraDeRangoError, match="entre 1 y 100"):
        validar_atributo("moral", valor)


@pytest.mark.parametrize("valor", [50.5, "50", True, None])
def test_valores_no_enteros_se_rechazan(valor):
    with pytest.raises(AtributoFueraDeRangoError, match="entero"):
        validar_atributo("fisico", valor)


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [(-30, 1), (0, 1), (1, 1), (50.4, 50), (100, 100), (101, 100), (250, 100)],
)
def test_acotar_satura_al_rango(entrada, esperado):
    assert acotar(entrada) == esperado


# ---------------------------------------------------------------- Construcción del jugador


@pytest.mark.parametrize("atributo", ["calidad", "fisico", "moral"])
@pytest.mark.parametrize("valor", [0, 101])
def test_jugador_no_se_crea_con_atributos_fuera_de_rango(atributo, valor):
    with pytest.raises(AtributoFueraDeRangoError):
        crear_jugador(**{atributo: valor})


@pytest.mark.parametrize("atributo", ["calidad", "fisico", "moral"])
@pytest.mark.parametrize("valor", [1, 100])
def test_jugador_acepta_los_limites(atributo, valor):
    assert getattr(crear_jugador(**{atributo: valor}), atributo) == valor


def test_asignar_un_atributo_invalido_despues_de_crear_falla(jugador):
    with pytest.raises(AtributoFueraDeRangoError):
        jugador.moral = 0
    assert jugador.moral == 60


@pytest.mark.parametrize(
    "cambios",
    [
        {"id": ""},
        {"nombre": " "},
        {"edad": 14},
        {"edad": 46},
        {"salario": -1},
        {"partidos_lesion": -1},
    ],
)
def test_datos_basicos_invalidos(cambios):
    with pytest.raises(DatoInvalidoError):
        crear_jugador(**cambios)


# ---------------------------------------------------------------- Moral (Information Expert)


def test_impacto_positivo_no_depende_de_la_personalidad():
    temperamental = crear_jugador(personalidad="TEMPERAMENTAL", moral=50)
    lider = crear_jugador(personalidad="LIDER", moral=50)
    assert temperamental.actualizar_moral(10) == lider.actualizar_moral(10) == 10


@pytest.mark.parametrize(
    ("personalidad", "cambio_esperado"),
    [
        ("TEMPERAMENTAL", -15),
        ("AMBICIOSO", -12),
        ("RESERVADO", -10),
        ("PROFESIONAL", -8),
        ("LIDER", -6),
    ],
)
def test_impacto_negativo_modulado_por_personalidad(personalidad, cambio_esperado):
    j = crear_jugador(personalidad=personalidad, moral=50)
    assert j.actualizar_moral(-10) == cambio_esperado


def test_moral_satura_en_los_limites():
    j = crear_jugador(moral=95)
    assert j.actualizar_moral(30) == 5
    assert j.moral == 100
    j.moral = 3
    j.actualizar_moral(-50)
    assert j.moral == 1


# ---------------------------------------------------------------- Rendimiento


def test_rendimiento_con_valores_de_referencia():
    # base = 0.6*80 + 0.4*80 = 80; factor moral = 0.7 + 0.6*0.5 = 1.0; Estable = 1.0
    j = crear_jugador(calidad=80, fisico=80, moral=50)
    assert j.calcular_rendimiento_actual() == 80.0


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [("MOTIVADO", 88.0), ("ESTABLE", 80.0), ("MOLESTO", 72.0), ("REBELDE", 60.0)],
)
def test_estado_de_animo_modifica_el_rendimiento(estado, esperado):
    j = crear_jugador(calidad=80, fisico=80, moral=50, estado_animo=estado)
    assert j.calcular_rendimiento_actual() == esperado


@pytest.mark.parametrize(
    ("calidad", "fisico", "moral", "estado"),
    [(100, 100, 100, "MOTIVADO"), (1, 1, 1, "REBELDE"), (1, 1, 1, "ESTABLE")],
)
def test_rendimiento_siempre_en_el_rango(calidad, fisico, moral, estado):
    j = crear_jugador(calidad=calidad, fisico=fisico, moral=moral, estado_animo=estado)
    assert 1.0 <= j.calcular_rendimiento_actual() <= 100.0


def test_lesionado_rinde_al_treinta_por_ciento():
    j = crear_jugador(calidad=80, fisico=80, moral=50)
    j.lesionar(2)
    assert j.calcular_rendimiento_actual() == 24.0


# ---------------------------------------------------------------- Disponibilidad y estado


def test_disponibilidad_segun_bajas():
    j = crear_jugador()
    assert j.habilitado and j.convocable and j.motivo_inhabilitacion() is None
    j.castigar()
    assert not j.habilitado and j.convocable
    assert "sanción interna" in j.motivo_inhabilitacion()
    j.partidos_castigo = 0
    j.suspender()
    assert not j.habilitado and not j.convocable
    assert "suspendido" in j.motivo_inhabilitacion()
    j.partidos_suspension = 0
    j.lesionar(3)
    assert j.lesionado and not j.convocable
    assert "lesionado" in j.motivo_inhabilitacion()


def test_lesion_de_cero_partidos_es_invalida(jugador):
    with pytest.raises(DatoInvalidoError):
        jugador.lesionar(0)


def test_lesion_conserva_la_baja_mas_larga(jugador):
    jugador.lesionar(3)
    jugador.lesionar(1)
    assert jugador.partidos_lesion == 3


def test_desgaste_y_recuperacion_saturan(jugador):
    jugador.desgastar(500)
    assert jugador.fisico == 1
    jugador.recuperar(500)
    assert jugador.fisico == 100


def test_aplicar_evento_reporta_si_cambio_el_estado(jugador):
    assert jugador.aplicar_evento_animo(EventoAnimo.ELOGIO) is True
    assert jugador.estado_animo == EstadoAnimo.MOTIVADO
    assert jugador.aplicar_evento_animo(EventoAnimo.ELOGIO) is False


def test_historia_personal(jugador):
    jugador.registrar_historia("Debutó con gol.")
    assert jugador.historia == ["Debutó con gol."]


def test_valores_por_defecto():
    j = Jugador("x", "X", "POR", 50, 50, 50)
    assert j.estado_animo == EstadoAnimo.ESTABLE
    assert j.partidos_sin_jugar == 0
