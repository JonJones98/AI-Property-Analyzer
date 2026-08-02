import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import { Link } from "react-router-dom";

import { useMapData } from "../hooks/useMapData";
import type { ScoreColor } from "../types/listing";

const NC_I85_CORRIDOR_CENTER: [number, number] = [35.75, -79.8];
const DEFAULT_ZOOM = 8;

const MARKER_COLORS: Record<ScoreColor, string> = {
  green: "#059669",
  blue: "#2563eb",
  yellow: "#d97706",
  red: "#e11d48",
};

export function MapViewPage() {
  const { data, isLoading, isError } = useMapData();

  if (isLoading) return <p className="p-6 text-slate-500">Loading map…</p>;
  if (isError || !data) return <p className="p-6 text-rose-600">Couldn't load map data.</p>;

  return (
    <div className="h-[calc(100vh-57px)] w-full">
      <MapContainer
        center={NC_I85_CORRIDOR_CENTER}
        zoom={DEFAULT_ZOOM}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {data.features.map((feature) => (
          <CircleMarker
            key={feature.properties.id}
            center={[feature.geometry.coordinates[1], feature.geometry.coordinates[0]]}
            radius={7}
            pathOptions={{
              color: feature.properties.score_color
                ? MARKER_COLORS[feature.properties.score_color]
                : "#64748b",
              fillOpacity: 0.8,
            }}
          >
            <Popup>
              <div className="space-y-1 text-sm">
                <div className="font-medium">
                  {feature.properties.address ?? feature.properties.county ?? "Parcel"}
                </div>
                <div>${feature.properties.price.toLocaleString()}</div>
                <div>{feature.properties.acres} acres</div>
                <div>Score: {feature.properties.overall_score?.toFixed(0) ?? "—"}</div>
                <Link
                  to={`/listings/${feature.properties.id}`}
                  className="text-emerald-700 hover:underline dark:text-emerald-400"
                >
                  View details →
                </Link>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
