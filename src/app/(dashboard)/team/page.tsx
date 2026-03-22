"use client";

import { useEffect, useState } from "react";
import { Users, Clock, Shield, Activity } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface LogEntry {
  id: string;
  userName: string;
  projectName: string | null;
  action: string;
  details: any;
  createdAt: string;
}

const ROLE_LABELS: Record<string, string> = {
  admin: "管理员",
  director: "导演",
  artist: "美术",
  readonly: "只读",
};

const ACTION_LABELS: Record<string, string> = {
  "project.create": "创建项目",
  "project.archive": "归档项目",
  "project.unarchive": "恢复项目",
  "shot.create": "添加镜头",
  "shot.parse": "拆解剧本",
  "asset.upload": "上传资产",
  "annotation.create": "添加批注",
  "task.create": "创建任务",
  "task.update": "更新任务",
  "credit.log": "登记积分",
  "character.create": "创建角色",
  "prop.create": "创建道具",
  "scene.create": "创建场景",
  "style.extract": "提取风格",
  "style.template": "保存模板",
};

export default function TeamPage() {
  const [activeTab, setActiveTab] = useState<"members" | "logs">("members");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);

  async function loadLogs() {
    setLogsLoading(true);
    try {
      const data = await apiFetch<{ logs: LogEntry[] }>("/api/activity-logs");
      setLogs(data.logs);
    } catch {
      // May not be admin
    } finally {
      setLogsLoading(false);
    }
  }

  useEffect(() => {
    if (activeTab === "logs") loadLogs();
  }, [activeTab]);

  return (
    <div className="p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Users className="h-5 w-5 text-[var(--primary)]" />
          团队管理
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] mt-1">
          成员管理和操作日志
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-[var(--border)]">
        <button
          onClick={() => setActiveTab("members")}
          className={`flex items-center gap-1.5 px-4 py-2 text-sm transition-colors border-b-2 -mb-px ${
            activeTab === "members"
              ? "border-[var(--primary)] text-[var(--foreground)] font-medium"
              : "border-transparent text-[var(--muted-foreground)]"
          }`}
        >
          <Shield className="h-3.5 w-3.5" />
          成员列表
        </button>
        <button
          onClick={() => setActiveTab("logs")}
          className={`flex items-center gap-1.5 px-4 py-2 text-sm transition-colors border-b-2 -mb-px ${
            activeTab === "logs"
              ? "border-[var(--primary)] text-[var(--foreground)] font-medium"
              : "border-transparent text-[var(--muted-foreground)]"
          }`}
        >
          <Activity className="h-3.5 w-3.5" />
          操作日志
        </button>
      </div>

      {/* Members Tab */}
      {activeTab === "members" && (
        <div className="space-y-3">
          <p className="text-sm text-[var(--muted-foreground)]">
            默认管理员账号：13800000000 / admin123
          </p>
          <p className="text-sm text-[var(--muted-foreground)]">
            邀请码：HUAZONG2026（注册时使用）
          </p>
          <div className="mt-4 bg-[var(--card)] border border-[var(--border)] rounded-lg p-4">
            <h3 className="font-medium text-sm mb-3">角色权限说明</h3>
            <div className="space-y-2">
              {Object.entries(ROLE_LABELS).map(([role, label]) => (
                <div key={role} className="flex items-center gap-3">
                  <span className="text-xs font-medium px-2 py-1 rounded bg-[var(--secondary)] w-16 text-center">
                    {label}
                  </span>
                  <span className="text-xs text-[var(--muted-foreground)]">
                    {role === "admin" && "全部权限 + 成员管理 + 项目设置 + 操作日志"}
                    {role === "director" && "审查批注 + 状态变更 + 角色/道具管理 + 创建项目"}
                    {role === "artist" && "上传资产 + 查看批注 + 使用提示词库"}
                    {role === "readonly" && "只能浏览不能修改"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Activity Logs Tab */}
      {activeTab === "logs" && (
        <div>
          {logsLoading ? (
            <div className="flex justify-center py-12">
              <span className="animate-spin h-6 w-6 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 text-[var(--muted-foreground)]">
              <Activity className="h-10 w-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">暂无操作日志</p>
            </div>
          ) : (
            <div className="space-y-1.5">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-center gap-3 px-3 py-2.5 bg-[var(--card)] border border-[var(--border)] rounded-lg"
                >
                  <Clock className="h-3.5 w-3.5 text-[var(--muted-foreground)] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs">
                      <span className="font-medium">{log.userName}</span>
                      <span className="text-[var(--muted-foreground)]">
                        {" "}
                        {ACTION_LABELS[log.action] || log.action}
                      </span>
                      {log.projectName && (
                        <span className="text-[var(--muted-foreground)]">
                          {" "}— {log.projectName}
                        </span>
                      )}
                    </p>
                  </div>
                  <span className="text-xs text-[var(--muted-foreground)] shrink-0">
                    {new Date(log.createdAt).toLocaleString("zh-CN", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
