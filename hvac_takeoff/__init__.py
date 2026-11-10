from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Project:
    id: Optional[int] = None
    name: str = "New HVAC Estimate"
    unit_system: str = "Imperial"


@dataclass
class EstimateItem:
    id: Optional[int] = None
    project_id: Optional[int] = None
    category: str = "Duct"
    description: str = ""
    quantity: float = 0.0
    unit: str = "LF"
    unit_cost: float = 0.0
    labor_rate: float = 0.0
    adjustment_factor: float = 1.0
    notes: str = ""
    material_total: float = 0.0
    labor_total: float = 0.0
    total: float = 0.0
