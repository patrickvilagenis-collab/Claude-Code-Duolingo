"""Pestaña Planificador: combina calendario + tareas y pide a Claude un plan."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from .. import paths
from .util import run_async


class PlannerTab(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(top, text="Horizonte:").pack(side="left", padx=4)
        self.horizon = ctk.CTkOptionMenu(top, values=["hoy", "esta semana"], width=140)
        self.horizon.set("hoy")
        self.horizon.pack(side="left", padx=4)
        ctk.CTkButton(top, text="🧭 Planificar", command=self.plan).pack(side="left", padx=8)
        ctk.CTkButton(top, text="📤 Exportar .md", command=self.export).pack(side="right", padx=4)
        ctk.CTkLabel(
            top, text="Usa tu calendario y tus tareas pendientes para proponerte un plan.",
        ).pack(side="left", padx=8)

        self.output = ctk.CTkTextbox(self, wrap="word")
        self.output.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.output.insert(
            "1.0",
            "Pulsa «Planificar».\n\n"
            "Consejo: actualiza primero el Calendario y revisa tus Tareas para "
            "que el plan sea más preciso.",
        )

    def plan(self) -> None:
        try:
            ai = self.app.ai()
        except RuntimeError as e:
            messagebox.showwarning("IA no configurada", str(e))
            return

        events_text = self.app.calendar_tab.events_as_text()
        tasks_text = self.app.tasks_tab.tasks_as_text()
        if not events_text and not tasks_text:
            messagebox.showinfo(
                "Sin datos",
                "No hay eventos ni tareas. Actualiza el Calendario o añade tareas primero.",
            )
            return
        horizon = self.horizon.get()
        self._set_output("🧭 Planificando con Claude…\n")
        self.app.set_status("Generando plan…")

        def work():
            return ai.plan_schedule(events_text, tasks_text, horizon)

        run_async(
            self, work,
            on_done=lambda p: (self._set_output(p), self.app.set_status("Plan listo.")),
            on_error=self._err,
        )

    def export(self) -> None:
        content = self.output.get("1.0", "end").strip()
        if not content:
            return
        path = paths.exports_dir() / "plan.md"
        path.write_text(content, encoding="utf-8")
        messagebox.showinfo("Exportado", f"Plan guardado en:\n{path}")

    def _set_output(self, text: str) -> None:
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)

    def _err(self, exc: Exception) -> None:
        self.app.set_status("Error.")
        messagebox.showerror("Error", str(exc))
