"""
Sensitivity analysis engine.

Generates data for:
  1. Tornado chart — one-at-a-time ±20% sensitivity on a single target metric
  2. 2D Heatmap — two variables varied simultaneously on a grid

Target metrics: "coc_return", "dscr", "noi", "irr"

Design note: sensitivity is computed relative to the BASE scenario only.
Monte Carlo explores correlated multi-variable uncertainty; sensitivity
explores the marginal impact of each variable independently.
"""

from __future__ import annotations

from typing import Optional

from app.models.inputs import PropertyInput
from app.models.outputs import (
    HeatmapCell,
    SensitivityHeatmap,
    SensitivityPoint,
    TornadoChartData,
)
from app.services.financial_engine import FinancialEngine
from app.services.projection import ProjectionService


# Variables available for sensitivity analysis
SENSITIVITY_VARIABLES = {
    "purchase_price": {
        "display_name": "Purchase Price",
        "description": "Acquisition cost",
        "low_pct": 0.80,
        "high_pct": 1.20,
    },
    "general_vacancy_rate": {
        "display_name": "Vacancy Rate",
        "description": "Annual unit vacancy",
        "low_pct": 0.50,    # half the base vacancy (optimistic)
        "high_pct": 2.00,   # double the base vacancy (pessimistic)
    },
    "expense_growth_rate": {
        "display_name": "Expense Growth",
        "description": "Annual operating expense inflation",
        "low_pct": 0.50,
        "high_pct": 2.00,
    },
    "fm_rent_growth_rate": {
        "display_name": "FM Rent Growth",
        "description": "Free-market annual rent growth",
        "low_pct": 0.0,     # absolute values for growth rates
        "high_pct": 2.00,
    },
    "exit_cap_rate": {
        "display_name": "Exit Cap Rate",
        "description": "Cap rate at sale (higher = lower exit value)",
        "low_pct": 0.80,
        "high_pct": 1.20,
    },
    "interest_rate": {
        "display_name": "Interest Rate",
        "description": "Mortgage interest rate",
        "low_pct": 0.80,
        "high_pct": 1.20,
    },
    "rs_rent_growth_rate": {
        "display_name": "RS Rent Growth",
        "description": "Rent-stabilized annual growth (RGB orders)",
        "low_pct": 0.0,
        "high_pct": 2.00,
    },
}


def _get_metric(prop: PropertyInput, target: str) -> float:
    """Extract a single metric value from a property's financial calculation."""
    if target == "irr":
        result = ProjectionService.project(prop)
        return result.irr
    result = FinancialEngine.calculate(prop)
    mapping = {
        "coc_return": result.returns.cash_on_cash_return,
        "dscr": result.debt.dscr if result.debt else 0.0,
        "noi": result.operating.net_operating_income,
        "cap_rate": result.returns.cap_rate,
        "cash_flow": result.returns.cash_flow_before_tax,
    }
    return mapping.get(target, 0.0)


def _apply_override(prop: PropertyInput, variable: str, new_value: float) -> PropertyInput:
    """
    Return a modified copy of the property with one variable changed.
    We reconstruct the relevant nested object to avoid mutating the original.
    """
    # Deep copy via Pydantic model_copy
    p = prop.model_copy(deep=True)

    if variable == "purchase_price":
        p.purchase_price = new_value
    elif variable == "interest_rate":
        if p.loan:
            p.loan.interest_rate = new_value
    elif variable in (
        "general_vacancy_rate", "expense_growth_rate",
        "fm_rent_growth_rate", "rs_rent_growth_rate",
        "exit_cap_rate",
    ):
        setattr(p.assumptions, variable, new_value)

    return p


class SensitivityService:

    @classmethod
    def tornado_chart(
        cls,
        prop: PropertyInput,
        target_metric: str = "coc_return",
        variables: Optional[list[str]] = None,
    ) -> TornadoChartData:
        """
        One-at-a-time sensitivity analysis.
        Each variable is moved ±20% (or custom range) from its base value.
        Variables sorted by absolute swing (widest bar at top).
        """
        if variables is None:
            variables = list(SENSITIVITY_VARIABLES.keys())
            # Remove interest_rate if no loan
            if not prop.loan and "interest_rate" in variables:
                variables.remove("interest_rate")

        base_metric = _get_metric(prop, target_metric)

        points: list[SensitivityPoint] = []
        for var in variables:
            meta = SENSITIVITY_VARIABLES.get(var)
            if meta is None:
                continue

            base_val = _get_base_value(prop, var)
            if base_val == 0:
                continue

            low_pct = meta["low_pct"]
            high_pct = meta["high_pct"]

            # Growth rates: use additive adjustments when base is very small
            if var.endswith("_rate") and base_val < 0.02:
                low_val = max(0.0, base_val - 0.01)
                high_val = base_val + 0.02
            else:
                low_val = base_val * low_pct
                high_val = base_val * high_pct

            try:
                prop_low = _apply_override(prop, var, low_val)
                prop_high = _apply_override(prop, var, high_val)
                metric_low = _get_metric(prop_low, target_metric)
                metric_high = _get_metric(prop_high, target_metric)
            except Exception:
                continue

            swing = abs(metric_high - metric_low)
            direction = "positive" if metric_high > metric_low else "inverse"

            points.append(SensitivityPoint(
                variable=var,
                display_name=meta["display_name"],
                base_value=round(base_val, 6),
                low_value=round(low_val, 6),
                high_value=round(high_val, 6),
                base_metric=round(base_metric, 6),
                low_metric=round(metric_low, 6),
                high_metric=round(metric_high, 6),
                swing=round(swing, 6),
                direction=direction,
            ))

        # Sort by absolute swing descending (widest bar at top of tornado)
        points.sort(key=lambda p: p.swing, reverse=True)

        return TornadoChartData(
            target_metric=target_metric,
            base_value=round(base_metric, 6),
            variables=points,
        )

    @classmethod
    def heatmap(
        cls,
        prop: PropertyInput,
        x_variable: str,
        y_variable: str,
        target_metric: str = "coc_return",
        grid_size: int = 5,
    ) -> SensitivityHeatmap:
        """
        2D sensitivity heatmap varying two variables simultaneously.
        grid_size × grid_size cells, each showing the target metric value.
        """
        x_meta = SENSITIVITY_VARIABLES.get(x_variable)
        y_meta = SENSITIVITY_VARIABLES.get(y_variable)
        if not x_meta or not y_meta:
            raise ValueError(f"Unknown variable: {x_variable} or {y_variable}")

        x_base = _get_base_value(prop, x_variable)
        y_base = _get_base_value(prop, y_variable)

        x_values = [
            x_base * (x_meta["low_pct"] + (x_meta["high_pct"] - x_meta["low_pct"]) * i / (grid_size - 1))
            for i in range(grid_size)
        ]
        y_values = [
            y_base * (y_meta["low_pct"] + (y_meta["high_pct"] - y_meta["low_pct"]) * i / (grid_size - 1))
            for i in range(grid_size)
        ]

        cells: list[HeatmapCell] = []
        for x_val in x_values:
            for y_val in y_values:
                try:
                    p = _apply_override(prop, x_variable, x_val)
                    p = _apply_override(p, y_variable, y_val)
                    metric = _get_metric(p, target_metric)
                except Exception:
                    metric = 0.0
                cells.append(HeatmapCell(
                    x_value=round(x_val, 6),
                    y_value=round(y_val, 6),
                    metric_value=round(metric, 6),
                ))

        return SensitivityHeatmap(
            x_variable=x_variable,
            y_variable=y_variable,
            target_metric=target_metric,
            cells=cells,
            x_values=[round(v, 6) for v in x_values],
            y_values=[round(v, 6) for v in y_values],
        )


def _get_base_value(prop: PropertyInput, variable: str) -> float:
    """Extract the current (base) value of a variable from the property."""
    mapping = {
        "purchase_price": prop.purchase_price,
        "general_vacancy_rate": prop.assumptions.general_vacancy_rate,
        "expense_growth_rate": prop.assumptions.expense_growth_rate,
        "fm_rent_growth_rate": prop.assumptions.fm_rent_growth_rate,
        "rs_rent_growth_rate": prop.assumptions.rs_rent_growth_rate,
        "exit_cap_rate": prop.assumptions.exit_cap_rate,
        "interest_rate": prop.loan.interest_rate if prop.loan else 0.0,
    }
    return mapping.get(variable, 0.0)
