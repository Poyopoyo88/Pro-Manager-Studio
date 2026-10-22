"""Pro Manager Studio — Simulador de Dirección Técnica de Fútbol.

El paquete está organizado en cuatro capas (ver ``docs/04_arquitectura.md``):

* ``dominio``: motor de partidos, reglas financieras y comportamiento de jugadores.
  No depende de FastAPI, Pydantic ni de ninguna otra capa.
* ``aplicacion``: controladores que coordinan los casos de uso sin lógica de negocio.
* ``infraestructura``: persistencia de partidas guardadas y carga de datos iniciales.
* ``presentacion``: API REST (FastAPI) e interfaz web del Director Técnico.
"""

__version__ = "0.1.0"
