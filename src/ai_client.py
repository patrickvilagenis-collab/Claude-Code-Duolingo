"""Cliente de Claude (API de Anthropic) para las funciones de IA.

Funciones:
  - resumir correos
  - extraer tareas/acciones de un texto
  - generar actas de reunión (MoM) en Markdown
  - planificar el día/semana a partir de calendario y tareas

Usa streaming para evitar timeouts en respuestas largas y "adaptive thinking"
en las tareas que se benefician de razonar (actas y planificación).
"""
from __future__ import annotations

import json
import re
from typing import Callable

import anthropic

# Tope de salida generoso (con streaming no hay riesgo de timeout).
_MAX_TOKENS = 8000


class AIClient:
    def __init__(self, api_key: str, model: str, language: str = "español") -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.language = language

    # ---- Núcleo -------------------------------------------------------
    def _complete(
        self,
        system: str,
        user: str,
        *,
        think: bool = False,
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        """Lanza una petición en streaming y devuelve el texto final.

        Si `on_delta` se proporciona, se llama con cada fragmento de texto
        (útil para ir mostrando la respuesta en la interfaz en tiempo real).
        """
        thinking = {"type": "adaptive"} if think else {"type": "disabled"}
        parts: list[str] = []
        with self.client.messages.stream(
            model=self.model,
            max_tokens=_MAX_TOKENS,
            thinking=thinking,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for text in stream.text_stream:
                parts.append(text)
                if on_delta:
                    on_delta(text)
        return "".join(parts).strip()

    # ---- Resumen de correo -------------------------------------------
    def summarize_email(self, subject: str, body: str) -> str:
        system = (
            f"Eres un asistente ejecutivo. Resume correos en {self.language} de forma "
            "clara y accionable. Sé conciso."
        )
        user = (
            "Resume este correo. Indica: (1) de qué trata en 1-2 frases, "
            "(2) puntos clave en viñetas, (3) si requiere acción por mi parte y el plazo.\n\n"
            f"ASUNTO: {subject}\n\nCUERPO:\n{body[:12000]}"
        )
        return self._complete(system, user, think=False)

    # ---- Extracción de tareas ----------------------------------------
    def extract_tasks(self, text: str) -> list[dict]:
        """Devuelve una lista de tareas como dicts con claves:
        title, due_date (YYYY-MM-DD o ''), priority (Alta|Media|Baja).
        """
        system = (
            "Eres un asistente que extrae tareas accionables de un texto. "
            "Responde SOLO con un array JSON válido, sin texto adicional ni vallas de código."
        )
        user = (
            "Extrae las tareas/acciones de este texto. Para cada una devuelve un objeto con: "
            '"title" (string, imperativo y breve), "due_date" (formato YYYY-MM-DD o "" si no se indica), '
            '"priority" ("Alta", "Media" o "Baja"). '
            "Si no hay tareas, devuelve []. \n\nTEXTO:\n" + text[:12000]
        )
        raw = self._complete(system, user, think=False)
        return _parse_json_array(raw)

    # ---- Acta de reunión (MoM) ---------------------------------------
    def generate_mom(self, meeting_title: str, notes: str, attendees: str = "") -> str:
        system = (
            f"Eres un asistente que redacta actas de reunión (Minutes of Meeting) en {self.language}, "
            "profesionales y bien estructuradas en Markdown."
        )
        user = (
            "Redacta un acta de reunión a partir de estas notas. Usa esta estructura en Markdown:\n"
            "# Acta de reunión\n"
            "**Título:** ...\n**Fecha:** (si se infiere)\n**Asistentes:** ...\n\n"
            "## Resumen\n(2-4 frases)\n\n"
            "## Temas tratados\n- ...\n\n"
            "## Decisiones\n- ...\n\n"
            "## Acciones (tareas)\n| Tarea | Responsable | Fecha límite |\n|---|---|---|\n| ... | ... | ... |\n\n"
            "## Próximos pasos\n- ...\n\n"
            f"TÍTULO: {meeting_title or '(sin título)'}\n"
            f"ASISTENTES: {attendees or '(no especificados)'}\n\n"
            f"NOTAS:\n{notes[:14000]}"
        )
        return self._complete(system, user, think=True)

    # ---- Planificación ------------------------------------------------
    def plan_schedule(self, events_text: str, tasks_text: str, horizon: str = "hoy") -> str:
        system = (
            f"Eres un asistente de planificación personal. Planificas en {self.language} de forma "
            "realista, considerando reuniones fijas y priorizando tareas por urgencia e importancia."
        )
        user = (
            f"Planifica mi jornada/semana ({horizon}). Tengo estas reuniones fijas y estas tareas pendientes. "
            "Genera un plan por bloques horarios que respete las reuniones, deje huecos realistas, "
            "agrupe tareas similares y señale qué priorizar. Añade al final 3 consejos breves.\n\n"
            f"REUNIONES (calendario):\n{events_text or '(ninguna)'}\n\n"
            f"TAREAS PENDIENTES:\n{tasks_text or '(ninguna)'}"
        )
        return self._complete(system, user, think=True)


# ---- Utilidades ------------------------------------------------------
def _parse_json_array(raw: str) -> list[dict]:
    """Extrae un array JSON aunque venga con vallas de código o texto alrededor."""
    s = raw.strip()
    # Quita vallas ```json ... ```
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        # Último intento: localizar el primer '[' y el último ']'.
        i, j = s.find("["), s.rfind("]")
        if i == -1 or j == -1 or j < i:
            return []
        try:
            data = json.loads(s[i : j + 1])
        except json.JSONDecodeError:
            return []
    if not isinstance(data, list):
        return []
    out: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        priority = str(item.get("priority", "Media")).strip().capitalize()
        if priority not in ("Alta", "Media", "Baja"):
            priority = "Media"
        out.append(
            {
                "title": title,
                "due_date": str(item.get("due_date", "")).strip(),
                "priority": priority,
            }
        )
    return out
