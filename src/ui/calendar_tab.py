"""Pestaña Calendario: próximos eventos de Microsoft 365."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from ..graph_client import CalendarEvent
from .util import fmt_datetime, run_async


class CalendarTab(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app
        self.events: list[CalendarEvent] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ctk.CTkButton(top, text="🔄 Actualizar", command=self.refresh).pack(side="left", padx=4)
        ctk.CTkLabel(
            top, text=f"Próximos {self.app.config_data.calendar_days_ahead} días"
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            top, text="📌 Crear tareas de preparación", command=self.prep_tasks
        ).pack(side="right", padx=4)

        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Eventos")
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

    def refresh(self) -> None:
        try:
            token = self.app.token()
        except RuntimeError as e:
            messagebox.showwarning("Sin sesión", str(e))
            return
        self.app.set_status("Cargando calendario…")

        def work():
            return self.app.graph().get_calendar_events(
                token, self.app.config_data.calendar_days_ahead
            )

        run_async(self, work, on_done=self._populate, on_error=self._err)

    def _populate(self, events: list[CalendarEvent]) -> None:
        self.events = events
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not events:
            ctk.CTkLabel(self.list_frame, text="(Sin eventos próximos)").pack(pady=10)
        for e in events:
            online = "  💻 En línea" if e.is_online else ""
            loc = f"  📍 {e.location}" if e.location else ""
            text = (
                f"🕑 {fmt_datetime(e.start)} → {fmt_datetime(e.end)}\n"
                f"{e.subject}\n"
                f"Organiza: {e.organizer or '—'}{loc}{online}"
            )
            ctk.CTkLabel(
                self.list_frame, text=text, anchor="w", justify="left",
                fg_color=("gray85", "gray25"), corner_radius=6,
            ).pack(fill="x", padx=4, pady=3, ipady=4)
        self.app.set_status(f"{len(events)} eventos cargados.")

    def prep_tasks(self) -> None:
        """Crea una tarea de preparación por cada reunión próxima."""
        if not self.events:
            messagebox.showinfo("Sin eventos", "Actualiza el calendario primero.")
            return
        count = 0
        for e in self.events:
            self.app.storage.add_task(
                title=f"Preparar reunión: {e.subject}",
                due_date="",
                priority="Media",
                source="reunión",
                notes=f"Inicio: {fmt_datetime(e.start)} · {e.location or 'sin ubicación'}",
            )
            count += 1
        self.app.tasks_tab.refresh()
        messagebox.showinfo("Listo", f"Se crearon {count} tareas de preparación.")
        self.app.set_status(f"{count} tareas de preparación creadas.")

    def events_as_text(self) -> str:
        return "\n".join(
            f"- {fmt_datetime(e.start)}–{fmt_datetime(e.end)}: {e.subject}"
            f" ({e.organizer or 'sin organizador'})"
            for e in self.events
        )

    def _err(self, exc: Exception) -> None:
        self.app.set_status("Error.")
        messagebox.showerror("Error", str(exc))
