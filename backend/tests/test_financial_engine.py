"""
Tests for the core financial calculation engine.

Each test verifies a specific formula with known expected values.
Where NYC-specific behavior is tested (RS rent caps, preferential rent),
the test description explains the rule being verified.
"""

from __future__ import annotations

import pytest

from app.models.inputs import (
    ExpenseCategory,
    ExpenseInput,
    LoanInput,
    PropertyInput,
    RentType,
    UnitInput,
)
from app.services.financial_engine import (
    FinancialEngine,
    annual_debt_service,
    break_even_occupancy,
    cap_rate,
    cash_on_cash,
    dscr,
    effective_gross_income,
    expense_ratio,
    gross_scheduled_income,
    loan_to_value,
    monthly_payment,
    net_operating_income,
)


# ---------------------------------------------------------------------------
# Formula unit tests — each verifies a single function with known inputs
# ---------------------------------------------------------------------------

class TestMonthlyPayment:

    def test_standard_30yr_loan(self):
        """
        PMT = P × [r(1+r)^n] / [(1+r)^n - 1]
        $1M at 6.5% / 30yr → known value ≈ $6,320.68/mo
        """
        pmt = monthly_payment(1_000_000, 0.065, 30)
        assert abs(pmt - 6_320.68) < 1.0, f"Expected ~$6,320.68, got {pmt:.2f}"

    def test_zero_interest_rate(self):
        """Zero rate: payment = principal / n."""
        pmt = monthly_payment(1_200_000, 0.0, 30)
        expected = 1_200_000 / 360
        assert abs(pmt - expected) < 0.01

    def test_15yr_loan_higher_payment(self):
        """15-year loan has higher payment than 30-year for same amount/rate."""
        pmt_30 = monthly_payment(500_000, 0.07, 30)
        pmt_15 = monthly_payment(500_000, 0.07, 15)
        assert pmt_15 > pmt_30

    def test_payment_positive(self):
        """Payment is always positive for positive inputs."""
        assert monthly_payment(750_000, 0.05, 20) > 0

    def test_higher_rate_higher_payment(self):
        """Same principal/term: higher rate → higher payment."""
        low = monthly_payment(500_000, 0.04, 30)
        high = monthly_payment(500_000, 0.10, 30)
        assert high > low


class TestAnnualDebtService:

    def test_standard_fully_amortizing(self, standard_loan):
        ads = annual_debt_service(standard_loan)
        # $1M at 6.5% / 30yr → ~$6,320.68/mo × 12 = ~$75,848
        assert abs(ads - 75_848) < 50

    def test_interest_only_loan(self):
        loan = LoanInput(
            loan_amount=1_000_000,
            interest_rate=0.065,
            term_years=30,
            is_interest_only=True,
        )
        ads = annual_debt_service(loan)
        # IO: 1M × 6.5% = $65,000
        assert abs(ads - 65_000) < 1.0

    def test_io_period_uses_interest_only_payment(self):
        """Year-1 ADS during IO period = loan × rate."""
        loan = LoanInput(
            loan_amount=1_000_000,
            interest_rate=0.07,
            term_years=30,
            io_period_years=3,
        )
        ads = annual_debt_service(loan)
        assert abs(ads - 70_000) < 1.0


class TestGrossScheduledIncome:

    def test_excludes_vacant_units(self):
        units = [
            UnitInput(unit_number="1", bedrooms=1, rent_type=RentType.FREE_MARKET, current_rent=2_000),
            UnitInput(unit_number="2", bedrooms=1, rent_type=RentType.VACANT, current_rent=0),
        ]
        gsi = gross_scheduled_income(units)
        assert gsi == 24_000  # only unit 1 contributes

    def test_excludes_owner_occupied(self):
        units = [
            UnitInput(unit_number="1", bedrooms=2, rent_type=RentType.FREE_MARKET, current_rent=2_000),
            UnitInput(unit_number="2", bedrooms=2, rent_type=RentType.OWNER_OCCUPIED, current_rent=0),
        ]
        gsi = gross_scheduled_income(units)
        assert gsi == 24_000

    def test_mixed_unit_types(self):
        units = [
            UnitInput(unit_number="1", bedrooms=1, rent_type=RentType.STABILIZED, current_rent=1_500),
            UnitInput(unit_number="2", bedrooms=1, rent_type=RentType.FREE_MARKET, current_rent=2_000),
            UnitInput(unit_number="3", bedrooms=1, rent_type=RentType.VACANT, current_rent=0),
        ]
        gsi = gross_scheduled_income(units)
        assert gsi == (1_500 + 2_000) * 12

    def test_single_unit(self):
        units = [UnitInput(unit_number="1", bedrooms=1, rent_type=RentType.FREE_MARKET, current_rent=3_000)]
        assert gross_scheduled_income(units) == 36_000


class TestEffectiveGrossIncome:

    def test_basic_vacancy_application(self):
        units = [
            UnitInput(unit_number="1", bedrooms=1, rent_type=RentType.FREE_MARKET,
                      current_rent=2_000, vacancy_rate=0.05),
        ]
        gsi = 24_000
        egi, vac_loss = effective_gross_income(gsi, units, 0.05)
        assert abs(vac_loss - 1_200) < 0.01   # 24000 × 5%
        assert abs(egi - 22_800) < 0.01

    def test_unit_level_vacancy_overrides_default(self):
        """Unit with vacancy_rate=0.10 should use 10%, not the 5% default."""
        units = [
            UnitInput(unit_number="1", bedrooms=1, rent_type=RentType.FREE_MARKET,
                      current_rent=2_000, vacancy_rate=0.10),
        ]
        gsi = 24_000
        egi, vac_loss = effective_gross_income(gsi, units, 0.05)
        assert abs(vac_loss - 2_400) < 0.01   # 24000 × 10%

    def test_other_income_added(self):
        # vacancy_rate=0.0 so vacancy_loss=0, isolating the other_income addition
        units = [UnitInput(unit_number="1", bedrooms=1, rent_type=RentType.FREE_MARKET,
                           current_rent=2_000, vacancy_rate=0.0)]
        gsi = 24_000
        egi, _ = effective_gross_income(gsi, units, 0.0, other_income=1_200)
        assert abs(egi - 25_200) < 0.01

    def test_zero_vacancy(self):
        units = [UnitInput(unit_number="1", bedrooms=1, rent_type=RentType.FREE_MARKET,
                           current_rent=2_000, vacancy_rate=0.0)]
        gsi = 24_000
        egi, vac_loss = effective_gross_income(gsi, units, 0.0)
        assert vac_loss == 0.0
        assert egi == 24_000


class TestNOI:

    def test_noi_equals_egi_minus_opex(self):
        assert net_operating_income(100_000, 45_000) == 55_000

    def test_negative_noi_possible(self):
        """NOI can be negative if expenses exceed income."""
        assert net_operating_income(40_000, 50_000) == -10_000


class TestCapRate:

    def test_standard_cap_rate(self):
        assert abs(cap_rate(50_000, 1_000_000) - 0.05) < 1e-6

    def test_zero_price_returns_zero(self):
        assert cap_rate(50_000, 0) == 0.0

    def test_higher_noi_higher_cap(self):
        c1 = cap_rate(60_000, 1_000_000)
        c2 = cap_rate(80_000, 1_000_000)
        assert c2 > c1


class TestDSCR:

    def test_standard_dscr(self):
        """NOI of $130K / ADS of $100K = 1.30x."""
        assert abs(dscr(130_000, 100_000) - 1.30) < 1e-6

    def test_dscr_below_1_negative_coverage(self):
        """DSCR < 1.0 means income doesn't cover debt."""
        assert dscr(80_000, 100_000) < 1.0

    def test_zero_debt_service_returns_inf(self):
        assert dscr(100_000, 0) == float("inf")


class TestCashOnCash:

    def test_standard_coc(self):
        """$10K CF / $200K invested = 5%."""
        assert abs(cash_on_cash(10_000, 200_000) - 0.05) < 1e-6

    def test_negative_coc(self):
        assert cash_on_cash(-5_000, 200_000) < 0

    def test_zero_invested_returns_zero(self):
        assert cash_on_cash(10_000, 0) == 0.0


class TestBreakEvenOccupancy:

    def test_standard_break_even(self):
        """(40K opex + 60K ads) / 120K gsi = 83.3%."""
        be = break_even_occupancy(40_000, 60_000, 120_000)
        assert abs(be - 100_000 / 120_000) < 1e-6

    def test_above_100pct_is_possible(self):
        """If expenses + debt > GSI at 100% occupancy, building can't break even."""
        be = break_even_occupancy(80_000, 60_000, 100_000)
        assert be > 1.0

    def test_zero_gsi_returns_one(self):
        assert break_even_occupancy(40_000, 60_000, 0) == 1.0


class TestExpenseRatio:

    def test_standard_ratio(self):
        """50K opex / 100K EGI = 50%."""
        assert abs(expense_ratio(50_000, 100_000) - 0.50) < 1e-6

    def test_zero_egi_returns_zero(self):
        assert expense_ratio(50_000, 0) == 0.0


class TestLTV:

    def test_standard_ltv(self):
        assert abs(loan_to_value(800_000, 1_000_000) - 0.80) < 1e-6

    def test_zero_price_returns_zero(self):
        assert loan_to_value(800_000, 0) == 0.0


# ---------------------------------------------------------------------------
# Integration tests — FinancialEngine.calculate()
# ---------------------------------------------------------------------------

class TestFinancialEngine:

    def test_calculate_returns_all_sections(self, simple_property):
        result = FinancialEngine.calculate(simple_property)
        assert result.income is not None
        assert result.operating is not None
        assert result.debt is not None
        assert result.returns is not None
        assert result.valuation is not None
        assert result.break_even is not None
        assert result.rent_roll is not None

    def test_gsi_matches_unit_rents(self, simple_property):
        """GSI = (1500 + 2500) × 12 = $48,000."""
        result = FinancialEngine.calculate(simple_property)
        assert abs(result.income.gross_scheduled_income - 48_000) < 1.0

    def test_egi_less_than_gsi(self, simple_property):
        """EGI < GSI when vacancy > 0."""
        result = FinancialEngine.calculate(simple_property)
        assert result.income.effective_gross_income < result.income.gross_scheduled_income

    def test_noi_equals_egi_minus_opex(self, simple_property):
        result = FinancialEngine.calculate(simple_property)
        expected_noi = result.income.total_income - result.operating.total_operating_expenses
        assert abs(result.operating.net_operating_income - expected_noi) < 0.01

    def test_cap_rate_formula(self, simple_property):
        result = FinancialEngine.calculate(simple_property)
        expected_cap = result.operating.net_operating_income / simple_property.purchase_price
        assert abs(result.returns.cap_rate - expected_cap) < 1e-6

    def test_dscr_formula(self, simple_property):
        result = FinancialEngine.calculate(simple_property)
        expected_dscr = result.operating.net_operating_income / result.debt.annual_debt_service
        assert abs(result.debt.dscr - expected_dscr) < 1e-4

    def test_all_cash_has_no_debt_section(self, all_cash_property):
        result = FinancialEngine.calculate(all_cash_property)
        assert result.debt is None

    def test_all_cash_coc_equals_cap_rate(self, all_cash_property):
        """
        For an all-cash purchase, CoC = cap rate because
        total cash invested = purchase price and CF = NOI.
        """
        result = FinancialEngine.calculate(all_cash_property)
        # CoC = CF / total_invested, CF = NOI, total_invested ≈ purchase_price + closing
        # Not exactly equal due to closing costs in denominator
        assert abs(result.returns.cash_on_cash_return - result.returns.cap_rate) < 0.01

    def test_rent_roll_rs_percentage(self, simple_property):
        """1 RS + 1 FM → 50% RS."""
        result = FinancialEngine.calculate(simple_property)
        assert abs(result.rent_roll.rs_percentage - 0.50) < 1e-6

    def test_vacancy_loss_positive(self, simple_property):
        result = FinancialEngine.calculate(simple_property)
        assert result.income.vacancy_loss > 0

    def test_expense_by_category_sums_to_total(self, simple_property):
        result = FinancialEngine.calculate(simple_property)
        cat_total = sum(result.operating.expense_by_category.values())
        assert abs(cat_total - result.operating.total_operating_expenses) < 0.01

    def test_price_per_unit(self, simple_property):
        result = FinancialEngine.calculate(simple_property)
        expected = simple_property.purchase_price / simple_property.num_units
        assert abs(result.valuation.price_per_unit - expected) < 0.01


class TestSeedProperties:
    """Integration tests against realistic NYC seed data."""

    def test_bronx_negative_cash_flow(self, seed_bronx):
        """Bronx RS-heavy building should have negative cash flow — that's the story."""
        result = FinancialEngine.calculate(seed_bronx)
        assert result.returns.cash_flow_before_tax < 0, \
            "Bronx RS building should be cash-flow negative at 80% LTV"

    def test_bronx_dscr_below_1(self, seed_bronx):
        """DSCR < 1.0 expected for this property."""
        result = FinancialEngine.calculate(seed_bronx)
        assert result.debt.dscr < 1.0

    def test_brooklyn_cap_rate_in_range(self, seed_brooklyn):
        """Brooklyn mixed building: 3.5–5% cap rate is realistic."""
        result = FinancialEngine.calculate(seed_brooklyn)
        assert 0.035 < result.returns.cap_rate < 0.05, \
            f"Expected 3.5-5% cap rate, got {result.returns.cap_rate:.2%}"

    def test_lower_ltv_raises_dscr_same_property(self, seed_bronx):
        """
        Holding NOI constant: lower LTV reduces debt service → higher DSCR.
        Test by reducing the Bronx loan amount (more equity down).
        """
        high_ltv = FinancialEngine.calculate(seed_bronx)  # 80% LTV
        low_ltv_prop = seed_bronx.model_copy(deep=True)
        low_ltv_prop.loan.loan_amount = 630_000  # ~70% LTV
        low_ltv_result = FinancialEngine.calculate(low_ltv_prop)
        assert low_ltv_result.debt.dscr > high_ltv.debt.dscr

    def test_all_seed_properties_have_positive_noi(self, all_seed_properties):
        """All seed properties should have positive NOI (expenses < income)."""
        result = FinancialEngine.calculate(all_seed_properties)
        assert result.operating.net_operating_income > 0, \
            f"NOI should be positive, got {result.operating.net_operating_income:.0f}"

    def test_all_seed_properties_expense_ratio_reasonable(self, all_seed_properties):
        """Expense ratio should be between 30% and 75% for NYC multifamily."""
        result = FinancialEngine.calculate(all_seed_properties)
        er = result.operating.expense_ratio
        assert 0.30 <= er <= 0.75, f"Expense ratio {er:.0%} outside expected range"

    def test_brooklyn_rs_percentage(self, seed_brooklyn):
        """Brooklyn building: 8 of 12 rentable units are RS = 66.7%."""
        result = FinancialEngine.calculate(seed_brooklyn)
        expected = 8 / 12
        assert abs(result.rent_roll.rs_percentage - expected) < 0.01

    def test_queens_vacant_unit_excluded_from_gsi(self, seed_queens):
        """Queens has 1 vacant unit — GSI should only count 3 occupied units."""
        result = FinancialEngine.calculate(seed_queens)
        # Units: 1 RS @ $1,550, 2 FM @ $2,400 + $1,950. Vacant @ $0.
        expected_gsi = (1_550 + 2_400 + 1_950) * 12
        assert abs(result.income.gross_scheduled_income - expected_gsi) < 1.0


class TestQuickEstimate:

    def test_quick_estimate_returns_expected_keys(self):
        result = FinancialEngine.quick_estimate(
            purchase_price=1_000_000,
            total_monthly_rent=6_000,
            vacancy_rate=0.05,
            total_annual_expenses=35_000,
            loan_amount=800_000,
            annual_rate=0.065,
            term_years=30,
        )
        for key in ("gsi", "egi", "noi", "annual_debt_service", "cash_flow",
                    "cap_rate", "coc_return", "dscr", "break_even_occupancy"):
            assert key in result

    def test_quick_estimate_cap_rate_calculation(self):
        result = FinancialEngine.quick_estimate(
            purchase_price=1_000_000,
            total_monthly_rent=6_000,
            vacancy_rate=0.0,
            total_annual_expenses=35_000,
            loan_amount=800_000,
            annual_rate=0.065,
            term_years=30,
            closing_costs=0,
        )
        # GSI = 72,000, EGI = 72,000, NOI = 37,000, cap = 3.7%
        assert abs(result["cap_rate"] - 3.7) < 0.1
