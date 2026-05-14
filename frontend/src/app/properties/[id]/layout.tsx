"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { PropertyNav } from "@/components/layout/PropertyNav";
import { propertiesApi } from "@/lib/api/properties";

export default function PropertyLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: property } = useQuery({
    queryKey: ["property", id],
    queryFn: () => propertiesApi.get(id),
  });

  return (
    <AppShell>
      <PropertyNav propertyId={id} propertyName={property?.name || property?.address || "Loading…"} />
      <div className="p-6">{children}</div>
    </AppShell>
  );
}
