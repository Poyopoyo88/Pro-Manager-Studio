"""API REST (FastAPI) de punta a punta, incluido el CU-01 con sus excepciones."""

import pytest

BASE = "/api/v1"


@pytest.fixture
def partida_id(cliente):
    respuesta = cliente.post(f"{BASE}/partidas", json={"nombre_dt": "Profe API", "semilla": 77})
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def url(partida_id, resto=""):
    return f"{BASE}/partidas/{partida_id}{resto}"


def resolver_vestuario(cliente, partida_id, accion="DIALOGAR"):
    for evento in cliente.get(url(partida_id, "/vestuario/eventos?pendientes=true")).json():
        r = cliente.post(
            url(partida_id, f"/vestuario/eventos/{evento['id']}/resolucion"),
            json={"accion": accion},
        )
        assert r.status_code == 200


def guardar_sugerida(cliente, partida_id, formacion="4-4-2", excluir=(), banca_extra=()):
    sugerida = cliente.get(url(partida_id, f"/alineacion/sugerida?formacion={formacion}")).json()
    sugerida["suplentes"] = [s for s in sugerida["suplentes"] if s not in excluir][
        : 9 - len(banca_extra)
    ]
    sugerida["suplentes"] += list(banca_extra)
    r = cliente.put(url(partida_id, "/alineacion"), json=sugerida)
    assert r.status_code == 200, r.json()
    return r.json()


def iniciar_y_pausar(cliente, partida_id):
    assert cliente.post(url(partida_id, "/partido")).status_code == 201
    cliente.post(url(partida_id, "/partido/simulacion"), json={"minutos": 5})
    partido = cliente.get(url(partida_id, "/partido")).json()
    if partido["estado"] == "EN_JUEGO":
        partido = cliente.post(url(partida_id, "/partido/pausa")).json()
    assert partido["estado"] == "PAUSADO"
    return partido


def equipo_usuario(partido):
    return partido["local"] if partido["local"]["es_usuario"] else partido["visitante"]


# ---------------------------------------------------------------- Sistema y partidas


def test_salud_e_interfaz_web(cliente):
    assert cliente.get(f"{BASE}/salud").json()["estado"] == "ok"
    pagina = cliente.get("/")
    assert pagina.status_code == 200 and "Pro Manager Studio" in pagina.text
    assert cliente.get("/static/app.js").status_code == 200
    assert "/api/v1/partidas" in cliente.get("/openapi.json").json()["paths"]


def test_crear_listar_consultar_y_eliminar(cliente, partida_id):
    partida = cliente.get(url(partida_id)).json()
    assert partida["club"]["nombre"] == "Halcones del Desierto FC"
    assert partida["eventos_pendientes"] == 1
    assert partida["temporada"]["proximo_rival"]["id"] == "union-pitic"
    assert partida["hay_partido"] is False
    listado = cliente.get(f"{BASE}/partidas").json()
    assert [p["id"] for p in listado] == [partida_id]
    assert cliente.delete(url(partida_id)).status_code == 204
    error = cliente.get(url(partida_id))
    assert error.status_code == 404 and error.json()["codigo"] == "partida_no_encontrada"


def test_validacion_de_entrada_en_espanol(cliente):
    r = cliente.post(f"{BASE}/partidas", json={"nombre_dt": ""})
    assert r.status_code == 422
    assert r.json()["codigo"] == "solicitud_invalida" and r.json()["errores"]


# ---------------------------------------------------------------- HU-01 Plantilla y alineación


def test_plantilla_y_jugador(cliente, partida_id):
    plantilla = cliente.get(url(partida_id, "/plantilla")).json()
    assert len(plantilla) == 23
    assert all(1 <= j["rendimiento"] <= 100 for j in plantilla)
    goleador = cliente.get(url(partida_id, "/plantilla/hal-09")).json()
    assert goleador["estado_animo"] == "MOLESTO" and goleador["historia"]
    assert cliente.get(url(partida_id, "/plantilla/nadie")).status_code == 404
    assert cliente.get(url(partida_id, "/formaciones")).json()[0] == "4-4-2"


def test_alineacion_valida_e_invalida(cliente, partida_id):
    assert cliente.get(url(partida_id, "/alineacion")).json() is None
    guardada = guardar_sugerida(cliente, partida_id, "3-5-2")
    assert guardada["formacion"] == "3-5-2" and len(guardada["titulares"]) == 11
    assert cliente.get(url(partida_id, "/alineacion")).json()["titulares"] == guardada["titulares"]
    r = cliente.put(
        url(partida_id, "/alineacion"), json={"formacion": "4-4-2", "titulares": ["hal-01"]}
    )
    assert r.status_code == 422
    assert r.json()["codigo"] == "alineacion_invalida" and r.json()["errores"]


def test_elogio_una_vez_por_jornada(cliente, partida_id):
    r = cliente.post(url(partida_id, "/plantilla/hal-02/elogio"))
    assert r.status_code == 200 and r.json()["cambio_estado"] is True
    assert r.json()["jugador"]["estado_animo"] == "MOTIVADO"
    assert cliente.post(url(partida_id, "/plantilla/hal-03/elogio")).status_code == 409


# ---------------------------------------------------------------- HU-04 Vestuario


def test_escenario_critico_sancion(cliente, partida_id):
    eventos = cliente.get(url(partida_id, "/vestuario/eventos?pendientes=true")).json()
    assert eventos[0]["protagonista"]["id"] == "hal-09"
    assert eventos[0]["afectado"]["id"] == "hal-04"
    detalle = cliente.get(url(partida_id, f"/vestuario/eventos/{eventos[0]['id']}")).json()
    assert detalle["titulo"] == eventos[0]["titulo"]
    r = cliente.post(
        url(partida_id, f"/vestuario/eventos/{eventos[0]['id']}/resolucion"),
        json={"accion": "SANCIONAR"},
    ).json()
    assert r["resuelto"] and r["aval_directiva"] is True
    assert any("REBELDE" in c for c in r["cambios"])
    repetido = cliente.post(
        url(partida_id, f"/vestuario/eventos/{eventos[0]['id']}/resolucion"),
        json={"accion": "DIALOGAR"},
    )
    assert repetido.status_code == 409 and repetido.json()["codigo"] == "evento_ya_resuelto"
    assert cliente.get(url(partida_id, "/vestuario/eventos/EV-404")).status_code == 404
    assert len(cliente.get(url(partida_id, "/vestuario/eventos")).json()) == 1


def test_no_hay_partido_con_crisis_pendiente(cliente, partida_id):
    r = cliente.post(url(partida_id, "/partido"))
    assert r.status_code == 409 and r.json()["codigo"] == "eventos_pendientes"
    assert cliente.get(url(partida_id, "/partido")).status_code == 409


# ---------------------------------------------------------------- HU-05 / CU-01


def test_cu01_flujo_principal(cliente, partida_id):
    resolver_vestuario(cliente, partida_id)
    guardar_sugerida(cliente, partida_id)
    partido = iniciar_y_pausar(cliente, partida_id)  # 1 y 2: pausa y panel
    equipo = equipo_usuario(partido)
    sale, entra = equipo["en_campo"][4]["id"], equipo["banca"][2]["id"]
    r = cliente.post(
        url(partida_id, "/partido/sustituciones"), json={"id_sale": sale, "id_entra": entra}
    )
    assert r.status_code == 200 and r.json()["aplicada"] is True  # 3 y 5
    assert equipo_usuario(r.json()["partido"])["sustituciones_restantes"] == 4
    m = cliente.put(url(partida_id, "/partido/mentalidad"), json={"mentalidad": "DEFENSIVA"})
    assert equipo_usuario(m.json())["mentalidad"] == "DEFENSIVA"  # 4
    reanudado = cliente.post(url(partida_id, "/partido/reanudacion")).json()  # 6
    assert reanudado["estado"] == "EN_JUEGO"

    while True:
        respuesta = cliente.post(
            url(partida_id, "/partido/simulacion"), json={"minutos": 90}
        ).json()
        if respuesta["partido"]["estado"] == "FINALIZADO":
            break
        cliente.post(url(partida_id, "/partido/reanudacion"))
    assert respuesta["partido"]["resultado"] in ("VICTORIA", "EMPATE", "DERROTA")
    assert respuesta["noticias"][0].startswith("Jornada 1")
    partida = cliente.get(url(partida_id)).json()
    assert partida["temporada"]["jornada_actual"] == 2 and partida["hay_partido"]


def test_cu01_excepcion_3a_jugador_inhabilitado(cliente, partida_id):
    resolver_vestuario(cliente, partida_id, accion="SANCIONAR")  # Valenzuela va castigado
    guardar_sugerida(cliente, partida_id, banca_extra=["hal-09"])
    iniciar_y_pausar(cliente, partida_id)
    partido = cliente.get(url(partida_id, "/partido")).json()
    sale = equipo_usuario(partido)["en_campo"][9]["id"]
    r = cliente.post(
        url(partida_id, "/partido/sustituciones"), json={"id_sale": sale, "id_entra": "hal-09"}
    )
    assert r.status_code == 422
    assert r.json()["codigo"] == "jugador_inhabilitado"
    assert "Elige otro suplente" in r.json()["mensaje"]


def test_cu01_excepcion_5a_limite_de_cambios(cliente, partida_id):
    resolver_vestuario(cliente, partida_id)
    guardar_sugerida(cliente, partida_id)
    partido = iniciar_y_pausar(cliente, partida_id)
    equipo = equipo_usuario(partido)
    campo = [j["id"] for j in equipo["en_campo"]]
    banca = [j["id"] for j in equipo["banca"] if j["habilitado"]]
    for i in range(5):
        r = cliente.post(
            url(partida_id, "/partido/sustituciones"),
            json={"id_sale": campo[i + 1], "id_entra": banca[i]},
        )
        assert r.status_code == 200
    r = cliente.post(
        url(partida_id, "/partido/sustituciones"), json={"id_sale": campo[8], "id_entra": banca[5]}
    )
    assert r.status_code == 422 and r.json()["codigo"] == "sustituciones_agotadas"


def test_simular_con_el_partido_pausado_es_un_conflicto(cliente, partida_id):
    resolver_vestuario(cliente, partida_id)
    guardar_sugerida(cliente, partida_id)
    iniciar_y_pausar(cliente, partida_id)
    r = cliente.post(url(partida_id, "/partido/simulacion"), json={"minutos": 5})
    assert r.status_code == 409 and r.json()["codigo"] == "partido_no_activo"
    assert cliente.post(url(partida_id, "/partido/pausa")).status_code == 409


# ---------------------------------------------------------------- HU-02 / HU-03 / HU-06


def test_finanzas_mercado_ojeo_y_oferta(cliente, partida_id):
    finanzas = cliente.get(url(partida_id, "/finanzas")).json()
    assert finanzas["presupuesto_fichajes"] == 3_500_000
    assert (
        finanzas["margen_salarial"] == finanzas["limite_masa_salarial"] - finanzas["masa_salarial"]
    )
    mercado = cliente.get(url(partida_id, "/mercado")).json()
    assert len(mercado) == 10 and "calidad" not in mercado[0]
    informes = cliente.get(url(partida_id, "/mercado/informes?posicion=DEL")).json()
    assert informes and all(i["posicion"] == "DEL" for i in informes)

    barato = min(mercado, key=lambda j: j["valor_mercado"])
    contra = cliente.post(
        url(partida_id, f"/mercado/{barato['id']}/ofertas"),
        json={
            "monto_transferencia": int(barato["valor_mercado"] * 0.8),
            "salario": barato["salario_pretendido"],
        },
    ).json()
    assert contra["aceptada"] is False and contra["contraoferta_monto"] == barato["valor_mercado"]
    trato = cliente.post(
        url(partida_id, f"/mercado/{barato['id']}/ofertas"),
        json={
            "monto_transferencia": barato["valor_mercado"],
            "salario": barato["salario_pretendido"],
        },
    ).json()
    assert trato["aceptada"] is True
    finanzas = cliente.get(url(partida_id, "/finanzas")).json()
    assert finanzas["gastos_totales"] == barato["valor_mercado"]
    assert finanzas["movimientos"][0]["monto"] == -barato["valor_mercado"]


def test_oferta_que_excede_el_presupuesto(cliente, partida_id):
    objetivo = cliente.get(url(partida_id, "/mercado")).json()[0]
    r = cliente.post(
        url(partida_id, f"/mercado/{objetivo['id']}/ofertas"),
        json={"monto_transferencia": 50_000_000, "salario": 1000},
    )
    assert r.status_code == 422 and r.json()["codigo"] == "presupuesto_excedido"
