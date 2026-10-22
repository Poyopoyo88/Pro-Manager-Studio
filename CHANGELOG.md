# Historial de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
versionado semántico.

## [0.1.0] - 2026-10-22

Primera versión construible del módulo *Núcleo de Gestión, Motor de Partidos y Sistema de
Vestuario*.

### Agregado

- Capa de dominio independiente del framework: jugadores con personalidad, moral, estado
  de ánimo e historia; club con reglas financieras; partido con incidencias; motor de
  simulación minuto a minuto; IA del entrenador rival; gestor de vestuario con narrativa
  dinámica; temporada de 5 jornadas con objetivo de ascenso; ojeadores y negociación.
- Reglas de negocio RN-01 a RN-03 de la especificación y RN-04 a RN-12 precisadas durante
  la construcción.
- Caso de uso CU-01 completo, con las excepciones 3a y 5a.
- API REST con FastAPI (`/api/v1`) y documentación OpenAPI en `/docs`.
- Interfaz web del Director Técnico: vestuario, alineación con cancha, partido en vivo,
  plantilla, mercado y finanzas.
- Persistencia de partidas en JSON (o en memoria) con formato versionado.
- 271 pruebas automatizadas (98.6 % de cobertura) y Quality Gate en GitHub Actions.
- Documentación técnica en español (`docs/`), guía de contribución y despliegue en Render.

### Pendiente

- HU-02: cantera y promoción de juveniles.
- HU-03: venta de jugadores.
- Ruedas de prensa y tabla de liga completa.
