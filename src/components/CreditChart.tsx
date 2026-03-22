"use client";

/** Simple bar chart for credit consumption - pure CSS, no dependencies */

interface BarData {
  label: string;
  value: number;
  color: string;
}

const PLATFORM_COLORS: Record<string, string> = {
  "即梦 (Seedance)": "bg-violet-400",
  "可灵 (Kling)": "bg-blue-400",
  "Midjourney": "bg-cyan-400",
  "Flux": "bg-amber-400",
  "ComfyUI": "bg-emerald-400",
  "Gemini": "bg-red-400",
  "海螺 (Hailuo)": "bg-pink-400",
  "Vidu": "bg-indigo-400",
  "其他": "bg-gray-400",
};

interface Props {
  byPlatform: Record<string, number>;
  byUser: Record<string, { name: string; amount: number }>;
}

export function CreditChart({ byPlatform, byUser }: Props) {
  const platformBars: BarData[] = Object.entries(byPlatform)
    .sort(([, a], [, b]) => b - a)
    .map(([platform, value]) => ({
      label: platform.replace(/\s*\(.*\)/, ""),
      value,
      color: PLATFORM_COLORS[platform] || "bg-gray-400",
    }));

  const userBars: BarData[] = Object.values(byUser)
    .sort((a, b) => b.amount - a.amount)
    .map((u, i) => ({
      label: u.name,
      value: u.amount,
      color: ["bg-blue-400", "bg-emerald-400", "bg-amber-400", "bg-violet-400", "bg-rose-400"][i % 5],
    }));

  const maxPlatform = Math.max(...platformBars.map((b) => b.value), 1);
  const maxUser = Math.max(...userBars.map((b) => b.value), 1);

  if (platformBars.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Platform chart */}
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-4">
        <h4 className="text-xs font-medium mb-3">按平台消耗</h4>
        <div className="space-y-2">
          {platformBars.map((bar) => (
            <div key={bar.label} className="flex items-center gap-2">
              <span className="text-xs w-14 truncate text-right text-[var(--muted-foreground)]">
                {bar.label}
              </span>
              <div className="flex-1 h-5 bg-[var(--secondary)] rounded overflow-hidden">
                <div
                  className={`h-full ${bar.color} rounded transition-all flex items-center justify-end pr-1`}
                  style={{ width: `${(bar.value / maxPlatform) * 100}%`, minWidth: bar.value > 0 ? "24px" : "0" }}
                >
                  <span className="text-xs text-white font-mono">
                    {bar.value}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* User chart */}
      {userBars.length > 0 && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-4">
          <h4 className="text-xs font-medium mb-3">按成员消耗</h4>
          <div className="space-y-2">
            {userBars.map((bar) => (
              <div key={bar.label} className="flex items-center gap-2">
                <span className="text-xs w-14 truncate text-right text-[var(--muted-foreground)]">
                  {bar.label}
                </span>
                <div className="flex-1 h-5 bg-[var(--secondary)] rounded overflow-hidden">
                  <div
                    className={`h-full ${bar.color} rounded transition-all flex items-center justify-end pr-1`}
                    style={{ width: `${(bar.value / maxUser) * 100}%`, minWidth: bar.value > 0 ? "24px" : "0" }}
                  >
                    <span className="text-xs text-white font-mono">
                      {bar.value}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
