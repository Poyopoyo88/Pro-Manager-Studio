# 10 · Licencias de terceros y tratamiento de datos

Este documento es un inventario técnico de apoyo, no una opinión legal. Si el proyecto se
comercializa o publica con datos de usuarios reales, conviene una revisión profesional.

## Dependencias y sus licencias

| Componente | Uso | Licencia |
|---|---|---|
| FastAPI | Framework web | MIT |
| Starlette | Base de FastAPI | BSD-3-Clause |
| Pydantic | Validación de datos | MIT |
| Uvicorn | Servidor ASGI | BSD-3-Clause |
| pytest, pytest-cov | Pruebas (solo desarrollo) | MIT |
| HTTPX | Cliente de pruebas (solo desarrollo) | BSD-3-Clause |
| Ruff | Análisis estático (solo desarrollo) | MIT |
| Barlow y Barlow Condensed (Google Fonts) | Tipografía de la interfaz, cargada desde Google | SIL Open Font License 1.1 |

Todas son licencias permisivas compatibles con publicar el código bajo MIT. Verifica las
versiones exactas con `pip show <paquete>` antes de una entrega formal.

**Licencia del proyecto:** el repositorio aún no incluye un archivo `LICENSE`. Sin él, el
código queda con todos los derechos reservados para su autor. Si quieres que otras
personas lo reutilicen, agrega una licencia (por ejemplo MIT) desde GitHub con
*Add file → Create new file → LICENSE → Choose a license template*.

## Contenido ficticio

Clubes, jugadores, ciudades de origen de los rivales y sus historias son inventados. Los
nombres de los jugadores rivales y del mercado se generan al azar a partir de listas de
nombres y apellidos comunes. Cualquier parecido con personas reales es coincidencia.

## Datos que guarda la aplicación

| Dato | Dónde | Para qué | Quién lo ve |
|---|---|---|---|
| Nombre del DT que escribe el jugador | Archivo JSON de la partida en el servidor | Mostrarlo en la interfaz | Quien tenga acceso al servidor o a la API |
| Estado de la partida | Mismo archivo | Continuar la carrera | Igual |
| Identificador de la partida actual | `localStorage` del navegador | Reabrir la última partida | Solo ese navegador |

No hay cuentas, contraseñas, pagos, cookies de seguimiento ni analítica. La interfaz
carga las fuentes desde Google Fonts, lo que implica una petición del navegador a los
servidores de Google; si eso no es deseable, descarga las fuentes y sírvelas desde
`presentacion/web/static/`.

**Recomendación:** si despliegas la aplicación para otras personas, avisa que el nombre
del DT queda guardado en el servidor y que no deben escribir datos personales sensibles,
y agrega autenticación para que nadie pueda ver o borrar partidas ajenas.
