"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import type { UnitCreate, UnitResponse } from "@/lib/types/property";

// Manual form type (avoids Zod v4 coerce inference issues with RHF)
type FormValues = {
  unit_number: string;
  bedrooms: number;
  bathrooms: number;
  sq_ft: number;
  rent_type: "stabilized" | "free_market" | "vacant" | "owner_occupied";
  current_rent: number;
  legal_rent: number;
  preferential_rent: number;
  market_rent_est: number;
  lease_expiry: string;
  vacancy_rate: number;
  renovation_budget: number;
  notes: string;
};

interface Props {
  unit?: UnitResponse | null;
  onClose: () => void;
  onSave: (data: UnitCreate) => Promise<void>;
}

const rentTypeOpts = [
  { value: "stabilized",     label: "Rent-Stabilized" },
  { value: "free_market",    label: "Free Market" },
  { value: "vacant",         label: "Vacant" },
  { value: "owner_occupied", label: "Owner-Occupied" },
];

export function UnitFormModal({ unit, onClose, onSave }: Props) {
  const { register, handleSubmit, watch, reset, formState: { errors, isSubmitting } } = useForm<FormValues>({
    defaultValues: {
      unit_number: "", bedrooms: 1, bathrooms: 1, sq_ft: 0, rent_type: "free_market",
      current_rent: 0, legal_rent: 0, preferential_rent: 0, market_rent_est: 0,
      lease_expiry: "", vacancy_rate: 0.05, renovation_budget: 0, notes: "",
    },
  });

  useEffect(() => {
    if (unit) {
      reset({
        unit_number:      unit.unit_number,
        bedrooms:         unit.bedrooms,
        bathrooms:        unit.bathrooms,
        sq_ft:            unit.sq_ft ?? 0,
        rent_type:        unit.rent_type as FormValues["rent_type"],
        current_rent:     unit.current_rent,
        legal_rent:       unit.legal_rent ?? 0,
        preferential_rent:unit.preferential_rent ?? 0,
        market_rent_est:  unit.market_rent_est ?? 0,
        lease_expiry:     unit.lease_expiry ?? "",
        vacancy_rate:     unit.vacancy_rate ?? 0.05,
        renovation_budget:unit.renovation_budget ?? 0,
        notes:            unit.notes ?? "",
      });
    }
  }, [unit, reset]);

  const rentType = watch("rent_type");
  const isRS = rentType === "stabilized";

  async function onSubmit(data: FormValues) {
    const payload: UnitCreate = {
      unit_number:      data.unit_number,
      bedrooms:         data.bedrooms,
      bathrooms:        data.bathrooms,
      sq_ft:            data.sq_ft || undefined,
      rent_type:        data.rent_type,
      current_rent:     data.current_rent,
      legal_rent:       data.legal_rent || undefined,
      preferential_rent:data.preferential_rent || undefined,
      market_rent_est:  data.market_rent_est || undefined,
      lease_expiry:     data.lease_expiry || undefined,
      vacancy_rate:     data.vacancy_rate,
      renovation_budget:data.renovation_budget,
      notes:            data.notes || undefined,
    };
    await onSave(payload);
    onClose();
  }

  const n = { valueAsNumber: true };  // shorthand for numeric registration

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
          <h2 className="text-base font-semibold text-gray-100">{unit ? "Edit Unit" : "Add Unit"}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 p-1.5 hover:bg-gray-800 rounded-lg">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="px-5 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Unit Number" placeholder="1A" {...register("unit_number", { required: true })} />
            <Select label="Rent Type" options={rentTypeOpts} {...register("rent_type")} />
            <Input label="Bedrooms" type="number" min={0} max={10} {...register("bedrooms", n)} />
            <Input label="Bathrooms" type="number" min={0} step={0.5} {...register("bathrooms", n)} />
            <Input label="Sq Ft" type="number" min={0} {...register("sq_ft", n)} />
            <Input label="Vacancy Rate" type="number" min={0} max={1} step={0.01} hint="0.05 = 5%" {...register("vacancy_rate", n)} />
          </div>

          {rentType !== "vacant" && rentType !== "owner_occupied" && (
            <div className="grid grid-cols-2 gap-3">
              <Input label="Current Rent/Mo" prefix="$" type="number" min={0} {...register("current_rent", n)} />
              <Input label="Market Rent Est." prefix="$" type="number" min={0} {...register("market_rent_est", n)} />
              {isRS && (
                <>
                  <Input label="Legal Rent" prefix="$" type="number" min={0} hint="DHCR max" {...register("legal_rent", n)} />
                  <Input label="Preferential Rent" prefix="$" type="number" min={0} hint="If below legal" {...register("preferential_rent", n)} />
                </>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Input label="Lease Expiry" type="date" {...register("lease_expiry")} />
            <Input label="Renovation Budget" prefix="$" type="number" min={0} {...register("renovation_budget", n)} />
          </div>

          <Input label="Notes" placeholder="Optional notes" {...register("notes")} />

          <div className="flex gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose} className="flex-1">Cancel</Button>
            <Button type="submit" loading={isSubmitting} className="flex-1">
              {unit ? "Save Changes" : "Add Unit"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
