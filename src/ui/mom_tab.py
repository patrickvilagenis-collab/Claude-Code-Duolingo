"""Pestaña Actas (MoM): genera actas de reunión con IA y las guarda/exporta."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from .. import paths
from ..storage import Minute
from .util import run_async


class MomTab(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app
        self.current_minute_id: int | None = None

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- Columna izquierda: editor + salida ----
        left = ctk.CTkFrame(self)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(3, weight=1)

        meta = ctk.CTkFrame(left)
        meta.grid(row=0, column=0, sticky="ew", pady=4)
        self.title_entry = ctk.CTkEntry(meta, placeholder_text="Título de la reunión", width=280)
        self.title_entry.pack(side="left", padx=4)
        self.attendees_entry = ctk.CTkEntry(meta, placeholder_text="Asistentes (coma)", width=240)
        self.attendees_entry.pack(side="left", padx=4)

        ctk.CTkLabel(left, text="Notas de la reunión (pega aquí lo que tengas):").grid(
            row=1, column=0, sticky="w", padx=4
        )
        self.notes = ctk.CTkTextbox(left, height=140, wrap="word")
        self.notes.grid(row=2, column=0, sticky="ew", padx=4, pady=4)

        actions = ctk.CTkFrame(left)
        actions.grid(row=4, column=0, sticky="ew", pady=4)
        ctk.CTkButton(actions, text="🪄 Generar acta", command=self.generate).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="💾 Guardar", command=self.save).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="📤 Exportar .md", command=self.export).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="📌 Extraer tareas", command=self.extract_tasks).pack(side="left", padx=4)

        self.output = ctk.CTkTextbox(left, wrap="word")
        self.output.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)

        # ---- Columna derecha: actas guardadas ----
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        ctk.CTkButton(right, text="🔄 Recargar lista", command=self.refresh).grid(
            row=0, column=0, sticky="ew", padx=4, pady=4
        )
        self.saved_frame = ctk.CTkScrollableFrame(right, label_text="Actas guardadas")
        self.saved_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        self.refresh()

    # ---- Acciones -----------------------------------------------------
    def generate(self) -> None:
        notes = self.notes.get("1.0", "end").strip()
        if not notes:
            messagebox.showinfo("Faltan notas", "Escribe o pega las notas de la reunión.")
            return
        try:
            ai = self.app.ai()
        except RuntimeError as e:
            messagebox.showwarning("IA no configurada", str(e))
            return
        title = self.title_entry.get().strip()
        attendees = self.attendees_entry.get().strip()
        self.current_minute_id = None
        self._set_output("🪄 Generando acta con Claude…\n")
        self.app.set_status("Generando acta…")

        def work():
            return ai.generate_mom(title, notes, attendees)

        run_async(
            self, work,
            on_done=lambda md: (self._set_output(md), self.app.set_status("Acta generada.")),
            on_error=self._err,
        )

    def save(self) -> None:
        content = self.output.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Nada que guardar", "Primero genera o escribe un acta.")
            return
        title = self.title_entry.get().strip() or "Acta sin título"
        self.current_minute_id = self.app.storage.add_minute(title, content)
        self.refresh()
        self.app.set_status("Acta guardada.")

    def export(self) -> None:
        content = self.output.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Nada que exportar", "Primero genera o escribe un acta.")
            return
        title = (self.title_entry.get().strip() or "acta").replace(" ", "_")
        safe = "".join(c for c in title if c.isalnum() or c in ("_", "-"))
        path = paths.exports_dir() / f"{safe or 'acta'}.md"
        path.write_text(content, encoding="utf-8")
        messagebox.showinfo("Exportado", f"Acta guardada en:\n{path}")
        self.app.set_status(f"Exportado a {path.name}.")

    def extract_tasks(self) -> None:
        content = self.output.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Sin acta", "Genera un acta primero.")
            return
        try:
            ai = self.app.ai()
        except RuntimeError as e:
            messagebox.showwarning("IA no configurada", str(e))
            return
        self.app.set_status("Extrayendo tareas del acta…")

        def work():
            return ai.extract_tasks(content)

        run_async(self, work, on_done=self._save_tasks, on_error=self._err)

    def _save_tasks(self, tasks: list[dict]) -> None:
        if not tasks:
            messagebox.showinfo("Sin tareas", "No se detectaron tareas en el acta.")
            return
        for t in tasks:
            self.app.storage.add_task(
                title=t["title"], due_date=t.get("due_date", ""),
                priority=t.get("priority", "Media"), source="reunión",
            )
        self.app.tasks_tab.refresh()
        messagebox.showinfo("Tareas añadidas", f"Se añadieron {len(tasks)} tarea(s).")

    # ---- Actas guardadas ---------------------------------------------
    def refresh(self) -> None:
        for w in self.saved_frame.winfo_children():
            w.destroy()
        minutes = self.app.storage.list_minutes()
        if not minutes:
            ctk.CTkLabel(self.saved_frame, text="(No hay actas guardadas)").pack(pady=10)
            return
        for m in minutes:
            self._render_saved(m)

    def _render_saved(self, m: Minute) -> None:
        row = ctk.CTkFrame(self.saved_frame)
        row.pack(fill="x", padx=4, pady=3)
        ctk.CTkButton(
            row, text=f"{m.title}\n{m.created_at[:16]}", anchor="w",
            command=lambda mm=m: self._load(mm),
        ).pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkButton(
            row, text="🗑", width=36, fg_color="transparent",
            command=lambda mid=m.id: self._delete(mid),
        ).pack(side="right", padx=2)

    def _load(self, m: Minute) -> None:
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, m.title)
        self._set_output(m.content)
        self.current_minute_id = m.id
        self.app.set_status(f"Acta «{m.title}» cargada.")

    def _delete(self, minute_id: int) -> None:
        self.app.storage.delete_minute(minute_id)
        self.refresh()

    # ---- Helpers ------------------------------------------------------
    def _set_output(self, text: str) -> None:
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)

    def _err(self, exc: Exception) -> None:
        self.app.set_status("Error.")
        messagebox.showerror("Error", str(exc))
