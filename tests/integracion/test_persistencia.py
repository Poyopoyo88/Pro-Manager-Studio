"""Infraestructura: serialización de partidas, repositorios y datos iniciales."""

import json

import pytest

from pro_manager.aplicacion import (
    ControladorCarrera,
    ControladorPartido,
    ControladorPlantilla,
    ControladorVestuario,
    PartidaNoEncontradaError,
)
from pro_manager.dominio import AccionDT, EstadoAnimo
from pro_manager.dominio.errores import DatoInvalidoError
from pro_manager.infraestructura import (
    ProveedorDatosJSON,
    RepositorioEnMemoria,
    RepositorioJSON,
    crear_repositorio_desde_entorno,
)
from pro_manager.infraestructura.datos_iniciales import salario_estimado, valor_estimado
from pro_manager.infraestructura.serializacion import (
    partida_a_dict,
    partida_desde_dict,
    partido_desde_dict,
)


@pytest.fixture(params=["memoria", "json"])
def repo(request, tmp_path):
    return RepositorioEnMemoria() if request.param == "memoria" else RepositorioJSON(tmp_path)


def partida_con_partido_en_curso(repo):
    carrera = ControladorCarrera(repo, ProveedorDatosJSON())
    partida = carrera.crear_partida("DT Persistente", semilla=11)
    vestuario = ControladorVestuario(repo)
    vestuario.resolver_evento(partida.id, partida.eventos[0].id, AccionDT.SANCIONAR)
    plantilla = ControladorPlantilla(repo)
    alineacion, _ = plantilla.sugerir_alineacion(partida.id, "4-3-3")
    plantilla.definir_alineacion(
        partida.id, alineacion.formacion, alineacion.titulares, alineacion.suplentes
    )
    partido = ControladorPartido(repo)
    partido.iniciar_partido(partida.id)
    partido.simular(partida.id, 20)
    return repo.obtener(partida.id)


def test_ida_y_vuelta_conserva_todo_el_estado(repo):
    original = partida_con_partido_en_curso(repo)
    copia = repo.obtener(original.id)
    assert partida_a_dict(copia) == partida_a_dict(original)
    goleador = copia.club.obtener_jugador("hal-09")
    assert goleador.estado_animo == EstadoAnimo.REBELDE and goleador.partidos_castigo == 1
    assert copia.partido.minuto == original.partido.minuto > 0
    assert copia.partido.local is copia.club or copia.partido.visitante is copia.club


def test_listar_y_eliminar(repo):
    carrera = ControladorCarrera(repo, ProveedorDatosJSON())
    a = carrera.crear_partida("A", semilla=1)
    b = carrera.crear_partida("B", semilla=2)
    assert repo.listar() == sorted([a.id, b.id])
    assert {p.id for p in carrera.listar()} == {a.id, b.id}
    carrera.eliminar(a.id)
    assert repo.listar() == [b.id]
    with pytest.raises(PartidaNoEncontradaError):
        repo.eliminar(a.id)
    with pytest.raises(PartidaNoEncontradaError):
        repo.obtener(a.id)


@pytest.mark.parametrize("identificador", ["../secreto", "a/b", "", "x" * 65])
def test_repositorio_json_rechaza_identificadores_peligrosos(tmp_path, identificador):
    with pytest.raises(PartidaNoEncontradaError):
        RepositorioJSON(tmp_path).obtener(identificador)


def test_repositorio_json_escribe_archivos_legibles(tmp_path):
    repo = RepositorioJSON(tmp_path)
    partida = ControladorCarrera(repo, ProveedorDatosJSON()).crear_partida("DT", semilla=3)
    archivo = tmp_path / f"{partida.id}.json"
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    assert datos["dt"]["nombre"] == "DT"
    assert not list(tmp_path.glob("*.tmp"))


def test_formato_de_version_desconocida():
    with pytest.raises(DatoInvalidoError):
        partida_desde_dict({"version_formato": 999})


def test_partido_que_referencia_un_club_inexistente():
    with pytest.raises(DatoInvalidoError):
        partido_desde_dict({"local_id": "x", "visitante_id": "y"}, {})


def test_configuracion_por_entorno(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_REPOSITORIO", "memoria")
    assert isinstance(crear_repositorio_desde_entorno(), RepositorioEnMemoria)
    monkeypatch.setenv("PM_REPOSITORIO", "json")
    monkeypatch.setenv("PM_DIRECTORIO_PARTIDAS", str(tmp_path / "partidas"))
    assert isinstance(crear_repositorio_desde_entorno(), RepositorioJSON)
    assert (tmp_path / "partidas").is_dir()
    monkeypatch.setenv("PM_REPOSITORIO", "postgres")
    with pytest.raises(ValueError):
        crear_repositorio_desde_entorno()


# ---------------------------------------------------------------- Datos iniciales


def test_datos_iniciales_del_club(datos):
    club = datos.crear_club_usuario()
    assert club.nombre == "Halcones del Desierto FC"
    assert len(club.plantilla) == 23
    assert club.masa_salarial() <= club.limite_masa_salarial
    assert club.capitan().id == "hal-04"
    eventos = datos.eventos_iniciales(club)
    assert eventos[0].protagonista_id == "hal-09" and eventos[0].afectado_id == "hal-04"


def test_rivales_y_mercado_son_reproducibles(datos):
    import random

    rivales_a = datos.crear_rivales(random.Random(5))
    rivales_b = datos.crear_rivales(random.Random(5))
    assert [j.nombre for j in rivales_a[0].plantilla] == [j.nombre for j in rivales_b[0].plantilla]
    assert len(rivales_a) == 5 and all(len(r.plantilla) == 18 for r in rivales_a)
    mercado = datos.crear_mercado(random.Random(5))
    assert len(mercado) == 10 and len({m.jugador.id for m in mercado}) == 10


def test_eventos_iniciales_ignoran_jugadores_ausentes(datos):
    from tests.conftest import crear_club

    assert datos.eventos_iniciales(crear_club()) == []


def test_estimaciones_economicas():
    assert valor_estimado(80, 20) > valor_estimado(80, 26) > valor_estimado(80, 33)
    assert salario_estimado(40) == 15_000
    assert salario_estimado(85) == 100_000
