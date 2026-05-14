"""
Scenario management endpoints.

Scenarios are named sets of assumption overrides that get persisted to the DB.
The results are computed on demand and optionally cached in the scenarios.results JSONB column.

Preset scenarios (base/optimistic/pessimistic) use standard override templates
so users can quickly compare without building overrides from scratch.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.properties import _load_property
from app.core.deps import get_current_user
from app.db.models.scenario import Scenario
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.property import ScenarioCreate, ScenarioResponse
from app.services.financial_engine import FinancialEngine
from app.services.projection import ProjectionService
from app.services.scoring import ScoringService
from app.utils.converters import orm_to_property_input

router = APIRouter(tags=["scenarios"])

# Standard preset scenario overrides
PRESET_OVERRIDES = {
    "base": {},
    "optimistic": {
        "fm_rent_growth_rate": 0.04,
        "rs_rent_growth_rate": 0.03,
        "general_vacancy_rate": 0.03,
        "expense_growth_rate": 0.02,
        "exit_cap_rate": 0.045,
    },
    "pessimistic": {
        "fm_rent_growth_rate": 0.01,
        "rs_rent_growth_rate": 0.015,
        "general_vacancy_rate": 0.08,
        "expense_growth_rate": 0.05,
        "exit_cap_rate": 0.07,
    },
    "rent_freeze": {
        "fm_rent_growth_rate": 0.0,
        "rs_rent_growth_rate": 0.0,
        "expense_growth_rate": 0.04,
    },
    "high_rates": {
        "exit_cap_rate": 0.08,
        "expense_growth_rate": 0.04,
    },
    "high_vacancy": {
        "general_vacancy_rate": 0.12,
        "fm_rent_growth_rate": 0.02,
    },
}


@router.get("/properties/{property_id}/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _load_property(db, property_id, user.id, with_relations=False)
    result = await db.execute(
        select(Scenario)
        .where(Scenario.property_id == property_id)
        .order_by(Scenario.created_at)
    )
    return result.scalars().all()


@router.post("/properties/{property_id}/scenarios", response_model=ScenarioResponse, status_code=201)
async def create_scenario(
    property_id: uuid.UUID,
    body: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create and persist a scenario. If type matches a preset (base/optimistic/etc.),
    the standard overrides are applied automatically unless custom overrides are provided.
    """
    await _load_property(db, property_id, user.id, with_relations=False)

    overrides = body.overrides
    if not overrides and body.type in PRESET_OVERRIDES:
        overrides = PRESET_OVERRIDES[body.type]

    scenario = Scenario(
        property_id=property_id,
        name=body.name,
        type=body.type,
        overrides=overrides,
    )
    db.add(scenario)
    await db.flush()
    return scenario


@router.get("/properties/{property_id}/scenarios/{scenario_id}/run")
async def run_scenario(
    property_id: uuid.UUID,
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Run a saved scenario against the property's current data.
    Computes full projection + score + flags with scenario overrides applied.
    Caches results in scenario.results.
    """
    prop = await _load_property(db, property_id, user.id)
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id, Scenario.property_id == property_id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    prop_input = orm_to_property_input(prop)
    financials = FinancialEngine.calculate(prop_input)
    projection = ProjectionService.project(prop_input, override_assumptions=scenario.overrides or None)
    score = ScoringService.score(prop_input, financials, projection)

    output = {
        "scenario": {
            "id": str(scenario.id),
            "name": scenario.name,
            "type": scenario.type,
            "overrides": scenario.overrides,
        },
        "financials": financials.model_dump(),
        "projection_summary": {
            "irr": projection.irr,
            "equity_multiple": projection.equity_multiple,
            "total_return": projection.total_return,
            "exit_net_proceeds": projection.exit_net_proceeds,
            "year1_cash_flow": projection.years[0].cash_flow if projection.years else 0,
            "year1_dscr": projection.years[0].dscr if projection.years else 0,
        },
        "score": score.model_dump(),
    }

    # Cache results
    scenario.results = output
    return output


@router.get("/properties/{property_id}/scenarios/compare")
async def compare_scenarios(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Side-by-side comparison of all saved scenarios for a property.
    Returns a table-friendly structure for the frontend comparison view.
    """
    prop = await _load_property(db, property_id, user.id)
    result = await db.execute(
        select(Scenario).where(Scenario.property_id == property_id).order_by(Scenario.created_at)
    )
    scenarios = result.scalars().all()

    if not scenarios:
        return {"scenarios": [], "metrics": []}

    prop_input = orm_to_property_input(prop)
    rows = []

    for s in scenarios:
        financials = FinancialEngine.calculate(prop_input)
        projection = ProjectionService.project(prop_input, override_assumptions=s.overrides or None)
        score = ScoringService.score(prop_input, financials, projection)

        rows.append({
            "scenario_id": str(s.id),
            "scenario_name": s.name,
            "type": s.type,
            "overrides": s.overrides,
            "noi": financials.operating.net_operating_income,
            "cap_rate": financials.returns.cap_rate,
            "dscr": financials.debt.dscr if financials.debt else None,
            "cash_flow": financials.returns.cash_flow_before_tax,
            "coc_return": financials.returns.cash_on_cash_return,
            "irr": projection.irr,
            "equity_multiple": projection.equity_multiple,
            "score": score.total,
            "grade": score.letter_grade,
        })

    return {"scenarios": rows}
