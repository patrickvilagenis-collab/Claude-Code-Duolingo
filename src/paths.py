"""Resolución de rutas para datos persistentes.

La app es portable: guarda configuración, caché de token y base de datos en
una carpeta `data/` junto al ejecutable (o junto al proyecto en desarrollo).
Así puedes copiar la carpeta entera a otro ordenador y conservar tus datos,
o borrar `data/` para empezar de cero.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def base_dir() -> Path:
    """Carpeta donde vive el ejecutable (o el proyecto en desarrollo)."""
    if getattr(sys, "frozen", False):  # empaquetado con PyInstaller
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """Carpeta `data/` portable; se crea si no existe."""
    d = base_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return data_dir() / "config.json"


def token_cache_path() -> Path:
    return data_dir() / "token_cache.bin"


def db_path() -> Path:
    return data_dir() / "asistente.db"


def exports_dir() -> Path:
    d = data_dir() / "exports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)
