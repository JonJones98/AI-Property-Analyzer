import { useParams } from "react-router-dom";

import { ScoreBadge } from "../components/ScoreBadge";
import { useCostEstimateForListing } from "../hooks/useCostEstimate";
import { useListingDetail } from "../hooks/useListings";

function Row({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="flex justify-between border-b border-slate-100 py-1.5 text-sm last:border-0 dark:border-slate-800">
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      <span className="font-medium">{value ?? "—"}</span>
    </div>
  );
}

export function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: listing, isLoading, isError } = useListingDetail(id);
  const { data: costEstimate } = useCostEstimateForListing(id);

  if (isLoading) return <p className="p-6 text-slate-500">Loading listing…</p>;
  if (isError || !listing) return <p className="p-6 text-rose-600">Listing not found.</p>;

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">
            {listing.address ?? listing.city ?? "Unnamed parcel"}
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            {listing.county} · {listing.acres} acres · ${listing.price.toLocaleString()}
          </p>
        </div>
        <ScoreBadge
          score={listing.scores?.overall_score ?? null}
          color={listing.scores?.color ?? null}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-2 font-medium">Homestead Score</h2>
          <Row label="Price Score" value={listing.scores?.price_score} />
          <Row label="Location Score" value={listing.scores?.location_score} />
          <Row label="Build Score" value={listing.scores?.build_score} />
          <Row label="Overall" value={listing.scores?.overall_score} />
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-2 font-medium">Buildability</h2>
          <Row label="Flood Zone" value={listing.flood?.flood_zone} />
          <Row label="Soil Type" value={listing.soil?.soil_type} />
          <Row label="Perk Possible" value={listing.soil?.perk_possible ? "Yes" : "No"} />
          <Row
            label="Est. Site Cost"
            value={
              listing.buildability?.estimated_site_cost
                ? `$${listing.buildability.estimated_site_cost.toLocaleString()}`
                : null
            }
          />
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-2 font-medium">Utilities</h2>
          <Row label="Electric" value={listing.utilities?.electric ? "At road" : "Not present"} />
          <Row
            label="Internet"
            value={listing.utilities?.internet ? "Available" : "Not confirmed"}
          />
          <Row label="Gas" value={listing.utilities?.gas ? "Available" : "Not present"} />
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-2 font-medium">Drive Times (minutes)</h2>
          <Row label="Costco" value={listing.distances?.costco} />
          <Row label="Whole Foods" value={listing.distances?.whole_foods} />
          <Row label="Walmart" value={listing.distances?.walmart} />
          <Row label="CVS" value={listing.distances?.cvs} />
          <Row label="Home Depot" value={listing.distances?.home_depot} />
          <Row label="Lowe's" value={listing.distances?.lowes} />
          <Row label="Hospital" value={listing.distances?.hospital} />
          <Row label="I-85" value={listing.distances?.i85} />
        </section>
      </div>

      {costEstimate && (
        <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-2 font-medium">Project Cost Estimate</h2>
          <div className="grid gap-x-8 gap-y-1 md:grid-cols-2">
            <Row label="Land Purchase" value={`$${costEstimate.land_purchase.toLocaleString()}`} />
            <Row label="Site Clearing" value={`$${costEstimate.site_clearing.toLocaleString()}`} />
            <Row label="Grading" value={`$${costEstimate.grading.toLocaleString()}`} />
            <Row label="Driveway" value={`$${costEstimate.driveway.toLocaleString()}`} />
            <Row label="Well" value={`$${costEstimate.well.toLocaleString()}`} />
            <Row label="Septic" value={`$${costEstimate.septic.toLocaleString()}`} />
            <Row label="Electrical" value={`$${costEstimate.electrical.toLocaleString()}`} />
            <Row label="Survey" value={`$${costEstimate.survey.toLocaleString()}`} />
            <Row label="Engineering" value={`$${costEstimate.engineering.toLocaleString()}`} />
            <Row label="Permits" value={`$${costEstimate.permits.toLocaleString()}`} />
            <Row
              label="Construction"
              value={`$${costEstimate.construction_cost.toLocaleString()}`}
            />
            <Row label="Solar" value={`$${costEstimate.solar.toLocaleString()}`} />
          </div>
          <div className="mt-3 border-t border-slate-200 pt-3 dark:border-slate-800">
            <Row
              label="Total Project Cost"
              value={`$${costEstimate.total_project_cost.toLocaleString()}`}
            />
            <Row
              label="Monthly Mortgage"
              value={`$${costEstimate.monthly_mortgage.toLocaleString()}`}
            />
            <Row label="Monthly Taxes" value={`$${costEstimate.monthly_taxes.toLocaleString()}`} />
            <Row
              label="Monthly Insurance"
              value={`$${costEstimate.monthly_insurance.toLocaleString()}`}
            />
            <Row label="Monthly PMI" value={`$${costEstimate.monthly_pmi.toLocaleString()}`} />
            <Row
              label="Total Monthly Payment"
              value={`$${costEstimate.total_monthly_payment.toLocaleString()}`}
            />
          </div>
        </section>
      )}

      {listing.url && (
        <a
          href={listing.url}
          target="_blank"
          rel="noreferrer"
          className="inline-block text-sm text-emerald-700 hover:underline dark:text-emerald-400"
        >
          View original listing →
        </a>
      )}
    </div>
  );
}
