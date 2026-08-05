import { useMemo, useState } from "react";
import { MapContainer, Polygon, Popup, TileLayer } from "react-leaflet";
import { Link } from "react-router-dom";

import { useMapData } from "../hooks/useMapData";
import type { MapFeature, ScoreColor } from "../types/listing";

const NC_I85_CORRIDOR_CENTER: [number, number] = [35.75, -79.8];
const DEFAULT_ZOOM = 8;

const MARKER_COLORS: Record<ScoreColor, string> = {
  green: "#059669",
  blue: "#2563eb",
  yellow: "#d97706",
  red: "#e11d48",
};

type LayerMode = "score" | "flood" | "value" | "elevation";

function getMarkerStyle(feature: MapFeature, mode: LayerMode) {
  if (mode === "flood") {
    const zone = feature.properties.flood_zone?.toUpperCase() ?? "";
    if (zone.includes("A") || zone.includes("V")) return { color: "#dc2626", fillOpacity: 0.8 };
    if (zone.includes("X")) return { color: "#16a34a", fillOpacity: 0.7 };
    return { color: "#64748b", fillOpacity: 0.7 };
  }

  if (mode === "value") {
    const pricePerAcre = feature.properties.price_per_acre;
    if (pricePerAcre >= 11000) return { color: "#7c3aed", fillOpacity: 0.8 };
    if (pricePerAcre >= 8000) return { color: "#0284c7", fillOpacity: 0.75 };
    return { color: "#f59e0b", fillOpacity: 0.7 };
  }

  if (mode === "elevation") {
    const elevation = feature.properties.elevation_ft ?? 0;
    if (elevation >= 900) return { color: "#92400e", fillOpacity: 0.8 };
    if (elevation >= 600) return { color: "#65a30d", fillOpacity: 0.75 };
    return { color: "#2563eb", fillOpacity: 0.7 };
  }

  return {
    color: feature.properties.score_color ? MARKER_COLORS[feature.properties.score_color] : "#64748b",
    fillOpacity: 0.8,
  };
}

export function MapViewPage() {
  const { data, isLoading, isError } = useMapData();
  const [layerMode, setLayerMode] = useState<LayerMode>("score");

  const legend = useMemo(() => {
    if (layerMode === "flood") {
      return [
        { label: "High flood risk", color: "#dc2626" },
        { label: "Low flood risk", color: "#16a34a" },
        { label: "Unknown", color: "#64748b" },
      ];
    }

    if (layerMode === "value") {
      return [
        { label: "High $/acre", color: "#7c3aed" },
        { label: "Mid $/acre", color: "#0284c7" },
        { label: "Lower $/acre", color: "#f59e0b" },
      ];
    }

    if (layerMode === "elevation") {
      return [
        { label: "High elevation", color: "#92400e" },
        { label: "Mid elevation", color: "#65a30d" },
        { label: "Low elevation", color: "#2563eb" },
      ];
    }

    return [
      { label: "Green", color: MARKER_COLORS.green },
      { label: "Blue", color: MARKER_COLORS.blue },
      { label: "Yellow", color: MARKER_COLORS.yellow },
      { label: "Red", color: MARKER_COLORS.red },
    ];
  }, [layerMode]);

  if (isLoading) return <p className="p-6 text-slate-500">Loading map…</p>;
  if (isError || !data) return <p className="p-6 text-rose-600">Couldn't load map data.</p>;

  return (
    <div className="flex h-[calc(100vh-57px)] w-full flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
        <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Visual layer:</span>
        {(["score", "flood", "value", "elevation"] as LayerMode[]).map((mode) => (
          <button
            key={mode}
            type="button"
            onClick={() => setLayerMode(mode)}
            className={`rounded-full px-3 py-1 text-sm ${
              layerMode === mode
                ? "bg-emerald-600 text-white"
                : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
            }`}
          >
            {mode === "score" ? "Homestead score" : mode === "flood" ? "Flood risk" : mode === "value" ? "Value / acre" : "Elevation"}
          </button>
        ))}
      </div>

      <div className="relative flex-1">
        <MapContainer
          center={NC_I85_CORRIDOR_CENTER}
          zoom={DEFAULT_ZOOM}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {data.features.map((feature) => {
            const style = getMarkerStyle(feature, layerMode);
            const lat = feature.geometry.coordinates[1];
            const lng = feature.geometry.coordinates[0];
            const acres = feature.properties.acres || 10;
            const scale = Math.max(0.0045, Math.min(0.04, acres / 600));
            const polygon = [
              [lat + scale * 1.15, lng - scale * 0.85],
              [lat + scale * 0.9, lng + scale * 1.2],
              [lat - scale * 0.6, lng + scale * 1.05],
              [lat - scale * 1.1, lng + scale * 0.25],
              [lat - scale * 0.8, lng - scale * 1.0],
            ] as [number, number][];

            return (
              <Polygon
                key={feature.properties.id}
                positions={polygon}
                pathOptions={{
                  color: style.color,
                  fillOpacity: Math.max(style.fillOpacity, 0.35),
                  weight: 2.5,
                  dashArray: "3",
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
                    {feature.properties.flood_zone ? (
                      <div>Flood zone: {feature.properties.flood_zone}</div>
                    ) : null}
                    <div>$/{feature.properties.price_per_acre.toLocaleString()} / acre</div>
                    {feature.properties.elevation_ft != null ? (
                      <div>Elevation: {feature.properties.elevation_ft.toFixed(0)} ft</div>
                    ) : null}
                    <Link
                      to={`/listings/${feature.properties.id}`}
                      className="text-emerald-700 hover:underline dark:text-emerald-400"
                    >
                      View details →
                    </Link>
                  </div>
                </Popup>
              </Polygon>
            );
          })}
        </MapContainer>

        <div className="absolute bottom-4 left-4 rounded-lg border border-slate-200 bg-white/95 p-3 text-sm shadow dark:border-slate-700 dark:bg-slate-900/95">
          <div className="mb-2 font-medium">Legend</div>
          <div className="space-y-1">
            {legend.map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
