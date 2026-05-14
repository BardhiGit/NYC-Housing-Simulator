/** TypeScript types mirroring the Python financial engine output models. */

export interface IncomeMetrics {
  gross_scheduled_income: number;
  vacancy_loss: number;
  effective_gross_income: number;
  other_income: number;
  total_income: number;
}

export interface OperatingMetrics {
  total_operating_expenses: number;
  expense_by_category: Record<string, number>;
  net_operating_income: number;
  expense_ratio: number;
}

export interface DebtMetrics {
  monthly_payment: number;
  annual_debt_service: number;
  year1_interest: number;
  year1_principal: number;
  dscr: number;
  loan_to_value: number;
}

export interface ReturnMetrics {
  cash_flow_before_tax: number;
  cash_on_cash_return: number;
  cap_rate: number;
  total_cash_invested: number;
  equity_at_purchase: number;
}

export interface ValuationMetrics {
  price_per_unit: number;
  price_per_sq_ft: number | null;
  implied_value_at_cap: number;
}

export interface BreakEvenMetrics {
  break_even_occupancy: number;
  break_even_rent: number;
}

export interface RentRollSummary {
  num_stabilized: number;
  num_free_market: number;
  num_vacant: number;
  num_owner_occupied: number;
  rs_percentage: number;
  monthly_gsi: number;
  annual_gsi: number;
  avg_rent_stabilized: number | null;
  avg_rent_free_market: number | null;
  total_market_rent_estimate: number | null;
  stabilization_discount: number | null;
}

export interface FullFinancialResult {
  income: IncomeMetrics;
  operating: OperatingMetrics;
  debt: DebtMetrics | null;
  returns: ReturnMetrics;
  valuation: ValuationMetrics;
  break_even: BreakEvenMetrics;
  rent_roll: RentRollSummary;
}

export interface YearlyProjection {
  year: number;
  gsi: number;
  egi: number;
  operating_expenses: number;
  noi: number;
  debt_service: number;
  cash_flow: number;
  loan_balance: number;
  property_value: number;
  equity: number;
  cumulative_cash_flow: number;
  dscr: number;
  cap_rate: number;
  coc_return: number;
}

export interface ProjectionResult {
  years: YearlyProjection[];
  holding_period: number;
  exit_year: number;
  exit_property_value: number;
  exit_loan_balance: number;
  exit_selling_costs: number;
  exit_net_proceeds: number;
  total_operating_cash_flow: number;
  total_return: number;
  equity_multiple: number;
  irr: number;
  npv: number;
}

export interface AmortizationRow {
  month: number;
  year: number;
  payment: number;
  principal: number;
  interest: number;
  balance: number;
  cumulative_interest: number;
  cumulative_principal: number;
}

export interface AnnualAmortizationSummary {
  year: number;
  total_payment: number;
  total_interest: number;
  total_principal: number;
  year_end_balance: number;
  interest_pct_of_payment: number;
}

export interface AmortizationSchedule {
  monthly_payment: number;
  total_interest: number;
  total_principal: number;
  rows: AmortizationRow[];
  annual_summary: AnnualAmortizationSummary[];
}

export interface DistributionStats {
  p10: number; p25: number; p50: number; p75: number; p90: number;
  mean: number; std: number; min_val: number; max_val: number;
}

export interface MonteCarloResults {
  n_iterations: number;
  irr: DistributionStats;
  coc_year1: DistributionStats;
  min_dscr: DistributionStats;
  total_return: DistributionStats;
  p_negative_cashflow_yr1: number;
  p_dscr_below_1: number;
  p_dscr_below_125: number;
  p_negative_irr: number;
  worst_case: Record<string, number>;
  median_case: Record<string, number>;
  best_case: Record<string, number>;
  irr_histogram: number[];
  coc_histogram: number[];
  total_return_histogram: number[];
}

export interface SensitivityPoint {
  variable: string;
  display_name: string;
  base_value: number;
  low_value: number;
  high_value: number;
  base_metric: number;
  low_metric: number;
  high_metric: number;
  swing: number;
  direction: string;
}

export interface TornadoChartData {
  target_metric: string;
  base_value: number;
  variables: SensitivityPoint[];
}

export interface ScoreComponent {
  name: string;
  display_name: string;
  score: number;
  max_score: number;
  raw_value: number;
  benchmark: string;
  explanation: string;
}

export interface InvestmentScore {
  total: number;
  letter_grade: string;
  components: ScoreComponent[];
  interpretation: string;
  strengths: string[];
  weaknesses: string[];
}

export interface RedFlag {
  code: string;
  title: string;
  description: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  affected_metric: string;
  current_value: string;
  threshold: string;
  recommendation: string;
}

export interface MemoSection {
  title: string;
  bullets: string[];
  narrative: string;
}

export interface InvestmentMemo {
  property_name: string;
  generated_at: string;
  executive_summary: string;
  deal_type: string;
  deal_overview: MemoSection;
  strengths: MemoSection;
  weaknesses: MemoSection;
  key_risks: MemoSection;
  what_makes_it_work: MemoSection;
  suggested_offer_price: number | null;
  suggested_offer_rationale: string;
  negotiation_points: string[];
  questions_before_buying: string[];
  disclaimer: string;
}

export interface QuickEstimateResult {
  gsi: number;
  egi: number;
  noi: number;
  annual_debt_service: number;
  cash_flow: number;
  cap_rate: number;
  coc_return: number;
  dscr: number;
  break_even_occupancy: number;
}
