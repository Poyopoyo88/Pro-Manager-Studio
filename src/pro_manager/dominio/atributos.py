"""Regla de negocio RN-01: los atributos de un jugador viven en el rango cerrado [1, 100].

Se aplican dos políticas complementarias:

* **Validación** (``validar_atributo``): un valor de entrada fuera de rango se rechaza
  con ``AtributoFueraDeRangoError``. Se usa al crear o asignar atributos.
* **Saturación** (``acotar``): un valor *calculado* por la simulación (por ejemplo,
  moral + impacto) se recorta al límite más cercano. Así el sistema nunca produce
  un estado inválido aunque el cálculo intermedio se salga del rango.
"""

from __future__ import annotations

from .errores import AtributoFueraDeRangoError

ATRIBUTO_MIN = 1
ATRIBUTO_MAX = 100


def validar_atributo(nombre: str, valor: int) -> int:
    """Devuelve ``valor`` si es un entero dentro de [1, 100]; si no, lanza un error."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise AtributoFueraDeRangoError(
            f"El atributo '{nombre}' debe ser un número entero; se recibió {valor!r}."
        )
    if not ATRIBUTO_MIN <= valor <= ATRIBUTO_MAX:
        raise AtributoFueraDeRangoError(
            f"El atributo '{nombre}' debe estar entre {ATRIBUTO_MIN} y {ATRIBUTO_MAX}; "
            f"se recibió {valor}."
        )
    return valor


def acotar(valor: float) -> int:
    """Redondea y satura un valor calculado al rango [1, 100]."""
    return int(max(ATRIBUTO_MIN, min(ATRIBUTO_MAX, round(valor))))
