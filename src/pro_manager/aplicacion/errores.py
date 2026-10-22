"""Errores propios de la capa de aplicación."""

from ..dominio.errores import EstadoInvalidoError, RecursoNoEncontradoError


class PartidaNoEncontradaError(RecursoNoEncontradoError):
    codigo = "partida_no_encontrada"


class SinPartidoError(EstadoInvalidoError):
    codigo = "sin_partido"
