# 01 · Visión y requisitos

Fuente: secciones 0 a 4 de la [especificación original](especificacion_original.pdf).
Este documento conserva esa información y la amplía con los criterios de aceptación y las
reglas que se precisaron durante la construcción.

## Propósito

Establecer la especificación, el diseño y la estrategia de calidad de **Pro Manager
Studio**, y servir como guía técnica durante todo el ciclo de vida, con trazabilidad desde
el problema hasta el código y las pruebas.

## Contexto

Pro Manager Studio es un simulador de gestión técnica y administrativa de fútbol. El
usuario asume el rol completo de Director Técnico (DT): combina la táctica en tiempo real
con la gestión humana, la economía del club y la construcción de un legado deportivo.

## Visión del producto

- **PARA** aficionados al fútbol y a los videojuegos de gestión deportiva,
- **QUIENES** buscan una experiencia de dirección técnica que vaya más allá de la táctica
  (gestión humana, financiera y de legado),
- **PRO MANAGER STUDIO ES UN** videojuego de simulación y gestión deportiva
- **QUE** permite asumir el rol integral de un DT: alineaciones, fichajes, finanzas,
  cantera, decisiones tácticas e interacciones disciplinarias,
- **A DIFERENCIA DE** simuladores arcade o de gestión puramente estadística,
- **NUESTRO PRODUCTO** integra narrativa dinámica con historias propias para cada jugador,
  progresión orgánica y eventos imprevistos.

## Proto-personas

| Persona | Perfil | Qué le ofrece la versión actual |
|---|---|---|
| **Carlos «El Táctico» Mendoza** (24) | Análisis de datos, esquemas tácticos, cantera. | Rendimiento numérico por jugador, cinco formaciones, mentalidad en vivo, fatiga visible, informes de ojeadores con rangos. |
| **Sofía «La Directora» Ramos** (19) | Narrativa del vestuario, conflictos de ego, historias personales. | Crisis con protagonistas y consecuencias, estados de ánimo, historia personal de cada jugador que se escribe con tus decisiones. |

## Escenario crítico de uso

> Faltan 24 horas para un partido decisivo. El delantero estrella discute en el
> entrenamiento con el capitán por rumores de transferencia. El DT debe sancionar al
> goleador enviándolo a la banca o mediar arriesgándose a perder autoridad. Durante el
> partido, el portero titular se lesiona en el minuto 60 y obliga a hacer ajustes bajo
> presión.

**Cómo se reproduce en la aplicación:** toda partida nueva arranca con el evento
`EV-001` («Pelea en el entrenamiento: Valenzuela contra el capitán»), definido en
`infraestructura/datos/club_inicial.json`. Las lesiones en partido son aleatorias; cuando
le ocurren a un jugador del usuario, la simulación se detiene sola (incidencia crítica).

## Historias de usuario y criterios de aceptación

### HU-01 · Configuración táctica y alineación pre-partido — Prioridad alta

**Como** DT **quiero** elegir formación, mentalidad, titulares y suplentes **para**
preparar el partido según el rival y el estado del plantel.

- **Dado** que elijo 11 titulares con exactamente un portero y hasta 9 suplentes,
  **cuando** guardo la alineación, **entonces** se acepta y queda lista para el partido.
- **Dado** un titular lesionado, suspendido o sancionado, **cuando** guardo,
  **entonces** el sistema rechaza la alineación y explica el motivo.
- **Dado** un jugador sancionado internamente, **cuando** lo pongo en la banca,
  **entonces** se acepta (puede ir a la banca, pero no jugar).
- **Dado** que los jugadores no coinciden con la formación, **cuando** guardo,
  **entonces** se acepta con advertencias de «fuera de posición».
- **Cuando** pido una sugerencia, **entonces** el cuerpo técnico propone a los mejores
  disponibles por rendimiento actual, con un portero suplente.

### HU-02 · Búsqueda y reclutamiento de talento — Prioridad media

**Como** DT **quiero** enviar ojeadores **para** conocer la calidad aproximada de los
jugadores del mercado antes de ofertar.

- **Cuando** consulto el mercado, **entonces** veo edad, club, valor y salario, pero no la
  calidad real.
- **Cuando** envío ojeadores, **entonces** recibo un rango de calidad que siempre contiene
  el valor real, más estrecho cuanto mayor es la reputación del club.
- **Cuando** repito el ojeo, **entonces** obtengo el mismo informe.
- *Pendiente:* cantera y promoción de juveniles.

### HU-03 · Negociación de fichajes — Prioridad media

**Como** DT **quiero** ofertar por un jugador **para** reforzar la plantilla.

- **Dada** una oferta de al menos el 95 % del valor y del salario pretendido, **entonces**
  el jugador firma y se descuenta el monto del presupuesto.
- **Dada** una oferta entre el 60 % y el 95 %, **entonces** recibo una contraoferta.
- **Dada** una oferta por debajo del 60 %, **entonces** se rechaza sin contraoferta.
- **Dada** una oferta que excede el presupuesto o el margen salarial, **entonces** se
  rechaza antes de negociar (RN-02).
- *Pendiente:* venta de jugadores.

### HU-04 · Conflictos de vestuario e historias personales — Prioridad alta

**Como** DT **quiero** intervenir en las crisis del vestuario **para** mantener la
disciplina y la moral.

- **Dada** una crisis pendiente, **cuando** intento iniciar el partido, **entonces** el
  sistema exige resolverla primero.
- **Cuando** sanciono y la directiva me respalda, **entonces** el protagonista pierde
  moral, va a la banca un partido, un Molesto pasa a Rebelde y el afectado gana moral.
- **Cuando** sanciono y la directiva no me respalda, **entonces** la crisis sigue abierta
  y pierdo reputación.
- **Cuando** dialogo, **entonces** la moral de los involucrados se equilibra, un Rebelde o
  Molesto vuelve a Estable y pierdo un poco de reputación.
- **Después** de cada jornada puede surgir un nuevo evento según el estado del plantel.

### HU-05 · Decisiones tácticas en tiempo real — Prioridad alta

**Como** DT **quiero** pausar, sustituir y cambiar la mentalidad durante el partido
**para** reaccionar a lo que pasa en la cancha. Detalle en el
[CU-01](02_caso_de_uso_CU01.md).

### HU-06 · Administración financiera — Prioridad media

**Como** DT **quiero** ver el presupuesto, la masa salarial y los movimientos **para**
decidir fichajes dentro de las restricciones del club.

- **Cuando** gano en casa, **entonces** se suman taquilla y premio por victoria.
- **Cuando** ficho, **entonces** se registra el gasto y baja el presupuesto.

## Requisitos

| Tipo | Requisito | Cómo se cumple |
|---|---|---|
| Funcional | Simular partidos en tiempo real, procesar la personalidad del vestuario y permitir cambios tácticos inmediatos. | `SimuladorPartido` avanza minuto a minuto; la interfaz pide bloques de 3 minutos y se detiene ante pausas. |
| Calidad | La simulación no debe degradar el rendimiento de la interfaz. | Un partido completo se simula en unos 7 ms; prueba `test_requisito_de_calidad_un_partido_completo_en_menos_de_150_ms`. |
| Restricción | El motor de dominio es independiente del motor gráfico y de la interfaz. | El paquete `dominio` solo usa la biblioteca estándar; lo verifica `test_arquitectura.py`. |

## Reglas de negocio

### Reglas de la especificación

| ID | Regla |
|---|---|
| **RN-01** | Ningún atributo de jugador (moral, rendimiento, físico, calidad) sale del rango cerrado `[1, 100]`. Los valores de entrada fuera de rango se rechazan; los valores calculados se saturan al límite más cercano. |
| **RN-02** | Ningún club puede exceder el presupuesto de fichajes ni el límite de masa salarial. |
| **RN-03** | Un jugador Rebelde requiere mediación o sanción antes de volver a Estable. |

### Reglas precisadas durante la construcción

| ID | Regla | Motivo |
|---|---|---|
| RN-04 | Máximo 5 sustituciones por equipo y un jugador sustituido no vuelve a entrar. | CU-01, excepción 5a. |
| RN-05 | Solo ingresa un suplente habilitado: sin lesión, suspensión ni sanción interna. | CU-01, excepción 3a. |
| RN-06 | Una alineación tiene 11 titulares, exactamente 1 portero y hasta 9 suplentes, sin repetidos. | HU-01. |
| RN-07 | No se inicia un partido con crisis de vestuario pendientes. | Escenario crítico: «el DT debe intervenir inmediatamente». |
| RN-08 | La directiva avala una sanción si la reputación del DT es ≥ 30, o ≥ 50 cuando el sancionado es una figura (calidad ≥ 85) o el capitán. | Diagrama de secuencia: «solicita aval a Club». |
| RN-09 | El DT puede elogiar en público a un solo jugador por jornada. | Evita que el elogio pierda valor y que la transición a Motivado sea gratuita. |
| RN-10 | Un jugador del grupo de 15 con mayor calidad que pasa 2 partidos seguidos sin jugar sufre «falta de minutos». | Transición Estable → Molesto de la máquina de estados. |
| RN-11 | Una expulsión suspende un partido; la sanción interna dura un partido y al cumplirse devuelve al Rebelde a Estable. | RN-03. |
| RN-12 | No se negocian fichajes con un partido en curso. | Coherencia del mercado. |
