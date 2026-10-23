/* Pro Manager Studio — cliente web del Director Técnico.
   Consume la API REST de /api/v1. Sin dependencias externas.
   El DOM se construye con h() (textContent), nunca con innerHTML, para evitar inyección. */
"use strict";

const API = "/api/v1";
const CLAVE_PARTIDA = "pm_partida";
const VISTAS = [
  ["vestuario", "Vestuario"],
  ["alineacion", "Alineación"],
  ["partido", "Partido"],
  ["plantilla", "Plantilla"],
  ["mercado", "Mercado"],
  ["finanzas", "Finanzas"],
];
const ORDEN_POSICION = { POR: 0, DEF: 1, MED: 2, DEL: 3 };
const NOMBRE_POSICION = { POR: "Porteros", DEF: "Defensas", MED: "Mediocampistas", DEL: "Delanteros" };
const NOMBRE_MENTALIDAD = { DEFENSIVA: "Defensiva", EQUILIBRADA: "Equilibrada", OFENSIVA: "Ofensiva" };
const ANIMO = { MOTIVADO: "Motivado", ESTABLE: "Estable", MOLESTO: "Molesto", REBELDE: "Rebelde" };
const COLOR_ANIMO = {
  MOTIVADO: "var(--motivado)", ESTABLE: "var(--estable)", MOLESTO: "var(--molesto)", REBELDE: "var(--rebelde)",
};
const dinero = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });

const st = {
  partidaId: leer(CLAVE_PARTIDA),
  partida: null,
  vista: "vestuario",
  aviso: null,
  eventos: [],
  resoluciones: {},
  plantilla: [],
  formaciones: [],
  alin: null,
  advertencias: [],
  partido: null,
  jugando: false,
  quierePausar: false,
  nuevas: new Set(),
  mercado: [],
  informes: {},
  ofertaAbierta: null,
  respuestas: {},
  finanzas: null,
  detalle: null,
  seccionesAbiertas: new Set(["POR"]),
};

// ------------------------------------------------------------------ utilidades
function leer(clave) { try { return localStorage.getItem(clave); } catch { return null; } }
function escribir(clave, valor) {
  try { valor === null ? localStorage.removeItem(clave) : localStorage.setItem(clave, valor); } catch { /* sin almacenamiento */ }
}
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

class ErrorApi extends Error {
  constructor(datos, estado) {
    super(datos.mensaje || "Ocurrió un error inesperado.");
    this.datos = datos;
    this.estado = estado;
  }
}

async function api(ruta, { metodo = "GET", cuerpo } = {}) {
  const respuesta = await fetch(API + ruta, {
    method: metodo,
    headers: cuerpo ? { "Content-Type": "application/json" } : {},
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  if (respuesta.status === 204) return null;
  const datos = await respuesta.json().catch(() => ({ mensaje: `Error ${respuesta.status}` }));
  if (!respuesta.ok) throw new ErrorApi(datos, respuesta.status);
  return datos;
}
const rutaPartida = (resto = "") => `/partidas/${encodeURIComponent(st.partidaId)}${resto}`;

function h(etiqueta, atributos = {}, ...hijos) {
  const el = document.createElement(etiqueta);
  for (const [clave, valor] of Object.entries(atributos || {})) {
    if (valor === null || valor === undefined || valor === false) continue;
    if (clave === "clase") el.className = valor;
    else if (clave === "estilo") el.setAttribute("style", valor);
    else if (clave.startsWith("on")) el.addEventListener(clave.slice(2), valor);
    else if (valor === true) el.setAttribute(clave, "");
    else el.setAttribute(clave, valor);
  }
  for (const hijo of hijos.flat(Infinity)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    el.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
  return el;
}

function avisar(tipo, mensaje, errores = []) { st.aviso = { tipo, mensaje, errores }; }
function avisarError(error) {
  if (error instanceof ErrorApi) avisar("error", error.message, error.datos.errores || []);
  else avisar("error", "No se pudo conectar con el servidor. Revisa que esté en marcha.");
}
function nodoAviso() {
  if (!st.aviso) return null;
  const { tipo, mensaje, errores } = st.aviso;
  return h("div", { clase: `aviso ${tipo}`, role: tipo === "error" ? "alert" : "status" },
    mensaje,
    errores && errores.length ? h("ul", {}, errores.map((e) => h("li", {}, e))) : null);
}

const chipAnimo = (estado) => h("span", { clase: `animo ${estado}` }, ANIMO[estado] || estado);
const nombreCorto = (nombre) => nombre.replace(/«[^»]*»\s*/g, "").trim().split(/\s+/).slice(-1)[0];
function iniciales(nombre) {
  const partes = nombre.replace(/«[^»]*»\s*/g, "").trim().split(/\s+/);
  return (partes[0][0] + (partes.length > 1 ? partes[partes.length - 1][0] : "")).toUpperCase();
}
const ordenarPorPosicion = (lista) =>
  [...lista].sort((a, b) => ORDEN_POSICION[a.posicion] - ORDEN_POSICION[b.posicion] || b.rendimiento - a.rendimiento);

// ------------------------------------------------------------------ la cancha
function cancha(jugadores, { energia = false } = {}) {
  const lineas = { DEL: [], MED: [], DEF: [], POR: [] };
  for (const j of jugadores) lineas[j.posicion].push(j);
  return h("div", { clase: "cancha", role: "img", "aria-label": `Alineación en cancha: ${jugadores.map((j) => j.nombre).join(", ")}` },
    h("div", { clase: "area arriba" }),
    h("div", { clase: "area abajo" }),
    ["DEL", "MED", "DEF", "POR"].map((pos) =>
      h("div", { clase: "linea-cancha" },
        lineas[pos].map((j) =>
          h("div", { clase: `ficha${j.lesionado ? " lesionado" : ""}`, title: `${j.nombre}: ${ANIMO[j.estado_animo]}` },
            h("div", { clase: "disco", estilo: `--anillo:${COLOR_ANIMO[j.estado_animo]}` }, iniciales(j.nombre)),
            h("div", { clase: "nombre" }, nombreCorto(j.nombre)),
            energia ? h("div", { clase: "energia" }, h("span", { estilo: `width:${j.fisico}%` })) : null)))));
}
const leyendaAnimo = () => h("div", { clase: "leyenda" }, Object.keys(ANIMO).map((e) => chipAnimo(e)));

// ------------------------------------------------------------------ arranque y portada
const raiz = document.getElementById("app");

async function cargarPartida() {
  st.partida = await api(rutaPartida());
}

async function iniciar() {
  if (st.partidaId) {
    try {
      await cargarPartida();
      st.vista = st.partida.eventos_pendientes ? "vestuario" : st.partida.partido_en_curso ? "partido" : "alineacion";
      return mostrar(st.vista);
    } catch {
      escribir(CLAVE_PARTIDA, null);
      st.partidaId = null;
    }
  }
  portada();
}

async function portada() {
  let guardadas = [];
  try { guardadas = await api("/partidas"); } catch { /* el servidor responderá al crear */ }
  const entrada = h("input", { type: "text", id: "nombre-dt", required: true, maxlength: "60", autocomplete: "name", placeholder: "Por ejemplo: Profe Ramírez" });
  const formulario = h("form", {
    clase: "fila",
    onsubmit: async (ev) => {
      ev.preventDefault();
      try {
        const partida = await api("/partidas", { metodo: "POST", cuerpo: { nombre_dt: entrada.value.trim() } });
        abrirPartida(partida.id);
      } catch (error) {
        avisarError(error);
        portada();
      }
    },
  }, h("label", {}, "Nombre del Director Técnico", entrada), h("button", { clase: "boton principal", type: "submit" }, "Empezar carrera"));

  raiz.replaceChildren(h("div", { clase: "portada", id: "contenido" },
    h("h1", {}, "Pro Manager Studio"),
    h("p", { clase: "lema" },
      "Toma el banquillo de los Halcones del Desierto FC. Cinco jornadas para ascender, un vestuario con carácter y decisiones que se toman en segundos."),
    nodoAviso(),
    formulario,
    guardadas.length ? h("section", { estilo: "margin-top:2.5rem" },
      h("h2", {}, "Continuar una carrera"),
      h("div", { clase: "tabla-contenedor" }, h("table", {},
        h("thead", {}, h("tr", {}, h("th", {}, "DT"), h("th", {}, "Jornada"), h("th", { clase: "num" }, "Puntos"), h("th", {}, ""))),
        h("tbody", {}, guardadas.map((p) => h("tr", {},
          h("td", {}, p.nombre_dt), h("td", { clase: "num" }, p.jornada), h("td", { clase: "num" }, p.puntos),
          h("td", {}, h("button", { clase: "boton pequeno", onclick: () => abrirPartida(p.id) }, "Continuar")))))))) : null));
  st.aviso = null;
}

function abrirPartida(id) {
  st.partidaId = id;
  escribir(CLAVE_PARTIDA, id);
  Object.assign(st, { alin: null, partido: null, informes: {}, respuestas: {}, resoluciones: {}, aviso: null });
  iniciar();
}

function salir() {
  st.jugando = false;
  escribir(CLAVE_PARTIDA, null);
  Object.assign(st, { partidaId: null, partida: null, alin: null, partido: null, aviso: null });
  portada();
}

// ------------------------------------------------------------------ marco general
function encabezado() {
  const { partida: p } = st;
  const t = p.temporada;
  let linea;
  if (t.finalizada) linea = t.ascendio ? "Temporada terminada con ascenso." : "Temporada terminada sin ascenso.";
  else linea = `Jornada ${t.jornada_actual} de ${t.total_jornadas}, contra ${t.proximo_rival.nombre} ${t.es_local ? "en casa" : "de visita"}${t.es_decisiva ? ". Partido decisivo" : ""}.`;
  const avance = Math.min(100, Math.round((100 * t.puntos) / t.puntos_ascenso));
  return h("header", { clase: "encabezado" },
    h("div", {},
      h("div", { clase: "club" }, p.club.nombre),
      h("div", { clase: "meta" }, `DT ${p.dt.nombre}. ${linea}`)),
    h("div", { clase: "meta-ascenso" },
      h("div", { clase: "meta num" }, `${t.puntos} de ${t.puntos_ascenso} puntos para ascender`),
      h("div", { clase: "barra", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": String(t.puntos_ascenso), "aria-valuenow": String(t.puntos) },
        h("span", { estilo: `width:${avance}%` })),
      h("div", { clase: "meta num", estilo: "margin-top:.35rem; display:flex; gap:.75rem; align-items:center" },
        `Reputación del DT: ${p.dt.reputacion}`,
        h("button", { clase: "boton pequeno", onclick: salir }, "Cambiar partida"))));
}

function navegacion() {
  return h("nav", { clase: "navegacion", "aria-label": "Secciones" },
    VISTAS.map(([clave, texto]) => h("button", {
      "aria-current": st.vista === clave ? "page" : null,
      onclick: () => { st.aviso = null; mostrar(clave); },
    }, texto, clave === "vestuario" && st.partida.eventos_pendientes ? h("span", { clase: "insignia", "aria-label": "pendientes" }, st.partida.eventos_pendientes) : null)));
}

function noticias() {
  // Las novedades acompañan a las decisiones: vestuario y previa del partido.
  const lista = st.partida.noticias || [];
  const enPartido = st.vista === "partido" && st.partido && st.partido.estado !== "FINALIZADO";
  if (!lista.length || !["vestuario", "partido"].includes(st.vista) || enPartido) return null;
  return h("section", { clase: "noticias", "aria-label": "Novedades" },
    h("h3", {}, "Novedades"), h("ul", {}, lista.map((n) => h("li", {}, n))));
}

const DIBUJAR = {};
const CARGAR = {};

async function mostrar(vista) {
  st.vista = vista;
  try {
    if (CARGAR[vista]) await CARGAR[vista]();
  } catch (error) {
    avisarError(error);
  }
  dibujar();
}

function dibujar() {
  if (!st.partida) return portada();
  raiz.replaceChildren(
    encabezado(),
    navegacion(),
    h("main", { id: "contenido" }, nodoAviso(), noticias(), DIBUJAR[st.vista]()));
}

// ------------------------------------------------------------------ Vestuario (HU-04)
CARGAR.vestuario = async () => {
  await cargarPartida();
  st.eventos = await api(rutaPartida("/vestuario/eventos"));
};

async function resolver(evento, accion) {
  try {
    const resultado = await api(rutaPartida(`/vestuario/eventos/${evento.id}/resolucion`), { metodo: "POST", cuerpo: { accion } });
    st.resoluciones[evento.id] = resultado;
    st.alin = null; // una sanción puede invalidar el once guardado
    st.aviso = null;
  } catch (error) {
    avisarError(error);
  }
  mostrar("vestuario");
}

function involucrado(jugador, rol) {
  return h("div", {},
    h("div", { clase: "tenue" }, rol),
    h("strong", {}, jugador.nombre), " ", chipAnimo(jugador.estado_animo),
    h("div", { clase: "tenue num" }, `Moral ${jugador.moral}`));
}

function listaCambios(resolucion) {
  return resolucion && resolucion.cambios.length ? h("ul", { clase: "cambios" }, resolucion.cambios.map((c) => h("li", {}, c))) : null;
}

DIBUJAR.vestuario = () => {
  const pendientes = st.eventos.filter((e) => !e.resuelto);
  const resueltos = st.eventos.filter((e) => e.resuelto).reverse();
  return h("div", {},
    pendientes.length === 0
      ? h("div", { clase: "panel" },
          h("h2", {}, "El vestuario está en calma"),
          h("p", { clase: "tenue" }, "No hay asuntos pendientes. Prepara el once para la próxima jornada."),
          h("button", { clase: "boton principal", onclick: () => mostrar("alineacion") }, "Ir a la alineación"))
      : pendientes.map((ev) => {
          const intento = st.resoluciones[ev.id];
          return h("article", { clase: "panel crisis" },
            h("h2", {}, ev.titulo),
            h("p", {}, ev.descripcion),
            h("div", { clase: "involucrados" },
              involucrado(ev.protagonista, "Protagonista"),
              ev.afectado ? involucrado(ev.afectado, "También involucrado") : null),
            intento && !intento.resuelto ? h("div", { clase: "aviso error" }, intento.desenlace, listaCambios(intento)) : null,
            h("div", { clase: "fila" },
              h("button", { clase: "boton peligro", onclick: () => resolver(ev, "SANCIONAR") }, "Sancionar y mandarlo a la banca"),
              h("button", { clase: "boton", onclick: () => resolver(ev, "DIALOGAR") }, ev.afectado ? "Mediar entre ellos" : "Hablar con él")),
            h("p", { clase: "tenue", estilo: "margin-top:.75rem" },
              "Sancionar requiere el aval de la directiva y refuerza tu autoridad. Mediar calma los ánimos, pero algunos lo leen como debilidad."));
        }),
    resueltos.length ? h("section", { estilo: "margin-top:2rem" },
      h("h2", {}, "Decisiones tomadas"),
      resueltos.map((ev) => h("div", { clase: "panel resuelto" },
        h("h3", {}, `Jornada ${ev.jornada}: ${ev.titulo}`),
        h("p", {}, ev.desenlace),
        listaCambios(st.resoluciones[ev.id])))) : null);
};

// ------------------------------------------------------------------ Alineación (HU-01)
function aAlineacion(datos) {
  return {
    formacion: datos.formacion,
    mentalidad: datos.mentalidad,
    titulares: new Set(datos.titulares),
    suplentes: new Set(datos.suplentes),
  };
}

CARGAR.alineacion = async () => {
  await cargarPartida();
  st.plantilla = await api(rutaPartida("/plantilla"));
  if (!st.formaciones.length) st.formaciones = await api(rutaPartida("/formaciones"));
  if (!st.alin) {
    const actual = await api(rutaPartida("/alineacion"));
    const base = actual || (await api(rutaPartida("/alineacion/sugerida?formacion=4-4-2")));
    st.alin = aAlineacion(base);
    st.advertencias = base.advertencias || [];
  }
};

async function sugerir() {
  try {
    const q = new URLSearchParams({ formacion: st.alin.formacion, mentalidad: st.alin.mentalidad });
    const datos = await api(rutaPartida(`/alineacion/sugerida?${q}`));
    st.alin = aAlineacion(datos);
    st.advertencias = datos.advertencias;
    avisar("info", "El cuerpo técnico propone este once según el rendimiento actual. Guárdalo si te convence.");
  } catch (error) { avisarError(error); }
  dibujar();
}

async function guardarAlineacion() {
  try {
    const datos = await api(rutaPartida("/alineacion"), {
      metodo: "PUT",
      cuerpo: { formacion: st.alin.formacion, mentalidad: st.alin.mentalidad, titulares: [...st.alin.titulares], suplentes: [...st.alin.suplentes] },
    });
    st.advertencias = datos.advertencias;
    await cargarPartida();
    avisar("info", "Alineación guardada. Cuando el vestuario esté en calma, ve a Partido.", datos.advertencias);
  } catch (error) { avisarError(error); }
  dibujar();
}

function alternar(jugador, destino) {
  const { titulares, suplentes } = st.alin;
  const conjunto = destino === "titular" ? titulares : suplentes;
  const otro = destino === "titular" ? suplentes : titulares;
  if (conjunto.has(jugador.id)) conjunto.delete(jugador.id);
  else { conjunto.add(jugador.id); otro.delete(jugador.id); }
  dibujar();
}

DIBUJAR.alineacion = () => {
  const { alin } = st;
  const titulares = st.plantilla.filter((j) => alin.titulares.has(j.id));
  const grupos = ["POR", "DEF", "MED", "DEL"].map((pos) => [pos, ordenarPorPosicion(st.plantilla.filter((j) => j.posicion === pos))]);
  return h("div", {},
    h("div", { clase: "panel fila" },
      h("label", {}, "Formación",
        h("select", { onchange: (e) => { alin.formacion = e.target.value; dibujar(); } },
          st.formaciones.map((f) => h("option", { value: f, selected: f === alin.formacion }, f)))),
      h("div", {}, h("div", { clase: "tenue", estilo: "font-size:.9rem; margin-bottom:.25rem" }, "Mentalidad"),
        h("div", { clase: "segmentado", role: "group", "aria-label": "Mentalidad" },
          Object.entries(NOMBRE_MENTALIDAD).map(([clave, texto]) =>
            h("button", { type: "button", "aria-pressed": String(alin.mentalidad === clave), onclick: () => { alin.mentalidad = clave; dibujar(); } }, texto)))),
      h("button", { clase: "boton", onclick: sugerir }, "Pedir sugerencia al cuerpo técnico"),
      h("button", { clase: "boton principal", onclick: guardarAlineacion }, "Guardar alineación"),
      h("span", { clase: "tenue num" }, `Titulares ${alin.titulares.size} de 11. Banca ${alin.suplentes.size} de 9.`)),
    st.advertencias.length && !st.aviso ? h("div", { clase: "aviso info" }, "Fuera de posición:", h("ul", {}, st.advertencias.map((a) => h("li", {}, a)))) : null,
    h("div", { clase: "columnas", estilo: "margin-top:1rem" },
      h("div", {}, cancha(titulares), leyendaAnimo()),
      h("div", { clase: "panel" }, tablaConvocatoria(grupos))));
};

function filaConvocatoria(j) {
  const { alin } = st;
  const botones = h("div", { clase: "segmentado" },
    h("button", { type: "button", "aria-pressed": String(alin.titulares.has(j.id)), disabled: !j.habilitado, onclick: () => alternar(j, "titular") }, "Titular"),
    h("button", { type: "button", "aria-pressed": String(alin.suplentes.has(j.id)), disabled: !j.convocable, onclick: () => alternar(j, "banca") }, "Banca"));
  return h("tr", { clase: j.habilitado ? "" : "inhabilitado" },
    h("td", {}, j.nombre, j.es_capitan ? h("span", { clase: "capitan", title: "Capitán" }, "C") : null,
      j.motivo_inhabilitacion ? h("div", { clase: "tenue", estilo: "font-size:.8rem" }, j.motivo_inhabilitacion) : null),
    h("td", {}, chipAnimo(j.estado_animo)),
    h("td", { clase: "num" }, j.rendimiento.toFixed(0)),
    h("td", {}, botones));
}

// Cupos por línea según la formación: "4-2-3-1" → DEF 4, MED 5, DEL 1.
function cuposFormacion(formacion) {
  const lineas = formacion.split("-").map(Number);
  return { POR: 1, DEF: lineas[0], MED: lineas.slice(1, -1).reduce((a, b) => a + b, 0), DEL: lineas[lineas.length - 1] };
}

function alternarSeccion(pos, abierta) {
  if (abierta) st.seccionesAbiertas.add(pos);
  else st.seccionesAbiertas.delete(pos);
}

function seccionConvocatoria(pos, jugadores, cupo) {
  const { alin } = st;
  const titulares = jugadores.filter((j) => alin.titulares.has(j.id)).length;
  const banca = jugadores.filter((j) => alin.suplentes.has(j.id)).length;
  const completo = titulares === cupo;
  const resumen = h("summary", { clase: "seccion-resumen" },
    h("span", { clase: "seccion-titulo" }, NOMBRE_POSICION[pos]),
    h("span", { clase: "seccion-total tenue" }, `${jugadores.length} jugadores`),
    h("span", { clase: `seccion-conteo num${completo ? "" : " incompleto"}`, title: `La ${alin.formacion} pide ${cupo}` },
      `Titulares ${titulares} de ${cupo}`),
    h("span", { clase: "seccion-conteo tenue num" }, `Banca ${banca}`));
  const tabla = h("table", { clase: "tabla-convocatoria" },
    h("colgroup", {}, h("col", {}), h("col", { estilo: "width:7.5rem" }), h("col", { estilo: "width:4rem" }), h("col", { estilo: "width:10rem" })),
    h("thead", {}, h("tr", {},
      h("th", {}, "Jugador"), h("th", {}, "Ánimo"), h("th", { clase: "num" }, "Rend."), h("th", {}, "Convocatoria"))),
    h("tbody", {}, jugadores.map(filaConvocatoria)));
  return h("details", {
    clase: "seccion-posicion",
    open: st.seccionesAbiertas.has(pos),
    ontoggle: (e) => alternarSeccion(pos, e.currentTarget.open),
  }, resumen, h("div", { clase: "tabla-contenedor" }, tabla));
}

function tablaConvocatoria(grupos) {
  const cupos = cuposFormacion(st.alin.formacion);
  const todas = grupos.every(([pos]) => st.seccionesAbiertas.has(pos));
  const control = h("div", { clase: "fila", estilo: "justify-content:space-between; align-items:center; margin-bottom:.5rem" },
    h("h3", { estilo: "margin:0" }, "Convocatoria"),
    h("button", {
      clase: "boton pequeno",
      onclick: () => {
        st.seccionesAbiertas = todas ? new Set() : new Set(grupos.map(([pos]) => pos));
        dibujar();
      },
    }, todas ? "Contraer todo" : "Expandir todo"));
  return h("div", {}, control, grupos.map(([pos, jugadores]) => seccionConvocatoria(pos, jugadores, cupos[pos])));
}

// ------------------------------------------------------------------ Partido (HU-05 / CU-01)
CARGAR.partido = async () => {
  await cargarPartida();
  st.partido = st.partida.hay_partido ? await api(rutaPartida("/partido")) : null;
};

const claveIncidencia = (i) => `${i.minuto}|${i.tipo}|${i.descripcion}`;
const equipoUsuario = (p) => (p.local.es_usuario ? p.local : p.visitante);

async function iniciarPartido() {
  try {
    st.partido = await api(rutaPartida("/partido"), { metodo: "POST" });
    st.aviso = null;
    await cargarPartida();
    jugar();
  } catch (error) {
    avisarError(error);
    dibujar();
  }
}

async function jugar() {
  if (st.jugando) return;
  st.jugando = true;
  st.quierePausar = false;
  dibujar();
  try {
    while (st.jugando) {
      const r = await api(rutaPartida("/partido/simulacion"), { metodo: "POST", cuerpo: { minutos: 3 } });
      st.partido = r.partido;
      st.nuevas = new Set(r.nuevas_incidencias.map(claveIncidencia));
      if (r.partido.estado !== "EN_JUEGO") {
        st.jugando = false;
        if (r.partido.estado === "FINALIZADO") st.alin = null; // lesiones y sanciones cambian el once
        await cargarPartida();
      } else if (st.quierePausar) {
        st.jugando = false;
        st.partido = await api(rutaPartida("/partido/pausa"), { metodo: "POST" });
      }
      dibujar();
      if (st.jugando) await espera(650);
    }
  } catch (error) {
    st.jugando = false;
    avisarError(error);
    dibujar();
  }
}

function pausar() { st.quierePausar = true; }

async function reanudar() {
  try {
    st.partido = await api(rutaPartida("/partido/reanudacion"), { metodo: "POST" });
    st.aviso = null;
    jugar();
  } catch (error) { avisarError(error); dibujar(); }
}

async function sustituir(idSale, idEntra) {
  try {
    const r = await api(rutaPartida("/partido/sustituciones"), { metodo: "POST", cuerpo: { id_sale: idSale, id_entra: idEntra } });
    st.partido = r.partido;
    avisar("info", "Cambio aplicado. Cuando termines los ajustes, reanuda el partido.");
  } catch (error) { avisarError(error); }
  dibujar();
}

async function cambiarMentalidad(mentalidad) {
  try {
    st.partido = await api(rutaPartida("/partido/mentalidad"), { metodo: "PUT", cuerpo: { mentalidad } });
  } catch (error) { avisarError(error); }
  dibujar();
}

function marcador(p) {
  const pausado = p.estado === "PAUSADO";
  const textoMinuto = p.estado === "FINALIZADO" ? "Final" : `${p.minuto}'${pausado ? " en pausa" : ""}`;
  return h("div", { clase: "marcador", role: "status" },
    h("div", { clase: `equipo${p.local.es_usuario ? " usuario" : ""}` }, p.local.nombre),
    h("div", {},
      h("div", { clase: "goles num" }, `${p.local.goles} - ${p.visitante.goles}`),
      h("span", { clase: `minuto${pausado ? " pausado" : ""}` }, textoMinuto)),
    h("div", { clase: `equipo visitante${p.visitante.es_usuario ? " usuario" : ""}` }, p.visitante.nombre));
}

function cronica(p) {
  return h("div", { clase: "panel" },
    h("h3", {}, "Crónica"),
    h("ul", { clase: "cronica" }, [...p.incidencias].reverse().map((i) =>
      h("li", { clase: [i.tipo, i.critica ? "critica" : "", st.nuevas.has(claveIncidencia(i)) ? "nueva" : ""].join(" ") },
        h("span", { clase: "min num" }, `${i.minuto}'`), h("span", {}, i.descripcion)))));
}

function panelBanda(p) {
  const equipo = equipoUsuario(p);
  const sale = h("select", { "aria-label": "Jugador que sale" },
    equipo.en_campo.map((j) => h("option", { value: j.id },
      `${j.nombre} (${j.posicion}), físico ${j.fisico}${j.lesionado ? ", lesionado" : ""}`)));
  const entra = h("select", { "aria-label": "Jugador que entra" },
    equipo.banca.map((j) => h("option", { value: j.id },
      `${j.nombre} (${j.posicion})${j.habilitado ? "" : ", inhabilitado"}`)));
  const lesionado = equipo.en_campo.find((j) => j.lesionado);
  if (lesionado) sale.value = lesionado.id;
  return h("div", { clase: "panel" },
    h("h3", {}, "Desde la banda"),
    p.motivo_pausa ? h("p", {}, p.motivo_pausa) : null,
    h("div", { clase: "fila" },
      h("label", {}, "Sale", sale),
      h("label", {}, "Entra", entra),
      h("button", { clase: "boton", disabled: !equipo.banca.length || !equipo.sustituciones_restantes, onclick: () => sustituir(sale.value, entra.value) }, "Hacer cambio")),
    h("p", { clase: "tenue num", estilo: "margin-top:.5rem" }, `Cambios disponibles: ${equipo.sustituciones_restantes}`),
    h("div", { estilo: "margin-top:.75rem" },
      h("div", { clase: "tenue", estilo: "font-size:.9rem; margin-bottom:.25rem" }, "Mentalidad"),
      h("div", { clase: "segmentado", role: "group", "aria-label": "Mentalidad" },
        Object.entries(NOMBRE_MENTALIDAD).map(([clave, texto]) =>
          h("button", { type: "button", "aria-pressed": String(equipo.mentalidad === clave), onclick: () => cambiarMentalidad(clave) }, texto)))));
}

DIBUJAR.partido = () => {
  const p = st.partido;
  const t = st.partida.temporada;
  if (!p || p.estado === "FINALIZADO") {
    const proximo = !t.finalizada
      ? h("div", { clase: "panel" },
          h("h2", {}, `Jornada ${t.jornada_actual}: contra ${t.proximo_rival.nombre}`),
          h("p", { clase: "tenue" }, `${t.es_local ? "En casa" : "De visita en " + t.proximo_rival.ciudad}.${t.es_decisiva ? " Es el partido decisivo de la temporada." : ""}`),
          st.partida.eventos_pendientes ? h("div", { clase: "aviso error" }, "Hay asuntos de vestuario sin resolver. ",
            h("button", { clase: "boton pequeno", onclick: () => mostrar("vestuario") }, "Ir al vestuario")) : null,
          !st.partida.alineacion_definida ? h("div", { clase: "aviso error" }, "Todavía no guardas una alineación. ",
            h("button", { clase: "boton pequeno", onclick: () => mostrar("alineacion") }, "Ir a la alineación")) : null,
          h("button", { clase: "boton principal", onclick: iniciarPartido }, "Iniciar partido"))
      : h("div", { clase: "panel" }, h("h2", {}, t.ascendio ? "Temporada cerrada con ascenso" : "Temporada cerrada"),
          h("p", {}, `Sumaste ${t.puntos} puntos (meta: ${t.puntos_ascenso}).`),
          h("button", { clase: "boton", onclick: salir }, "Empezar otra carrera"));
    return h("div", {},
      p ? h("div", { estilo: "margin-bottom:1rem" }, marcador(p)) : null,
      proximo,
      p ? h("div", { estilo: "margin-top:1rem" }, cronica(p)) : null);
  }

  const equipo = equipoUsuario(p);
  const controles = h("div", { clase: "controles-partido" },
    p.estado === "EN_JUEGO"
      ? (st.jugando
          ? h("button", { clase: "boton principal", onclick: pausar, disabled: st.quierePausar }, st.quierePausar ? "Pausando…" : "Pausar para dar indicaciones")
          : h("button", { clase: "boton principal", onclick: jugar }, "Continuar simulación"))
      : h("button", { clase: "boton principal", onclick: reanudar }, "Reanudar partido"),
    p.es_decisivo ? h("span", { clase: "tenue", estilo: "align-self:center" }, "Partido decisivo: la reputación cuenta doble.") : null);

  return h("div", {},
    marcador(p),
    controles,
    h("div", { clase: "columnas" },
      h("div", {}, cancha(equipo.en_campo, { energia: true }), leyendaAnimo()),
      h("div", {}, p.estado === "PAUSADO" ? panelBanda(p) : null, h("div", { estilo: "margin-top:1rem" }, cronica(p)))));
};

// ------------------------------------------------------------------ Plantilla
CARGAR.plantilla = async () => {
  await cargarPartida();
  st.plantilla = await api(rutaPartida("/plantilla"));
};

async function elogiar(jugador) {
  try {
    const r = await api(rutaPartida(`/plantilla/${jugador.id}/elogio`), { metodo: "POST" });
    avisar("info", r.cambio_estado
      ? `${r.jugador.nombre} recibe el elogio con entusiasmo: ahora está ${ANIMO[r.jugador.estado_animo].toLowerCase()}.`
      : `${r.jugador.nombre} agradece el elogio (moral ${r.jugador.moral}).`);
  } catch (error) { avisarError(error); }
  mostrar("plantilla");
}

DIBUJAR.plantilla = () => h("div", { clase: "panel tabla-contenedor" },
  h("table", {},
    h("thead", {}, h("tr", {},
      h("th", {}, "Pos."), h("th", {}, "Jugador"), h("th", { clase: "num" }, "Edad"), h("th", { clase: "num" }, "Calidad"),
      h("th", { clase: "num" }, "Físico"), h("th", { clase: "num" }, "Moral"), h("th", {}, "Ánimo"), h("th", { clase: "num" }, "Rend."), h("th", {}, "Disponibilidad"))),
    h("tbody", {}, ordenarPorPosicion(st.plantilla).flatMap((j) => {
      const abierto = st.detalle === j.id;
      const fila = h("tr", { clase: "clicable", tabindex: "0", "aria-expanded": String(abierto),
        onclick: () => { st.detalle = abierto ? null : j.id; dibujar(); },
        onkeydown: (e) => { if (e.key === "Enter") { st.detalle = abierto ? null : j.id; dibujar(); } } },
        h("td", { clase: "posicion" }, j.posicion),
        h("td", {}, j.nombre, j.es_capitan ? h("span", { clase: "capitan", title: "Capitán" }, "C") : null),
        h("td", { clase: "num" }, j.edad), h("td", { clase: "num" }, j.calidad), h("td", { clase: "num" }, j.fisico),
        h("td", { clase: "num" }, j.moral), h("td", {}, chipAnimo(j.estado_animo)), h("td", { clase: "num" }, j.rendimiento.toFixed(1)),
        h("td", { clase: "tenue" }, j.motivo_inhabilitacion || "Disponible"));
      if (!abierto) return [fila];
      return [fila, h("tr", {}, h("td", { colspan: "9" },
        h("div", { clase: "fila", estilo: "justify-content:space-between; align-items:start" },
          h("div", {}, h("h3", {}, `Historia de ${j.nombre}`),
            h("ul", { clase: "cambios" }, j.historia.map((linea) => h("li", {}, linea))),
            h("p", { clase: "tenue", estilo: "margin-top:.5rem" }, `Personalidad: ${j.personalidad.toLowerCase()}. Salario ${dinero.format(j.salario)} al mes.`)),
          h("button", { clase: "boton", onclick: (e) => { e.stopPropagation(); elogiar(j); } }, "Elogiar en público"))))];
    }))));

// ------------------------------------------------------------------ Mercado (HU-02, HU-03)
CARGAR.mercado = async () => {
  await cargarPartida();
  [st.mercado, st.finanzas] = await Promise.all([api(rutaPartida("/mercado")), api(rutaPartida("/finanzas"))]);
};

async function enviarOjeadores() {
  try {
    const informes = await api(rutaPartida("/mercado/informes"));
    st.informes = Object.fromEntries(informes.map((i) => [i.jugador_id, i]));
    avisar("info", "Los ojeadores entregaron sus informes. La calidad es un rango estimado: más reputación, mejores ojeadores.");
  } catch (error) { avisarError(error); }
  dibujar();
}

async function ofertar(jugador, monto, salario) {
  try {
    const r = await api(rutaPartida(`/mercado/${jugador.id}/ofertas`), { metodo: "POST", cuerpo: { monto_transferencia: Number(monto), salario: Number(salario) } });
    st.respuestas[jugador.id] = r;
    st.aviso = null;
    if (r.aceptada) { st.ofertaAbierta = null; avisar("info", r.mensaje); return mostrar("mercado"); }
  } catch (error) { avisarError(error); }
  dibujar();
}

DIBUJAR.mercado = () => {
  const f = st.finanzas;
  return h("div", {},
    h("div", { clase: "panel fila", estilo: "justify-content:space-between" },
      h("div", {}, h("div", { clase: "tenue" }, "Presupuesto de fichajes"), h("strong", { clase: "num" }, dinero.format(f.presupuesto_fichajes))),
      h("div", {}, h("div", { clase: "tenue" }, "Margen salarial mensual"), h("strong", { clase: "num" }, dinero.format(f.margen_salarial))),
      h("button", { clase: "boton principal", onclick: enviarOjeadores }, "Enviar ojeadores")),
    st.mercado.length === 0 ? h("p", { clase: "tenue" }, "No quedan jugadores disponibles en el mercado.") :
    h("div", { clase: "panel tabla-contenedor", estilo: "margin-top:1rem" }, h("table", {},
      h("thead", {}, h("tr", {}, h("th", {}, "Pos."), h("th", {}, "Jugador"), h("th", { clase: "num" }, "Edad"), h("th", {}, "Club"),
        h("th", { clase: "num" }, "Valor"), h("th", { clase: "num" }, "Salario pedido"), h("th", {}, "Informe"), h("th", {}, ""))),
      h("tbody", {}, st.mercado.flatMap((j) => {
        const informe = st.informes[j.id];
        const respuesta = st.respuestas[j.id];
        const abierto = st.ofertaAbierta === j.id;
        const filas = [h("tr", {},
          h("td", { clase: "posicion" }, j.posicion), h("td", {}, j.nombre), h("td", { clase: "num" }, j.edad), h("td", {}, j.club_origen),
          h("td", { clase: "num" }, dinero.format(j.valor_mercado)), h("td", { clase: "num" }, dinero.format(j.salario_pretendido)),
          h("td", {}, informe ? h("div", {}, h("strong", { clase: "num" }, `Calidad ${informe.calidad_min}–${informe.calidad_max}`),
            h("div", { clase: "tenue", estilo: "font-size:.8rem" }, informe.recomendacion)) : h("span", { clase: "tenue" }, "Sin informe")),
          h("td", {}, h("button", { clase: "boton pequeno", "aria-expanded": String(abierto), onclick: () => { st.ofertaAbierta = abierto ? null : j.id; dibujar(); } }, "Ofertar")))];
        if (abierto) {
          const monto = h("input", { type: "number", min: "0", step: "10000", value: String(respuesta?.contraoferta_monto ?? j.valor_mercado) });
          const salario = h("input", { type: "number", min: "1", step: "1000", value: String(respuesta?.contraoferta_salario ?? j.salario_pretendido) });
          filas.push(h("tr", {}, h("td", { colspan: "8" },
            h("div", { clase: "fila" },
              h("label", {}, "Monto de transferencia", monto),
              h("label", {}, "Salario mensual", salario),
              h("button", { clase: "boton principal", onclick: () => ofertar(j, monto.value, salario.value) }, "Enviar oferta")),
            respuesta ? h("div", { clase: `aviso ${respuesta.aceptada ? "info" : "error"}` }, respuesta.mensaje,
              respuesta.contraoferta_monto ? ` Pide ${dinero.format(respuesta.contraoferta_monto)} y ${dinero.format(respuesta.contraoferta_salario)} al mes.` : "") : null)));
        }
        return filas;
      })))));
};

// ------------------------------------------------------------------ Finanzas (HU-06)
CARGAR.finanzas = async () => {
  await cargarPartida();
  st.finanzas = await api(rutaPartida("/finanzas"));
};

DIBUJAR.finanzas = () => {
  const f = st.finanzas;
  const uso = Math.min(100, Math.round((100 * f.masa_salarial) / f.limite_masa_salarial));
  return h("div", {},
    h("div", { clase: "columnas" },
      h("div", { clase: "panel" },
        h("h2", { clase: "num" }, dinero.format(f.presupuesto_fichajes)),
        h("p", { clase: "tenue" }, "Presupuesto disponible para fichajes. Las victorias y la taquilla lo aumentan."),
        h("h3", { clase: "num", estilo: "margin-top:1rem" }, `${dinero.format(f.masa_salarial)} de ${dinero.format(f.limite_masa_salarial)}`),
        h("p", { clase: "tenue" }, `Masa salarial mensual (${uso}% del límite). Ningún fichaje puede rebasar el límite.`),
        h("div", { clase: "barra" }, h("span", { estilo: `width:${uso}%` })),
        h("p", { clase: "num", estilo: "margin-top:1rem" }, `Ingresos: ${dinero.format(f.ingresos_totales)}. Gastos: ${dinero.format(f.gastos_totales)}.`)),
      h("div", { clase: "panel tabla-contenedor" },
        h("h3", {}, "Movimientos"),
        f.movimientos.length === 0 ? h("p", { clase: "tenue" }, "Todavía no hay movimientos. Juega la primera jornada.") :
        h("table", {},
          h("thead", {}, h("tr", {}, h("th", { clase: "num" }, "Jornada"), h("th", {}, "Concepto"), h("th", { clase: "num" }, "Monto"))),
          h("tbody", {}, f.movimientos.map((m) => h("tr", {},
            h("td", { clase: "num" }, m.jornada ?? ""), h("td", {}, m.concepto),
            h("td", { clase: "num", estilo: `color:${m.monto >= 0 ? "var(--motivado)" : "var(--alerta)"}` }, dinero.format(m.monto)))))))));
};

iniciar();
