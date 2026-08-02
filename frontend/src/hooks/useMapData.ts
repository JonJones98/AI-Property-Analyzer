import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api/client";
import type { MapData } from "../types/listing";

export function useMapData() {
  return useQuery({
    queryKey: ["map"],
    queryFn: () => apiGet<MapData>("/map"),
  });
}
