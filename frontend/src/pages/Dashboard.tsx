import { API_BASE_URL } from "../api/client";
import { useDashboard } from "../hooks/useDashboard";

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}

export function DashboardPage() {
  const { data, isLoading, isError } = useDashboard();

  if (isLoading) return <p className="p-6 text-slate-500">Loading dashboard…</p>;
  if (isError || !data)
    return (
      <p className="p-6 text-rose-600">
        Couldn't load dashboard metrics. Is the backend running and reachable at{" "}
        {API_BASE_URL}?
      </p>
    );

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <h1 className="text-xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatTile label="Properties Found" value={String(data.properties_found)} />
        <StatTile label="Average Price" value={`$${data.average_price.toLocaleString()}`} />
        <StatTile
          label="Avg Price / Acre"
          value={`$${data.average_price_per_acre.toLocaleString()}`}
        />
        <StatTile
          label="Top Homestead Score"
          value={data.top_homestead_score?.toFixed(0) ?? "—"}
        />
        <StatTile label="New Today" value={String(data.new_today)} />
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="mb-3 font-medium">County Breakdown</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500 dark:text-slate-400">
              <th className="pb-2">County</th>
              <th className="pb-2">Listings</th>
              <th className="pb-2">Avg Price</th>
            </tr>
          </thead>
          <tbody>
            {data.county_breakdown.map((row) => (
              <tr key={row.county} className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-2">{row.county}</td>
                <td className="py-2">{row.count}</td>
                <td className="py-2">${row.avg_price.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
