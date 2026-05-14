import { apiClient } from "./client";
import type {
  AmortizationSchedule, FullFinancialResult, InvestmentMemo,
  InvestmentScore, MonteCarloResults, ProjectionResult,
  QuickEstimateResult, RedFlag, TornadoChartData,
} from "../types/financial";

export const financialApi = {
  calculate: (id: string): Promise<FullFinancialResult> =>
    apiClient.post(`/properties/${id}/calculate`).then((r) => r.data),

  project: (id: string, overrides?: Record<string, number>): Promise<ProjectionResult> =>
    apiClient.post(`/properties/${id}/project`, overrides ?? {}).then((r) => r.data),

  amortize: (id: string): Promise<AmortizationSchedule> =>
    apiClient.post(`/properties/${id}/amortize`).then((r) => r.data),

  score: (id: string): Promise<InvestmentScore> =>
    apiClient.post(`/properties/${id}/score`).then((r) => r.data),

  flags: (id: string): Promise<{ flags: RedFlag[]; count: number }> =>
    apiClient.post(`/properties/${id}/flags`).then((r) => r.data),

  memo: (id: string): Promise<InvestmentMemo> =>
    apiClient.post(`/properties/${id}/memo`).then((r) => r.data),

  simulate: (id: string, iterations = 2000): Promise<MonteCarloResults> =>
    apiClient.post(`/properties/${id}/simulate`, { n_iterations: iterations }).then((r) => r.data),

  sensitivity: (id: string, target = "coc_return"): Promise<TornadoChartData> =>
    apiClient.post(`/properties/${id}/sensitivity`, { target_metric: target }).then((r) => r.data),

  quickEstimate: (body: {
    purchase_price: number; total_monthly_rent: number; vacancy_rate: number;
    total_annual_expenses: number; loan_amount: number; annual_rate: number;
    term_years: number; closing_costs: number;
  }): Promise<QuickEstimateResult> =>
    apiClient.post("/quick-estimate", body).then((r) => r.data),
};

// Reference data (no auth)
export const referenceApi = {
  rgbOrders: () => apiClient.get("/reference/rgb-orders").then((r) => r.data),
  benchmarks: (borough: string) =>
    apiClient.get(`/reference/expense-benchmarks/${borough}`).then((r) => r.data),
  metrics: () => apiClient.get("/reference/metrics").then((r) => r.data),
  presetScenarios: () => apiClient.get("/reference/preset-scenarios").then((r) => r.data),
};
