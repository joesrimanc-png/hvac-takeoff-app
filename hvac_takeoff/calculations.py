from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "hvac_takeoff.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                unit_system TEXT NOT NULL DEFAULT 'Imperial',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL,
                unit_cost REAL NOT NULL DEFAULT 0,
                labor_rate REAL NOT NULL DEFAULT 0,
                adjustment_factor REAL NOT NULL DEFAULT 1,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """
        )


def create_project(name: str, unit_system: str = "Imperial") -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO projects (name, unit_system) VALUES (?, ?)",
            (name.strip() or "New HVAC Estimate", unit_system),
        )
        return int(cursor.lastrowid)


def list_projects() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, unit_system, created_at, updated_at FROM projects ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def get_project(project_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, unit_system FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        return dict(row) if row else None


def add_item(
    project_id: int,
    category: str,
    description: str,
    quantity: float,
    unit: str,
    unit_cost: float,
    labor_rate: float,
    adjustment_factor: float,
    notes: str,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO line_items (
                project_id, category, description, quantity, unit, unit_cost, labor_rate,
                adjustment_factor, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                category,
                description.strip() or "Unnamed item",
                float(quantity),
                unit.strip() or "EA",
                float(unit_cost),
                float(labor_rate),
                float(adjustment_factor),
                notes.strip(),
            ),
        )
        return int(cursor.lastrowid)


def list_items(project_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id, project_id, category, description, quantity, unit,
                unit_cost, labor_rate, adjustment_factor, notes,
                created_at
            FROM line_items
            WHERE project_id = ?
            ORDER BY id ASC
            """,
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def delete_item(item_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM line_items WHERE id = ?", (item_id,))


def touch_project(project_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,),
        )
