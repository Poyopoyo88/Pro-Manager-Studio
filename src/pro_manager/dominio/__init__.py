"""Capa de Dominio.

Contiene el motor de partidos, las reglas financieras y los modelos de
comportamiento de los jugadores. Restricción de la especificación (sección 4):
esta capa es independiente de la interfaz y del framework web; solo usa la
biblioteca estándar de Python. Una prueba automatizada lo verifica
(``tests/unitarias/test_arquitectura.py``).
"""

from .club import Club, MovimientoFinanciero
from .director_tecnico import DirectorTecnico
from .enums import (
    AccionDT,
    EstadoAnimo,
    EstadoPartido,
    EventoAnimo,
    Mentalidad,
    Personalidad,
    Posicion,
    Resultado,
    TipoEventoVestuario,
    TipoIncidencia,
)
from .jugador import Jugador
from .mercado import InformeOjeo, JugadorEnMercado, NegociadorFichajes, Ojeador
from .partido import IncidenciaJuego, Partido
from .post_partido import ProcesadorPostPartido, ResumenPostPartido
from .simulador import SimuladorPartido
from .tactica import FORMACIONES, Alineacion, sugerir_alineacion
from .temporada import ResultadoJornada, Temporada
from .vestuario import EventoVestuario, GestorVestuario, ResultadoResolucion

__all__ = [
    "FORMACIONES",
    "AccionDT",
    "Alineacion",
    "Club",
    "DirectorTecnico",
    "EstadoAnimo",
    "EstadoPartido",
    "EventoAnimo",
    "EventoVestuario",
    "GestorVestuario",
    "IncidenciaJuego",
    "InformeOjeo",
    "Jugador",
    "JugadorEnMercado",
    "Mentalidad",
    "MovimientoFinanciero",
    "NegociadorFichajes",
    "Ojeador",
    "Partido",
    "Personalidad",
    "Posicion",
    "ProcesadorPostPartido",
    "Resultado",
    "ResultadoJornada",
    "ResultadoResolucion",
    "ResumenPostPartido",
    "SimuladorPartido",
    "Temporada",
    "TipoEventoVestuario",
    "TipoIncidencia",
    "sugerir_alineacion",
]
