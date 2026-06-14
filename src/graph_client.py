"""Cliente de Microsoft Graph para leer correo y calendario.

Autenticación: flujo "device code" con MSAL (cliente público). No requiere
secreto de cliente, ideal para una app portable. La caché de token se guarda
cifrada-por-usuario en `data/token_cache.bin`, de modo que no tengas que
iniciar sesión cada vez.

Necesitas registrar una app en Azure AD (Portal de Azure) como cliente público
y habilitar "Allow public client flows". Los permisos delegados que usa son:
User.Read, Mail.Read, Calendars.Read.  Ver README.md para el paso a paso.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

import msal
import requests

from . import paths
from .config import AppConfig, GRAPH_SCOPES

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_AUTHORITY = "https://login.microsoftonline.com/{tenant}"
_TIMEOUT = 30


@dataclass
class MailMessage:
    id: str
    subject: str
    sender: str
    received: str       # ISO datetime
    preview: str
    is_read: bool
    web_link: str


@dataclass
class CalendarEvent:
    id: str
    subject: str
    start: str          # ISO datetime
    end: str
    location: str
    organizer: str
    is_online: bool
    web_link: str


class GraphError(RuntimeError):
    pass


class GraphClient:
    """Encapsula auth + llamadas REST a Microsoft Graph."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._cache = msal.SerializableTokenCache()
        self._cache_file = paths.token_cache_path()
        if self._cache_file.exists():
            try:
                self._cache.deserialize(self._cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass  # caché ilegible: se regenerará al iniciar sesión
        self._app = msal.PublicClientApplication(
            client_id=config.azure_client_id,
            authority=_AUTHORITY.format(tenant=config.azure_tenant_id or "common"),
            token_cache=self._cache,
        )

    # ---- Autenticación ------------------------------------------------
    def _persist_cache(self) -> None:
        if self._cache.has_state_changed:
            self._cache_file.write_text(self._cache.serialize(), encoding="utf-8")

    def has_account(self) -> bool:
        return bool(self._app.get_accounts())

    def acquire_token_silent(self) -> str | None:
        """Devuelve un token sin interacción si hay una sesión válida."""
        accounts = self._app.get_accounts()
        if not accounts:
            return None
        result = self._app.acquire_token_silent(GRAPH_SCOPES, account=accounts[0])
        self._persist_cache()
        if result and "access_token" in result:
            return result["access_token"]
        return None

    def sign_in_device_code(self, on_code: Callable[[str, str], None]) -> str:
        """Inicia sesión con device code.

        `on_code(user_code, verification_uri)` se llama para que muestres al
        usuario el código y la URL donde introducirlo. Bloquea hasta que el
        usuario completa el login en el navegador (o caduca).
        """
        flow = self._app.initiate_device_flow(scopes=GRAPH_SCOPES)
        if "user_code" not in flow:
            raise GraphError(
                "No se pudo iniciar el flujo de autenticación. "
                "Revisa el Client ID y que la app permita 'public client flows'.\n"
                f"Detalle: {flow.get('error_description', flow)}"
            )
        on_code(flow["user_code"], flow.get("verification_uri", "https://microsoft.com/devicelogin"))
        result = self._app.acquire_token_by_device_flow(flow)  # bloqueante
        self._persist_cache()
        if "access_token" not in result:
            raise GraphError(
                f"Error de autenticación: {result.get('error_description', result)}"
            )
        return result["access_token"]

    def sign_out(self) -> None:
        for acc in self._app.get_accounts():
            self._app.remove_account(acc)
        self._persist_cache()
        try:
            if self._cache_file.exists():
                self._cache_file.unlink()
        except OSError:
            pass

    # ---- Llamadas a la API -------------------------------------------
    def _get(self, token: str, url: str) -> dict:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=_TIMEOUT,
        )
        if resp.status_code == 401:
            raise GraphError("Sesión caducada. Vuelve a iniciar sesión en Ajustes.")
        if not resp.ok:
            raise GraphError(f"Graph {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def get_messages(self, token: str, top: int = 25) -> list[MailMessage]:
        url = (
            f"{GRAPH_BASE}/me/messages"
            f"?$top={int(top)}"
            "&$select=subject,from,receivedDateTime,bodyPreview,isRead,webLink"
            "&$orderby=receivedDateTime desc"
        )
        data = self._get(token, url)
        out: list[MailMessage] = []
        for m in data.get("value", []):
            sender = (
                m.get("from", {})
                .get("emailAddress", {})
                .get("name")
                or m.get("from", {}).get("emailAddress", {}).get("address", "")
                or "(desconocido)"
            )
            out.append(
                MailMessage(
                    id=m.get("id", ""),
                    subject=m.get("subject") or "(sin asunto)",
                    sender=sender,
                    received=m.get("receivedDateTime", ""),
                    preview=(m.get("bodyPreview") or "").strip(),
                    is_read=bool(m.get("isRead")),
                    web_link=m.get("webLink", ""),
                )
            )
        return out

    def get_message_body(self, token: str, message_id: str) -> str:
        url = f"{GRAPH_BASE}/me/messages/{message_id}?$select=subject,body"
        data = self._get(token, url)
        body = data.get("body", {})
        content = body.get("content", "")
        if body.get("contentType") == "html":
            content = _strip_html(content)
        return content.strip()

    def get_calendar_events(self, token: str, days_ahead: int = 7) -> list[CalendarEvent]:
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=max(1, days_ahead))
        url = (
            f"{GRAPH_BASE}/me/calendarView"
            f"?startDateTime={now.isoformat()}"
            f"&endDateTime={end.isoformat()}"
            "&$select=subject,start,end,location,organizer,isOnlineMeeting,webLink"
            "&$orderby=start/dateTime"
            "&$top=100"
        )
        data = self._get(token, url)
        out: list[CalendarEvent] = []
        for e in data.get("value", []):
            out.append(
                CalendarEvent(
                    id=e.get("id", ""),
                    subject=e.get("subject") or "(sin título)",
                    start=e.get("start", {}).get("dateTime", ""),
                    end=e.get("end", {}).get("dateTime", ""),
                    location=e.get("location", {}).get("displayName", "") or "",
                    organizer=e.get("organizer", {})
                    .get("emailAddress", {})
                    .get("name", "") or "",
                    is_online=bool(e.get("isOnlineMeeting")),
                    web_link=e.get("webLink", ""),
                )
            )
        return out


def _strip_html(html: str) -> str:
    """Convierte HTML básico a texto plano legible (sin dependencias extra)."""
    import re
    from html import unescape

    text = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"(?i)</(div|tr|li|h[1-6])>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    # Colapsa líneas en blanco excesivas.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
