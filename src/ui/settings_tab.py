"""Pestaña Ajustes: credenciales, modelo, sesión de Microsoft 365."""
from __future__ import annotations

import webbrowser

import customtkinter as ctk
from tkinter import messagebox

from ..config import AVAILABLE_MODELS
from .util import run_async


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app
        cfg = app.config_data

        container = ctk.CTkScrollableFrame(self)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- Microsoft 365 / Azure ----
        ctk.CTkLabel(
            container, text="Microsoft 365 (Azure AD)", font=("", 16, "bold")
        ).pack(anchor="w", pady=(6, 2))
        ctk.CTkLabel(
            container, justify="left", anchor="w",
            text="Registra una app en el Portal de Azure como cliente público y pega aquí su\n"
                 "Client ID. Tenant: 'common' o el ID de tu organización (ver README).",
        ).pack(anchor="w")

        self.client_id = self._field(container, "Client ID (Azure)", cfg.azure_client_id)
        self.tenant_id = self._field(container, "Tenant ID", cfg.azure_tenant_id or "common")

        sess = ctk.CTkFrame(container)
        sess.pack(fill="x", pady=6)
        ctk.CTkButton(sess, text="🔐 Iniciar sesión", command=self.sign_in).pack(side="left", padx=4)
        ctk.CTkButton(sess, text="🚪 Cerrar sesión", command=self.sign_out).pack(side="left", padx=4)
        self.sess_label = ctk.CTkLabel(sess, text="")
        self.sess_label.pack(side="left", padx=8)

        # ---- Anthropic / IA ----
        ctk.CTkLabel(
            container, text="Inteligencia Artificial (Claude)", font=("", 16, "bold")
        ).pack(anchor="w", pady=(14, 2))
        self.api_key = self._field(
            container, "API Key de Anthropic", cfg.anthropic_api_key, show="•"
        )

        modelf = ctk.CTkFrame(container)
        modelf.pack(fill="x", pady=4)
        ctk.CTkLabel(modelf, text="Modelo", width=160, anchor="w").pack(side="left", padx=4)
        self.model = ctk.CTkOptionMenu(modelf, values=AVAILABLE_MODELS, width=240)
        self.model.set(cfg.model)
        self.model.pack(side="left", padx=4)

        langf = ctk.CTkFrame(container)
        langf.pack(fill="x", pady=4)
        ctk.CTkLabel(langf, text="Idioma de la IA", width=160, anchor="w").pack(side="left", padx=4)
        self.language = ctk.CTkOptionMenu(
            langf, values=["español", "inglés", "catalán", "francés"], width=200
        )
        self.language.set(cfg.language)
        self.language.pack(side="left", padx=4)

        # ---- Preferencias ----
        ctk.CTkLabel(
            container, text="Preferencias", font=("", 16, "bold")
        ).pack(anchor="w", pady=(14, 2))

        self.mail_count = self._field(
            container, "Nº de correos a cargar", str(cfg.mail_fetch_count)
        )
        self.cal_days = self._field(
            container, "Días de calendario", str(cfg.calendar_days_ahead)
        )

        appf = ctk.CTkFrame(container)
        appf.pack(fill="x", pady=4)
        ctk.CTkLabel(appf, text="Apariencia", width=160, anchor="w").pack(side="left", padx=4)
        self.appearance = ctk.CTkOptionMenu(
            appf, values=["System", "Dark", "Light"], width=160, command=self._change_appearance
        )
        self.appearance.set(cfg.appearance)
        self.appearance.pack(side="left", padx=4)

        ctk.CTkButton(
            container, text="💾 Guardar ajustes", command=self.save, height=40
        ).pack(pady=16)

        self._update_session_label()

    # ---- Helpers de formulario ---------------------------------------
    def _field(self, parent, label: str, value: str, show: str | None = None) -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=label, width=160, anchor="w").pack(side="left", padx=4)
        entry = ctk.CTkEntry(row, width=380, show=show or "")
        entry.insert(0, value)
        entry.pack(side="left", padx=4, fill="x", expand=True)
        return entry

    # ---- Guardado -----------------------------------------------------
    def save(self) -> None:
        cfg = self.app.config_data
        cfg.azure_client_id = self.client_id.get().strip()
        cfg.azure_tenant_id = self.tenant_id.get().strip() or "common"
        cfg.anthropic_api_key = self.api_key.get().strip()
        cfg.model = self.model.get()
        cfg.language = self.language.get()
        cfg.appearance = self.appearance.get()
        cfg.mail_fetch_count = _safe_int(self.mail_count.get(), cfg.mail_fetch_count, 1, 100)
        cfg.calendar_days_ahead = _safe_int(self.cal_days.get(), cfg.calendar_days_ahead, 1, 31)
        self.app.save_config()
        self.app.reset_clients()
        self._update_session_label()
        messagebox.showinfo("Guardado", "Ajustes guardados correctamente.")
        self.app.set_status("Ajustes guardados.")

    def _change_appearance(self, value: str) -> None:
        ctk.set_appearance_mode(value)

    # ---- Sesión Microsoft 365 ----------------------------------------
    def sign_in(self) -> None:
        # Asegura que el client_id actual está aplicado antes de autenticar.
        self.app.config_data.azure_client_id = self.client_id.get().strip()
        self.app.config_data.azure_tenant_id = self.tenant_id.get().strip() or "common"
        if not self.app.config_data.is_graph_ready():
            messagebox.showwarning("Falta Client ID", "Introduce el Client ID de Azure primero.")
            return
        self.app.reset_clients()
        self.app.set_status("Iniciando sesión en Microsoft 365…")

        def on_code(user_code: str, uri: str) -> None:
            # Se llama desde el hilo de trabajo: reprogramar en el hilo de UI.
            self.after(0, lambda: self._show_device_code(user_code, uri))

        def work():
            return self.app.graph().sign_in_device_code(on_code)

        run_async(self, work, on_done=self._on_signed_in, on_error=self._err)

    def _show_device_code(self, user_code: str, uri: str) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Iniciar sesión en Microsoft 365")
        win.geometry("440x240")
        win.transient(self.winfo_toplevel())
        ctk.CTkLabel(win, text="Inicia sesión con tu cuenta corporativa", font=("", 15, "bold")).pack(pady=(16, 8))
        ctk.CTkLabel(win, text="1) Abre esta dirección:").pack()
        ctk.CTkLabel(win, text=uri, text_color="#3b82f6").pack()
        ctk.CTkLabel(win, text="2) Introduce este código:").pack(pady=(8, 0))
        code = ctk.CTkEntry(win, width=200, justify="center", font=("", 20, "bold"))
        code.insert(0, user_code)
        code.configure(state="readonly")
        code.pack(pady=6)

        def copy_code():
            self.clipboard_clear()
            self.clipboard_append(user_code)
            self.app.set_status("Código copiado al portapapeles.")

        btns = ctk.CTkFrame(win)
        btns.pack(pady=8)
        ctk.CTkButton(btns, text="📋 Copiar código", command=copy_code).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="🌐 Abrir navegador", command=lambda: webbrowser.open(uri)).pack(side="left", padx=4)
        self._device_win = win

    def _on_signed_in(self, token: str) -> None:
        self.app.set_token(token)
        if getattr(self, "_device_win", None) is not None:
            try:
                self._device_win.destroy()
            except Exception:
                pass
            self._device_win = None
        self._update_session_label()
        messagebox.showinfo("Conectado", "Sesión iniciada en Microsoft 365.")
        self.app.set_status("Conectado a Microsoft 365.")

    def sign_out(self) -> None:
        try:
            self.app.graph().sign_out()
        except Exception:
            pass
        self.app.set_token(None)
        self.app.reset_clients()
        self._update_session_label()
        self.app.set_status("Sesión cerrada.")

    def _update_session_label(self) -> None:
        connected = self.app._token is not None  # noqa: SLF001 - estado interno compartido
        self.sess_label.configure(
            text="● Conectado" if connected else "○ Sin sesión",
            text_color="#10b981" if connected else "#9ca3af",
        )

    def _err(self, exc: Exception) -> None:
        self.app.set_status("Error de autenticación.")
        messagebox.showerror("Error", str(exc))


def _safe_int(value: str, default: int, lo: int, hi: int) -> int:
    try:
        n = int(value)
    except (ValueError, TypeError):
        return default
    return max(lo, min(hi, n))
