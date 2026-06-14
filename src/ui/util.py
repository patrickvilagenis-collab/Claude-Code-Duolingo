"""Utilidades de interfaz: ejecución en segundo plano y formato de fechas."""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Callable

import tkinter as tk


def run_async(
    widget: tk.Misc,
    work: Callable[[], Any],
    on_done: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    """Ejecuta `work()` en un hilo y devuelve el resultado al hilo de la GUI.

    Tkinter no es thread-safe, por eso los callbacks se reprograman con
    `widget.after(...)` para correr en el hilo principal.
    """

    def runner() -> None:
        try:
            result = work()
        except Exception as exc:  # noqa: BLE001 - lo propagamos al callback
            if on_error is not None:
                widget.after(0, lambda e=exc: on_error(e))
            return
        if on_done is not None:
            widget.after(0, lambda r=result: on_done(r))

    threading.Thread(target=runner, daemon=True).start()


def fmt_datetime(iso: str) -> str:
    """Formatea un datetime ISO de Graph a algo legible en local."""
    if not iso:
        return ""
    try:
        # Graph usa 'Z' o offset; normalizamos.
        cleaned = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt.astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso


def fmt_time(iso: str) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%H:%M")
    except ValueError:
        return iso
