"""Conversión de una ``Partida`` a diccionarios JSON y de regreso (mapeador de datos).

El formato incluye ``version_formato`` para poder migrar partidas guardadas si el
modelo cambia en el futuro.
"""

from __future__ import annotations

from typing import Any

from ..aplicacion.partida import Partida
from ..dominio import (
    Alineacion,
    Club,
    DirectorTecnico,
    EventoVestuario,
    IncidenciaJuego,
    Jugador,
    JugadorEnMercado,
    MovimientoFinanciero,
    Partido,
    ResultadoJornada,
    Temporada,
)
from ..dominio.enums import EstadoPartido, Mentalidad, Resultado, TipoIncidencia
from ..dominio.errores import DatoInvalidoError

VERSION_FORMATO = 1


# -- Jugador / Club / DT ------------------------------------------------------
def jugador_a_dict(j: Jugador) -> dict[str, Any]:
    return {
        "id": j.id,
        "nombre": j.nombre,
        "posicion": j.posicion.value,
        "calidad": j.calidad,
        "fisico": j.fisico,
        "moral": j.moral,
        "personalidad": j.personalidad.value,
        "edad": j.edad,
        "salario": j.salario,
        "valor_mercado": j.valor_mercado,
        "estado_animo": j.estado_animo.value,
        "es_capitan": j.es_capitan,
        "partidos_lesion": j.partidos_lesion,
        "partidos_suspension": j.partidos_suspension,
        "partidos_castigo": j.partidos_castigo,
        "partidos_sin_jugar": j.partidos_sin_jugar,
        "historia": list(j.historia),
    }


def jugador_desde_dict(d: dict[str, Any]) -> Jugador:
    return Jugador(**d)


def club_a_dict(c: Club) -> dict[str, Any]:
    return {
        "id": c.id,
        "nombre": c.nombre,
        "ciudad": c.ciudad,
        "presupuesto_fichajes": c.presupuesto_fichajes,
        "limite_masa_salarial": c.limite_masa_salarial,
        "reputacion": c.reputacion,
        "plantilla": [jugador_a_dict(j) for j in c.plantilla],
        "movimientos": [
            {"concepto": m.concepto, "monto": m.monto, "jornada": m.jornada} for m in c.movimientos
        ],
    }


def club_desde_dict(d: dict[str, Any]) -> Club:
    datos = dict(d)
    datos["plantilla"] = [jugador_desde_dict(j) for j in d["plantilla"]]
    datos["movimientos"] = [MovimientoFinanciero(**m) for m in d.get("movimientos", [])]
    return Club(**datos)


def dt_a_dict(dt: DirectorTecnico) -> dict[str, Any]:
    return {
        "nombre": dt.nombre,
        "experiencia": dt.experiencia,
        "reputacion": dt.reputacion,
        "ultima_jornada_elogio": dt.ultima_jornada_elogio,
    }


# -- Táctica / Vestuario / Temporada ------------------------------------------
def alineacion_a_dict(a: Alineacion | None) -> dict[str, Any] | None:
    if a is None:
        return None
    return {
        "formacion": a.formacion,
        "titulares": list(a.titulares),
        "suplentes": list(a.suplentes),
        "mentalidad": a.mentalidad.value,
    }


def alineacion_desde_dict(d: dict[str, Any] | None) -> Alineacion | None:
    return Alineacion(**d) if d else None


def evento_a_dict(e: EventoVestuario) -> dict[str, Any]:
    return {
        "id": e.id,
        "tipo": e.tipo.value,
        "titulo": e.titulo,
        "descripcion": e.descripcion,
        "protagonista_id": e.protagonista_id,
        "afectado_id": e.afectado_id,
        "jornada": e.jornada,
        "severidad": e.severidad,
        "resuelto": e.resuelto,
        "accion_tomada": e.accion_tomada.value if e.accion_tomada else None,
        "desenlace": e.desenlace,
    }


def temporada_a_dict(t: Temporada) -> dict[str, Any]:
    return {
        "rivales_ids": list(t.rivales_ids),
        "puntos_ascenso": t.puntos_ascenso,
        "jornada_actual": t.jornada_actual,
        "historial": [
            {
                "jornada": r.jornada,
                "rival_id": r.rival_id,
                "rival_nombre": r.rival_nombre,
                "local": r.local,
                "goles_favor": r.goles_favor,
                "goles_contra": r.goles_contra,
                "resultado": Resultado(r.resultado).value,
            }
            for r in t.historial
        ],
    }


def temporada_desde_dict(d: dict[str, Any]) -> Temporada:
    historial = [
        ResultadoJornada(**{**r, "resultado": Resultado(r["resultado"])}) for r in d["historial"]
    ]
    return Temporada(d["rivales_ids"], d["puntos_ascenso"], d["jornada_actual"], historial)


# -- Partido -------------------------------------------------------------------
def partido_a_dict(p: Partido | None) -> dict[str, Any] | None:
    if p is None:
        return None
    return {
        "id": p.id,
        "local_id": p.local.id,
        "visitante_id": p.visitante.id,
        "club_usuario_id": p.club_usuario_id,
        "jornada": p.jornada,
        "es_decisivo": p.es_decisivo,
        "formaciones": dict(p.formaciones),
        "estado": p.estado.value,
        "minuto": p.minuto,
        "goles": dict(p.goles),
        "mentalidad": {k: v.value for k, v in p.mentalidad.items()},
        "en_campo": {k: list(v) for k, v in p.en_campo.items()},
        "banca": {k: list(v) for k, v in p.banca.items()},
        "participantes": {k: list(v) for k, v in p.participantes.items()},
        "sustituciones": dict(p.sustituciones),
        "amarillas": dict(p.amarillas),
        "expulsados": list(p.expulsados),
        "lesionados_en_partido": list(p.lesionados_en_partido),
        "incidencias": [
            {
                "minuto": i.minuto,
                "tipo": i.tipo.value,
                "descripcion": i.descripcion,
                "club_id": i.club_id,
                "jugador_id": i.jugador_id,
                "jugador_entra_id": i.jugador_entra_id,
                "critica": i.critica,
            }
            for i in p.incidencias
        ],
        "motivo_pausa": p.motivo_pausa,
        "descanso_realizado": p.descanso_realizado,
    }


def partido_desde_dict(d: dict[str, Any] | None, clubes: dict[str, Club]) -> Partido | None:
    """Reconstruye un partido en curso sin volver a validar las alineaciones originales."""
    if d is None:
        return None
    try:
        local, visitante = clubes[d["local_id"]], clubes[d["visitante_id"]]
    except KeyError as exc:
        raise DatoInvalidoError(
            f"La partida guardada referencia un club inexistente: {exc}"
        ) from exc
    partido = Partido.__new__(Partido)
    partido.id = d["id"]
    partido.local = local
    partido.visitante = visitante
    partido.club_usuario_id = d["club_usuario_id"]
    partido.jornada = d["jornada"]
    partido.es_decisivo = d["es_decisivo"]
    partido.formaciones = dict(d["formaciones"])
    partido.estado = EstadoPartido(d["estado"])
    partido.minuto = d["minuto"]
    partido.goles = dict(d["goles"])
    partido.mentalidad = {k: Mentalidad(v) for k, v in d["mentalidad"].items()}
    partido.en_campo = {k: list(v) for k, v in d["en_campo"].items()}
    partido.banca = {k: list(v) for k, v in d["banca"].items()}
    partido.participantes = {k: list(v) for k, v in d["participantes"].items()}
    partido.sustituciones = dict(d["sustituciones"])
    partido.amarillas = dict(d["amarillas"])
    partido.expulsados = list(d["expulsados"])
    partido.lesionados_en_partido = list(d["lesionados_en_partido"])
    partido.incidencias = [
        IncidenciaJuego(**{**i, "tipo": TipoIncidencia(i["tipo"])}) for i in d["incidencias"]
    ]
    partido.motivo_pausa = d["motivo_pausa"]
    partido.descanso_realizado = d["descanso_realizado"]
    return partido


# -- Partida completa ----------------------------------------------------------
def partida_a_dict(p: Partida) -> dict[str, Any]:
    return {
        "version_formato": VERSION_FORMATO,
        "id": p.id,
        "semilla": p.semilla,
        "contador_acciones": p.contador_acciones,
        "creada_en": p.creada_en,
        "dt": dt_a_dict(p.dt),
        "club": club_a_dict(p.club),
        "rivales": [club_a_dict(r) for r in p.rivales],
        "temporada": temporada_a_dict(p.temporada),
        "eventos": [evento_a_dict(e) for e in p.eventos],
        "mercado": [
            {"jugador": jugador_a_dict(m.jugador), "club_origen": m.club_origen} for m in p.mercado
        ],
        "alineacion": alineacion_a_dict(p.alineacion),
        "partido": partido_a_dict(p.partido),
        "noticias": list(p.noticias),
    }


def partida_desde_dict(d: dict[str, Any]) -> Partida:
    version = d.get("version_formato")
    if version != VERSION_FORMATO:
        raise DatoInvalidoError(f"Formato de partida no soportado: {version!r}.")
    club = club_desde_dict(d["club"])
    rivales = [club_desde_dict(r) for r in d["rivales"]]
    clubes = {c.id: c for c in [club, *rivales]}
    return Partida(
        id=d["id"],
        semilla=d["semilla"],
        contador_acciones=d["contador_acciones"],
        creada_en=d["creada_en"],
        dt=DirectorTecnico(**d["dt"]),
        club=club,
        rivales=rivales,
        temporada=temporada_desde_dict(d["temporada"]),
        eventos=[EventoVestuario(**e) for e in d["eventos"]],
        mercado=[
            JugadorEnMercado(jugador_desde_dict(m["jugador"]), m["club_origen"])
            for m in d["mercado"]
        ],
        alineacion=alineacion_desde_dict(d["alineacion"]),
        partido=partido_desde_dict(d["partido"], clubes),
        noticias=list(d.get("noticias", [])),
    )
