# 06 · API REST

Base: `/api/v1`. La documentación interactiva generada por FastAPI está en `/docs`
(Swagger UI) y `/redoc` mientras el servidor corre. Todas las rutas de juego cuelgan de
`/api/v1/partidas/{partida_id}`.

## Endpoints

### Sistema y partidas

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/salud` | Estado del servicio y versión. |
| POST | `/partidas` | Crea una carrera. Cuerpo: `{"nombre_dt": "...", "semilla": 123}` (semilla opcional). |
| GET | `/partidas` | Lista las partidas guardadas. |
| GET | `/partidas/{id}` | Estado general: club, DT, temporada, crisis pendientes, novedades. |
| DELETE | `/partidas/{id}` | Borra la partida. |

### Plantilla y alineación (HU-01)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/plantilla` | Jugadores con atributos, rendimiento actual, estado y disponibilidad. |
| GET | `/plantilla/{jugador_id}` | Un jugador, con su historia personal. |
| POST | `/plantilla/{jugador_id}/elogio` | Elogio público (una vez por jornada). |
| GET | `/formaciones` | Formaciones disponibles. |
| GET | `/alineacion/sugerida?formacion=4-3-3&mentalidad=OFENSIVA` | Propuesta del cuerpo técnico. |
| GET | `/alineacion` | Alineación guardada (o `null`). |
| PUT | `/alineacion` | Valida y guarda `{formacion, titulares[11], suplentes[≤9], mentalidad}`. |

### Vestuario (HU-04)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/vestuario/eventos?pendientes=true` | Crisis del vestuario (todas o solo pendientes). |
| GET | `/vestuario/eventos/{evento_id}` | Detalle de una crisis. |
| POST | `/vestuario/eventos/{evento_id}/resolucion` | `{"accion": "SANCIONAR" \| "DIALOGAR"}`. |

### Partido (HU-05 y CU-01)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/partido` | Inicia el partido de la jornada. |
| GET | `/partido` | Marcador, minuto, jugadores en campo y banca, crónica. |
| POST | `/partido/simulacion` | `{"minutos": 1..90}`. Se detiene antes si hay descanso o incidencia crítica. |
| POST | `/partido/pausa` | Pausa solicitada por el DT. |
| POST | `/partido/reanudacion` | Reanuda tras los ajustes. |
| POST | `/partido/sustituciones` | `{"id_sale": "...", "id_entra": "..."}`. |
| PUT | `/partido/mentalidad` | `{"mentalidad": "DEFENSIVA" \| "EQUILIBRADA" \| "OFENSIVA"}`. |

### Club (HU-02, HU-03, HU-06)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/finanzas` | Presupuesto, masa salarial, margen y movimientos. |
| GET | `/mercado` | Jugadores transferibles (sin calidad: hay que ojearlos). |
| GET | `/mercado/informes?posicion=DEL` | Informes de ojeadores con rango de calidad. |
| POST | `/mercado/{jugador_id}/ofertas` | `{"monto_transferencia": 900000, "salario": 60000}`. |

## Formato de errores

Todos los errores de negocio responden con el mismo formato:

```json
{
  "codigo": "sustituciones_agotadas",
  "mensaje": "Ya se realizaron los 5 cambios permitidos.",
  "errores": null
}
```

| HTTP | Familia | Códigos |
|---|---|---|
| 404 | Recurso no encontrado | `partida_no_encontrada`, `jugador_no_encontrado`, `evento_no_encontrado`, `club_no_encontrado` |
| 409 | Estado inválido para la acción | `eventos_pendientes`, `partido_no_activo`, `sin_partido`, `evento_ya_resuelto`, `temporada_finalizada`, `estado_invalido` |
| 422 | Regla de negocio o datos inválidos | `alineacion_invalida` (con lista `errores`), `jugador_inhabilitado`, `sustituciones_agotadas`, `sustitucion_invalida`, `presupuesto_excedido`, `masa_salarial_excedida`, `atributo_fuera_de_rango`, `dato_invalido`, `solicitud_invalida` |

## Ejemplo con `curl`

```bash
API=http://127.0.0.1:8000/api/v1

# 1. Crear la partida
ID=$(curl -s -X POST $API/partidas -H "Content-Type: application/json" \
  -d '{"nombre_dt": "Profe Ramírez", "semilla": 42}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 2. Resolver la crisis inicial dialogando
curl -s -X POST $API/partidas/$ID/vestuario/eventos/EV-001/resolucion \
  -H "Content-Type: application/json" -d '{"accion": "DIALOGAR"}'

# 3. Guardar la alineación sugerida
curl -s "$API/partidas/$ID/alineacion/sugerida?formacion=4-3-3" \
  | curl -s -X PUT $API/partidas/$ID/alineacion -H "Content-Type: application/json" -d @-

# 4. Iniciar y simular
curl -s -X POST $API/partidas/$ID/partido
curl -s -X POST $API/partidas/$ID/partido/simulacion \
  -H "Content-Type: application/json" -d '{"minutos": 45}'
```
