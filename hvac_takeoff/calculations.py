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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                unit TEXT NOT NULL,
                unit_cost REAL NOT NULL DEFAULT 0,
                labor_rate REAL NOT NULL DEFAULT 0,
                adjustment_factor REAL NOT NULL DEFAULT 1,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                location TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assemblies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                quantity REAL NOT NULL DEFAULT 0,
                factor REAL NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """
        )


def create_project(name: str, unit_system: str = "Imperial") -> int:
    clean_name = (name or "New HVAC Estimate").strip() or "New HVAC Estimate"
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO projects (name, unit_system) VALUES (?, ?)",
            (clean_name, unit_system),
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
    system_name: str | None = None,
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
                (description or "Unnamed item").strip() or "Unnamed item",
                float(quantity or 0),
                (unit or "EA").strip() or "EA",
                float(unit_cost or 0),
                float(labor_rate or 0),
                float(adjustment_factor or 1.0),
                notes or "",
            ),
        )
    return int(cursor.lastrowid)


def list_items(project_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, project_id, category, description, quantity, unit,
                   unit_cost, labor_rate, adjustment_factor, notes, created_at
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


def save_pricing_record(category: str, description: str, unit: str, unit_cost: float, labor_rate: float, adjustment_factor: float, notes: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pricing_library (category, description, unit, unit_cost, labor_rate, adjustment_factor, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category,
                (description or "Pricing item").strip() or "Pricing item",
                (unit or "EA").strip() or "EA",
                float(unit_cost or 0),
                float(labor_rate or 0),
                float(adjustment_factor or 1.0),
                notes or "",
            ),
        )
    return int(cursor.lastrowid)


def list_pricing_records() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, category, description, unit, unit_cost, labor_rate, adjustment_factor, notes FROM pricing_library ORDER BY category, description"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_pricing_record(item_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM pricing_library WHERE id = ?", (item_id,))


def save_system(project_id: int, name: str, location: str | None = None) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO systems (project_id, name, location) VALUES (?, ?, ?)",
            (project_id, (name or "Unnamed System").strip(), location or ""),
        )
        return int(cursor.lastrowid)


def list_systems(project_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, project_id, name, location FROM systems WHERE project_id = ? ORDER BY name",
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def save_assembly(project_id: int, name: str, description: str, quantity: float, factor: float) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO assemblies (project_id, name, description, quantity, factor) VALUES (?, ?, ?, ?, ?)",
            (project_id, (name or "Assembly").strip(), description or "", float(quantity or 0), float(factor or 1.0)),
        )
        return int(cursor.lastrowid)


def list_assemblies(project_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, project_id, name, description, quantity, factor FROM assemblies WHERE project_id = ? ORDER BY name",
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]
