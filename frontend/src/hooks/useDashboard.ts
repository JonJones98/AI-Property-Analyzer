import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api/client";
import type { Dashboard } from "../types/listing";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiGet<Dashboard>("/dashboard"),
  });
}
