# 03 · Modelo de dominio y diseño orientado a objetos

Fuente: secciones 6, 7 y 8 de la especificación.

## Modelo conceptual

```mermaid
classDiagram
    direction LR
    class Club {
        presupuesto
        reputación
        límite de masa salarial
    }
    class DirectorTecnico {
        experiencia
        reputación
    }
    class Jugador {
        posición
        calidad, físico, moral
        personalidad
        estado de ánimo
    }
    class Partido {
        marcador
        minuto
        estado
    }
    class IncidenciaJuego
    class EventoVestuario {
        tipo
        severidad
    }
    class Temporada {
        jornada
        puntos
    }
    DirectorTecnico "1" --> "1" Club : dirige
    Club "1" o-- "*" Jugador : plantilla
    Partido "*" --> "2" Club : local / visitante
    Partido "1" *-- "*" IncidenciaJuego : registra
    EventoVestuario "*" --> "1..2" Jugador : involucra
    Temporada "1" --> "*" Partido : calendario
```

| Entidad | Responsabilidad |
|---|---|
| **Club** | Entidad institucional con presupuesto, reputación y plantilla. Aplica RN-02 y decide el aval a las sanciones. |
| **DirectorTecnico** | Avatar del usuario con experiencia y reputación. Administra su elogio por jornada. |
| **Jugador** | Integrante con posición, atributos, moral, personalidad, estado de ánimo e historia. |
| **Partido** | Enfrentamiento simulado: marcador, jugadores en campo y en banca, cambios e incidencias. |
| **EventoVestuario** | Acontecimiento interactivo que altera la moral (conflicto, rumor, queja, indisciplina). |
| **Temporada** | Calendario de rivales, puntos y objetivo de ascenso. |

## Patrones GRASP aplicados

| Patrón | Dónde | Justificación |
|---|---|---|
| **Information Expert** | `Jugador.calcular_rendimiento_actual()`, `Jugador.actualizar_moral()` | El jugador conoce su calidad, físico, moral, personalidad y estado de ánimo. |
| **Information Expert** | `Club.validar_fichaje()`, `Club.masa_salarial()` | El club conoce su presupuesto, su límite y los salarios de su plantilla. |
| **Creator** | `Partido.registrar_incidencia()` | El partido contiene y registra las `IncidenciaJuego`, así que las crea. |
| **Controller** | `ControladorPartido`, `ControladorVestuario` (y `ControladorPlantilla`, `ControladorClub`, `ControladorCarrera`) | Reciben las peticiones de la interfaz y las coordinan hacia el dominio. |
| **Low Coupling / High Cohesion** | `SimuladorPartido`, `GestorVestuario`, `Club` | Simulación, personalidades y finanzas están separadas; cada clase tiene un solo motivo de cambio. |
| **Pure Fabrication** | `SimuladorPartido`, `GestorVestuario`, `ProcesadorPostPartido`, `IAEntrenadorRival` | Servicios sin equivalente en el mundo real que mantienen cohesivas a las entidades. |
| **Protected Variations** | Puertos `RepositorioPartidas` y `ProveedorDatosIniciales` | Cambiar JSON por una base de datos no afecta a la aplicación ni al dominio. |
| **Polymorphism** | Jerarquía de `ErrorDominio` | La presentación traduce cada familia de errores a un código HTTP sin preguntar por tipos concretos. |

## Diagrama de clases de diseño (DCD)

Versión ampliada del DCD de la sección 8, con las firmas reales del código.

```mermaid
classDiagram
    class ControladorPartido {
        -repositorio: RepositorioPartidas
        +iniciar_partido(partida_id) Partida
        +simular(partida_id, minutos) tuple
        +pausar_partido(partida_id) Partida
        +reanudar_partido(partida_id) Partida
        +ejecutar_sustitucion(partida_id, id_sale, id_entra) bool
        +cambiar_mentalidad(partida_id, mentalidad) Partida
    }
    class ControladorVestuario {
        -repositorio: RepositorioPartidas
        +eventos(partida_id, solo_pendientes) tuple
        +revisar_crisis(partida_id, evento_id) tuple
        +resolver_evento(partida_id, evento_id, accion) ResultadoResolucion
    }
    class Partido {
        +estado: EstadoPartido
        +minuto: int
        +goles: dict
        +en_campo: dict
        +banca: dict
        +incidencias: list~IncidenciaJuego~
        +iniciar() IncidenciaJuego
        +pausar(motivo, critica) IncidenciaJuego
        +reanudar() IncidenciaJuego
        +sustituir(club_id, id_sale, id_entra) IncidenciaJuego
        +cambiar_mentalidad(club_id, mentalidad) IncidenciaJuego
        +registrar_incidencia(...) IncidenciaJuego
    }
    class Jugador {
        -_calidad: int
        -_fisico: int
        -_moral: int
        +personalidad: Personalidad
        +estado_animo: EstadoAnimo
        +actualizar_moral(impacto: int) int
        +calcular_rendimiento_actual() float
        +aplicar_evento_animo(evento) bool
        +habilitado: bool
    }
    class Club {
        -_plantilla: list~Jugador~
        +presupuesto_fichajes: int
        +limite_masa_salarial: int
        +validar_fichaje(costo, salario)
        +fichar(jugador, costo, jornada)
        +avalar_sancion(jugador, dt) bool
    }
    class SimuladorPartido {
        -rng: Random
        +fuerza(partido, club_id) tuple
        +simular(partido, minutos) list
    }
    class GestorVestuario {
        +resolver(evento, accion, club, dt) ResultadoResolucion
        +generar_evento(club, jornada, id, existentes) EventoVestuario
    }
    class EventoVestuario
    class DirectorTecnico {
        +reputacion: int
        +elogiar(jugador, jornada) bool
    }
    ControladorPartido ..> Partido : coordina
    ControladorPartido ..> SimuladorPartido : usa
    ControladorVestuario ..> GestorVestuario : usa
    GestorVestuario ..> EventoVestuario : resuelve
    GestorVestuario ..> Club : pide aval
    Partido --> "2" Club
    Partido *-- IncidenciaJuego
    Club o-- Jugador
    SimuladorPartido ..> Jugador : rendimiento
    GestorVestuario ..> Jugador : moral y estado
    GestorVestuario ..> DirectorTecnico : reputación
```

## Decisiones de visibilidad

| Tipo | Ejemplo | Por qué |
|---|---|---|
| **Por parámetro** | `GestorVestuario.resolver(evento, accion, club, dt)` recibe referencias temporales; `ControladorPartido` recibe solo identificadores (`id_sale`, `id_entra`). | Los servicios no guardan estado del juego: se pueden probar de forma aislada. |
| **Por atributo** | `Club._plantilla` conserva la lista interna de jugadores; `Club.plantilla` devuelve una copia. | El club protege su invariante: nadie agrega jugadores sin pasar por `agregar_jugador` o `fichar`. |
| **Por atributo** | `Partido.local` / `Partido.visitante` | El partido necesita a sus clubes durante toda su vida. |
| **Local** | `ControladorPartido.simular()` crea un `SimuladorPartido` con el generador aleatorio de la partida. | El simulador vive solo durante la petición. |
| **Encapsulamiento de atributos** | `Jugador.calidad`, `fisico`, `moral` son propiedades con validación. | Cualquier asignación pasa por RN-01. |

## Modelo de rendimiento del jugador

```text
base            = 0.6 · calidad + 0.4 · físico
factor_moral    = 0.7 + 0.6 · (moral / 100)            → entre 0.706 y 1.3
modificador     = Motivado 1.10 · Estable 1.00 · Molesto 0.90 · Rebelde 0.75
rendimiento     = base · factor_moral · modificador     (× 0.3 si está lesionado)
resultado final = recortado a [1, 100]                  (RN-01)
```

La personalidad amplifica los impactos **negativos** en la moral:
Temperamental ×1.5, Ambicioso ×1.2, Reservado ×1.0, Profesional ×0.75, Líder ×0.6.
