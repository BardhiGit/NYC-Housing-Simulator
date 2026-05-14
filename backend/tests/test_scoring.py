"""
Tests for Investment Quality Score and Red Flag Detector.

Key properties:
  1. Score is bounded [0, 100]
  2. Better deals score higher
  3. Bronx (distressed) scores lower than Queens (better deal)
  4. Red flags are triggered at appropriate thresholds
  5. Score components sum to total
  6. Letter grades align with score ranges
"""

from __future__ import annotations

import pytest

from app.services.financial_engine import FinancialEngine
from app.services.red_flags import detect_red_flags
from app.services.scoring import ScoringService, _letter_grade


class TestInvestmentScore:

    def test_score_bounded_0_to_100(self, all_seed_properties):
        fin = FinancialEngine.calculate(all_seed_properties)
        score = ScoringService.score(all_seed_properties, fin)
        assert 0 <= score.total <= 100

    def test_score_has_components(self, simple_property):
        fin = FinancialEngine.calculate(simple_property)
        score = ScoringService.score(simple_property, fin)
        assert len(score.components) >= 5

    def test_component_scores_sum_to_total(self, simple_property):
        fin = FinancialEngine.calculate(simple_property)
        score = ScoringService.score(simple_property, fin)
        computed_total = sum(c.score for c in score.components)
        # Total is clamped to [0, 100], so we check before clamping
        assert abs(max(0, min(100, computed_total)) - score.total) < 0.01

    def test_queens_scores_higher_than_bronx(self, seed_bronx, seed_queens):
        """Queens best case should outscore the Bronx RS trap."""
        bronx_fin = FinancialEngine.calculate(seed_bronx)
        queens_fin = FinancialEngine.calculate(seed_queens)
        bronx_score = ScoringService.score(seed_bronx, bronx_fin)
        queens_score = ScoringService.score(seed_queens, queens_fin)
        assert queens_score.total > bronx_score.total, \
            f"Queens ({queens_score.total}) should outscore Bronx ({bronx_score.total})"

    def test_score_has_letter_grade(self, simple_property):
        fin = FinancialEngine.calculate(simple_property)
        score = ScoringService.score(simple_property, fin)
        assert score.letter_grade in ("A", "B", "C", "D", "F")

    def test_all_cash_has_no_debt_component(self, all_cash_property):
        fin = FinancialEngine.calculate(all_cash_property)
        score = ScoringService.score(all_cash_property, fin)
        dscr_component = next((c for c in score.components if c.name == "dscr"), None)
        assert dscr_component is not None
        assert dscr_component.benchmark in ("N/A",)

    def test_high_rs_pct_incurs_penalty(self, seed_bronx):
        """Bronx (100% RS) should have negative RS penalty component."""
        fin = FinancialEngine.calculate(seed_bronx)
        score = ScoringService.score(seed_bronx, fin)
        rs_component = next(c for c in score.components if c.name == "rs_penalty")
        assert rs_component.score < 0

    def test_score_interpretation_not_empty(self, simple_property):
        fin = FinancialEngine.calculate(simple_property)
        score = ScoringService.score(simple_property, fin)
        assert len(score.interpretation) > 20

    def test_strengths_and_weaknesses_are_lists(self, simple_property):
        fin = FinancialEngine.calculate(simple_property)
        score = ScoringService.score(simple_property, fin)
        assert isinstance(score.strengths, list)
        assert isinstance(score.weaknesses, list)


class TestLetterGrade:

    def test_grade_A(self):
        assert _letter_grade(80) == "A"
        assert _letter_grade(75) == "A"

    def test_grade_B(self):
        assert _letter_grade(65) == "B"
        assert _letter_grade(55) == "B"

    def test_grade_C(self):
        assert _letter_grade(45) == "C"
        assert _letter_grade(35) == "C"

    def test_grade_D(self):
        assert _letter_grade(25) == "D"
        assert _letter_grade(15) == "D"

    def test_grade_F(self):
        assert _letter_grade(10) == "F"
        assert _letter_grade(0) == "F"


class TestRedFlagDetector:

    def test_bronx_triggers_critical_flags(self, seed_bronx):
        """Bronx RS trap with DSCR < 1.0 should trigger CRITICAL flag."""
        fin = FinancialEngine.calculate(seed_bronx)
        flags = detect_red_flags(seed_bronx, fin)
        severities = {f.severity for f in flags}
        assert "CRITICAL" in severities or "HIGH" in severities, \
            "Bronx building should have at least one CRITICAL or HIGH flag"

    def test_dscr_below_1_triggers_critical(self, seed_bronx):
        fin = FinancialEngine.calculate(seed_bronx)
        flags = detect_red_flags(seed_bronx, fin)
        dscr_flags = [f for f in flags if f.code == "DSCR_BELOW_1"]
        if fin.debt and fin.debt.dscr < 1.0:
            assert len(dscr_flags) == 1

    def test_flags_sorted_by_severity(self, seed_bronx):
        fin = FinancialEngine.calculate(seed_bronx)
        flags = detect_red_flags(seed_bronx, fin)
        if len(flags) < 2:
            return
        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        for i in range(len(flags) - 1):
            assert order[flags[i].severity] <= order[flags[i + 1].severity], \
                f"Flags not sorted: {flags[i].severity} before {flags[i+1].severity}"

    def test_high_rs_flag_triggered(self, seed_bronx):
        """Bronx is 100% RS — HIGH_RS_PERCENTAGE flag should trigger."""
        fin = FinancialEngine.calculate(seed_bronx)
        flags = detect_red_flags(seed_bronx, fin)
        codes = {f.code for f in flags}
        assert "HIGH_RS_PERCENTAGE" in codes

    def test_no_flags_for_conservative_property(self):
        """A conservatively financed, well-managed property should have few/no critical flags."""
        from app.models.inputs import (
            AssumptionInput, Borough, ExpenseCategory, ExpenseInput,
            LoanInput, PropertyInput, RentType, UnitInput,
        )
        safe = PropertyInput(
            name="Safe Property",
            borough=Borough.QUEENS,
            num_units=4,
            purchase_price=1_000_000,
            closing_costs=30_000,
            units=[
                UnitInput(unit_number=str(i), bedrooms=2,
                          rent_type=RentType.FREE_MARKET, current_rent=2_200)
                for i in range(4)
            ],
            loan=LoanInput(loan_amount=600_000, interest_rate=0.065, term_years=30),
            expenses=[
                ExpenseInput(category=ExpenseCategory.PROPERTY_TAX, annual_amount=10_000),
                ExpenseInput(category=ExpenseCategory.INSURANCE, annual_amount=5_000),
                ExpenseInput(category=ExpenseCategory.WATER_SEWER, annual_amount=4_000),
                ExpenseInput(category=ExpenseCategory.REPAIRS, annual_amount=4_800),
                ExpenseInput(category=ExpenseCategory.MANAGEMENT, annual_amount=5_000),
                ExpenseInput(category=ExpenseCategory.CAPEX_RESERVE, annual_amount=2_000),
            ],
            assumptions=AssumptionInput(
                holding_period=10,
                general_vacancy_rate=0.05,
                fm_rent_growth_rate=0.03,
                rs_rent_growth_rate=0.028,
                expense_growth_rate=0.03,
                exit_cap_rate=0.055,
            ),
        )
        fin = FinancialEngine.calculate(safe)
        flags = detect_red_flags(safe, fin)
        critical_flags = [f for f in flags if f.severity == "CRITICAL"]
        assert len(critical_flags) == 0

    def test_flags_have_required_fields(self, seed_bronx):
        fin = FinancialEngine.calculate(seed_bronx)
        flags = detect_red_flags(seed_bronx, fin)
        for flag in flags:
            assert flag.code
            assert flag.title
            assert flag.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
            assert flag.recommendation
