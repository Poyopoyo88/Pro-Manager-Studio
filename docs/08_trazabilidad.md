# 08 · Trazabilidad

Cadena de la sección 11 de la especificación:

```text
Problema de gestión → HU-04 / HU-05 → CU-01 → DCD y GRASP → Diseño dinámico → TDD y pruebas
```

## Matriz de trazabilidad

| Historia | Caso de uso / regla | Clases de dominio | Controlador | Endpoints | Pruebas |
|---|---|---|---|---|---|
| **HU-01** Alineación | RN-06 | `Alineacion`, `sugerir_alineacion`, `FORMACIONES` | `ControladorPlantilla` | `GET/PUT /alineacion`, `GET /alineacion/sugerida`, `GET /plantilla` | `test_tactica.py`, `test_api.py::test_alineacion_valida_e_invalida` |
| **HU-02** Ojeadores | — | `Ojeador`, `InformeOjeo`, `JugadorEnMercado` | `ControladorClub.ojear` | `GET /mercado`, `GET /mercado/informes` | `test_post_partido_temporada_mercado.py` (ojeador), `test_controladores.py::test_ojeo_y_fichaje` |
| **HU-03** Fichajes | RN-02, RN-12 | `NegociadorFichajes`, `Club.fichar` | `ControladorClub.ofertar` | `POST /mercado/{id}/ofertas` | `test_club_y_dt.py`, `test_api.py::test_finanzas_mercado_ojeo_y_oferta` |
| **HU-04** Vestuario | RN-03, RN-07, RN-08 | `GestorVestuario`, `EventoVestuario`, `Jugador`, `Club.avalar_sancion` | `ControladorVestuario` | `GET /vestuario/eventos`, `POST .../resolucion` | `test_vestuario.py`, `test_maquina_estados.py`, `test_api.py::test_escenario_critico_sancion` |
| **HU-05** Tiempo real | **CU-01**, RN-04, RN-05 | `Partido`, `SimuladorPartido`, `IAEntrenadorRival`, `IncidenciaJuego` | `ControladorPartido` | `/partido`, `/partido/simulacion`, `/pausa`, `/reanudacion`, `/sustituciones`, `/mentalidad` | `test_partido.py`, `test_simulador.py`, `test_api.py::test_cu01_*` |
| **HU-06** Finanzas | RN-02 | `Club`, `MovimientoFinanciero`, `ProcesadorPostPartido` | `ControladorClub.finanzas` | `GET /finanzas` | `test_club_y_dt.py`, `test_post_partido_temporada_mercado.py` |
| Transversal | RN-01 | `atributos.py`, `Jugador`, `DirectorTecnico` | — | todas las que muestran atributos | `test_atributos_y_jugador.py` |
| Transversal | Restricción sección 4 | paquete `dominio` | — | — | `test_arquitectura.py` |
| Transversal | Requisito de calidad | `SimuladorPartido` | — | `/partido/simulacion` | `test_simulador.py::test_requisito_de_calidad_*` |

## De la especificación al código

| Elemento de la especificación | Implementación |
|---|---|
| `ControladorPartido.pausarPartido()` | `ControladorPartido.pausar_partido()` |
| `ControladorPartido.ejecutarSustitucion(idSale, idEntra): boolean` | `ControladorPartido.ejecutar_sustitucion(partida_id, id_sale, id_entra) -> bool` |
| `Jugador.actualizarMoral(impacto)` | `Jugador.actualizar_moral(impacto) -> int` (devuelve el cambio real) |
| `Jugador.calcularRendimientoActual(): float` | `Jugador.calcular_rendimiento_actual() -> float` |
| `Partido` crea `IncidenciaJuego` | `Partido.registrar_incidencia()` |
| `GestorEventos` (secuencia) | `GestorVestuario` (resolución y generación de eventos) |
| `SimuladorPartido`, `GestorVestuario` | Mismos nombres, en `dominio/` |
| Club conserva la lista de jugadores | `Club._plantilla` + propiedad `plantilla` que devuelve copia |
| Máquina de estados (sección 10) | `dominio/estado_animo.py` |
| Estructura `src/Presentation`, `src/Application`, … | `src/pro_manager/presentacion`, `aplicacion`, `dominio`, `infraestructura` (PEP 8) |
| `tests/UnitTests`, `tests/IntegrationTests` | `tests/unitarias`, `tests/integracion` |

Los nombres pasan de *camelCase* a *snake_case* por la convención de Python (PEP 8).
