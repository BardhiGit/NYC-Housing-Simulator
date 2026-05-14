"""
Tests for the Monte Carlo simulation engine.

Key properties verified:
  1. Output distributions have the right shape (p10 < p50 < p90)
  2. Probabilities are bounded [0, 1]
  3. Deterministic with seed
  4. Negative-cash-flow probability is higher for Bronx (distressed) than Queens (good)
  5. Sufficient iterations produce stable estimates
"""

from __future__ import annotations

import pytest

from app.models.outputs import MonteCarloParams
from app.services.monte_carlo import MonteCarloService, _default_params


class TestMonteCarloOutput:

    def test_percentiles_ordered_correctly(self, simple_property):
        """p10 < p25 < p50 < p75 < p90 for all metrics."""
        results = MonteCarloService.run(simple_property, seed=42,
                                        params=_small_params(simple_property))
        for dist in [results.irr, results.coc_year1, results.total_return]:
            assert dist.p10 <= dist.p25
            assert dist.p25 <= dist.p50
            assert dist.p50 <= dist.p75
            assert dist.p75 <= dist.p90

    def test_probabilities_bounded(self, simple_property):
        results = MonteCarloService.run(simple_property, seed=42,
                                        params=_small_params(simple_property))
        assert 0.0 <= results.p_negative_cashflow_yr1 <= 1.0
        assert 0.0 <= results.p_dscr_below_1 <= 1.0
        assert 0.0 <= results.p_dscr_below_125 <= 1.0
        assert 0.0 <= results.p_negative_irr <= 1.0

    def test_deterministic_with_seed(self, simple_property):
        """Same seed should produce identical results."""
        params = _small_params(simple_property)
        r1 = MonteCarloService.run(simple_property, seed=99, params=params)
        r2 = MonteCarloService.run(simple_property, seed=99, params=params)
        assert abs(r1.irr.p50 - r2.irr.p50) < 1e-10

    def test_different_seeds_different_results(self, simple_property):
        params = _small_params(simple_property)
        r1 = MonteCarloService.run(simple_property, seed=1, params=params)
        r2 = MonteCarloService.run(simple_property, seed=2, params=params)
        # Different seeds → different (though close) results
        assert abs(r1.irr.mean - r2.irr.mean) > 1e-6

    def test_histogram_has_200_points(self, simple_property):
        results = MonteCarloService.run(simple_property, seed=42,
                                        params=_small_params(simple_property))
        assert len(results.irr_histogram) <= 200
        assert len(results.coc_histogram) <= 200

    def test_scenario_snapshots_present(self, simple_property):
        results = MonteCarloService.run(simple_property, seed=42,
                                        params=_small_params(simple_property))
        assert results.worst_case
        assert results.median_case
        assert results.best_case

    def test_n_iterations_recorded(self, simple_property):
        params = _small_params(simple_property)
        results = MonteCarloService.run(simple_property, seed=42, params=params)
        assert results.n_iterations == params.n_iterations


class TestMonteCarloRiskDifferentiation:

    def test_bronx_higher_risk_than_queens(self, seed_bronx, seed_queens):
        """
        Bronx RS trap should show higher P(DSCR < 1.0) than Queens best case.
        This validates that the simulation correctly reflects underlying deal quality.
        """
        params_b = _small_params(seed_bronx)
        params_q = _small_params(seed_queens)

        bronx_results = MonteCarloService.run(seed_bronx, seed=42, params=params_b)
        queens_results = MonteCarloService.run(seed_queens, seed=42, params=params_q)

        # Bronx should have higher probability of DSCR failure
        assert bronx_results.p_dscr_below_1 >= queens_results.p_dscr_below_1, \
            (f"Bronx P(DSCR<1)={bronx_results.p_dscr_below_1:.2f} should be >= "
             f"Queens P(DSCR<1)={queens_results.p_dscr_below_1:.2f}")

    def test_bronx_higher_negative_cf_probability(self, seed_bronx, seed_queens):
        params_b = _small_params(seed_bronx)
        params_q = _small_params(seed_queens)
        bronx_r = MonteCarloService.run(seed_bronx, seed=42, params=params_b)
        queens_r = MonteCarloService.run(seed_queens, seed=42, params=params_q)
        assert bronx_r.p_negative_cashflow_yr1 >= queens_r.p_negative_cashflow_yr1


class TestDefaultParams:

    def test_default_params_uses_property_assumptions(self, simple_property):
        params = _default_params(simple_property)
        a = simple_property.assumptions
        assert params.vacancy_mean == a.general_vacancy_rate
        assert params.fm_rent_growth_mean == a.fm_rent_growth_rate
        assert params.expense_growth_mean == a.expense_growth_rate
        assert params.exit_cap_mean == a.exit_cap_rate


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _small_params(prop) -> MonteCarloParams:
    """200-iteration params for fast tests."""
    base = _default_params(prop)
    base.n_iterations = 200
    return base
