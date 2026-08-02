import type { ScoreColor } from "../types/listing";

const COLOR_CLASSES: Record<ScoreColor, string> = {
  green: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  blue: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  yellow: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  red: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200",
};

interface ScoreBadgeProps {
  score: number | null;
  color: ScoreColor | null;
}

export function ScoreBadge({ score, color }: ScoreBadgeProps) {
  if (score === null || color === null) {
    return (
      <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-400">
        Not scored
      </span>
    );
  }

  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${COLOR_CLASSES[color]}`}>
      {score.toFixed(0)}
    </span>
  );
}
