export type Borough = "manhattan" | "brooklyn" | "queens" | "bronx" | "staten_island";
export type RentType = "stabilized" | "free_market" | "vacant" | "owner_occupied";
export type ExpenseCategory =
  | "property_tax" | "insurance" | "water_sewer" | "heat" | "electric"
  | "repairs" | "payroll" | "management" | "legal_accounting" | "capex_reserve" | "misc";

export interface AssumptionInput {
  holding_period: number;
  general_vacancy_rate: number;
  fm_rent_growth_rate: number;
  rs_rent_growth_rate: number;
  expense_growth_rate: number;
  exit_cap_rate: number;
  selling_costs_pct: number;
  discount_rate: number;
  other_income_annual: number;
  capex_reserve_per_unit_annual: number;
}

export interface UnitCreate {
  unit_number: string;
  bedrooms: number;
  bathrooms: number;
  sq_ft?: number;
  rent_type: RentType;
  current_rent: number;
  legal_rent?: number;
  preferential_rent?: number;
  market_rent_est?: number;
  lease_expiry?: string;
  vacancy_rate: number;
  rent_growth_override?: number;
  renovation_budget: number;
  notes?: string;
}

export interface UnitResponse extends UnitCreate {
  id: string;
  property_id: string;
}

export interface LoanCreate {
  loan_amount: number;
  interest_rate: number;
  term_years: number;
  amortization_years?: number;
  is_interest_only: boolean;
  io_period_years: number;
}

export interface LoanResponse extends LoanCreate {
  id: string;
  property_id: string;
}

export interface ExpenseCreate {
  category: ExpenseCategory;
  annual_amount: number;
  growth_rate: number;
  notes?: string;
}

export interface ExpenseResponse extends ExpenseCreate {
  id: string;
  property_id: string;
}

export interface PropertyCreate {
  name: string;
  address: string;
  borough: Borough;
  year_built?: number;
  gross_sq_ft?: number;
  num_units: number;
  purchase_price: number;
  closing_costs: number;
  renovation_budget_total: number;
  assumptions: AssumptionInput;
}

export interface PropertyResponse extends PropertyCreate {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface PropertyDetailResponse extends PropertyResponse {
  units: UnitResponse[];
  loan: LoanResponse | null;
  expenses: ExpenseResponse[];
}

export interface ScenarioCreate {
  name: string;
  type: string;
  overrides: Record<string, number>;
}

export interface ScenarioResponse extends ScenarioCreate {
  id: string;
  property_id: string;
  results: Record<string, unknown> | null;
  created_at: string;
}

export const BOROUGH_LABELS: Record<Borough, string> = {
  manhattan: "Manhattan",
  brooklyn: "Brooklyn",
  queens: "Queens",
  bronx: "Bronx",
  staten_island: "Staten Island",
};

export const RENT_TYPE_LABELS: Record<RentType, string> = {
  stabilized: "Rent-Stabilized",
  free_market: "Free Market",
  vacant: "Vacant",
  owner_occupied: "Owner-Occupied",
};

export const EXPENSE_LABELS: Record<ExpenseCategory, string> = {
  property_tax: "Property Tax",
  insurance: "Insurance",
  water_sewer: "Water & Sewer",
  heat: "Heat",
  electric: "Electric",
  repairs: "Repairs & Maintenance",
  payroll: "Payroll / Super",
  management: "Management Fee",
  legal_accounting: "Legal & Accounting",
  capex_reserve: "CapEx Reserve",
  misc: "Miscellaneous",
};
