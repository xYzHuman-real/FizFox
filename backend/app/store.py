from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock

from .models import Project


class ProjectStore:
    """Small SQLite-backed project store for the v0.1 MVP."""

    def __init__(self, path: str = "data/fizfox.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
            """)

    def save(self, project: Project) -> Project:
        payload = project.model_dump_json()
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO projects(id, payload) VALUES(?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                (project.id, payload),
            )
        return project

    def get(self, project_id: str) -> Project | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM projects WHERE id = ?", (project_id,)).fetchone()
        return Project.model_validate(json.loads(row["payload"])) if row else None
