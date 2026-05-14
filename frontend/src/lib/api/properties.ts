import { apiClient } from "./client";
import type {
  ExpenseCreate, ExpenseResponse,
  LoanCreate, LoanResponse,
  PropertyCreate, PropertyDetailResponse, PropertyResponse,
  ScenarioCreate, ScenarioResponse,
  UnitCreate, UnitResponse,
} from "../types/property";

// Properties
export const propertiesApi = {
  list: (): Promise<PropertyResponse[]> =>
    apiClient.get("/properties").then((r) => r.data),

  get: (id: string): Promise<PropertyDetailResponse> =>
    apiClient.get(`/properties/${id}`).then((r) => r.data),

  create: (body: PropertyCreate): Promise<PropertyResponse> =>
    apiClient.post("/properties", body).then((r) => r.data),

  update: (id: string, body: Partial<PropertyCreate>): Promise<PropertyResponse> =>
    apiClient.put(`/properties/${id}`, body).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    apiClient.delete(`/properties/${id}`).then(() => {}),

  // Units
  listUnits: (id: string): Promise<UnitResponse[]> =>
    apiClient.get(`/properties/${id}/units`).then((r) => r.data),

  addUnit: (id: string, body: UnitCreate): Promise<UnitResponse> =>
    apiClient.post(`/properties/${id}/units`, body).then((r) => r.data),

  updateUnit: (id: string, uid: string, body: UnitCreate): Promise<UnitResponse> =>
    apiClient.put(`/properties/${id}/units/${uid}`, body).then((r) => r.data),

  deleteUnit: (id: string, uid: string): Promise<void> =>
    apiClient.delete(`/properties/${id}/units/${uid}`).then(() => {}),

  // Loan
  setLoan: (id: string, body: LoanCreate): Promise<LoanResponse> =>
    apiClient.post(`/properties/${id}/loan`, body).then((r) => r.data),

  updateLoan: (id: string, body: LoanCreate): Promise<LoanResponse> =>
    apiClient.put(`/properties/${id}/loan`, body).then((r) => r.data),

  // Expenses
  listExpenses: (id: string): Promise<ExpenseResponse[]> =>
    apiClient.get(`/properties/${id}/expenses`).then((r) => r.data),

  addExpense: (id: string, body: ExpenseCreate): Promise<ExpenseResponse> =>
    apiClient.post(`/properties/${id}/expenses`, body).then((r) => r.data),

  updateExpense: (id: string, eid: string, body: ExpenseCreate): Promise<ExpenseResponse> =>
    apiClient.put(`/properties/${id}/expenses/${eid}`, body).then((r) => r.data),

  deleteExpense: (id: string, eid: string): Promise<void> =>
    apiClient.delete(`/properties/${id}/expenses/${eid}`).then(() => {}),

  // Scenarios
  listScenarios: (id: string): Promise<ScenarioResponse[]> =>
    apiClient.get(`/properties/${id}/scenarios`).then((r) => r.data),

  createScenario: (id: string, body: ScenarioCreate): Promise<ScenarioResponse> =>
    apiClient.post(`/properties/${id}/scenarios`, body).then((r) => r.data),

  runScenario: (id: string, sid: string) =>
    apiClient.get(`/properties/${id}/scenarios/${sid}/run`).then((r) => r.data),

  compareScenarios: (id: string) =>
    apiClient.get(`/properties/${id}/scenarios/compare`).then((r) => r.data),
};
