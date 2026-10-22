"""Jerarquía de errores del dominio.

Cada error representa la violación de una regla de negocio o de un estado válido.
La capa de presentación traduce estas excepciones a códigos HTTP
(ver ``presentacion/api/manejadores_error.py``):

* ``RecursoNoEncontradoError`` → 404
* ``ReglaNegocioError``        → 422
* ``EstadoInvalidoError``      → 409
"""

from __future__ import annotations


class ErrorDominio(Exception):
    """Base de todos los errores del dominio."""

    codigo = "error_dominio"

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


# --- Recursos inexistentes -------------------------------------------------


class RecursoNoEncontradoError(ErrorDominio):
    codigo = "no_encontrado"


class JugadorNoEncontradoError(RecursoNoEncontradoError):
    codigo = "jugador_no_encontrado"


class EventoNoEncontradoError(RecursoNoEncontradoError):
    codigo = "evento_no_encontrado"


class ClubNoEncontradoError(RecursoNoEncontradoError):
    codigo = "club_no_encontrado"


# --- Reglas de negocio -----------------------------------------------------


class ReglaNegocioError(ErrorDominio):
    codigo = "regla_de_negocio"


class DatoInvalidoError(ReglaNegocioError):
    codigo = "dato_invalido"


class AtributoFueraDeRangoError(ReglaNegocioError):
    """RN-01: un atributo de jugador fuera del rango cerrado [1, 100]."""

    codigo = "atributo_fuera_de_rango"


class PresupuestoExcedidoError(ReglaNegocioError):
    """RN-02: la operación excede el presupuesto de fichajes."""

    codigo = "presupuesto_excedido"


class MasaSalarialExcedidaError(ReglaNegocioError):
    """RN-02: la operación excede el límite de masa salarial."""

    codigo = "masa_salarial_excedida"


class AlineacionInvalidaError(ReglaNegocioError):
    codigo = "alineacion_invalida"

    def __init__(self, errores: list[str]) -> None:
        super().__init__("La alineación no es válida: " + " ".join(errores))
        self.errores = list(errores)


class JugadorInhabilitadoError(ReglaNegocioError):
    """CU-01, excepción 3a: el suplente elegido no puede ingresar."""

    codigo = "jugador_inhabilitado"


class SustitucionesAgotadasError(ReglaNegocioError):
    """CU-01, excepción 5a: se alcanzó el límite de cambios."""

    codigo = "sustituciones_agotadas"


class SustitucionInvalidaError(ReglaNegocioError):
    codigo = "sustitucion_invalida"


# --- Estados inválidos -----------------------------------------------------


class EstadoInvalidoError(ErrorDominio):
    codigo = "estado_invalido"


class PartidoNoActivoError(EstadoInvalidoError):
    codigo = "partido_no_activo"


class EventoYaResueltoError(EstadoInvalidoError):
    codigo = "evento_ya_resuelto"


class EventosPendientesError(EstadoInvalidoError):
    codigo = "eventos_pendientes"


class TemporadaFinalizadaError(EstadoInvalidoError):
    codigo = "temporada_finalizada"
