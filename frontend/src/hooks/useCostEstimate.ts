import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api/client";
import type { CostEstimateResult } from "../types/listing";

export function useCostEstimateForListing(listingId: string | undefined) {
  return useQuery({
    queryKey: ["cost-estimate", listingId],
    queryFn: () => apiGet<CostEstimateResult>(`/cost-estimator/${listingId}`),
    enabled: Boolean(listingId),
  });
}
