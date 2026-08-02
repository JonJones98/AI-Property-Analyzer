import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api/client";
import type { Listing, ListingDetail, ListingFilters } from "../types/listing";

function buildQueryString(filters: ListingFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function useListings(filters: ListingFilters) {
  return useQuery({
    queryKey: ["listings", filters],
    queryFn: () => apiGet<Listing[]>(`/listings${buildQueryString(filters)}`),
  });
}

export function useListingDetail(listingId: string | undefined) {
  return useQuery({
    queryKey: ["listing", listingId],
    queryFn: () => apiGet<ListingDetail>(`/listing/${listingId}`),
    enabled: Boolean(listingId),
  });
}
