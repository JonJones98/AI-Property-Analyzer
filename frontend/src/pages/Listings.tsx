import { useState } from "react";
import { Link } from "react-router-dom";

import { ScoreBadge } from "../components/ScoreBadge";
import { useListings } from "../hooks/useListings";
import type { ListingFilters } from "../types/listing";

export function ListingsPage() {
  const [filters, setFilters] = useState<ListingFilters>({ limit: 50, offset: 0 });
  const { data: listings, isLoading, isError } = useListings(filters);

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <h1 className="text-xl font-semibold">Listings</h1>

      <div className="flex flex-wrap gap-3">
        <input
          type="number"
          placeholder="Min price"
          className="w-32 rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              min_price: e.target.value ? Number(e.target.value) : undefined,
            }))
          }
        />
        <input
          type="number"
          placeholder="Max price"
          className="w-32 rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              max_price: e.target.value ? Number(e.target.value) : undefined,
            }))
          }
        />
        <input
          type="number"
          placeholder="Min score"
          className="w-32 rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              min_score: e.target.value ? Number(e.target.value) : undefined,
            }))
          }
        />
        <input
          type="text"
          placeholder="County"
          className="w-40 rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
          onChange={(e) =>
            setFilters((f) => ({ ...f, county: e.target.value || undefined }))
          }
        />
      </div>

      {isLoading && <p className="text-slate-500">Loading listings…</p>}
      {isError && <p className="text-rose-600">Couldn't load listings.</p>}

      {listings && (
        <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left dark:bg-slate-800">
              <tr>
                <th className="p-3">Address</th>
                <th className="p-3">County</th>
                <th className="p-3">Price</th>
                <th className="p-3">Acres</th>
                <th className="p-3">$/Acre</th>
                <th className="p-3">Score</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-slate-900">
              {listings.map((listing) => (
                <tr
                  key={listing.id}
                  className="border-t border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="p-3">
                    <Link to={`/listings/${listing.id}`} className="hover:underline">
                      {listing.address ?? listing.city ?? "Unnamed parcel"}
                    </Link>
                  </td>
                  <td className="p-3">{listing.county}</td>
                  <td className="p-3">${listing.price.toLocaleString()}</td>
                  <td className="p-3">{listing.acres}</td>
                  <td className="p-3">${listing.price_per_acre.toLocaleString()}</td>
                  <td className="p-3">
                    <ScoreBadge
                      score={listing.scores?.overall_score ?? null}
                      color={listing.scores?.color ?? null}
                    />
                  </td>
                </tr>
              ))}
              {listings.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-500">
                    No listings match these filters yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
