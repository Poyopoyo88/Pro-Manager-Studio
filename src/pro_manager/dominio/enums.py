"""Enumeraciones del dominio."""

from __future__ import annotations

from enum import StrEnum


class Posicion(StrEnum):
    PORTERO = "POR"
    DEFENSA = "DEF"
    MEDIOCAMPISTA = "MED"
    DELANTERO = "DEL"


class Personalidad(StrEnum):
    """Rasgo que modula cómo el jugador encaja los golpes a su moral."""

    LIDER = "LIDER"
    PROFESIONAL = "PROFESIONAL"
    TEMPERAMENTAL = "TEMPERAMENTAL"
    AMBICIOSO = "AMBICIOSO"
    RESERVADO = "RESERVADO"


class EstadoAnimo(StrEnum):
    """Estados de la máquina de estados del jugador (sección 10 de la especificación)."""

    ESTABLE = "ESTABLE"
    MOTIVADO = "MOTIVADO"
    MOLESTO = "MOLESTO"
    REBELDE = "REBELDE"


class EventoAnimo(StrEnum):
    """Disparadores de transición de la máquina de estados del jugador."""

    ELOGIO = "ELOGIO"
    VICTORIA = "VICTORIA"
    DERROTA = "DERROTA"
    FALTA_DE_MINUTOS = "FALTA_DE_MINUTOS"
    SANCION_SEVERA = "SANCION_SEVERA"
    SANCION_CUMPLIDA = "SANCION_CUMPLIDA"
    MEDIACION_COMPLETADA = "MEDIACION_COMPLETADA"


class Mentalidad(StrEnum):
    DEFENSIVA = "DEFENSIVA"
    EQUILIBRADA = "EQUILIBRADA"
    OFENSIVA = "OFENSIVA"


class EstadoPartido(StrEnum):
    PROGRAMADO = "PROGRAMADO"
    EN_JUEGO = "EN_JUEGO"
    PAUSADO = "PAUSADO"
    FINALIZADO = "FINALIZADO"


class TipoIncidencia(StrEnum):
    INICIO = "INICIO"
    GOL = "GOL"
    LESION = "LESION"
    TARJETA_AMARILLA = "TARJETA_AMARILLA"
    EXPULSION = "EXPULSION"
    SUSTITUCION = "SUSTITUCION"
    CAMBIO_MENTALIDAD = "CAMBIO_MENTALIDAD"
    PAUSA = "PAUSA"
    REANUDACION = "REANUDACION"
    FINAL = "FINAL"


class Resultado(StrEnum):
    VICTORIA = "VICTORIA"
    EMPATE = "EMPATE"
    DERROTA = "DERROTA"


class TipoEventoVestuario(StrEnum):
    CONFLICTO_ENTRE_JUGADORES = "CONFLICTO_ENTRE_JUGADORES"
    RUMOR_TRANSFERENCIA = "RUMOR_TRANSFERENCIA"
    QUEJA_POR_MINUTOS = "QUEJA_POR_MINUTOS"
    INDISCIPLINA = "INDISCIPLINA"


class AccionDT(StrEnum):
    """Decisión del DT ante una crisis de vestuario (HU-04)."""

    SANCIONAR = "SANCIONAR"
    DIALOGAR = "DIALOGAR"
