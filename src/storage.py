"""Almacenamiento local en SQLite para tareas y actas (MoM).

Todo es local y portable: vive en `data/asistente.db`.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from . import paths

PRIORITIES = ["Alta", "Media", "Baja"]
STATUSES = ["Pendiente", "En curso", "Hecha"]


@dataclass
class Task:
    id: int
    title: str
    notes: str
    due_date: str       # ISO date 'YYYY-MM-DD' o '' si no hay
    priority: str
    status: str
    source: str         # 'manual', 'correo', 'reunión'…
    created_at: str


@dataclass
class Minute:
    id: int
    title: str
    content: str        # markdown
    created_at: str


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Storage:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(str(paths.db_path()))
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                notes      TEXT NOT NULL DEFAULT '',
                due_date   TEXT NOT NULL DEFAULT '',
                priority   TEXT NOT NULL DEFAULT 'Media',
                status     TEXT NOT NULL DEFAULT 'Pendiente',
                source     TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS minutes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    # ---- Tareas -------------------------------------------------------
    def add_task(
        self,
        title: str,
        notes: str = "",
        due_date: str = "",
        priority: str = "Media",
        status: str = "Pendiente",
        source: str = "manual",
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO tasks (title, notes, due_date, priority, status, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title.strip(), notes.strip(), due_date, priority, status, source, _now()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_tasks(self, include_done: bool = True) -> list[Task]:
        cur = self.conn.cursor()
        q = "SELECT * FROM tasks"
        if not include_done:
            q += " WHERE status != 'Hecha'"
        # Orden: por estado (pendientes primero), prioridad, fecha.
        q += """ ORDER BY
                   CASE status WHEN 'Hecha' THEN 1 ELSE 0 END,
                   CASE priority WHEN 'Alta' THEN 0 WHEN 'Media' THEN 1 ELSE 2 END,
                   CASE WHEN due_date = '' THEN 1 ELSE 0 END,
                   due_date"""
        return [self._row_to_task(r) for r in cur.execute(q).fetchall()]

    def update_task_status(self, task_id: int, status: str) -> None:
        self.conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        self.conn.commit()

    def delete_task(self, task_id: int) -> None:
        self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    @staticmethod
    def _row_to_task(r: sqlite3.Row) -> Task:
        return Task(
            id=r["id"], title=r["title"], notes=r["notes"], due_date=r["due_date"],
            priority=r["priority"], status=r["status"], source=r["source"],
            created_at=r["created_at"],
        )

    # ---- Actas (MoM) --------------------------------------------------
    def add_minute(self, title: str, content: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO minutes (title, content, created_at) VALUES (?, ?, ?)",
            (title.strip() or "Acta sin título", content, _now()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_minutes(self) -> list[Minute]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM minutes ORDER BY created_at DESC").fetchall()
        return [
            Minute(id=r["id"], title=r["title"], content=r["content"], created_at=r["created_at"])
            for r in rows
        ]

    def delete_minute(self, minute_id: int) -> None:
        self.conn.execute("DELETE FROM minutes WHERE id = ?", (minute_id,))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
