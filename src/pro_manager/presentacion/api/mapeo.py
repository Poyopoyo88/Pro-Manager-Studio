"""Traducción de objetos del dominio a esquemas de salida de la API."""

from __future__ import annotations

from ...aplicacion.partida import Partida
from ...dominio import (
    Club,
    EventoVestuario,
    IncidenciaJuego,
    InformeOjeo,
    Jugador,
    JugadorEnMercado,
    Partido,
)
from ...dominio.enums import EstadoPartido
from . import esquemas as e


def jugador(j: Jugador) -> e.JugadorSalida:
    return e.JugadorSalida(
        id=j.id,
        nombre=j.nombre,
        posicion=j.posicion,
        edad=j.edad,
        calidad=j.calidad,
        fisico=j.fisico,
        moral=j.moral,
        personalidad=j.personalidad,
        estado_animo=j.estado_animo,
        rendimiento=j.calcular_rendimiento_actual(),
        es_capitan=j.es_capitan,
        salario=j.salario,
        valor_mercado=j.valor_mercado,
        lesionado=j.lesionado,
        partidos_lesion=j.partidos_lesion,
        partidos_suspension=j.partidos_suspension,
        partidos_castigo=j.partidos_castigo,
        habilitado=j.habilitado,
        convocable=j.convocable,
        motivo_inhabilitacion=j.motivo_inhabilitacion(),
        historia=list(j.historia),
    )


def club_resumen(c: Club) -> e.ClubResumenSalida:
    return e.ClubResumenSalida(
        id=c.id,
        nombre=c.nombre,
        ciudad=c.ciudad,
        reputacion=c.reputacion,
        presupuesto_fichajes=c.presupuesto_fichajes,
        masa_salarial=c.masa_salarial(),
        limite_masa_salarial=c.limite_masa_salarial,
    )


def temporada(p: Partida) -> e.TemporadaSalida:
    t = p.temporada
    proximo = None
    if not t.finalizada:
        rival = p.rival(t.rival_de_jornada())
        proximo = e.RivalSalida(id=rival.id, nombre=rival.nombre, ciudad=rival.ciudad)
    return e.TemporadaSalida(
        jornada_actual=min(t.jornada_actual, t.total_jornadas),
        total_jornadas=t.total_jornadas,
        puntos=t.puntos,
        puntos_ascenso=t.puntos_ascenso,
        record=t.record(),
        finalizada=t.finalizada,
        ascendio=t.ascendio,
        proximo_rival=proximo,
        es_local=None if t.finalizada else t.es_local(),
        es_decisiva=None if t.finalizada else t.es_decisiva(),
        historial=[
            e.JornadaSalida(
                jornada=r.jornada,
                rival=r.rival_nombre,
                local=r.local,
                goles_favor=r.goles_favor,
                goles_contra=r.goles_contra,
                resultado=r.resultado,
            )
            for r in t.historial
        ],
    )


def partida(p: Partida) -> e.PartidaSalida:
    return e.PartidaSalida(
        id=p.id,
        semilla=p.semilla,
        creada_en=p.creada_en,
        dt=e.DTSalida(nombre=p.dt.nombre, experiencia=p.dt.experiencia, reputacion=p.dt.reputacion),
        club=club_resumen(p.club),
        temporada=temporada(p),
        eventos_pendientes=len(p.eventos_pendientes()),
        alineacion_definida=p.alineacion is not None,
        hay_partido=p.partido is not None,
        partido_en_curso=p.hay_partido_en_curso,
        noticias=list(p.noticias),
    )


def partida_resumen(p: Partida) -> e.PartidaResumenSalida:
    return e.PartidaResumenSalida(
        id=p.id,
        nombre_dt=p.dt.nombre,
        club=p.club.nombre,
        jornada=min(p.temporada.jornada_actual, p.temporada.total_jornadas),
        puntos=p.temporada.puntos,
        creada_en=p.creada_en,
    )


def _involucrado(club: Club, jugador_id: str | None) -> e.Involucrado | None:
    if not jugador_id:
        return None
    j = club.obtener_jugador(jugador_id)
    return e.Involucrado(id=j.id, nombre=j.nombre, estado_animo=j.estado_animo, moral=j.moral)


def evento(ev: EventoVestuario, club: Club) -> e.EventoSalida:
    return e.EventoSalida(
        id=ev.id,
        tipo=ev.tipo,
        titulo=ev.titulo,
        descripcion=ev.descripcion,
        protagonista=_involucrado(club, ev.protagonista_id),
        afectado=_involucrado(club, ev.afectado_id),
        jornada=ev.jornada,
        severidad=ev.severidad,
        resuelto=ev.resuelto,
        accion_tomada=ev.accion_tomada,
        desenlace=ev.desenlace,
    )


def incidencia(i: IncidenciaJuego) -> e.IncidenciaSalida:
    return e.IncidenciaSalida(
        minuto=i.minuto,
        tipo=i.tipo,
        descripcion=i.descripcion,
        club_id=i.club_id,
        jugador_id=i.jugador_id,
        jugador_entra_id=i.jugador_entra_id,
        critica=i.critica,
    )


def _jugador_en_partido(p: Partido, j: Jugador) -> e.JugadorEnPartido:
    return e.JugadorEnPartido(
        id=j.id,
        nombre=j.nombre,
        posicion=j.posicion,
        fisico=j.fisico,
        moral=j.moral,
        rendimiento=j.calcular_rendimiento_actual(),
        estado_animo=j.estado_animo,
        lesionado=j.lesionado,
        amarillas=p.amarillas.get(j.id, 0),
        habilitado=j.habilitado,
        motivo_inhabilitacion=j.motivo_inhabilitacion(),
    )


def _equipo(p: Partido, club: Club) -> e.EquipoEnPartido:
    return e.EquipoEnPartido(
        id=club.id,
        nombre=club.nombre,
        es_usuario=club.id == p.club_usuario_id,
        goles=p.goles[club.id],
        formacion=p.formaciones[club.id],
        mentalidad=p.mentalidad[club.id],
        sustituciones_restantes=p.sustituciones_restantes(club.id),
        en_campo=[_jugador_en_partido(p, j) for j in p.jugadores_en_campo(club.id)],
        banca=[_jugador_en_partido(p, j) for j in p.jugadores_en_banca(club.id)],
    )


def partido(p: Partido) -> e.PartidoSalida:
    resultado = None
    if p.estado == EstadoPartido.FINALIZADO and p.club_usuario_id:
        resultado = p.resultado_para(p.club_usuario_id)
    return e.PartidoSalida(
        id=p.id,
        jornada=p.jornada,
        es_decisivo=p.es_decisivo,
        estado=p.estado,
        minuto=p.minuto,
        marcador=p.marcador,
        motivo_pausa=p.motivo_pausa,
        resultado=resultado,
        local=_equipo(p, p.local),
        visitante=_equipo(p, p.visitante),
        incidencias=[incidencia(i) for i in p.incidencias],
    )


def finanzas(c: Club) -> e.FinanzasSalida:
    ingresos = sum(m.monto for m in c.movimientos if m.monto > 0)
    gastos = -sum(m.monto for m in c.movimientos if m.monto < 0)
    return e.FinanzasSalida(
        presupuesto_fichajes=c.presupuesto_fichajes,
        masa_salarial=c.masa_salarial(),
        limite_masa_salarial=c.limite_masa_salarial,
        margen_salarial=c.margen_salarial(),
        ingresos_totales=ingresos,
        gastos_totales=gastos,
        movimientos=[
            e.MovimientoSalida(concepto=m.concepto, monto=m.monto, jornada=m.jornada)
            for m in reversed(c.movimientos)
        ],
    )


def jugador_mercado(m: JugadorEnMercado) -> e.JugadorMercadoSalida:
    j = m.jugador
    return e.JugadorMercadoSalida(
        id=j.id,
        nombre=j.nombre,
        posicion=j.posicion,
        edad=j.edad,
        club_origen=m.club_origen,
        valor_mercado=j.valor_mercado,
        salario_pretendido=j.salario,
    )


def informe(i: InformeOjeo) -> e.InformeOjeoSalida:
    return e.InformeOjeoSalida(**i.__dict__)
