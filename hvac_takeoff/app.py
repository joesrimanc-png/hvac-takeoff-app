from __future__ import annotations

from typing import Dict, Iterable, List, Any

CATEGORY_ORDER = [
    "Duct",
    "Pipe",
    "Fittings",
    "Accessories",
    "Equipment",
    "Controls",
    "Labor",
    "Other",
]


def calculate_line_total(quantity: float, unit_cost: float, labor_rate: float, adjustment_factor: float = 1.0) -> Dict[str, float]:
    qty = float(quantity or 0)
    unit_price = float(unit_cost or 0)
    labor = float(labor_rate or 0)
    factor = float(adjustment_factor or 1.0)

    material_total = qty * unit_price * factor
    labor_total = qty * labor * factor
    total = material_total + labor_total

    return {
        "material_total": material_total,
        "labor_total": labor_total,
        "total": total,
    }


def summarize_items(items: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    material = 0.0
    labor = 0.0
    total = 0.0
    count = 0

    for item in items:
        qty = float(item.get("quantity") or 0)
        unit_cost = float(item.get("unit_cost") or 0)
        labor_rate = float(item.get("labor_rate") or 0)
        factor = float(item.get("adjustment_factor") or 1.0)
        line = calculate_line_total(qty, unit_cost, labor_rate, factor)
        material += line["material_total"]
        labor += line["labor_total"]
        total += line["total"]
        count += 1

    return {
        "material": material,
        "labor": labor,
        "total": total,
        "items": count,
    }


def currency(value: float) -> str:
    return f"${value:,.2f}"


def unit_label(unit_system: str) -> str:
    if unit_system.lower() == "metric":
        return "m"
    return "ft"
