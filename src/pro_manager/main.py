"""Punto de entrada ASGI.

Desarrollo:   ``uvicorn pro_manager.main:app --reload``
Producción:   ``python -m pro_manager`` (respeta la variable ``PORT``).
"""

from .presentacion.app import crear_app

app = crear_app()
