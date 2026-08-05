import { Fragment, useMemo, useState } from "react";
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

// Real parcel boundaries + neighbors come from NC OneMap's statewide
// parcels FeatureServer (app/services/county_gis.py) when available. Some
// points fall outside its coverage (API hiccup, or a mock listing's random
// coordinate missing a mapped parcel) — for those we fall back to an
// illustrative synthetic shape (deterministic, seeded per-listing) so the
// map still shows *something* rather than nothing.
const NEIGHBOR_COUNT = 6;
const NEIGHBOR_RING_MULTIPLIER = 2.0;
const SYNTHETIC_NEIGHBOR_STYLE = {
  color: "#94a3b8",
  weight: 1,
  fillOpacity: 0,
  dashArray: "2,3",
  interactive: false,
} as const;
const REAL_NEIGHBOR_STYLE = {
  color: "#64748b",
  weight: 1.5,
  fillOpacity: 0,
  interactive: false,
} as const;

function hasRealRing(ring: [number, number][] | null | undefined): ring is [number, number][] {
  return Boolean(ring && ring.length > 2);
}

function hashSeed(id: string): number {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash << 5) - hash + id.charCodeAt(i);
    hash |= 0;
  }
  return hash >>> 0;
}

function mulberry32(seed: number): () => number {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Degrees-per-foot conversion so synthetic shapes are actually sized to
// the listing's real acreage, rather than an arbitrary visual scale — the
// previous formula (acres / 600 degrees, unclamped by geography) rendered
// a 12-acre parcel as ~1.4 miles across, easily swallowing nearby roads.
const FEET_PER_ACRE = 43_560;
const FEET_PER_DEGREE_LATITUDE = 364_320; // ~69 miles

function acreageToDegreeScale(acres: number, lat: number): { latScale: number; lonScale: number } {
  const halfSideFeet = Math.sqrt(acres * FEET_PER_ACRE) / 2;
  const latDegreesPerFoot = 1 / FEET_PER_DEGREE_LATITUDE;
  const lonDegreesPerFoot = latDegreesPerFoot / Math.cos((lat * Math.PI) / 180);
  return {
    latScale: halfSideFeet * latDegreesPerFoot,
    lonScale: halfSideFeet * lonDegreesPerFoot,
  };
}

function buildNeighborParcel(
  lat: number,
  lng: number,
  latScale: number,
  lonScale: number,
  rng: () => number
): [number, number][] {
  const vertexCount = 5 + Math.floor(rng() * 2);
  const baseAngle = rng() * Math.PI * 2;
  const points: [number, number][] = [];
  for (let i = 0; i < vertexCount; i++) {
    const angle = baseAngle + (i / vertexCount) * Math.PI * 2;
    const radiusFactor = 0.55 + rng() * 0.35;
    points.push([
      lat + Math.sin(angle) * latScale * radiusFactor,
      lng + Math.cos(angle) * lonScale * radiusFactor,
    ]);
  }
  return points;
}

function buildSurroundingParcels(
  lat: number,
  lng: number,
  latScale: number,
  lonScale: number,
  rng: () => number
): [number, number][][] {
  const neighbors: [number, number][][] = [];
  for (let i = 0; i < NEIGHBOR_COUNT; i++) {
    const angle = (i / NEIGHBOR_COUNT) * Math.PI * 2 + rng() * 0.4;
    const distanceFactor = NEIGHBOR_RING_MULTIPLIER + rng() * 0.6;
    const centerLat = lat + Math.sin(angle) * latScale * distanceFactor;
    const centerLng = lng + Math.cos(angle) * lonScale * distanceFactor;
    const neighborScaleFactor = 0.6 + rng() * 0.5;
    neighbors.push(
      buildNeighborParcel(
        centerLat,
        centerLng,
        latScale * neighborScaleFactor,
        lonScale * neighborScaleFactor,
        rng
      )
    );
  }
  return neighbors;
}

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

  const realBoundaryCount = useMemo(
    () =>
      data?.features.filter((f) => f.properties.parcel_data_source === "nc_onemap").length ?? 0,
    [data]
  );

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
            const { latScale, lonScale } = acreageToDegreeScale(acres, lat);

            const hasRealBoundary = hasRealRing(feature.properties.parcel_boundary);
            const syntheticPolygon = [
              [lat + latScale * 1.15, lng - lonScale * 0.85],
              [lat + latScale * 0.9, lng + lonScale * 1.2],
              [lat - latScale * 0.6, lng + lonScale * 1.05],
              [lat - latScale * 1.1, lng + lonScale * 0.25],
              [lat - latScale * 0.8, lng - lonScale * 1.0],
            ] as [number, number][];
            const polygon = hasRealBoundary
              ? feature.properties.parcel_boundary!
              : syntheticPolygon;

            const realNeighbors = (feature.properties.neighbor_parcels ?? []).filter((n) =>
              hasRealRing(n.boundary)
            );
            const useRealNeighbors = realNeighbors.length > 0;
            const rng = mulberry32(hashSeed(feature.properties.id));
            const syntheticNeighbors = useRealNeighbors
              ? []
              : buildSurroundingParcels(lat, lng, latScale, lonScale, rng);

            return (
              <Fragment key={feature.properties.id}>
                {useRealNeighbors
                  ? realNeighbors.map((neighbor, i) => (
                      <Polygon
                        key={`${feature.properties.id}-neighbor-${i}`}
                        positions={neighbor.boundary!}
                        pathOptions={REAL_NEIGHBOR_STYLE}
                      />
                    ))
                  : syntheticNeighbors.map((neighbor, i) => (
                      <Polygon
                        key={`${feature.properties.id}-neighbor-${i}`}
                        positions={neighbor}
                        pathOptions={SYNTHETIC_NEIGHBOR_STYLE}
                      />
                    ))}
                <Polygon
                  positions={polygon}
                  pathOptions={{
                    color: style.color,
                    fillOpacity: Math.max(style.fillOpacity, 0.35),
                    weight: 2.5,
                    dashArray: hasRealBoundary ? undefined : "3",
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
                      <div className="text-xs text-slate-500">
                        {feature.properties.parcel_data_source === "nc_onemap"
                          ? "Parcel boundary: NC OneMap (verified)"
                          : "Parcel boundary: estimated"}
                      </div>
                      <Link
                        to={`/listings/${feature.properties.id}`}
                        className="text-emerald-700 hover:underline dark:text-emerald-400"
                      >
                        View details →
                      </Link>
                    </div>
                  </Popup>
                </Polygon>
              </Fragment>
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
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full border border-slate-500" />
              <span>Neighboring parcels (NC OneMap)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full border border-dashed border-slate-400" />
              <span>Neighboring parcels (estimated)</span>
            </div>
          </div>
          <p className="mt-2 max-w-[220px] text-xs text-slate-400 dark:text-slate-500">
            {realBoundaryCount} of {data.features.length} parcels use verified NC OneMap
            boundaries; the rest are illustrative estimates.
          </p>
        </div>
      </div>
    </div>
  );
}
