"""Fábrica de la aplicación FastAPI (Capa de Presentación)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..aplicacion.puertos import ProveedorDatosIniciales, RepositorioPartidas
from .api.manejadores_error import registrar_manejadores
from .api.rutas_juego import router as router_juego
from .api.rutas_partidas import router as router_partidas

DIRECTORIO_WEB = Path(__file__).parent / "web"

DESCRIPCION = """
API del **Simulador de Dirección Técnica de Fútbol**.

Flujo típico de una jornada:

1. `POST /api/v1/partidas` — crea la carrera.
2. `GET  /vestuario/eventos?pendientes=true` y `POST .../resolucion` — atiende la crisis (HU-04).
3. `GET  /alineacion/sugerida` y `PUT /alineacion` — arma el once (HU-01).
4. `POST /partido` y `POST /partido/simulacion` — juega en tiempo real (HU-05).
5. Ante una pausa: `POST /partido/sustituciones`, `PUT /partido/mentalidad`,
   `POST /partido/reanudacion` (CU-01).

Los errores de negocio responden con `{"codigo": ..., "mensaje": ...}`.
"""


def crear_app(
    repositorio: RepositorioPartidas | None = None,
    datos: ProveedorDatosIniciales | None = None,
) -> FastAPI:
    # Importación tardía: la infraestructura solo se conecta al armar la aplicación.
    from ..infraestructura import ProveedorDatosJSON, crear_repositorio_desde_entorno

    app = FastAPI(
        title="Pro Manager Studio",
        version=__version__,
        description=DESCRIPCION,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.repositorio = repositorio or crear_repositorio_desde_entorno()
    app.state.datos = datos or ProveedorDatosJSON()

    registrar_manejadores(app)
    app.include_router(router_partidas, prefix="/api/v1")
    app.include_router(router_juego, prefix="/api/v1")

    @app.get("/api/v1/salud", tags=["Sistema"])
    def salud() -> dict[str, str]:
        return {"estado": "ok", "version": __version__}

    app.mount("/static", StaticFiles(directory=DIRECTORIO_WEB / "static"), name="static")

    @app.get("/", include_in_schema=False)
    def inicio() -> FileResponse:
        return FileResponse(DIRECTORIO_WEB / "index.html")

    return app
