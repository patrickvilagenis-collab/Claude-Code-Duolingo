"""Ventana principal de la aplicación."""
from __future__ import annotations

import customtkinter as ctk

from .. import __app_name__, __version__
from ..ai_client import AIClient
from ..config import AppConfig, load_config, save_config
from ..graph_client import GraphClient
from ..storage import Storage
from .calendar_tab import CalendarTab
from .inbox_tab import InboxTab
from .mom_tab import MomTab
from .planner_tab import PlannerTab
from .settings_tab import SettingsTab
from .tasks_tab import TasksTab


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.config_data: AppConfig = load_config()
        self.storage = Storage()
        self._graph: GraphClient | None = None
        self._token: str | None = None

        ctk.set_appearance_mode(self.config_data.appearance)
        ctk.set_default_color_theme("blue")

        self.title(f"{__app_name__} v{__version__}")
        self.geometry("1080x720")
        self.minsize(900, 600)

        self._build_tabs()
        self._build_status_bar()

        # Intento de re-login silencioso al arrancar (si ya había sesión).
        self._try_silent_signin()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- Construcción de UI ------------------------------------------
    def _build_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        self.tabview.add("📥 Bandeja")
        self.tabview.add("📅 Calendario")
        self.tabview.add("✅ Tareas")
        self.tabview.add("📝 Actas (MoM)")
        self.tabview.add("🗓 Planificador")
        self.tabview.add("⚙ Ajustes")

        self.inbox_tab = InboxTab(self.tabview.tab("📥 Bandeja"), self)
        self.calendar_tab = CalendarTab(self.tabview.tab("📅 Calendario"), self)
        self.tasks_tab = TasksTab(self.tabview.tab("✅ Tareas"), self)
        self.mom_tab = MomTab(self.tabview.tab("📝 Actas (MoM)"), self)
        self.planner_tab = PlannerTab(self.tabview.tab("🗓 Planificador"), self)
        self.settings_tab = SettingsTab(self.tabview.tab("⚙ Ajustes"), self)

        for tab in (
            self.inbox_tab, self.calendar_tab, self.tasks_tab,
            self.mom_tab, self.planner_tab, self.settings_tab,
        ):
            tab.pack(fill="both", expand=True)

    def _build_status_bar(self) -> None:
        bar = ctk.CTkFrame(self, height=28)
        bar.pack(fill="x", padx=10, pady=(0, 8))
        self.status_var = ctk.StringVar(value="Listo.")
        ctk.CTkLabel(bar, textvariable=self.status_var, anchor="w").pack(
            side="left", padx=10, fill="x", expand=True
        )
        self.session_var = ctk.StringVar(value="Sin sesión")
        ctk.CTkLabel(bar, textvariable=self.session_var, anchor="e").pack(side="right", padx=10)

    def set_status(self, text: str) -> None:
        self.status_var.set(text)
        self.update_idletasks()

    def _update_session_label(self) -> None:
        if self._token:
            self.session_var.set("Microsoft 365: conectado")
        else:
            self.session_var.set("Sin sesión")

    # ---- Estado compartido -------------------------------------------
    def save_config(self) -> None:
        save_config(self.config_data)

    def reset_clients(self) -> None:
        """Tras cambiar ajustes: descarta clientes cacheados."""
        self._graph = None
        self._token = None
        self._update_session_label()

    def graph(self) -> GraphClient:
        if not self.config_data.is_graph_ready():
            raise RuntimeError(
                "Falta el Client ID de Azure. Ve a Ajustes y configúralo."
            )
        if self._graph is None:
            self._graph = GraphClient(self.config_data)
        return self._graph

    def token(self) -> str:
        """Token de acceso vigente; lo refresca en silencio si puede."""
        if self._token:
            return self._token
        tok = self.graph().acquire_token_silent()
        if not tok:
            raise RuntimeError(
                "No hay sesión de Microsoft 365. Ve a Ajustes e inicia sesión."
            )
        self._token = tok
        self._update_session_label()
        return tok

    def set_token(self, token: str | None) -> None:
        self._token = token
        self._update_session_label()

    def ai(self) -> AIClient:
        if not self.config_data.is_ai_ready():
            raise RuntimeError(
                "Falta la API key de Anthropic. Ve a Ajustes y configúrala."
            )
        return AIClient(
            api_key=self.config_data.anthropic_api_key,
            model=self.config_data.model,
            language=self.config_data.language,
        )

    def _try_silent_signin(self) -> None:
        if not self.config_data.is_graph_ready():
            return
        try:
            tok = self.graph().acquire_token_silent()
            if tok:
                self.set_token(tok)
                self.set_status("Sesión de Microsoft 365 restaurada.")
        except Exception:
            pass  # sin sesión previa; el usuario iniciará desde Ajustes

    def _on_close(self) -> None:
        try:
            self.storage.close()
        finally:
            self.destroy()
