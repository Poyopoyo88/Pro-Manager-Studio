# 07 · Pruebas y calidad

Fuente: sección 12 de la especificación.

## Cómo ejecutar

```bash
pip install -e ".[dev]"
pytest                    # todas las pruebas
pytest --cov              # con cobertura (falla si baja de 80 %)
pytest -m rendimiento     # solo el requisito de calidad de rendimiento
pytest tests/unitarias    # solo pruebas unitarias
ruff check . && ruff format --check .
```

## Resultado actual

| Métrica | Valor | Umbral del Quality Gate |
|---|---|---|
| Pruebas | 271 aprobadas, 0 fallidas | 0 fallidas |
| Cobertura de líneas y ramas | 98.6 % | > 80 % |
| Análisis estático (ruff) | sin observaciones | sin observaciones |

## Inventario

| Archivo | Pruebas | Qué cubre |
|---|---|---|
| `unitarias/test_atributos_y_jugador.py` | 62 | RN-01, moral, personalidad, rendimiento, disponibilidad. |
| `unitarias/test_maquina_estados.py` | 42 | Todas las combinaciones estado × evento; RN-03. |
| `unitarias/test_arquitectura.py` | 26 | Independencia del dominio y dirección de las dependencias. |
| `unitarias/test_club_y_dt.py` | 21 | RN-02, plantilla, aval de la directiva, elogio. |
| `unitarias/test_tactica.py` | 20 | HU-01: reglas de alineación y sugerencias. |
| `unitarias/test_post_partido_temporada_mercado.py` | 20 | Consecuencias del partido, temporada, ojeadores, negociación. |
| `unitarias/test_simulador.py` | 16 | Motor de partidos, IA rival, pausas, determinismo, rendimiento. |
| `unitarias/test_partido.py` | 15 | Ciclo de vida, CU-01 3a y 5a, tarjetas, lesiones. |
| `unitarias/test_vestuario.py` | 11 | HU-04: sanción con y sin aval, diálogo, narrativa dinámica. |
| `integracion/test_persistencia.py` | 16 | Serialización, repositorios JSON y en memoria, datos iniciales, configuración. |
| `integracion/test_api.py` | 14 | API completa, CU-01 por HTTP, formato de errores. |
| `integracion/test_controladores.py` | 8 | Temporada completa, reproducibilidad, precondiciones, fichajes. |

## TDD: Red → Green → Refactor

Las reglas clave se escribieron guiadas por pruebas. Ejemplo con RN-02:

1. **Red:** `test_un_peso_por_encima_del_presupuesto_se_rechaza` falla porque
   `Club.fichar` no valida nada.
2. **Green:** se agrega `validar_fichaje` con la comparación contra el presupuesto.
3. **Refactor:** la misma validación se reutiliza en `puede_fichar` y en la negociación
   (`ControladorClub.ofertar`), que valida RN-02 **antes** de negociar.

Para cambios nuevos, la plantilla de *pull request* pide confirmar que se siguió el ciclo.

## Particiones de equivalencia y valores límite

### RN-01 · atributos en `[1, 100]`

| Partición | Rango | Representantes probados | Resultado esperado |
|---|---|---|---|
| P1 inválida | valor < 1 | −1, **0** | `AtributoFueraDeRangoError` |
| P2 válida | 1 ≤ valor ≤ 100 | **1**, **2**, 50, **99**, **100** | Se acepta |
| P3 inválida | valor > 100 | **101**, 1000 | `AtributoFueraDeRangoError` |
| P4 inválida | no entero | 50.5, "50", `True`, `None` | `AtributoFueraDeRangoError` |

En negritas, los valores límite. Las mismas particiones se prueban para `calidad`,
`fisico` y `moral` al crear un jugador, y para la reputación del DT y del club. Los
valores calculados (moral tras un impacto, rendimiento) se prueban en sus extremos para
confirmar que se saturan en 1 y 100.

### RN-02 · presupuesto y masa salarial

| Caso | Valor | Resultado |
|---|---|---|
| Costo = presupuesto disponible | límite exacto | Se permite (presupuesto queda en 0). |
| Costo = presupuesto + 1 | límite + 1 | `PresupuestoExcedidoError`. |
| Salario = margen salarial | límite exacto | Se permite. |
| Salario = margen + 1 | límite + 1 | `MasaSalarialExcedidaError`. |
| Montos negativos | < 0 | `DatoInvalidoError`. |

### Aval de la directiva (RN-08)

| Jugador | Reputación del DT | Aval |
|---|---|---|
| Normal | 30 (límite) | Sí |
| Normal | 29 | No |
| Figura (calidad ≥ 85) | 50 (límite) | Sí |
| Figura | 49 | No |
| Capitán | 49 | No |

### CU-01 · sustituciones

| Caso | Resultado |
|---|---|
| Cambios realizados: 0 a 4 | Se permite. |
| Cambios realizados: 5 (límite) | `SustitucionesAgotadasError` (5a). |
| Suplente con sanción interna | `JugadorInhabilitadoError` (3a). |
| Jugador que ya salió intenta volver | `SustitucionInvalidaError`. |

## Requisito de calidad: rendimiento

`test_requisito_de_calidad_un_partido_completo_en_menos_de_150_ms` simula 30 partidos
completos y exige que la mediana sea menor a 150 ms. Sin instrumentación, un partido de 90
minutos tarda unos 7 ms; el margen absorbe la sobrecarga de medir la cobertura en CI. La
interfaz pide bloques de 3 minutos, que tardan una fracción de milisegundo, así que la
simulación nunca bloquea la interfaz.

## Quality Gate automatizado

El flujo `.github/workflows/ci.yml` corre en cada *push* y *pull request* a `main` y
`develop`, con Python 3.11, 3.12 y 3.13:

1. `ruff check .` y `ruff format --check .`
2. `pytest --cov` (0 pruebas fallidas y cobertura > 80 %, por `fail_under = 80`).

La **revisión por pares obligatoria** se activa en GitHub (ver `CONTRIBUTING.md`):
protección de las ramas `main` y `develop` con «Require a pull request before merging»,
al menos una aprobación, y el check `CI` como requisito.
