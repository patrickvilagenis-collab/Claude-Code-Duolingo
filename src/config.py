"""Carga y guardado de la configuración de la app.

La configuración incluye las credenciales de Azure AD (client_id, tenant_id)
y la API key de Anthropic. Se guarda en `data/config.json`.

Las claves también pueden venir de variables de entorno, lo que es útil para
no escribir secretos en disco:
  - ANTHROPIC_API_KEY
  - AZURE_CLIENT_ID
  - AZURE_TENANT_ID
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field

from . import paths

# Modelos de Claude disponibles en la app (el primero es el predeterminado).
AVAILABLE_MODELS = [
    "claude-opus-4-8",     # el más capaz (recomendado para actas y planificación)
    "claude-sonnet-4-6",   # equilibrio velocidad/calidad, más económico
    "claude-haiku-4-5",    # el más rápido y barato, para tareas simples
]

# Permisos delegados que la app solicita a Microsoft Graph (solo lectura).
GRAPH_SCOPES = ["User.Read", "Mail.Read", "Calendars.Read"]


@dataclass
class AppConfig:
    azure_client_id: str = ""
    # "common" sirve para cuentas de cualquier organización; pon el tenant_id
    # de tu empresa si tu IT lo exige.
    azure_tenant_id: str = "common"
    anthropic_api_key: str = ""
    model: str = AVAILABLE_MODELS[0]
    # Idioma de las respuestas de la IA.
    language: str = "español"
    # Número de correos a traer en cada actualización de la bandeja.
    mail_fetch_count: int = 25
    # Días hacia delante a mostrar en el calendario.
    calendar_days_ahead: int = 7
    appearance: str = "System"  # System | Dark | Light

    def is_graph_ready(self) -> bool:
        return bool(self.azure_client_id.strip())

    def is_ai_ready(self) -> bool:
        return bool(self.anthropic_api_key.strip())


def _apply_env_overrides(cfg: AppConfig) -> AppConfig:
    if paths.env("ANTHROPIC_API_KEY"):
        cfg.anthropic_api_key = paths.env("ANTHROPIC_API_KEY")
    if paths.env("AZURE_CLIENT_ID"):
        cfg.azure_client_id = paths.env("AZURE_CLIENT_ID")
    if paths.env("AZURE_TENANT_ID"):
        cfg.azure_tenant_id = paths.env("AZURE_TENANT_ID")
    return cfg


def load_config() -> AppConfig:
    path = paths.config_path()
    cfg = AppConfig()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            known = {f for f in AppConfig().__dict__}
            cfg = AppConfig(**{k: v for k, v in data.items() if k in known})
        except (json.JSONDecodeError, TypeError, ValueError):
            # Config corrupta: arrancamos con valores por defecto en vez de fallar.
            cfg = AppConfig()
    return _apply_env_overrides(cfg)


def save_config(cfg: AppConfig) -> None:
    paths.config_path().write_text(
        json.dumps(asdict(cfg), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
