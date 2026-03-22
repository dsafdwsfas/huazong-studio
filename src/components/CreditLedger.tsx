"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Coins, TrendingUp, BarChart3 } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import { CREDIT_PLATFORMS } from "@/lib/constants";
import { CreditChart } from "./CreditChart";

interface CreditLog {
  id: string;
  userId: string;
  userName: string;
  platform: string;
  amount: number;
  note: string | null;
  loggedAt: string;
}

interface Summary {
  totalAmount: number;
  byPlatform: Record<string, number>;
  byUser: Record<string, { name: string; amount: number }>;
}

interface Props {
  projectId: string;
}

export function CreditLedger({ projectId }: Props) {
  const [logs, setLogs] = useState<CreditLog[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [formPlatform, setFormPlatform] = useState<string>(CREDIT_PLATFORMS[0]);
  const [formAmount, setFormAmount] = useState("");
  const [formNote, setFormNote] = useState("");
  const [creating, setCreating] = useState(false);
  const [filterPlatform, setFilterPlatform] = useState<string | null>(null);
  const [showChart, setShowChart] = useState(false);

  const loadLogs = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterPlatform) params.set("platform", filterPlatform);
      const data = await apiFetch<{ logs: CreditLog[]; summary: Summary }>(
        `/api/projects/${projectId}/credits?${params}`
      );
      setLogs(data.logs);
      setSummary(data.summary);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [projectId, filterPlatform]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const amount = Number(formAmount);
    if (!amount || amount <= 0) return;
    setCreating(true);
    try {
      await apiFetch(`/api/projects/${projectId}/credits`, {
        method: "POST",
        body: JSON.stringify({
          platform: formPlatform,
          amount,
          note: formNote || undefined,
        }),
      });
      setShowCreate(false);
      setFormAmount("");
      setFormNote("");
      loadLogs();
    } catch (err) {
      alert(err instanceof Error ? err.message : "登记失败");
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <span className="animate-spin h-6 w-6 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <Coins className="h-4 w-4 text-[var(--primary)]" />
          积分台账
        </h3>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90"
        >
          <Plus className="h-3 w-3" />
          快捷登记
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-3">
            <p className="text-xs text-[var(--muted-foreground)]">总消耗</p>
            <p className="text-lg font-bold mt-0.5">{summary.totalAmount.toLocaleString()}</p>
          </div>
          {Object.entries(summary.byPlatform)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 3)
            .map(([platform, amount]) => (
              <div key={platform} className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-3">
                <p className="text-xs text-[var(--muted-foreground)] truncate">{platform}</p>
                <p className="text-lg font-bold mt-0.5">{amount.toLocaleString()}</p>
              </div>
            ))}
        </div>
      )}

      {/* Chart toggle + visualization */}
      {summary && summary.totalAmount > 0 && (
        <div className="mb-4">
          <button
            onClick={() => setShowChart(!showChart)}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-lg bg-[var(--secondary)] hover:bg-[var(--accent)] mb-3"
          >
            <BarChart3 className="h-3 w-3" />
            {showChart ? "隐藏图表" : "显示图表"}
          </button>
          {showChart && (
            <CreditChart byPlatform={summary.byPlatform} byUser={summary.byUser} />
          )}
        </div>
      )}

      {/* Platform Filter */}
      <div className="flex gap-1.5 flex-wrap mb-4">
        <button
          onClick={() => setFilterPlatform(null)}
          className={`px-2 py-1 text-xs rounded-full transition-colors ${
            !filterPlatform
              ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
              : "bg-[var(--secondary)] hover:bg-[var(--accent)]"
          }`}
        >
          全部
        </button>
        {CREDIT_PLATFORMS.map((p) => (
          <button
            key={p}
            onClick={() => setFilterPlatform(filterPlatform === p ? null : p)}
            className={`px-2 py-1 text-xs rounded-full transition-colors ${
              filterPlatform === p
                ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                : "bg-[var(--secondary)] hover:bg-[var(--accent)]"
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Log List */}
      {logs.length === 0 ? (
        <div className="text-center py-12 text-[var(--muted-foreground)]">
          <TrendingUp className="h-10 w-10 mx-auto mb-2 opacity-30" />
          <p className="text-sm">暂无消耗记录</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {logs.map((log) => (
            <div
              key={log.id}
              className="flex items-center gap-3 px-3 py-2.5 bg-[var(--card)] border border-[var(--border)] rounded-lg"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium">{log.userName}</span>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--secondary)]">
                    {log.platform}
                  </span>
                </div>
                {log.note && (
                  <p className="text-xs text-[var(--muted-foreground)] mt-0.5 truncate">
                    {log.note}
                  </p>
                )}
              </div>
              <div className="text-right shrink-0">
                <p className="text-sm font-bold">{log.amount.toLocaleString()}</p>
                <p className="text-xs text-[var(--muted-foreground)]">
                  {new Date(log.loggedAt).toLocaleDateString("zh-CN", {
                    month: "short",
                    day: "numeric",
                  })}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-semibold mb-4">快捷登记</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="text-xs font-medium mb-1 block">平台 *</label>
                <div className="flex gap-1.5 flex-wrap">
                  {CREDIT_PLATFORMS.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setFormPlatform(p)}
                      className={`px-2.5 py-1.5 text-xs rounded-lg transition-colors ${
                        formPlatform === p
                          ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                          : "bg-[var(--secondary)] hover:bg-[var(--accent)]"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">消耗数量 *</label>
                <input
                  type="number"
                  value={formAmount}
                  onChange={(e) => setFormAmount(e.target.value)}
                  placeholder="积分/次数/金额"
                  min="1"
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  autoFocus
                />
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">备注</label>
                <input
                  type="text"
                  value={formNote}
                  onChange={(e) => setFormNote(e.target.value)}
                  placeholder="可选备注"
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                />
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-sm rounded-lg border border-[var(--border)] hover:bg-[var(--accent)]"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={creating || !formAmount}
                  className="px-4 py-2 text-sm font-medium rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50"
                >
                  {creating ? "登记中..." : "登记"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
