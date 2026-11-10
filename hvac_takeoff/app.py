from __future__ import annotations

from typing import Any, Dict, Iterable

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
    material = float(unit_cost or 0)
    labor = float(labor_rate or 0)
    factor = float(adjustment_factor or 1.0)

    material_total = qty * material * factor
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
        line = calculate_line_total(
            item.get("quantity"),
            item.get("unit_cost"),
            item.get("labor_rate"),
            item.get("adjustment_factor"),
        )
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


def format_money(value: float) -> str:
    return f"${value:,.2f}"


def unit_label(unit_system: str) -> str:
    return "m" if str(unit_system).lower() == "metric" else "ft"


def estimate_summary_breakdown(items: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    summary = {category: 0.0 for category in CATEGORY_ORDER}
    for item in items:
        category = item.get("category") or "Other"
        if category not in summary:
            summary[category] = 0.0
        totals = calculate_line_total(
            item.get("quantity"),
            item.get("unit_cost"),
            item.get("labor_rate"),
            item.get("adjustment_factor"),
        )
        summary[category] += totals["total"]
    return summary
