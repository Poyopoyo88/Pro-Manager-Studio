"""Motor de simulación de partidos (servicio de dominio).

Simula el encuentro minuto a minuto. Cada minuto:

1. Calcula la fuerza de ataque y defensa de cada equipo a partir del rendimiento
   de los jugadores en el campo, la forma del equipo y la mentalidad.
2. Sortea goles, tarjetas y lesiones.
3. Aplica fatiga cada 5 minutos.
4. Deja actuar a la IA del entrenador rival.

Cuando un jugador del usuario se lesiona o es expulsado, la simulación se detiene
(paso 1 del CU-01: «el sistema se detiene por una incidencia crítica»). También se
detiene en el descanso para que el DT revise al equipo.

Es determinista si recibe un ``random.Random`` con semilla, lo que permite
pruebas reproducibles. No conoce FastAPI ni la interfaz (restricción de la sección 4).
"""

from __future__ import annotations

import random

from .enums import EstadoPartido, Mentalidad, Personalidad, Posicion
from .errores import PartidoNoActivoError
from .ia_rival import IAEntrenadorRival
from .partido import IncidenciaJuego, Partido


class SimuladorPartido:
    PROB_GOL_BASE = 0.0135
    EXPONENTE_DOMINIO = 1.6
    PROB_GOL_MIN = 0.002
    PROB_GOL_MAX = 0.045
    VENTAJA_LOCAL = 1.08
    PROB_AMARILLA = 0.018
    PROB_ROJA = 0.0007
    PROB_LESION = 0.0035
    MINIMO_EN_CAMPO = 7
    RENDIMIENTO_PORTERO_IMPROVISADO = 25.0
    RENDIMIENTO_LINEA_VACIA = 35.0

    # (multiplicador de ataque, multiplicador de defensa)
    EFECTO_MENTALIDAD: dict[Mentalidad, tuple[float, float]] = {
        Mentalidad.DEFENSIVA: (0.85, 1.15),
        Mentalidad.EQUILIBRADA: (1.0, 1.0),
        Mentalidad.OFENSIVA: (1.15, 0.88),
    }

    PESO_GOLEADOR: dict[Posicion, float] = {
        Posicion.DELANTERO: 6.0,
        Posicion.MEDIOCAMPISTA: 3.0,
        Posicion.DEFENSA: 1.0,
        Posicion.PORTERO: 0.0,
    }

    def __init__(
        self,
        rng: random.Random | None = None,
        ia_rival: IAEntrenadorRival | None = None,
        pausar_en_descanso: bool = True,
    ) -> None:
        self.rng = rng or random.Random()
        self.ia_rival = ia_rival or IAEntrenadorRival()
        self.pausar_en_descanso = pausar_en_descanso

    # ------------------------------------------------------------------
    # Fuerza de los equipos
    # ------------------------------------------------------------------
    def fuerza(self, partido: Partido, club_id: str) -> tuple[float, float]:
        """Devuelve (ataque, defensa) del equipo en este momento del partido."""
        jugadores = partido.jugadores_en_campo(club_id)
        if not jugadores:
            return 1.0, 1.0
        por_linea: dict[Posicion, list[float]] = {p: [] for p in Posicion}
        for jugador in jugadores:
            por_linea[jugador.posicion].append(jugador.calcular_rendimiento_actual())

        def promedio(valores: list[float], defecto: float) -> float:
            return sum(valores) / len(valores) if valores else defecto

        portero = promedio(por_linea[Posicion.PORTERO], self.RENDIMIENTO_PORTERO_IMPROVISADO)
        defensa_l = promedio(por_linea[Posicion.DEFENSA], self.RENDIMIENTO_LINEA_VACIA)
        medio_l = promedio(por_linea[Posicion.MEDIOCAMPISTA], self.RENDIMIENTO_LINEA_VACIA)
        ataque_l = promedio(por_linea[Posicion.DELANTERO], self.RENDIMIENTO_LINEA_VACIA)

        n_def = len(por_linea[Posicion.DEFENSA])
        n_med = len(por_linea[Posicion.MEDIOCAMPISTA])
        n_del = len(por_linea[Posicion.DELANTERO])

        ataque = 0.55 * ataque_l + 0.35 * medio_l + 0.10 * defensa_l
        defensa = 0.30 * portero + 0.45 * defensa_l + 0.25 * medio_l
        # La forma del equipo pesa: más delanteros, más llegada; más defensas, más cierre.
        ataque *= 1 + 0.04 * (n_del - 2) + 0.02 * (n_med - 4)
        defensa *= 1 + 0.04 * (n_def - 4) + 0.02 * (n_med - 4)

        mult_ataque, mult_defensa = self.EFECTO_MENTALIDAD[partido.mentalidad[club_id]]
        inferioridad = len(jugadores) / 11
        return (
            max(1.0, ataque * mult_ataque * inferioridad),
            max(1.0, defensa * mult_defensa * inferioridad),
        )

    def probabilidad_gol(self, partido: Partido, club_id: str) -> float:
        ataque, _ = self.fuerza(partido, club_id)
        _, defensa_rival = self.fuerza(partido, partido.rival_de(club_id).id)
        prob = self.PROB_GOL_BASE * (ataque / defensa_rival) ** self.EXPONENTE_DOMINIO
        if club_id == partido.local.id:
            prob *= self.VENTAJA_LOCAL
        return max(self.PROB_GOL_MIN, min(self.PROB_GOL_MAX, prob))

    # ------------------------------------------------------------------
    # Simulación
    # ------------------------------------------------------------------
    def simular(self, partido: Partido, minutos: int = Partido.DURACION) -> list[IncidenciaJuego]:
        """Avanza ``minutos`` (o hasta una pausa / el final). Devuelve las incidencias nuevas."""
        if partido.estado != EstadoPartido.EN_JUEGO:
            raise PartidoNoActivoError(
                "El partido debe estar en juego para simular. Reanúdalo si está en pausa."
            )
        inicio = len(partido.incidencias)
        objetivo = min(partido.minuto + max(1, minutos), Partido.DURACION)
        while partido.estado == EstadoPartido.EN_JUEGO and partido.minuto < objetivo:
            partido.avanzar_minuto()
            self._simular_minuto(partido)
            if partido.minuto >= Partido.MINUTO_DESCANSO and not partido.descanso_realizado:
                partido.descanso_realizado = True
                if self.pausar_en_descanso and partido.estado == EstadoPartido.EN_JUEGO:
                    partido.pausar("Descanso. Revisa al equipo antes del segundo tiempo.")
        if partido.estado == EstadoPartido.EN_JUEGO and partido.minuto >= Partido.DURACION:
            partido.finalizar()
        return partido.incidencias[inicio:]

    def _simular_minuto(self, partido: Partido) -> None:
        clubes = (partido.local.id, partido.visitante.id)
        probabilidades = {cid: self.probabilidad_gol(partido, cid) for cid in clubes}
        for club_id in clubes:
            if self.rng.random() < probabilidades[club_id]:
                goleador = self._elegir_goleador(partido, club_id)
                if goleador:
                    partido.registrar_gol(club_id, goleador)
        for club_id in clubes:
            self._sortear_disciplina(partido, club_id)
            self._sortear_lesion(partido, club_id)
        if partido.minuto % 5 == 0:
            self._aplicar_fatiga(partido)
        for club_id in clubes:
            if club_id != partido.club_usuario_id:
                self.ia_rival.actuar(partido, club_id)

    def _elegir_goleador(self, partido: Partido, club_id: str) -> str | None:
        candidatos = partido.jugadores_en_campo(club_id)
        pesos = [
            self.PESO_GOLEADOR[j.posicion] * j.calcular_rendimiento_actual() for j in candidatos
        ]
        if not candidatos or sum(pesos) <= 0:
            return None
        return self.rng.choices(candidatos, weights=pesos, k=1)[0].id

    def _sortear_disciplina(self, partido: Partido, club_id: str) -> None:
        en_campo = partido.jugadores_en_campo(club_id)
        if len(en_campo) <= self.MINIMO_EN_CAMPO:
            return
        pesos = [2.0 if j.personalidad == Personalidad.TEMPERAMENTAL else 1.0 for j in en_campo]
        if self.rng.random() < self.PROB_AMARILLA:
            amonestado = self.rng.choices(en_campo, weights=pesos, k=1)[0]
            partido.registrar_tarjeta_amarilla(club_id, amonestado.id)
            self._pausar_si_critica(partido)
        elif self.rng.random() < self.PROB_ROJA:
            expulsado = self.rng.choices(en_campo, weights=pesos, k=1)[0]
            partido.expulsar(club_id, expulsado.id)
            self._pausar_si_critica(partido)

    def _sortear_lesion(self, partido: Partido, club_id: str) -> None:
        if self.rng.random() >= self.PROB_LESION:
            return
        sanos = [j for j in partido.jugadores_en_campo(club_id) if not j.lesionado]
        if not sanos:
            return
        lesionado = self.rng.choice(sanos)
        partido.registrar_lesion(club_id, lesionado.id, self.rng.randint(1, 3))
        self._pausar_si_critica(partido)

    def _pausar_si_critica(self, partido: Partido) -> None:
        ultima = partido.incidencias[-1]
        if ultima.critica and partido.estado == EstadoPartido.EN_JUEGO:
            partido.pausar(f"Incidencia crítica: {ultima.descripcion}", critica=True)

    def _aplicar_fatiga(self, partido: Partido) -> None:
        for club_id in (partido.local.id, partido.visitante.id):
            extra = 1 if partido.mentalidad[club_id] == Mentalidad.OFENSIVA else 0
            for jugador in partido.jugadores_en_campo(club_id):
                jugador.desgastar(1 + extra)
