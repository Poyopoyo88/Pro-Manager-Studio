"""Entidad Jugador.

Patrón GRASP *Information Expert*: el jugador conoce sus propios atributos, así que
es quien calcula su rendimiento actual y quien actualiza su moral.
"""

from __future__ import annotations

from .atributos import acotar, validar_atributo
from .enums import EstadoAnimo, EventoAnimo, Personalidad, Posicion
from .errores import DatoInvalidoError
from .estado_animo import siguiente_estado


class Jugador:
    # Peso de cada componente en el rendimiento base.
    PESO_CALIDAD = 0.6
    PESO_FISICO = 0.4

    # El estado de ánimo multiplica el rendimiento.
    MODIFICADOR_ESTADO: dict[EstadoAnimo, float] = {
        EstadoAnimo.MOTIVADO: 1.10,
        EstadoAnimo.ESTABLE: 1.00,
        EstadoAnimo.MOLESTO: 0.90,
        EstadoAnimo.REBELDE: 0.75,
    }

    # Amplificación de los impactos NEGATIVOS en la moral según personalidad.
    SENSIBILIDAD_NEGATIVA: dict[Personalidad, float] = {
        Personalidad.TEMPERAMENTAL: 1.5,
        Personalidad.AMBICIOSO: 1.2,
        Personalidad.RESERVADO: 1.0,
        Personalidad.PROFESIONAL: 0.75,
        Personalidad.LIDER: 0.6,
    }

    # Un jugador lesionado que sigue en el campo rinde al 30 %.
    FACTOR_LESION = 0.3

    def __init__(
        self,
        id: str,
        nombre: str,
        posicion: Posicion | str,
        calidad: int,
        fisico: int,
        moral: int,
        personalidad: Personalidad | str = Personalidad.PROFESIONAL,
        edad: int = 25,
        salario: int = 0,
        valor_mercado: int = 0,
        estado_animo: EstadoAnimo | str = EstadoAnimo.ESTABLE,
        es_capitan: bool = False,
        partidos_lesion: int = 0,
        partidos_suspension: int = 0,
        partidos_castigo: int = 0,
        partidos_sin_jugar: int = 0,
        historia: list[str] | None = None,
    ) -> None:
        if not id or not str(id).strip():
            raise DatoInvalidoError("El jugador necesita un identificador.")
        if not nombre or not str(nombre).strip():
            raise DatoInvalidoError("El jugador necesita un nombre.")
        if not 15 <= edad <= 45:
            raise DatoInvalidoError(f"La edad de {nombre} debe estar entre 15 y 45 años.")
        if salario < 0 or valor_mercado < 0:
            raise DatoInvalidoError("El salario y el valor de mercado no pueden ser negativos.")
        if min(partidos_lesion, partidos_suspension, partidos_castigo, partidos_sin_jugar) < 0:
            raise DatoInvalidoError("Los contadores de baja no pueden ser negativos.")

        self.id = str(id)
        self.nombre = nombre
        self.posicion = Posicion(posicion)
        self.personalidad = Personalidad(personalidad)
        self.edad = edad
        self.salario = salario
        self.valor_mercado = valor_mercado
        self.estado_animo = EstadoAnimo(estado_animo)
        self.es_capitan = es_capitan
        self.partidos_lesion = partidos_lesion
        self.partidos_suspension = partidos_suspension
        self.partidos_castigo = partidos_castigo
        self.partidos_sin_jugar = partidos_sin_jugar
        self.historia: list[str] = list(historia or [])
        # Los atributos pasan por los setters validados (RN-01).
        self.calidad = calidad
        self.fisico = fisico
        self.moral = moral

    # ------------------------------------------------------------------
    # Atributos con la regla RN-01 aplicada en cada asignación
    # ------------------------------------------------------------------
    @property
    def calidad(self) -> int:
        return self._calidad

    @calidad.setter
    def calidad(self, valor: int) -> None:
        self._calidad = validar_atributo("calidad", valor)

    @property
    def fisico(self) -> int:
        return self._fisico

    @fisico.setter
    def fisico(self, valor: int) -> None:
        self._fisico = validar_atributo("fisico", valor)

    @property
    def moral(self) -> int:
        return self._moral

    @moral.setter
    def moral(self, valor: int) -> None:
        self._moral = validar_atributo("moral", valor)

    # ------------------------------------------------------------------
    # Disponibilidad
    # ------------------------------------------------------------------
    @property
    def lesionado(self) -> bool:
        return self.partidos_lesion > 0

    @property
    def habilitado(self) -> bool:
        """Puede ser titular o ingresar de cambio."""
        return not self.lesionado and self.partidos_suspension == 0 and self.partidos_castigo == 0

    @property
    def convocable(self) -> bool:
        """Puede estar en la lista de suplentes (un castigado sí puede ir a la banca)."""
        return not self.lesionado and self.partidos_suspension == 0

    def motivo_inhabilitacion(self) -> str | None:
        if self.lesionado:
            return f"{self.nombre} está lesionado ({self.partidos_lesion} partido(s) de baja)."
        if self.partidos_suspension:
            return f"{self.nombre} está suspendido por la competición."
        if self.partidos_castigo:
            return f"{self.nombre} cumple una sanción interna del cuerpo técnico."
        return None

    # ------------------------------------------------------------------
    # Comportamiento (Information Expert)
    # ------------------------------------------------------------------
    def actualizar_moral(self, impacto: int) -> int:
        """Aplica un impacto a la moral y devuelve el cambio real.

        Los impactos negativos se amplifican o amortiguan según la personalidad.
        El resultado se satura en [1, 100] (RN-01).
        """
        efectivo: float = impacto
        if impacto < 0:
            efectivo = impacto * self.SENSIBILIDAD_NEGATIVA[self.personalidad]
        anterior = self._moral
        self._moral = acotar(self._moral + efectivo)
        return self._moral - anterior

    def calcular_rendimiento_actual(self) -> float:
        """Rendimiento en [1, 100] a partir de calidad, físico, moral y estado de ánimo."""
        base = self.PESO_CALIDAD * self._calidad + self.PESO_FISICO * self._fisico
        factor_moral = 0.7 + 0.6 * (self._moral / 100)
        rendimiento = base * factor_moral * self.MODIFICADOR_ESTADO[self.estado_animo]
        if self.lesionado:
            rendimiento *= self.FACTOR_LESION
        return round(max(1.0, min(100.0, rendimiento)), 2)

    def aplicar_evento_animo(self, evento: EventoAnimo) -> bool:
        """Dispara la máquina de estados. Devuelve ``True`` si el estado cambió."""
        nuevo = siguiente_estado(self.estado_animo, EventoAnimo(evento))
        cambio = nuevo != self.estado_animo
        self.estado_animo = nuevo
        return cambio

    def desgastar(self, cantidad: int) -> None:
        self._fisico = acotar(self._fisico - cantidad)

    def recuperar(self, cantidad: int) -> None:
        self._fisico = acotar(self._fisico + cantidad)

    def lesionar(self, partidos: int) -> None:
        if partidos < 1:
            raise DatoInvalidoError("Una lesión dura al menos un partido.")
        self.partidos_lesion = max(self.partidos_lesion, partidos)

    def suspender(self, partidos: int = 1) -> None:
        self.partidos_suspension += partidos

    def castigar(self, partidos: int = 1) -> None:
        """Sanción interna del DT: el jugador va a la banca y no puede ingresar."""
        self.partidos_castigo += partidos

    def registrar_historia(self, texto: str) -> None:
        self.historia.append(texto)

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"Jugador({self.id!r}, {self.nombre!r}, {self.posicion}, cal={self._calidad})"
