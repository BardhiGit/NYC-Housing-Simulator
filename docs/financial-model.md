# Financial Model Reference

Complete formula documentation for the StrataView calculation engine. Every formula here corresponds directly to code in `backend/app/services/`.

---

## 1. Income Metrics

### Gross Scheduled Income (GSI)

The maximum annual rent the building *could* collect if every rentable unit were occupied 100% of the time.

```
GSI = Σ (unit_monthly_rent_i × 12)
      for all units where rent_type ∈ {stabilized, free_market}
```

- Vacant and owner-occupied units contribute **$0** to GSI
- GSI represents the theoretical ceiling, not a realistic expectation
- Code: `financial_engine.py → gross_scheduled_income()`

### Effective Gross Income (EGI)

GSI adjusted for vacancy and augmented by non-rental income:

```
EGI = GSI × (1 − weighted_vacancy_rate) + other_income
```

Where `weighted_vacancy_rate` is applied per-unit (each unit can have its own vacancy assumption), not as a single building-level rate. This allows modeling partial rehabilitation or stabilized buildings where some units have lower-than-average turnover.

```python
vacancy_loss = Σ (unit_rent_i × 12 × unit_vacancy_rate_i)
EGI = GSI − vacancy_loss + other_income
```

- Other income: laundry, storage, parking, rooftop cell antenna, etc.
- Code: `financial_engine.py → effective_gross_income()`

---

## 2. Operating Expenses

### Operating Expense Categories (NYC multifamily)

| Category | Typical Range (NYC) | Notes |
|---|---|---|
| Property Tax | $8,000–$22,000/unit/yr | Class 2 buildings; varies by assessment |
| Insurance | $4,000–$10,000/unit/yr | Higher in flood zones |
| Water & Sewer | $3,000–$8,000/unit/yr | NYC DEP charges by building |
| Heat | $4,000–$9,000/unit/yr | Landlord-paid in most pre-war RS buildings |
| Electric (common) | $1,500–$4,000/unit/yr | Hallways, basement, mechanicals |
| Repairs & Maintenance | $600–$1,500/unit/yr | Higher in older buildings |
| Payroll / Super | $0–$18,000/unit/yr | Varies by building size and doorman |
| Management Fee | 4–8% of GSI | |
| Legal & Accounting | $1,500–$3,500/unit/yr | NYC landlord-tenant litigation adds up |
| CapEx Reserve | $500–$1,500/unit/yr | Roof, boiler, elevator, facade |
| Miscellaneous | $1,000–$3,000/unit/yr | |

**Critical rule**: Debt service (mortgage payments) is **not** an operating expense. It appears below the NOI line in the cash flow waterfall: `GSI → EGI → NOI → [subtract ADS] → Cash Flow`.

### Net Operating Income (NOI)

```
NOI = EGI − Total_Operating_Expenses
```

NOI is the single most important number in commercial real estate. It:
- Determines property value via the income approach
- Determines debt capacity via DSCR
- Is used for all cap rate calculations

A building with NOI > 0 is "income producing." A building where OpEx > EGI has negative NOI — a distressed asset.

---

## 3. Valuation Metrics

### Capitalization Rate

```
Cap Rate = NOI / Purchase_Price
```

Represents the unlevered yield on the asset — what you'd earn if you paid all cash. NYC multifamily cap rates (2024):

| Borough | Typical Range |
|---|---|
| Manhattan | 2.5–4.5% |
| Brooklyn | 3.5–5.5% |
| Queens | 4.0–6.0% |
| Bronx | 4.5–6.5% |
| Staten Island | 5.0–7.0% |

**Income approach valuation:**
```
Implied_Value = NOI / Market_Cap_Rate
```

If a building generates $120K NOI and the market cap rate is 5%, the implied value is $2.4M. If you paid $3M, you overpaid relative to current income.

### Price Per Unit / Per Square Foot

```
Price_per_Unit = Purchase_Price / num_units
Price_per_SF   = Purchase_Price / gross_sq_ft   (if provided)
```

NYC benchmarks (2024, rough):
- Bronx: $150K–$300K/unit
- Brooklyn: $350K–$700K/unit  
- Manhattan: $600K–$1.5M+/unit

---

## 4. Debt Analysis

### Monthly Mortgage Payment

Standard level-payment amortizing loan (PMT formula):

```
PMT = P × [r(1+r)^n] / [(1+r)^n − 1]

Where:
  P = principal (loan amount)
  r = monthly interest rate = annual_rate / 12
  n = total number of payments = term_years × 12
```

**Example:** $1,000,000 at 6.5% for 30 years
```
r = 0.065 / 12 = 0.005417
n = 360
PMT = 1,000,000 × [0.005417 × 1.005417^360] / [1.005417^360 − 1]
    = 1,000,000 × [0.005417 × 7.0267] / [6.0267]
    = 1,000,000 × 0.006321
    = $6,320.68/month
```

### Amortization Mechanics

Each payment splits into interest and principal:

```
Interest_month_t  = Balance_{t-1} × (annual_rate / 12)
Principal_month_t = PMT − Interest_month_t
Balance_t         = Balance_{t-1} − Principal_t
```

Early payments are mostly interest. In year 1 of a 30-year 6.5% loan, roughly 88% of each payment is interest. By year 25, it flips to mostly principal.

**Interest-only periods:** During IO, `Principal = 0` and payment equals `Balance × monthly_rate`. Balance stays constant. This reduces near-term cash burden but zero equity is built.

**Balloon loans:** Amortize over a longer period (e.g., 30 years) but term ends at year 10. At maturity, the remaining balance (the "balloon") is due. Typical for commercial bridge loans.

### Annual Debt Service (ADS)

```
ADS = PMT × 12
```

For IO periods: `ADS = loan_amount × annual_rate`

### Debt Service Coverage Ratio (DSCR)

```
DSCR = NOI / ADS
```

| DSCR | Interpretation |
|---|---|
| ≥ 1.50× | Very safe — significant income cushion above debt |
| ≥ 1.35× | Lender-comfortable |
| ≥ 1.25× | **Typical lender minimum for multifamily loans** |
| ≥ 1.10× | Tight — lender will scrutinize carefully |
| 1.00–1.10× | Break-even — no margin for error |
| < 1.00× | **Debt coverage failure** — income cannot cover mortgage |

A DSCR of 0.75× means the property generates income to cover only 75% of its mortgage payments. The owner must fund the 25% shortfall from outside the property.

### Break-Even Occupancy

```
Break_Even_Occupancy = (OpEx + ADS) / GSI
```

The minimum occupancy rate (as a fraction of GSI) required to cover all obligations. If GSI is $200K, OpEx is $90K, and ADS is $80K:

```
Break_Even = ($90K + $80K) / $200K = 85%
```

At 85% occupancy, you break even. Any additional vacancy is cash flow negative. Healthy buildings run below 80%.

### Loan-to-Value (LTV)

```
LTV = Loan_Amount / Purchase_Price
```

Typical limits:
- Fannie/Freddie multifamily: ≤ 80% LTV, minimum 1.25× DSCR
- Community banks: ≤ 75% LTV, minimum 1.25× DSCR
- Bridge/construction: up to 85–90% but at higher rates

---

## 5. Return Metrics

### Cash-on-Cash Return (CoC)

```
CoC = Annual_Cash_Flow_Before_Tax / Total_Cash_Invested

Total_Cash_Invested = Down_Payment + Closing_Costs + Renovation_Budget
Annual_Cash_Flow    = NOI − Annual_Debt_Service
```

CoC is the annual yield on equity invested, before tax effects. It is the most intuitive measure for cash flow investors. NYC CoC benchmarks:

| CoC | Assessment |
|---|---|
| ≥ 8% | Exceptional for NYC |
| 5–8% | Solid — above opportunity cost of capital |
| 3–5% | Marginal — below most investors' hurdle |
| 1–3% | Weak — money market rates are competitive |
| < 0% | Negative — appreciation bet only |

### Expense Ratio

```
Expense_Ratio = Total_OpEx / EGI
```

NYC multifamily benchmark: 35–55%. Above 65% signals operational inefficiency, underestimated expenses, or a broker pro forma. The most common trick in pro formas is understating repairs, water/sewer, and management fees.

---

## 6. Multi-Year Projection

### Year-by-Year Growth Model

For each year `t` in the holding period:

```python
# Rent growth
for each unit:
    if rent_type == "stabilized":
        new_rent = min(current_rent × (1 + rs_growth_rate), legal_rent)
    elif rent_type == "free_market":
        new_rent = current_rent × (1 + fm_growth_rate)

# Expense growth
opex_t = base_opex × (1 + expense_growth_rate)^t

# NOI
noi_t = egi_t − opex_t

# Loan balance (from amortization schedule)
balance_t = amortization_schedule[t].year_end_balance

# Property value (income approach)
value_t = noi_t / exit_cap_rate

# Equity
equity_t = value_t − balance_t

# Cash flow
cf_t = noi_t − annual_debt_service
```

### Exit Proceeds

At the end of the holding period:

```
Exit_Value   = NOI_exit / Exit_Cap_Rate
Selling_Costs = Exit_Value × selling_costs_pct   (broker + NYC transfer tax ≈ 5%)
Net_Proceeds  = Exit_Value − Selling_Costs − Remaining_Loan_Balance
```

### Net Present Value (NPV)

```
NPV = Σ [CF_t / (1 + discount_rate)^t]  for t = 0..holding_period
```

Where `CF_0 = −Total_Cash_Invested` (negative, outflow) and `CF_holding_period` includes the net exit proceeds added to the final year's operating cash flow.

NPV > 0 means the investment returns more than the discount rate on a present-value basis. NPV = 0 means the investment earns exactly the discount rate.

### Internal Rate of Return (IRR)

The IRR is the discount rate `r` that makes NPV = 0:

```
Σ [CF_t / (1+r)^t] = 0    solved for r
```

This equation has no closed-form solution and is solved numerically. The implementation uses:
1. **Primary**: `numpy_financial.irr()` (uses companion matrix method)
2. **Fallback**: Newton-Raphson iteration
3. **Fallback 2**: Bisection method (guaranteed convergence if root exists)

For deeply negative cash flow scenarios (like all three NYC seed properties at 2024 rates), the IRR equation may have no real solution — the app returns `0.0` in this case with appropriate warning.

### Equity Multiple

```
Equity_Multiple = (Total_Cash_Returned + Initial_Equity) / Initial_Equity

Where:
  Total_Cash_Returned = Σ annual_cash_flows + net_exit_proceeds
  Initial_Equity = Total_Cash_Invested
```

A 2.0× equity multiple means you doubled your invested equity over the holding period. Target: ≥ 1.5× over 10 years (mediocre), ≥ 2.0× (solid), ≥ 3.0× (strong).

---

## 7. Monte Carlo Simulation

### Probability Distributions

Each uncertain variable is modeled with a probability distribution calibrated to NYC market data:

| Variable | Distribution | Parameters |
|---|---|---|
| Vacancy rate | Truncated Normal | μ = base assumption, σ = 2.5%, bounds [0%, 30%] |
| FM rent growth | Truncated Normal | μ = base, σ = 1.5%, bounds [-5%, 12%] |
| RS rent growth | Truncated Normal | μ = 2.5%, σ = 1.0%, bounds [0%, 8%] |
| Expense growth | Truncated Normal | μ = base, σ = 1.2%, bounds [0%, 12%] |
| Exit cap rate | Truncated Normal | μ = base, σ = 0.5%, bounds [3%, 14%] |

**Why truncated normal?** Cap rates can't be negative; vacancy can't exceed 100%. Truncation prevents economically impossible draws while preserving the normal distribution shape in the feasible range.

**Why not log-normal for all?** Log-normal is appropriate for strictly positive, right-skewed quantities. Rent growth and cap rates can be negative (in theory) or compressed; truncated normal better represents analyst uncertainty.

### Simulation Algorithm

```python
def run_monte_carlo(property, n=10_000, seed=None):
    rng = np.random.default_rng(seed)   # reproducible with seed
    
    for i in range(n):
        # Independent draws for each trial
        vacancy    = truncated_normal(rng, μ_v, σ_v, 0, 0.30)
        fm_growth  = truncated_normal(rng, μ_fm, σ_fm, -0.05, 0.12)
        rs_growth  = truncated_normal(rng, μ_rs, σ_rs, 0, 0.08)
        exp_growth = truncated_normal(rng, μ_e, σ_e, 0, 0.12)
        exit_cap   = truncated_normal(rng, μ_cap, σ_cap, 0.03, 0.14)
        
        result = project_cashflows(property, overrides={...})
        store(result.irr, result.coc_yr1, result.min_dscr, result.total_return)
    
    return percentiles, probabilities, scenario_snapshots
```

### Key Output Metrics

- **IRR distribution**: P10/P25/P50/P75/P90 percentiles
- **P(CF < 0)**: Probability Year-1 cash flow is negative
- **P(DSCR < 1.0)**: Probability any year has DSCR below 1.0× (catastrophic scenario)
- **P(DSCR < 1.25)**: Probability any year fails lender minimum (refinancing risk)
- **P(IRR < 0)**: Probability the investment loses money in total

---

## 8. Sensitivity Analysis

### One-at-a-Time (Tornado Chart)

Each variable is perturbed ±20% from its base value (or ±custom range for rate variables) while all others are held constant. The metric is recalculated at each extreme.

```python
for variable in [purchase_price, vacancy_rate, exit_cap_rate, ...]:
    low_value  = base_value × 0.80
    high_value = base_value × 1.20
    
    metric_low  = calculate(property, override={variable: low_value})
    metric_high = calculate(property, override={variable: high_value})
    
    swing = abs(metric_high − metric_low)
    # Variables sorted by swing (widest bar at top)
```

The tornado shape occurs because variables are sorted by `|swing|` — the widest bar (highest impact variable) goes at the top.

### 2D Heatmap

Two variables are varied simultaneously on a grid (default 5×5 = 25 cells):

```python
x_values = linspace(x_low, x_high, grid_size)
y_values = linspace(y_low, y_high, grid_size)

for x in x_values:
    for y in y_values:
        metric = calculate(property, override={x_var: x, y_var: y})
        cells.append({x, y, metric})
```

The heatmap color maps metric value to a red→amber→green gradient, making it easy to identify the combination of inputs that produces acceptable returns.

---

## 9. NYC Rent Stabilization

### RGB Orders (Rent Guidelines Board)

The RGB is a NYC mayoral agency that sets maximum annual rent increases for stabilized apartments. Orders are issued each June for leases commencing October 1.

```python
RGB_ORDERS = {
    2024: {"one_year": 0.0275, "two_year": 0.0525},
    2023: {"one_year": 0.0300, "two_year": 0.0550},
    2022: {"one_year": 0.0325, "two_year": 0.0500},
    2021: {"one_year": 0.0000, "two_year": 0.0025},  # COVID
    ...
}
```

Historical average 1-year increase: ~2.5–3.5%/year (excluding COVID years).

### Preferential Rent

Some RS tenants pay less than their legal regulated rent (the DHCR-registered maximum). This below-legal amount is called the "preferential rent."

**Post-HSTPA 2019 (modeled here):**
- Landlord MUST continue preferential rent for the entire tenancy
- On renewal, landlord can ONLY increase by the RGB percentage applied to the preferential rent (not revert to legal)
- When tenant vacates, new tenant's starting rent is the legal rent (NOT market rate)

**Pre-2019 (not modeled):**
- Landlord could revert to legal rent on any lease renewal
- This made preferential rents a temporary benefit that could be revoked

### What Counts as an Operating Cost (RS context)

In RS buildings, the NYC Rent Stabilization Law (RSL) and DHCR regulate what expenses can justify rent increases through the MCI (Major Capital Improvement) and IAI (Individual Apartment Improvement) programs.

This model simplifies by treating all capital improvements as operating costs without modeling the specific DHCR approval process for rent increases.

---

## Code Location Reference

| Formula | File | Function |
|---|---|---|
| GSI | `services/financial_engine.py` | `gross_scheduled_income()` |
| EGI | `services/financial_engine.py` | `effective_gross_income()` |
| NOI | `services/financial_engine.py` | `net_operating_income()` |
| Cap Rate | `services/financial_engine.py` | `cap_rate()` |
| DSCR | `services/financial_engine.py` | `dscr()` |
| CoC | `services/financial_engine.py` | `cash_on_cash()` |
| Break-even | `services/financial_engine.py` | `break_even_occupancy()` |
| PMT formula | `services/financial_engine.py` | `monthly_payment()` |
| Amortization | `services/amortization.py` | `build_schedule()` |
| Projection | `services/projection.py` | `ProjectionService.project()` |
| IRR | `services/projection.py` | `calculate_irr()` |
| NPV | `services/projection.py` | `calculate_npv()` |
| Monte Carlo | `services/monte_carlo.py` | `MonteCarloService.run()` |
| Tornado | `services/sensitivity.py` | `SensitivityService.tornado_chart()` |
| Score | `services/scoring.py` | `ScoringService.score()` |
| Red flags | `services/red_flags.py` | `detect_red_flags()` |
| Memo | `services/memo_generator.py` | `generate_memo()` |
