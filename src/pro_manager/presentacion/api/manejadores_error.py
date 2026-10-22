"""Traducción de errores del dominio a respuestas HTTP con mensaje en español."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ...dominio.errores import (
    AlineacionInvalidaError,
    ErrorDominio,
    EstadoInvalidoError,
    RecursoNoEncontradoError,
)


def estado_http(error: ErrorDominio) -> int:
    if isinstance(error, RecursoNoEncontradoError):
        return 404
    if isinstance(error, EstadoInvalidoError):
        return 409
    return 422


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDominio)
    async def _error_dominio(_: Request, error: ErrorDominio) -> JSONResponse:
        cuerpo: dict = {"codigo": error.codigo, "mensaje": error.mensaje}
        if isinstance(error, AlineacionInvalidaError):
            cuerpo["errores"] = error.errores
        return JSONResponse(status_code=estado_http(error), content=cuerpo)

    @app.exception_handler(RequestValidationError)
    async def _error_validacion(_: Request, error: RequestValidationError) -> JSONResponse:
        errores = [
            f"{'.'.join(str(p) for p in detalle['loc'][1:]) or 'cuerpo'}: {detalle['msg']}"
            for detalle in error.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "codigo": "solicitud_invalida",
                "mensaje": "La solicitud contiene datos inválidos.",
                "errores": errores,
            },
        )
