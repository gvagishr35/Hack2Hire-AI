const STYLES: Record<string, string> = {
  easy: "bg-emerald-500/20 text-emerald-200 border-emerald-500/40",
  medium: "bg-amber-500/20 text-amber-200 border-amber-500/40",
  hard: "bg-red-500/20 text-red-200 border-red-500/40",
};

type DifficultyBadgeProps = {
  difficulty: string;
};

export function DifficultyBadge({ difficulty }: DifficultyBadgeProps) {
  const key = difficulty.toLowerCase();
  return (
    <span
      className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${
        STYLES[key] ?? STYLES.medium
      }`}
    >
      {difficulty}
    </span>
  );
}
