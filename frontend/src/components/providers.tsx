"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useRef, type ReactNode } from "react";
import { useAuthStore } from "@/lib/stores/auth";

function AuthInit() {
  const init = useAuthStore((s) => s.init);
  const ran = useRef(false);
  useEffect(() => {
    if (!ran.current) { ran.current = true; init(); }
  }, [init]);
  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const client = useRef(new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
  }));

  return (
    <QueryClientProvider client={client.current}>
      <AuthInit />
      {children}
    </QueryClientProvider>
  );
}
