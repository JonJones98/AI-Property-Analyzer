export type ListingStatus = "active" | "pending" | "sold" | "off_market";
export type ScoreColor = "green" | "blue" | "yellow" | "red";

export interface Scores {
  price_score: number | null;
  location_score: number | null;
  build_score: number | null;
  overall_score: number | null;
  color: ScoreColor | null;
}

export interface NeighborParcel {
  parcel_number: string | null;
  owner: string | null;
  acres: number | null;
  boundary: [number, number][] | null;
}

export interface Parcel {
  parcel_number: string | null;
  owner: string | null;
  tax_value: number | null;
  zoning: string | null;
  road_frontage: boolean | null;
  utilities: string | null;
  elevation_ft: number | null;
  /** "nc_onemap" for real statewide parcel data, "estimated" for the fallback stub. */
  data_source: "nc_onemap" | "estimated";
  boundary_coordinates: [number, number][] | null;
  neighbor_parcels: NeighborParcel[] | null;
}

export interface Soil {
  soil_type: string | null;
  perk_possible: boolean | null;
  soil_rating: number | null;
}

export interface Flood {
  flood_zone: string | null;
}

export interface Buildability {
  well_required: boolean | null;
  septic_required: boolean | null;
  estimated_site_cost: number | null;
}

export interface Utilities {
  electric: boolean | null;
  internet: boolean | null;
  gas: boolean | null;
}

export interface Distances {
  costco: number | null;
  whole_foods: number | null;
  walmart: number | null;
  cvs: number | null;
  hospital: number | null;
  lowes: number | null;
  home_depot: number | null;
  i85: number | null;
}

export interface Listing {
  id: string;
  provider: string;
  address: string | null;
  county: string | null;
  city: string | null;
  zipcode: string | null;
  latitude: number;
  longitude: number;
  price: number;
  acres: number;
  price_per_acre: number;
  status: ListingStatus;
  url: string | null;
  last_updated: string;
  scores: Scores | null;
}

export interface ListingDetail extends Listing {
  parcel: Parcel | null;
  soil: Soil | null;
  flood: Flood | null;
  buildability: Buildability | null;
  utilities: Utilities | null;
  distances: Distances | null;
}

export interface ListingFilters {
  county?: string;
  status?: ListingStatus;
  min_price?: number;
  max_price?: number;
  min_acres?: number;
  max_acres?: number;
  min_score?: number;
  road_frontage?: boolean;
  limit?: number;
  offset?: number;
}

export interface CountyBreakdown {
  county: string;
  count: number;
  avg_price: number;
}

export interface Dashboard {
  properties_found: number;
  average_price: number;
  average_price_per_acre: number;
  top_homestead_score: number | null;
  best_deal_listing_id: string | null;
  new_today: number;
  county_breakdown: CountyBreakdown[];
}

export interface CostEstimateInput {
  land_price: number;
  acres: number;
  needs_well?: boolean;
  needs_septic?: boolean;
  driveway_length_feet?: number;
  home_sqft?: number;
  solar_system_kw?: number;
  include_solar?: boolean;
  down_payment_pct?: number;
  annual_interest_rate?: number;
  term_years?: number;
  assessed_tax_value?: number;
}

export interface CostEstimateResult {
  land_purchase: number;
  site_clearing: number;
  grading: number;
  driveway: number;
  well: number;
  septic: number;
  electrical: number;
  survey: number;
  engineering: number;
  permits: number;
  construction_cost: number;
  solar: number;
  total_project_cost: number;
  down_payment: number;
  loan_amount: number;
  monthly_mortgage: number;
  monthly_taxes: number;
  monthly_insurance: number;
  monthly_pmi: number;
  total_monthly_payment: number;
}

export interface MapFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: {
    id: string;
    address: string | null;
    county: string | null;
    price: number;
    acres: number;
    price_per_acre: number;
    status: ListingStatus;
    overall_score: number | null;
    score_color: ScoreColor | null;
    flood_zone: string | null;
    soil_rating: number | null;
    perk_possible: boolean | null;
    estimated_site_cost: number | null;
    elevation_ft: number | null;
    /** "nc_onemap" for real statewide parcel data, "estimated" for the fallback stub. */
    parcel_data_source: "nc_onemap" | "estimated" | null;
    parcel_boundary: [number, number][] | null;
    neighbor_parcels: NeighborParcel[] | null;
  };
}

export interface MapData {
  type: "FeatureCollection";
  features: MapFeature[];
}
