# Architecture Reference

System design documentation for StrataView.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                          User's Browser                              │
│                                                                      │
│  Next.js 16 · React 19 · Tailwind v4 · Recharts v3                  │
│                                                                      │
│  ┌─────────┐ ┌──────────┐ ┌────────────────────┐ ┌───────────────┐  │
│  │ Landing │ │Dashboard │ │  Property Analysis  │ │  Risk / Memo  │  │
│  │   +     │ │          │ │  Financials / Units │ │  Scenarios    │  │
│  │Quick Est│ │Prop.cards│ │  Charts + KPI grid  │ │  Monte Carlo  │  │
│  └────┬────┘ └────┬─────┘ └──────────┬──────────┘ └──────┬────────┘  │
│       │           │                   │                    │          │
│       └─────────────────────┬─────────────────────────────┘          │
│                             │ HTTPS · JSON · JWT Bearer              │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                      API Layer                               │    │
│  │  auth.py          → JWT issue / validate                     │    │
│  │  properties.py    → CRUD + unit / loan / expense management  │    │
│  │  financial.py     → calculation endpoints (stateless)        │    │
│  │  scenarios.py     → create / run / compare scenarios         │    │
│  │  reference.py     → static data (RGB orders, benchmarks)     │    │
│  └────────────────────────────┬─────────────────────────────────┘    │
│                               │                                      │
│  ┌────────────────────────────▼─────────────────────────────────┐    │
│  │                   Service Layer                              │    │
│  │                                                              │    │
│  │  financial_engine ──► Core formulas (GSI, NOI, DSCR, ...)   │    │
│  │  amortization     ──► Monthly schedule, balance_at_year()   │    │
│  │  projection       ──► 30-yr DCF, IRR (Newton-Raphson)       │    │
│  │  monte_carlo      ──► 10K iterations, NumPy sampling        │    │
│  │  sensitivity      ──► Tornado chart, 2D heatmap             │    │
│  │  scoring          ──► 0-100 Investment Quality Score        │    │
│  │  red_flags        ──► Rules engine, 10+ warning types       │    │
│  │  memo_generator   ──► Deterministic deal memo               │    │
│  │                                                              │    │
│  │  NO database access in service layer (pure functions)       │    │
│  └────────────────────────────┬─────────────────────────────────┘    │
│                               │                                      │
│  ┌────────────────────────────▼─────────────────────────────────┐    │
│  │                   Data Layer                                 │    │
│  │  converters.py    → ORM models → Pydantic engine inputs      │    │
│  │  SQLAlchemy 2.0 async (asyncpg driver)                       │    │
│  └────────────────────────────┬─────────────────────────────────┘    │
│                               │                                      │
└───────────────────────────────┼──────────────────────────────────────┘
                                │ asyncpg
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL 16                                 │
│                                                                      │
│  users ──────────────────────────┐                                   │
│  properties ─────┐               │                                   │
│  units           ├── FK cascade  │ FK                                │
│  loans           │               │                                   │
│  expenses        │               │                                   │
│  scenarios ──────┘               │                                   │
│                                  │                                   │
│  Assumptions: JSONB on property  │                                   │
│  Scenario results: JSONB cache   │                                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Service Layer is Stateless and DB-Ignorant

The financial calculation services (`financial_engine.py`, `projection.py`, `monte_carlo.py`, etc.) take **pure Pydantic models as input** and return **pure Pydantic models as output**. They have zero imports from the database layer.

This means:
- Services are independently testable without any database
- Services can be called from anywhere (API, scripts, notebooks, other services)
- 137 unit tests run in milliseconds without spinning up a DB
- The API layer is responsible for loading DB data and converting it via `converters.py`

**Data flow for a calculation request:**
```
HTTP POST /properties/{id}/calculate
    → API handler loads PropertyORM from DB
    → converters.orm_to_property_input(prop_orm) → PropertyInput
    → FinancialEngine.calculate(prop_input) → FullFinancialResult
    → Serialized to JSON → HTTP response
```

### 2. Assumptions as JSONB

The `AssumptionInput` model (holding period, growth rates, exit cap rate, etc.) is stored as a JSONB column on the `properties` table rather than a separate `assumptions` table.

**Why JSONB:**
- `AssumptionInput` is a flat structure — no foreign keys, no relationships
- JSON is flexible: adding new assumption fields doesn't require a migration
- JSONB can be indexed if needed for query filtering
- Read-modify-write pattern is clean: `assumptions = prop.assumptions | {"holding_period": 15}`

**Tradeoff**: No column-level constraints on assumption values. Validation happens at the Pydantic layer when the JSONB is deserialized.

### 3. Scenario Results Cached as JSONB

When a scenario is "run" via `GET /properties/{id}/scenarios/{sid}/run`, the full result JSON (financials + projection summary + score) is cached in `scenario.results` (a JSONB column). Subsequent reads return the cached result without recomputing.

**Why cache:** The scenario comparison view shows results for all scenarios simultaneously. Without caching, loading 5 scenarios would trigger 5 × 3 financial engine calls (calculate + project + score) = 15 computations per page load.

**Cache invalidation:** Currently not implemented — results are stale if the property's units, expenses, or loan changes after a scenario was run. Future work: invalidate on any property mutation. For a portfolio project, the explicit "Run" button is an acceptable UX.

### 4. Monte Carlo is Synchronous

Monte Carlo (2,000–10,000 iterations) runs synchronously in the API request. At 10,000 iterations, a single property's simulation takes ~30–60 seconds.

**For the portfolio project:** This is acceptable — Monte Carlo runs on-demand when the user clicks a button. The frontend shows a spinner.

**For production:** Move to Celery + Redis background tasks. The API returns a `job_id` immediately; the client polls `/simulate/{run_id}` for status. The `simulation_runs` table (designed in the schema) supports this pattern.

### 5. Authentication: JWT with Refresh Tokens

- Access token: 60-minute expiry, used for all API requests
- Refresh token: 30-day expiry, used only at `/auth/refresh`
- Tokens stored in `localStorage` (not httpOnly cookies, for simplicity; production would use httpOnly)
- 401 responses trigger automatic redirect to `/login` via axios interceptor

### 6. Frontend: Client-Side Auth Gate

The `AppShell` component checks `isAuthenticated` from the Zustand store and redirects to `/login` if false. There's a 100ms delay to allow the `init()` function (which reads from `localStorage`) to run before the check fires. This prevents a flash of the login redirect on page load.

**Why not server-side auth?** This is a client-rendered SPA pattern. For production, use Next.js middleware to validate JWT server-side before rendering.

---

## Request Flow Examples

### Financial Dashboard Load

```
1. User navigates to /properties/{id}/financials
2. useQuery("financials", id) → POST /properties/{id}/calculate
3. useQuery("projection", id) → POST /properties/{id}/project
4. useQuery("amortization", id) → POST /properties/{id}/amortize
5. useQuery("score", id) → POST /properties/{id}/score
6. useQuery("flags", id) → POST /properties/{id}/flags
   (Queries 2-6 fire in parallel; query 3 waits for query 2 to know if a loan exists)
7. Results render incrementally as queries resolve
```

Total: 5 API calls, ~200–500ms each, parallelized by React Query.

### Monte Carlo Run

```
1. User clicks "Run Simulation" on risk page
2. useState(runMC) → true → enables useQuery("monte_carlo", id)
3. POST /properties/{id}/simulate → { n_iterations: 2000 }
4. Backend: loads property from DB
5. Converts to PropertyInput
6. MonteCarloService.run(prop_input, n=2000)
   → draws 2000 × 5 random samples (NumPy vectorized)
   → runs 2000 ProjectionService.project() calls (~5ms each)
   → computes percentiles, probabilities
7. Returns MonteCarloResults JSON
8. Frontend renders histogram + probability cards
```

Total round-trip: ~10–20 seconds for 2,000 iterations.

---

## Database Schema

```sql
users (
  id         UUID PK,
  email      VARCHAR UNIQUE,
  name       VARCHAR,
  password_hash VARCHAR,
  is_active  BOOLEAN,
  created_at TIMESTAMPTZ
)

properties (
  id          UUID PK,
  user_id     UUID FK → users,
  name        VARCHAR,
  address     VARCHAR,
  borough     VARCHAR,
  year_built  INT,
  gross_sq_ft FLOAT,
  num_units   INT,
  purchase_price FLOAT,
  closing_costs  FLOAT,
  renovation_budget_total FLOAT,
  assumptions JSONB,          ← AssumptionInput as JSON
  created_at  TIMESTAMPTZ,
  updated_at  TIMESTAMPTZ
)

units (
  id               UUID PK,
  property_id      UUID FK → properties CASCADE,
  unit_number      VARCHAR,
  bedrooms         INT,
  bathrooms        FLOAT,
  sq_ft            FLOAT,
  rent_type        VARCHAR,    ← stabilized|free_market|vacant|owner_occupied
  current_rent     FLOAT,
  legal_rent       FLOAT,      ← RS: DHCR maximum
  preferential_rent FLOAT,     ← RS: actual rent if below legal
  market_rent_est  FLOAT,
  lease_expiry     DATE,
  vacancy_rate     FLOAT,
  rent_growth_override FLOAT,
  renovation_budget    FLOAT,
  notes            TEXT
)

loans (
  id               UUID PK,
  property_id      UUID FK → properties CASCADE UNIQUE,
  loan_amount      FLOAT,
  interest_rate    FLOAT,
  term_years       INT,
  amortization_years INT,
  is_interest_only BOOLEAN,
  io_period_years  INT
)

expenses (
  id          UUID PK,
  property_id UUID FK → properties CASCADE,
  category    VARCHAR,
  annual_amount FLOAT,
  growth_rate FLOAT,
  notes       TEXT
)

scenarios (
  id          UUID PK,
  property_id UUID FK → properties CASCADE,
  name        VARCHAR,
  type        VARCHAR,    ← base|optimistic|pessimistic|custom
  overrides   JSONB,      ← assumption delta dict
  results     JSONB,      ← cached calculation output
  created_at  TIMESTAMPTZ
)
```

---

## Directory Layout

```
nyc-housing-simulator/
│
├── README.md                    ← Main portfolio doc
├── docker-compose.yml           ← postgres + api services
├── docs/
│   ├── architecture.md          ← This file
│   └── financial-model.md       ← Formula reference
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   ├── app/
│   │   ├── main.py              ← FastAPI app, CORS, router
│   │   ├── core/
│   │   │   ├── config.py        ← Pydantic Settings (env vars)
│   │   │   ├── security.py      ← JWT, bcrypt
│   │   │   └── deps.py          ← get_current_user dependency
│   │   ├── db/
│   │   │   ├── base.py          ← SQLAlchemy DeclarativeBase
│   │   │   ├── session.py       ← Async engine + session factory
│   │   │   └── models/          ← 6 ORM models
│   │   ├── models/
│   │   │   ├── inputs.py        ← Pydantic inputs to engine
│   │   │   └── outputs.py       ← Pydantic outputs from engine
│   │   ├── schemas/
│   │   │   ├── auth.py          ← Register/login request/response
│   │   │   └── property.py      ← API-layer schemas
│   │   ├── services/            ← Pure calculation layer (no DB)
│   │   │   ├── financial_engine.py
│   │   │   ├── amortization.py
│   │   │   ├── projection.py
│   │   │   ├── monte_carlo.py
│   │   │   ├── sensitivity.py
│   │   │   ├── scoring.py
│   │   │   ├── red_flags.py
│   │   │   └── memo_generator.py
│   │   ├── api/v1/              ← HTTP endpoints
│   │   └── utils/
│   │       └── converters.py    ← ORM → PropertyInput bridge
│   ├── data/
│   │   └── seed_data.py         ← 3 demo NYC properties
│   ├── scripts/
│   │   └── seed_db.py           ← One-time DB seeder
│   └── tests/
│       ├── conftest.py          ← Shared fixtures (3 seed properties)
│       ├── test_financial_engine.py   ← 58 tests
│       ├── test_amortization.py       ← 22 tests
│       ├── test_projection.py         ← 23 tests
│       ├── test_monte_carlo.py        ← 10 tests
│       └── test_scoring.py            ← 24 tests
│
└── frontend/
    └── src/
        ├── app/                 ← Next.js 16 App Router
        │   ├── page.tsx         ← Landing + QuickEstimator
        │   ├── (auth)/          ← login · register
        │   ├── dashboard/       ← Property grid
        │   └── properties/[id]/ ← 6 analysis pages
        ├── components/
        │   ├── charts/          ← 8 Recharts components
        │   ├── financial/       ← KPIGrid · MetricCard · RedFlagList
        │   ├── layout/          ← Sidebar · AppShell · PropertyNav
        │   ├── property/        ← PropertyCard
        │   ├── units/           ← RentRollTable · UnitFormModal
        │   └── ui/              ← Button · Input · Select · Badge
        └── lib/
            ├── api/             ← Typed axios client
            ├── stores/          ← Zustand auth store
            ├── types/           ← TypeScript interfaces
            └── utils/           ← Format · metric color coding
```

---

## Performance Characteristics

| Operation | Typical Latency | Notes |
|---|---|---|
| `POST /calculate` | 10–50ms | Pure Python math, no I/O |
| `POST /project` | 20–80ms | 30 × N inner loops |
| `POST /amortize` | 5–20ms | 360 rows for 30yr loan |
| `POST /score` | 30–100ms | Includes project() |
| `POST /simulate` (2,000 iter) | 10–20s | CPU-bound; scales linearly |
| `POST /simulate` (10,000 iter) | 50–100s | Production: move to Celery |
| `POST /sensitivity` | 200–500ms | 8 × 2 calculate() calls |
| DB read (property + relations) | 5–20ms | Eagerly loaded via selectinload |

---

## What Would Production Look Like

1. **Celery + Redis** for Monte Carlo async jobs with polling
2. **Redis cache** for `calculate()` results (invalidated on property mutation)
3. **httpOnly cookies** instead of localStorage for JWT tokens
4. **Next.js middleware** for server-side auth verification
5. **CDN** for static assets (Vercel handles this automatically)
6. **Rate limiting** on simulation endpoints (FastAPI + slowapi)
7. **Error monitoring** (Sentry)
8. **Structured logging** (structlog → CloudWatch/Datadog)
9. **Database connection pooling** (PgBouncer)
10. **Read replica** for reporting queries
