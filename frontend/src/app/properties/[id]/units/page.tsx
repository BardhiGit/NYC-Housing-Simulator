"use client";

import { use, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { propertiesApi } from "@/lib/api/properties";
import { RentRollTable } from "@/components/units/RentRollTable";
import { UnitFormModal } from "@/components/units/UnitFormModal";
import type { UnitCreate, UnitResponse } from "@/lib/types/property";

export default function UnitsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const qc = useQueryClient();
  const [modalUnit, setModalUnit] = useState<UnitResponse | null | undefined>(undefined);

  const { data: units = [], isPending } = useQuery({
    queryKey: ["units", id],
    queryFn: () => propertiesApi.listUnits(id),
  });

  const addMutation = useMutation({
    mutationFn: (data: UnitCreate) => propertiesApi.addUnit(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["units", id] }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ uid, data }: { uid: string; data: UnitCreate }) => propertiesApi.updateUnit(id, uid, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["units", id] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (uid: string) => propertiesApi.deleteUnit(id, uid),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["units", id] }),
  });

  async function handleSave(data: UnitCreate) {
    if (modalUnit) {
      await updateMutation.mutateAsync({ uid: modalUnit.id, data });
    } else {
      await addMutation.mutateAsync(data);
    }
  }

  if (isPending) return <div className="text-sm text-gray-500">Loading rent roll…</div>;

  return (
    <div className="max-w-5xl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white">Rent Roll</h2>
        <p className="text-xs text-gray-500">
          After adding units, visit Financials to run the full analysis.
        </p>
      </div>

      <RentRollTable
        units={units}
        onAdd={() => setModalUnit(null)}
        onEdit={(u) => setModalUnit(u)}
        onDelete={(u) => {
          if (window.confirm(`Delete unit ${u.unit_number}?`)) {
            deleteMutation.mutate(u.id);
          }
        }}
      />

      {modalUnit !== undefined && (
        <UnitFormModal
          unit={modalUnit}
          onClose={() => setModalUnit(undefined)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
