"""Máquina de estados del jugador (sección 10 de la especificación).

Transiciones de la especificación::

    Estable ──Elogio / Victoria──▶ Motivado
    Estable ──Falta de minutos───▶ Molesto
    Molesto ──Sanción severa─────▶ Rebelde
    Rebelde ──Mediación completada▶ Estable

La regla de negocio RN-03 («un jugador Rebelde requiere mediación **o sanción**
antes de volver a Estable») añade::

    Rebelde ──Sanción cumplida───▶ Estable

Extensiones de diseño (decisión DEC-03, ``docs/05_diseno_dinamico.md``) para que
ningún estado quede como callejón sin salida durante una temporada::

    Motivado ──Derrota / Falta de minutos──▶ Estable
    Molesto  ──Mediación completada───────▶ Estable

Cualquier otro par (estado, evento) deja el estado sin cambios. En particular,
**ningún evento distinto de mediación o sanción cumplida saca a un jugador de
Rebelde**, que es exactamente lo que exige RN-03.
"""

from __future__ import annotations

from .enums import EstadoAnimo as E
from .enums import EventoAnimo as Ev

TRANSICIONES_ESPECIFICACION: dict[tuple[E, Ev], E] = {
    (E.ESTABLE, Ev.ELOGIO): E.MOTIVADO,
    (E.ESTABLE, Ev.VICTORIA): E.MOTIVADO,
    (E.ESTABLE, Ev.FALTA_DE_MINUTOS): E.MOLESTO,
    (E.MOLESTO, Ev.SANCION_SEVERA): E.REBELDE,
    (E.REBELDE, Ev.MEDIACION_COMPLETADA): E.ESTABLE,
}

TRANSICIONES_REGLA_NEGOCIO: dict[tuple[E, Ev], E] = {
    (E.REBELDE, Ev.SANCION_CUMPLIDA): E.ESTABLE,
}

TRANSICIONES_EXTENSION: dict[tuple[E, Ev], E] = {
    (E.MOTIVADO, Ev.DERROTA): E.ESTABLE,
    (E.MOTIVADO, Ev.FALTA_DE_MINUTOS): E.ESTABLE,
    (E.MOLESTO, Ev.MEDIACION_COMPLETADA): E.ESTABLE,
}

TRANSICIONES: dict[tuple[E, Ev], E] = {
    **TRANSICIONES_ESPECIFICACION,
    **TRANSICIONES_REGLA_NEGOCIO,
    **TRANSICIONES_EXTENSION,
}


def siguiente_estado(actual: E, evento: Ev) -> E:
    """Devuelve el estado resultante; si la transición no existe, el estado no cambia."""
    return TRANSICIONES.get((actual, evento), actual)
