"""Restricción de la sección 4 y organización estricta en 4 capas (sección 9).

Se verifica leyendo los ``import`` de cada módulo (análisis estático con ``ast``):

* El dominio solo usa la biblioteca estándar: ni FastAPI, ni Pydantic, ni otras capas.
* La aplicación no conoce la presentación, la infraestructura ni el framework web.
* La infraestructura no conoce la presentación.
"""

import ast
from pathlib import Path

import pytest

import pro_manager

RAIZ = Path(pro_manager.__file__).parent
EXTERNOS_PROHIBIDOS = {"fastapi", "pydantic", "starlette", "uvicorn"}


def importaciones(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    modulos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            prefijo = "." * nodo.level
            modulos.add(prefijo + (nodo.module or ""))
    return modulos


def modulos_de(capa: str) -> list[Path]:
    return sorted((RAIZ / capa).rglob("*.py"))


@pytest.mark.parametrize("archivo", modulos_de("dominio"), ids=lambda p: p.name)
def test_el_dominio_es_independiente(archivo):
    for modulo in importaciones(archivo):
        raiz = modulo.lstrip(".").split(".")[0]
        assert raiz not in EXTERNOS_PROHIBIDOS, f"{archivo.name} importa {modulo}"
        assert not modulo.startswith(".."), f"{archivo.name} sale del dominio con {modulo}"


@pytest.mark.parametrize("archivo", modulos_de("aplicacion"), ids=lambda p: p.name)
def test_la_aplicacion_no_conoce_capas_externas(archivo):
    for modulo in importaciones(archivo):
        raiz = modulo.lstrip(".").split(".")[0]
        assert raiz not in EXTERNOS_PROHIBIDOS, f"{archivo.name} importa {modulo}"
        assert "presentacion" not in modulo and "infraestructura" not in modulo


@pytest.mark.parametrize("archivo", modulos_de("infraestructura"), ids=lambda p: p.name)
def test_la_infraestructura_no_conoce_la_presentacion(archivo):
    for modulo in importaciones(archivo):
        assert "presentacion" not in modulo
        assert modulo.lstrip(".").split(".")[0] not in EXTERNOS_PROHIBIDOS
