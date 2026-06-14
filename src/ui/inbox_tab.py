"""Pestaña Bandeja: lista de correos + resumen y extracción de tareas con IA."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from ..graph_client import MailMessage
from .util import fmt_datetime, run_async


class InboxTab(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app
        self.messages: list[MailMessage] = []
        self.selected: MailMessage | None = None
        self._body_cache: dict[str, str] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # Barra superior
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        ctk.CTkButton(top, text="🔄 Actualizar", command=self.refresh).pack(side="left", padx=4)
        ctk.CTkLabel(top, text="Tus correos más recientes de Microsoft 365").pack(side="left", padx=8)

        # Lista (izquierda)
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Correos")
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=4)

        # Detalle (derecha)
        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=4)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        btns = ctk.CTkFrame(right)
        btns.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ctk.CTkButton(btns, text="🧠 Resumir", command=self.summarize).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="📌 Extraer tareas", command=self.extract_tasks).pack(side="left", padx=4)

        self.detail = ctk.CTkTextbox(right, wrap="word")
        self.detail.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.detail.insert("1.0", "Selecciona un correo de la lista para verlo aquí.")
        self.detail.configure(state="disabled")

    # ---- Acciones -----------------------------------------------------
    def refresh(self) -> None:
        try:
            token = self.app.token()
        except RuntimeError as e:
            messagebox.showwarning("Sin sesión", str(e))
            return
        self.app.set_status("Cargando correos…")

        def work():
            return self.app.graph().get_messages(token, self.app.config_data.mail_fetch_count)

        run_async(self, work, on_done=self._populate, on_error=self._err)

    def _populate(self, messages: list[MailMessage]) -> None:
        self.messages = messages
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not messages:
            ctk.CTkLabel(self.list_frame, text="(Sin correos)").pack(pady=10)
        for m in messages:
            prefix = "● " if not m.is_read else "  "
            label = f"{prefix}{m.sender}\n{m.subject}\n{fmt_datetime(m.received)}"
            ctk.CTkButton(
                self.list_frame,
                text=label,
                anchor="w",
                fg_color=("gray85", "gray25") if m.is_read else ("#dbeafe", "#1e3a5f"),
                text_color=("black", "white"),
                command=lambda msg=m: self.select(msg),
            ).pack(fill="x", padx=4, pady=3)
        self.app.set_status(f"{len(messages)} correos cargados.")

    def select(self, msg: MailMessage) -> None:
        self.selected = msg
        self._set_detail(f"Cargando «{msg.subject}»…")
        if msg.id in self._body_cache:
            self._show_body(msg, self._body_cache[msg.id])
            return
        try:
            token = self.app.token()
        except RuntimeError as e:
            self._err(e)
            return

        def work():
            return self.app.graph().get_message_body(token, msg.id)

        run_async(
            self, work,
            on_done=lambda body: self._show_body(msg, body),
            on_error=self._err,
        )

    def _show_body(self, msg: MailMessage, body: str) -> None:
        self._body_cache[msg.id] = body
        header = f"De: {msg.sender}\nAsunto: {msg.subject}\nFecha: {fmt_datetime(msg.received)}\n{'-'*60}\n\n"
        self._set_detail(header + (body or "(Cuerpo vacío)"))

    def summarize(self) -> None:
        if not self.selected:
            messagebox.showinfo("Selecciona un correo", "Elige un correo de la lista primero.")
            return
        body = self._body_cache.get(self.selected.id, self.selected.preview)
        try:
            ai = self.app.ai()
        except RuntimeError as e:
            messagebox.showwarning("IA no configurada", str(e))
            return
        subject = self.selected.subject
        self.app.set_status("Resumiendo con Claude…")
        self._set_detail("🧠 Generando resumen…\n\n")

        def work():
            return ai.summarize_email(subject, body)

        run_async(
            self, work,
            on_done=lambda s: (self._set_detail(f"RESUMEN — {subject}\n{'='*60}\n\n{s}"),
                               self.app.set_status("Resumen listo.")),
            on_error=self._err,
        )

    def extract_tasks(self) -> None:
        if not self.selected:
            messagebox.showinfo("Selecciona un correo", "Elige un correo de la lista primero.")
            return
        body = self._body_cache.get(self.selected.id, self.selected.preview)
        try:
            ai = self.app.ai()
        except RuntimeError as e:
            messagebox.showwarning("IA no configurada", str(e))
            return
        text = f"{self.selected.subject}\n\n{body}"
        self.app.set_status("Extrayendo tareas con Claude…")

        def work():
            return ai.extract_tasks(text)

        run_async(self, work, on_done=self._save_tasks, on_error=self._err)

    def _save_tasks(self, tasks: list[dict]) -> None:
        if not tasks:
            messagebox.showinfo("Sin tareas", "No se encontraron tareas accionables en el correo.")
            self.app.set_status("Sin tareas detectadas.")
            return
        for t in tasks:
            self.app.storage.add_task(
                title=t["title"], due_date=t.get("due_date", ""),
                priority=t.get("priority", "Media"), source="correo",
            )
        self.app.tasks_tab.refresh()
        messagebox.showinfo(
            "Tareas añadidas",
            f"Se añadieron {len(tasks)} tarea(s) a la pestaña Tareas.",
        )
        self.app.set_status(f"{len(tasks)} tareas añadidas desde el correo.")

    # ---- Helpers ------------------------------------------------------
    def _set_detail(self, text: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", text)
        self.detail.configure(state="disabled")

    def _err(self, exc: Exception) -> None:
        self.app.set_status("Error.")
        messagebox.showerror("Error", str(exc))
