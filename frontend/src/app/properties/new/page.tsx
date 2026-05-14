"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { propertiesApi } from "@/lib/api/properties";
import type { PropertyCreate, AssumptionInput, Borough } from "@/lib/types/property";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { clsx } from "clsx";

const boroughOpts = [
  { value: "brooklyn",     label: "Brooklyn" },
  { value: "queens",       label: "Queens" },
  { value: "bronx",        label: "Bronx" },
  { value: "manhattan",    label: "Manhattan" },
  { value: "staten_island",label: "Staten Island" },
];

const defaultAssumptions: AssumptionInput = {
  holding_period: 10,
  general_vacancy_rate: 0.05,
  fm_rent_growth_rate: 0.03,
  rs_rent_growth_rate: 0.028,
  expense_growth_rate: 0.03,
  exit_cap_rate: 0.055,
  selling_costs_pct: 0.05,
  discount_rate: 0.08,
  other_income_annual: 0,
  capex_reserve_per_unit_annual: 500,
};

const steps = ["General Info", "Financing", "Assumptions", "Review"];

export default function NewPropertyPage() {
  const [step, setStep] = useState(0);
  const router = useRouter();
  const qc = useQueryClient();

  const [general, setGeneral] = useState({
    name: "", address: "", borough: "brooklyn" as Borough,
    year_built: "", gross_sq_ft: "", num_units: 6,
    purchase_price: 1200000, closing_costs: 36000, renovation_budget_total: 0,
  });
  const [loan, setLoan] = useState({
    loan_amount: 960000, interest_rate: 0.0695,
    term_years: 30, is_interest_only: false, io_period_years: 0,
  });
  const [assumptions, setAssumptions] = useState<AssumptionInput>(defaultAssumptions);

  const createMutation = useMutation({
    mutationFn: (body: PropertyCreate) => propertiesApi.create(body),
    onSuccess: async (prop) => {
      // Also set the loan
      if (loan.loan_amount > 0) {
        await propertiesApi.setLoan(prop.id, {
          ...loan,
          amortization_years: loan.term_years,
        });
      }
      qc.invalidateQueries({ queryKey: ["properties"] });
      router.push(`/properties/${prop.id}/units`);
    },
  });

  function num(k: string, obj: Record<string, unknown>, setObj: (o: Record<string, unknown>) => void, label: string, prefix?: string, suffix?: string) {
    return (
      <Input
        key={k}
        label={label}
        type="number"
        prefix={prefix}
        suffix={suffix}
        value={obj[k] as number}
        onChange={(e) => setObj({ ...obj, [k]: parseFloat(e.target.value) || 0 })}
      />
    );
  }

  async function handleCreate() {
    const body: PropertyCreate = {
      name: general.name,
      address: general.address,
      borough: general.borough,
      year_built: general.year_built ? parseInt(general.year_built) : undefined,
      gross_sq_ft: general.gross_sq_ft ? parseFloat(general.gross_sq_ft) : undefined,
      num_units: general.num_units,
      purchase_price: general.purchase_price,
      closing_costs: general.closing_costs,
      renovation_budget_total: general.renovation_budget_total,
      assumptions,
    };
    createMutation.mutate(body);
  }

  const pct = ((step + 1) / steps.length) * 100;

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-white mb-1">New Property</h1>
          <p className="text-sm text-gray-500">Step {step + 1} of {steps.length}: {steps[step]}</p>
          <div className="mt-3 h-1 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-600 rounded-full transition-all duration-300" style={{ width: `${pct}%` }} />
          </div>
        </div>

        {/* Step indicators */}
        <div className="flex items-center gap-2 mb-6">
          {steps.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={clsx(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-all",
                i < step ? "bg-emerald-600 text-white" :
                i === step ? "bg-indigo-600 text-white" :
                "bg-gray-800 text-gray-500"
              )}>
                {i < step ? <Check size={12} /> : i + 1}
              </div>
              <span className={clsx("text-xs", i === step ? "text-gray-200" : "text-gray-600")}>{s}</span>
              {i < steps.length - 1 && <div className="w-4 h-px bg-gray-800" />}
            </div>
          ))}
        </div>

        <div className="card space-y-4">
          {step === 0 && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Property Name" placeholder="e.g. 137 Grant Ave" value={general.name} onChange={(e) => setGeneral((g) => ({ ...g, name: e.target.value }))} />
                <Select label="Borough" options={boroughOpts} value={general.borough} onChange={(e) => setGeneral((g) => ({ ...g, borough: e.target.value as Borough }))} />
              </div>
              <Input label="Street Address" placeholder="Full address" value={general.address} onChange={(e) => setGeneral((g) => ({ ...g, address: e.target.value }))} />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Number of Units" type="number" min={1} value={general.num_units} onChange={(e) => setGeneral((g) => ({ ...g, num_units: parseInt(e.target.value) || 1 }))} />
                <Input label="Year Built" type="number" placeholder="e.g. 1952" value={general.year_built} onChange={(e) => setGeneral((g) => ({ ...g, year_built: e.target.value }))} />
                <Input label="Purchase Price" prefix="$" type="number" value={general.purchase_price} onChange={(e) => setGeneral((g) => ({ ...g, purchase_price: parseFloat(e.target.value) || 0 }))} />
                <Input label="Closing Costs" prefix="$" type="number" value={general.closing_costs} onChange={(e) => setGeneral((g) => ({ ...g, closing_costs: parseFloat(e.target.value) || 0 }))} />
                <Input label="Renovation Budget" prefix="$" type="number" value={general.renovation_budget_total} onChange={(e) => setGeneral((g) => ({ ...g, renovation_budget_total: parseFloat(e.target.value) || 0 }))} />
                <Input label="Building Size (sq ft)" type="number" value={general.gross_sq_ft} onChange={(e) => setGeneral((g) => ({ ...g, gross_sq_ft: e.target.value }))} />
              </div>
            </>
          )}

          {step === 1 && (
            <div className="space-y-3">
              <p className="text-xs text-gray-500 mb-2">Leave loan amount at 0 for all-cash purchase.</p>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Loan Amount" prefix="$" type="number" value={loan.loan_amount} onChange={(e) => setLoan((l) => ({ ...l, loan_amount: parseFloat(e.target.value) || 0 }))} />
                <Input label="Interest Rate" type="number" step={0.001} value={loan.interest_rate} onChange={(e) => setLoan((l) => ({ ...l, interest_rate: parseFloat(e.target.value) || 0 }))} hint="Decimal: 0.065 = 6.5%" />
                <Input label="Loan Term (years)" type="number" value={loan.term_years} onChange={(e) => setLoan((l) => ({ ...l, term_years: parseInt(e.target.value) || 30 }))} />
                <Input label="IO Period (years)" type="number" value={loan.io_period_years} onChange={(e) => setLoan((l) => ({ ...l, io_period_years: parseInt(e.target.value) || 0 }))} hint="0 = fully amortizing" />
              </div>
              {loan.loan_amount > 0 && (
                <div className="bg-gray-800/50 rounded-xl p-3 text-xs text-gray-400">
                  <span className="font-medium text-gray-200">LTV: </span>
                  {((loan.loan_amount / general.purchase_price) * 100).toFixed(1)}% &nbsp;·&nbsp;
                  <span className="font-medium text-gray-200">Down: </span>
                  ${(general.purchase_price - loan.loan_amount).toLocaleString()}
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="grid grid-cols-2 gap-3">
              {(
                [
                  ["holding_period",              "Holding Period (yrs)",   undefined],
                  ["general_vacancy_rate",         "Vacancy Rate",           undefined],
                  ["fm_rent_growth_rate",           "FM Rent Growth",         undefined],
                  ["rs_rent_growth_rate",           "RS Rent Growth",         undefined],
                  ["expense_growth_rate",           "Expense Growth",         undefined],
                  ["exit_cap_rate",                 "Exit Cap Rate",          undefined],
                  ["discount_rate",                 "Discount Rate (NPV)",    undefined],
                  ["other_income_annual",           "Other Income/yr",        "$"],
                ] as [keyof AssumptionInput, string, string | undefined][]
              ).map(([k, label, prefix]) => (
                <Input
                  key={k}
                  label={label}
                  type="number"
                  step={k.endsWith("rate") || k === "discount_rate" || k === "exit_cap_rate" ? 0.001 : 1}
                  prefix={prefix}
                  value={assumptions[k] as number}
                  onChange={(e) => setAssumptions((a) => ({ ...a, [k]: parseFloat(e.target.value) || 0 }))}
                  hint={typeof assumptions[k] === "number" && assumptions[k] < 1 && !prefix ? "Decimal: 0.03 = 3%" : undefined}
                />
              ))}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-200">Review Before Creating</h3>
              {[
                ["Property", general.name || "Unnamed", general.address],
                ["Location", `${boroughOpts.find((b) => b.value === general.borough)?.label} · ${general.num_units} units · Built ${general.year_built || "?"}`],
                ["Price", `$${general.purchase_price.toLocaleString()} · Closing $${general.closing_costs.toLocaleString()}`],
                ["Financing", loan.loan_amount > 0 ? `$${loan.loan_amount.toLocaleString()} @ ${(loan.interest_rate * 100).toFixed(2)}% / ${loan.term_years}yr` : "All-cash purchase"],
                ["Hold Period", `${assumptions.holding_period} years · Exit cap ${(assumptions.exit_cap_rate * 100).toFixed(2)}%`],
              ].map(([label, ...values]) => (
                <div key={label as string} className="flex items-start gap-3 py-2 border-b border-gray-800">
                  <span className="text-xs text-gray-500 w-24 shrink-0">{label}</span>
                  <div>
                    {values.map((v, i) => (
                      <div key={i} className="text-sm text-gray-200">{v}</div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between mt-4">
          <Button variant="ghost" onClick={() => (step === 0 ? router.push("/dashboard") : setStep(s => s - 1))}>
            <ArrowLeft size={14} /> {step === 0 ? "Cancel" : "Back"}
          </Button>
          {step < steps.length - 1 ? (
            <Button onClick={() => setStep(s => s + 1)}>
              Continue <ArrowRight size={14} />
            </Button>
          ) : (
            <Button loading={createMutation.isPending} onClick={handleCreate}>
              Create Property <ArrowRight size={14} />
            </Button>
          )}
        </div>
      </div>
    </AppShell>
  );
}
