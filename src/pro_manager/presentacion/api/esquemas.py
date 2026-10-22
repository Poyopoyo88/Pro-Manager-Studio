"""Esquemas Pydantic de entrada y salida de la API (contrato público)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ...dominio.enums import (
    AccionDT,
    EstadoAnimo,
    EstadoPartido,
    Mentalidad,
    Personalidad,
    Posicion,
    Resultado,
    TipoEventoVestuario,
    TipoIncidencia,
)

# ---------------------------------------------------------------- Errores


class ErrorSalida(BaseModel):
    codigo: str = Field(examples=["sustituciones_agotadas"])
    mensaje: str
    errores: list[str] | None = None


# ---------------------------------------------------------------- Partidas


class CrearPartidaEntrada(BaseModel):
    nombre_dt: str = Field(min_length=1, max_length=60, examples=["Profe Ramírez"])
    semilla: int | None = Field(
        default=None, ge=1, description="Opcional: misma semilla y mismas acciones = misma partida."
    )


class DTSalida(BaseModel):
    nombre: str
    experiencia: int = Field(description="Partidos dirigidos.")
    reputacion: int


class ClubResumenSalida(BaseModel):
    id: str
    nombre: str
    ciudad: str
    reputacion: int
    presupuesto_fichajes: int
    masa_salarial: int
    limite_masa_salarial: int


class RivalSalida(BaseModel):
    id: str
    nombre: str
    ciudad: str


class JornadaSalida(BaseModel):
    jornada: int
    rival: str
    local: bool
    goles_favor: int
    goles_contra: int
    resultado: Resultado


class TemporadaSalida(BaseModel):
    jornada_actual: int
    total_jornadas: int
    puntos: int
    puntos_ascenso: int
    record: dict[str, int]
    finalizada: bool
    ascendio: bool | None
    proximo_rival: RivalSalida | None
    es_local: bool | None
    es_decisiva: bool | None
    historial: list[JornadaSalida]


class PartidaSalida(BaseModel):
    id: str
    semilla: int
    creada_en: str
    dt: DTSalida
    club: ClubResumenSalida
    temporada: TemporadaSalida
    eventos_pendientes: int
    alineacion_definida: bool
    hay_partido: bool = Field(description="Existe un partido (en curso o el último jugado).")
    partido_en_curso: bool
    noticias: list[str]


class PartidaResumenSalida(BaseModel):
    id: str
    nombre_dt: str
    club: str
    jornada: int
    puntos: int
    creada_en: str


# ---------------------------------------------------------------- Plantilla / HU-01


class JugadorSalida(BaseModel):
    id: str
    nombre: str
    posicion: Posicion
    edad: int
    calidad: int
    fisico: int
    moral: int
    personalidad: Personalidad
    estado_animo: EstadoAnimo
    rendimiento: float
    es_capitan: bool
    salario: int
    valor_mercado: int
    lesionado: bool
    partidos_lesion: int
    partidos_suspension: int
    partidos_castigo: int
    habilitado: bool
    convocable: bool
    motivo_inhabilitacion: str | None
    historia: list[str]


class AlineacionEntrada(BaseModel):
    formacion: str = Field(examples=["4-3-3"])
    titulares: list[str] = Field(description="Exactamente 11 identificadores de jugador.")
    suplentes: list[str] = Field(default_factory=list, description="Hasta 9 suplentes.")
    mentalidad: Mentalidad = Mentalidad.EQUILIBRADA


class AlineacionSalida(BaseModel):
    formacion: str
    titulares: list[str]
    suplentes: list[str]
    mentalidad: Mentalidad
    advertencias: list[str] = Field(default_factory=list)


class ElogioSalida(BaseModel):
    jugador: JugadorSalida
    cambio_estado: bool


# ---------------------------------------------------------------- Vestuario / HU-04


class Involucrado(BaseModel):
    id: str
    nombre: str
    estado_animo: EstadoAnimo
    moral: int


class EventoSalida(BaseModel):
    id: str
    tipo: TipoEventoVestuario
    titulo: str
    descripcion: str
    protagonista: Involucrado
    afectado: Involucrado | None
    jornada: int
    severidad: int
    resuelto: bool
    accion_tomada: AccionDT | None
    desenlace: str | None


class ResolucionEntrada(BaseModel):
    accion: AccionDT = Field(description="SANCIONAR (a la banca) o DIALOGAR (mediación).")


class ResolucionSalida(BaseModel):
    evento_id: str
    accion: AccionDT
    resuelto: bool
    aval_directiva: bool | None
    desenlace: str
    cambios: list[str]


# ---------------------------------------------------------------- Partido / HU-05 / CU-01


class IncidenciaSalida(BaseModel):
    minuto: int
    tipo: TipoIncidencia
    descripcion: str
    club_id: str | None
    jugador_id: str | None
    jugador_entra_id: str | None
    critica: bool


class JugadorEnPartido(BaseModel):
    id: str
    nombre: str
    posicion: Posicion
    fisico: int
    moral: int
    rendimiento: float
    estado_animo: EstadoAnimo
    lesionado: bool
    amarillas: int
    habilitado: bool
    motivo_inhabilitacion: str | None


class EquipoEnPartido(BaseModel):
    id: str
    nombre: str
    es_usuario: bool
    goles: int
    formacion: str
    mentalidad: Mentalidad
    sustituciones_restantes: int
    en_campo: list[JugadorEnPartido]
    banca: list[JugadorEnPartido]


class PartidoSalida(BaseModel):
    id: str
    jornada: int
    es_decisivo: bool
    estado: EstadoPartido
    minuto: int
    marcador: str
    motivo_pausa: str | None
    resultado: Resultado | None
    local: EquipoEnPartido
    visitante: EquipoEnPartido
    incidencias: list[IncidenciaSalida]


class SimularEntrada(BaseModel):
    minutos: int = Field(
        default=5, ge=1, le=90, description="Minutos a simular (se detiene antes si hay una pausa)."
    )


class SimularSalida(BaseModel):
    partido: PartidoSalida
    nuevas_incidencias: list[IncidenciaSalida]
    noticias: list[str]


class SustitucionEntrada(BaseModel):
    id_sale: str
    id_entra: str


class SustitucionSalida(BaseModel):
    aplicada: bool
    partido: PartidoSalida


class MentalidadEntrada(BaseModel):
    mentalidad: Mentalidad


# ---------------------------------------------------------------- Club / HU-02 / HU-03 / HU-06


class MovimientoSalida(BaseModel):
    concepto: str
    monto: int
    jornada: int | None


class FinanzasSalida(BaseModel):
    presupuesto_fichajes: int
    masa_salarial: int
    limite_masa_salarial: int
    margen_salarial: int
    ingresos_totales: int
    gastos_totales: int
    movimientos: list[MovimientoSalida]


class JugadorMercadoSalida(BaseModel):
    id: str
    nombre: str
    posicion: Posicion
    edad: int
    club_origen: str
    valor_mercado: int
    salario_pretendido: int


class InformeOjeoSalida(BaseModel):
    jugador_id: str
    nombre: str
    posicion: Posicion
    edad: int
    club_origen: str
    calidad_min: int
    calidad_max: int
    valor_mercado: int
    salario_pretendido: int
    recomendacion: str


class OfertaEntrada(BaseModel):
    monto_transferencia: int = Field(ge=0)
    salario: int = Field(gt=0, description="Salario mensual ofrecido (MXN).")


class OfertaSalida(BaseModel):
    aceptada: bool
    mensaje: str
    contraoferta_monto: int | None
    contraoferta_salario: int | None
