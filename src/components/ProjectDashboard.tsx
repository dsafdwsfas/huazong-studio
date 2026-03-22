"use client";

import { useEffect, useState, useCallback } from "react";
import { BarChart3, CheckCircle, Clock, AlertTriangle, Users } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface Shot {
  status: string;
  assigneeName: string | null;
}

interface Props {
  projectId: string;
}

export function ProjectDashboard({ projectId }: Props) {
  const [shots, setShots] = useState<Shot[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiFetch<{ shots: Shot[] }>(
        `/api/projects/${projectId}/shots`
      );
      setShots(data.shots || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <span className="animate-spin h-5 w-5 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
      </div>
    );
  }

  const total = shots.length;
  const byStatus: Record<string, number> = {};
  const byAssignee: Record<string, number> = {};

  for (const s of shots) {
    byStatus[s.status] = (byStatus[s.status] || 0) + 1;
    const name = s.assigneeName || "未分配";
    byAssignee[name] = (byAssignee[name] || 0) + 1;
  }

  const approved = (byStatus["approved"] || 0) + (byStatus["delivered"] || 0);
  const needsWork = byStatus["needs_revision"] || 0;
  const pending = byStatus["pending_upload"] || 0;
  const progress = total > 0 ? Math.round((approved / total) * 100) : 0;

  const STATUS_LABELS: Record<string, { label: string; color: string }> = {
    pending_upload: { label: "待上传", color: "bg-yellow-400" },
    pending_review: { label: "待审查", color: "bg-blue-400" },
    needs_revision: { label: "需修改", color: "bg-red-400" },
    revised_pending_review: { label: "已修改", color: "bg-purple-400" },
    approved: { label: "通过", color: "bg-green-400" },
    delivered: { label: "已交付", color: "bg-gray-400" },
  };

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard icon={BarChart3} label="总镜头" value={total} color="text-blue-500" />
        <StatCard icon={CheckCircle} label="已通过" value={approved} color="text-green-500" />
        <StatCard icon={AlertTriangle} label="需修改" value={needsWork} color="text-red-500" />
        <StatCard icon={Clock} label="待上传" value={pending} color="text-yellow-500" />
      </div>

      {/* Progress Bar */}
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">整体进度</span>
          <span className="text-sm font-bold">{progress}%</span>
        </div>
        <div className="h-3 bg-[var(--secondary)] rounded-full overflow-hidden flex">
          {Object.entries(byStatus)
            .sort(([a], [b]) => {
              const order = ["approved", "delivered", "revised_pending_review", "pending_review", "needs_revision", "pending_upload"];
              return order.indexOf(a) - order.indexOf(b);
            })
            .map(([status, count]) => {
              const config = STATUS_LABELS[status];
              if (!config || count === 0) return null;
              return (
                <div
                  key={status}
                  className={`h-full ${config.color} transition-all`}
                  style={{ width: `${(count / total) * 100}%` }}
                  title={`${config.label}: ${count}`}
                />
              );
            })}
        </div>
        <div className="flex gap-3 mt-2 flex-wrap">
          {Object.entries(byStatus).map(([status, count]) => {
            const config = STATUS_LABELS[status];
            if (!config) return null;
            return (
              <div key={status} className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${config.color}`} />
                <span className="text-xs text-[var(--muted-foreground)]">
                  {config.label} {count}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Assignee Distribution */}
      {Object.keys(byAssignee).length > 0 && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-4">
          <h4 className="text-sm font-medium mb-3 flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5" />
            任务分配
          </h4>
          <div className="space-y-2">
            {Object.entries(byAssignee)
              .sort(([, a], [, b]) => b - a)
              .map(([name, count]) => (
                <div key={name} className="flex items-center gap-2">
                  <span className="text-xs w-16 truncate">{name}</span>
                  <div className="flex-1 h-2 bg-[var(--secondary)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[var(--primary)] rounded-full"
                      style={{ width: `${(count / total) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-[var(--muted-foreground)] w-8 text-right">
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof BarChart3;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="bg-[var(--card)] border border-[var(--border)] rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon className={`h-3.5 w-3.5 ${color}`} />
        <span className="text-xs text-[var(--muted-foreground)]">{label}</span>
      </div>
      <p className="text-xl font-bold">{value}</p>
    </div>
  );
}
