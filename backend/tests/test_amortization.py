"""
Tests for the amortization schedule generator.

Key invariants verified:
  1. Sum of all principal payments = original loan amount
  2. Balance decreases monotonically (for amortizing loans)
  3. Final balance = 0 for fully amortizing; balloon balance for balloon loans
  4. Each payment = interest + principal
  5. IO period: balance unchanged, payment = interest only
"""

from __future__ import annotations

import pytest

from app.models.inputs import LoanInput
from app.services.amortization import balance_at_year, build_schedule


class TestFullyAmortizingLoan:

    def test_schedule_has_correct_length(self, standard_loan):
        schedule = build_schedule(standard_loan)
        assert len(schedule.rows) == 30 * 12  # 360 months

    def test_principal_sums_to_loan_amount(self, standard_loan):
        schedule = build_schedule(standard_loan)
        total_principal = sum(r.principal for r in schedule.rows)
        assert abs(total_principal - standard_loan.loan_amount) < 0.50  # $0.50 tolerance for rounding

    def test_final_balance_near_zero(self, standard_loan):
        schedule = build_schedule(standard_loan)
        assert schedule.rows[-1].balance < 1.0  # final balance near $0

    def test_balance_decreases_monotonically(self, standard_loan):
        schedule = build_schedule(standard_loan)
        balances = [r.balance for r in schedule.rows]
        for i in range(1, len(balances)):
            assert balances[i] <= balances[i - 1], \
                f"Balance increased at month {i}: {balances[i-1]} → {balances[i]}"

    def test_payment_equals_interest_plus_principal(self, standard_loan):
        schedule = build_schedule(standard_loan)
        for row in schedule.rows[:24]:  # check first 2 years
            assert abs(row.payment - (row.interest + row.principal)) < 0.02

    def test_interest_decreases_over_time(self, standard_loan):
        """Early payments are mostly interest; later payments are mostly principal."""
        schedule = build_schedule(standard_loan)
        yr1_interest = sum(r.interest for r in schedule.rows[:12])
        yr30_interest = sum(r.interest for r in schedule.rows[-12:])
        assert yr1_interest > yr30_interest

    def test_monthly_payment_consistent(self, standard_loan):
        """All standard amortization payments should be equal."""
        schedule = build_schedule(standard_loan)
        payments = [r.payment for r in schedule.rows]
        # Should be within $0.02 of each other (rounding)
        assert max(payments) - min(payments) < 0.02

    def test_annual_summary_count(self, standard_loan):
        schedule = build_schedule(standard_loan)
        assert len(schedule.annual_summary) == 30

    def test_total_interest_field(self, standard_loan):
        schedule = build_schedule(standard_loan)
        computed = sum(r.interest for r in schedule.rows)
        assert abs(schedule.total_interest - computed) < 1.0


class TestInterestOnlyLoan:

    def test_io_period_no_principal_reduction(self, io_loan):
        """During IO period, every payment should have $0 principal."""
        schedule = build_schedule(io_loan)
        io_months = io_loan.io_period_years * 12
        for row in schedule.rows[:io_months]:
            assert row.principal == 0.0, \
                f"Principal should be 0 during IO at month {row.month}"

    def test_io_period_balance_unchanged(self, io_loan):
        """Balance should remain equal to original loan during IO period."""
        schedule = build_schedule(io_loan)
        io_months = io_loan.io_period_years * 12
        for row in schedule.rows[:io_months]:
            assert abs(row.balance - io_loan.loan_amount) < 0.01

    def test_amortization_begins_after_io(self, io_loan):
        """After IO period, principal should be positive."""
        schedule = build_schedule(io_loan)
        io_months = io_loan.io_period_years * 12
        amort_start = schedule.rows[io_months]
        assert amort_start.principal > 0

    def test_pure_io_never_pays_principal(self):
        loan = LoanInput(
            loan_amount=1_000_000,
            interest_rate=0.065,
            term_years=5,
            is_interest_only=True,
        )
        schedule = build_schedule(loan)
        total_principal = sum(r.principal for r in schedule.rows)
        assert total_principal == 0.0


class TestBalloonLoan:

    def test_balloon_loan_schedule_length(self, balloon_loan):
        """10-year balloon: schedule runs for 10 years (120 months)."""
        schedule = build_schedule(balloon_loan)
        assert len(schedule.rows) == 10 * 12

    def test_balloon_final_balance_nonzero(self, balloon_loan):
        """Balloon loan: final balance > 0 (the balloon payment)."""
        schedule = build_schedule(balloon_loan)
        final_balance = schedule.rows[-1].balance
        assert final_balance > 0, "Balloon loan should have positive ending balance"

    def test_balloon_balance_less_than_original(self, balloon_loan):
        """Some principal has been paid down, so balloon < original."""
        schedule = build_schedule(balloon_loan)
        assert schedule.rows[-1].balance < balloon_loan.loan_amount


class TestBalanceAtYear:

    def test_year_zero_returns_full_balance(self, standard_loan):
        assert balance_at_year(standard_loan, 0) == standard_loan.loan_amount

    def test_year_beyond_term_returns_zero(self, standard_loan):
        assert balance_at_year(standard_loan, 31) == 0.0

    def test_balance_at_midpoint(self, standard_loan):
        """Year 15 balance should be significantly less than original."""
        bal = balance_at_year(standard_loan, 15)
        assert bal < standard_loan.loan_amount * 0.80  # at least 20% paid down

    def test_balance_at_year_matches_schedule(self, standard_loan):
        """balance_at_year should match the schedule for the same loan."""
        schedule = build_schedule(standard_loan)
        for yr in [5, 10, 20, 30]:
            schedule_bal = schedule.annual_summary[yr - 1].year_end_balance
            function_bal = balance_at_year(standard_loan, yr)
            assert abs(schedule_bal - function_bal) < 0.50


class TestSeedPropertyAmortization:

    def test_bronx_amortization(self, seed_bronx):
        schedule = build_schedule(seed_bronx.loan)
        assert len(schedule.rows) == 30 * 12
        total_principal = sum(r.principal for r in schedule.rows)
        assert abs(total_principal - seed_bronx.loan.loan_amount) < 1.0

    def test_brooklyn_total_interest_substantial(self, seed_brooklyn):
        """30-year loan on $2.56M should generate significant interest."""
        schedule = build_schedule(seed_brooklyn.loan)
        # Total interest should be roughly 1x the principal (rule of thumb for ~7%)
        assert schedule.total_interest > seed_brooklyn.loan.loan_amount * 0.80
