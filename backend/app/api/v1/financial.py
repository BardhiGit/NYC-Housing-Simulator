"""
Financial calculation endpoints.

These are compute-only endpoints — they load the property from DB,
run the financial engine, and return results. Nothing is persisted
unless the caller explicitly saves a scenario.

All heavy computation stays in the services layer; the API layer
just handles HTTP concerns (auth, serialization, error handling).
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.properties import _load_property
from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.models.outputs import (
    AmortizationSchedule,
    FullFinancialResult,
    InvestmentMemo,
    InvestmentScore,
    MonteCarloResults,
    ProjectionResult,
    TornadoChartData,
)
from app.services.amortization import build_schedule
from app.services.financial_engine import FinancialEngine
from app.services.memo_generator import generate_memo
from app.services.monte_carlo import MonteCarloService
from app.services.projection import ProjectionService
from app.services.red_flags import detect_red_flags
from app.services.scoring import ScoringService
from app.services.sensitivity import SensitivityService
from app.utils.converters import orm_to_property_input

router = APIRouter(tags=["financial"])


class ProjectionRequest(BaseModel):
    holding_period: Optional[int] = None       # overrides property assumption
    exit_cap_rate: Optional[float] = None
    fm_rent_growth_rate: Optional[float] = None
    rs_rent_growth_rate: Optional[float] = None
    expense_growth_rate: Optional[float] = None
    general_vacancy_rate: Optional[float] = None


class SimulationRequest(BaseModel):
    n_iterations: int = 5_000   # cap at 10K for API; use 500 for demos
    seed: Optional[int] = None


class SensitivityRequest(BaseModel):
    target_metric: str = "coc_return"
    variables: Optional[list[str]] = None


class HeatmapRequest(BaseModel):
    x_variable: str = "purchase_price"
    y_variable: str = "interest_rate"
    target_metric: str = "dscr"
    grid_size: int = 5


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

@router.post("/properties/{property_id}/calculate", response_model=FullFinancialResult)
async def calculate(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Full Year-1 financial analysis: income, NOI, DSCR, cap rate,
    CoC return, break-even, rent roll summary.
    """
    prop = await _load_property(db, property_id, user.id)
    prop_input = orm_to_property_input(prop)
    return FinancialEngine.calculate(prop_input)


@router.post("/properties/{property_id}/project", response_model=ProjectionResult)
async def project(
    property_id: uuid.UUID,
    body: ProjectionRequest = ProjectionRequest(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Multi-year DCF projection with IRR, NPV, equity buildup, and exit proceeds.
    Accepts optional overrides to model scenarios without saving them.
    """
    prop = await _load_property(db, property_id, user.id)
    prop_input = orm_to_property_input(prop)
    overrides = body.model_dump(exclude_none=True)
    return ProjectionService.project(prop_input, override_assumptions=overrides or None)


@router.post("/properties/{property_id}/amortize", response_model=AmortizationSchedule)
async def amortize(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Full monthly amortization schedule for the property's loan."""
    prop = await _load_property(db, property_id, user.id)
    if not prop.loan:
        raise HTTPException(status_code=400, detail="Property has no loan — add one first")
    prop_input = orm_to_property_input(prop)
    return build_schedule(prop_input.loan)


@router.post("/properties/{property_id}/score", response_model=InvestmentScore)
async def score(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Investment Quality Score (0–100) with component breakdown."""
    prop = await _load_property(db, property_id, user.id)
    prop_input = orm_to_property_input(prop)
    financials = FinancialEngine.calculate(prop_input)
    projection = ProjectionService.project(prop_input)
    return ScoringService.score(prop_input, financials, projection)


@router.post("/properties/{property_id}/flags")
async def red_flags(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Red flag analysis — rules-based detection of financial warning signs."""
    prop = await _load_property(db, property_id, user.id)
    prop_input = orm_to_property_input(prop)
    financials = FinancialEngine.calculate(prop_input)
    flags = detect_red_flags(prop_input, financials)
    return {"flags": [f.model_dump() for f in flags], "count": len(flags)}


@router.post("/properties/{property_id}/memo", response_model=InvestmentMemo)
async def generate_investment_memo(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Generate a plain-English investment memo covering strengths,
    weaknesses, risks, negotiation points, and due diligence questions.
    Rule-based — no LLM required.
    """
    prop = await _load_property(db, property_id, user.id)
    prop_input = orm_to_property_input(prop)
    financials = FinancialEngine.calculate(prop_input)
    score = ScoringService.score(prop_input, financials)
    flags = detect_red_flags(prop_input, financials)
    projection = ProjectionService.project(prop_input)
    return generate_memo(prop_input, financials, score, flags, projection)


# ---------------------------------------------------------------------------
# Risk / simulation
# ---------------------------------------------------------------------------

@router.post("/properties/{property_id}/simulate", response_model=MonteCarloResults)
async def simulate(
    property_id: uuid.UUID,
    body: SimulationRequest = SimulationRequest(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Monte Carlo simulation — distributional analysis of key return metrics.
    n_iterations capped at 10,000 for API; use 500 for quick demos.
    """
    n = min(body.n_iterations, 10_000)
    prop = await _load_property(db, property_id, user.id)
    prop_input = orm_to_property_input(prop)
    from app.models.outputs import MonteCarloParams
    from app.services.monte_carlo import _default_params
    params = _default_params(prop_input)
    params.n_iterations = n
    return MonteCarloService.run(prop_input, params=params, seed=body.seed)


@router.post("/properties/{property_id}/sensitivity", response_model=TornadoChartData)
async def sensitivity(
    property_id: uuid.UUID,
    body: SensitivityRequest = SensitivityRequest(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Tornado chart: one-at-a-time sensitivity on a target metric."""
    prop = await _load_property(db, property_id, user.id)
    prop_input = orm_to_property_input(prop)
    return SensitivityService.tornado_chart(
        prop_input,
        target_metric=body.target_metric,
        variables=body.variables,
    )


@router.post("/properties/{property_id}/heatmap")
async def heatmap(
    property_id: uuid.UUID,
    body: HeatmapRequest = HeatmapRequest(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """2D sensitivity heatmap — two variables varied simultaneously."""
    prop = await _load_property(db, property_id, user.id)
    prop_input = orm_to_property_input(prop)
    result = SensitivityService.heatmap(
        prop_input,
        x_variable=body.x_variable,
        y_variable=body.y_variable,
        target_metric=body.target_metric,
        grid_size=body.grid_size,
    )
    return result.model_dump()


# ---------------------------------------------------------------------------
# Quick estimate (no auth required — great for landing page demo)
# ---------------------------------------------------------------------------

class QuickEstimateRequest(BaseModel):
    purchase_price: float
    total_monthly_rent: float
    vacancy_rate: float = 0.05
    total_annual_expenses: float
    loan_amount: float
    annual_rate: float
    term_years: int = 30
    closing_costs: float = 0.0


@router.post("/quick-estimate", tags=["financial"])
async def quick_estimate(body: QuickEstimateRequest):
    """
    Fast back-of-envelope calculation — no auth required.
    Designed for the landing page demo widget.
    """
    return FinancialEngine.quick_estimate(
        purchase_price=body.purchase_price,
        total_monthly_rent=body.total_monthly_rent,
        vacancy_rate=body.vacancy_rate,
        total_annual_expenses=body.total_annual_expenses,
        loan_amount=body.loan_amount,
        annual_rate=body.annual_rate,
        term_years=body.term_years,
        closing_costs=body.closing_costs,
    )
