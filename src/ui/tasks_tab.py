"""Pestaña Tareas: gestor de tareas local (SQLite)."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from ..storage import PRIORITIES, STATUSES, Task


class TasksTab(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Formulario de alta
        form = ctk.CTkFrame(self)
        form.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.title_entry = ctk.CTkEntry(form, placeholder_text="Nueva tarea…", width=320)
        self.title_entry.pack(side="left", padx=4)
        self.due_entry = ctk.CTkEntry(form, placeholder_text="AAAA-MM-DD", width=120)
        self.due_entry.pack(side="left", padx=4)
        self.prio_menu = ctk.CTkOptionMenu(form, values=PRIORITIES, width=100)
        self.prio_menu.set("Media")
        self.prio_menu.pack(side="left", padx=4)
        ctk.CTkButton(form, text="➕ Añadir", command=self.add_task).pack(side="left", padx=4)

        # Filtros
        filt = ctk.CTkFrame(self)
        filt.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        self.show_done = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            filt, text="Mostrar completadas", variable=self.show_done, command=self.refresh
        ).pack(side="left", padx=4)
        ctk.CTkButton(filt, text="🔄 Refrescar", command=self.refresh).pack(side="right", padx=4)

        # Lista
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Tareas")
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)

        self.refresh()

    def add_task(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            return
        due = self.due_entry.get().strip()
        self.app.storage.add_task(
            title=title, due_date=due, priority=self.prio_menu.get(), source="manual"
        )
        self.title_entry.delete(0, "end")
        self.due_entry.delete(0, "end")
        self.refresh()
        self.app.set_status("Tarea añadida.")

    def refresh(self) -> None:
        tasks = self.app.storage.list_tasks(include_done=self.show_done.get())
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not tasks:
            ctk.CTkLabel(self.list_frame, text="(Sin tareas)").pack(pady=10)
            return
        for t in tasks:
            self._render_task(t)

    def _render_task(self, t: Task) -> None:
        row = ctk.CTkFrame(self.list_frame)
        row.pack(fill="x", padx=4, pady=3)

        color = {"Alta": "#ef4444", "Media": "#f59e0b", "Baja": "#10b981"}.get(t.priority, "#888")
        ctk.CTkLabel(row, text="●", text_color=color, width=20).pack(side="left")

        due = f"  ⏰ {t.due_date}" if t.due_date else ""
        strike = "  ✓" if t.status == "Hecha" else ""
        label = f"{t.title}{due}   [{t.source}]{strike}"
        ctk.CTkLabel(row, text=label, anchor="w", justify="left").pack(
            side="left", fill="x", expand=True, padx=4
        )

        status = ctk.CTkOptionMenu(
            row, values=STATUSES, width=110,
            command=lambda v, tid=t.id: self._set_status(tid, v),
        )
        status.set(t.status)
        status.pack(side="right", padx=4)
        ctk.CTkButton(
            row, text="🗑", width=36, fg_color="transparent",
            command=lambda tid=t.id: self._delete(tid),
        ).pack(side="right", padx=2)

    def _set_status(self, task_id: int, status: str) -> None:
        self.app.storage.update_task_status(task_id, status)
        if not self.show_done.get() and status == "Hecha":
            self.refresh()

    def _delete(self, task_id: int) -> None:
        self.app.storage.delete_task(task_id)
        self.refresh()

    def tasks_as_text(self) -> str:
        tasks = self.app.storage.list_tasks(include_done=False)
        return "\n".join(
            f"- [{t.priority}] {t.title}" + (f" (límite {t.due_date})" if t.due_date else "")
            for t in tasks
        )
