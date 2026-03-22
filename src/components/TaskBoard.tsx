"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, GripVertical, Calendar, Flag } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface Task {
  id: string;
  title: string;
  status: "pending" | "in_progress" | "completed";
  priority: "low" | "medium" | "high";
  assigneeName: string | null;
  assigneeId: string | null;
  dueDate: string | null;
  shotId: string | null;
  createdAt: string;
}

const COLUMNS = [
  { status: "pending", label: "待分配", color: "border-t-yellow-400" },
  { status: "in_progress", label: "进行中", color: "border-t-blue-400" },
  { status: "completed", label: "已完成", color: "border-t-green-400" },
] as const;

const PRIORITY_STYLES = {
  high: "text-red-600 bg-red-50",
  medium: "text-yellow-600 bg-yellow-50",
  low: "text-gray-500 bg-gray-50",
};

const PRIORITY_LABELS = { high: "高", medium: "中", low: "低" };

interface Props {
  projectId: string;
}

export function TaskBoard({ projectId }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [formTitle, setFormTitle] = useState("");
  const [formPriority, setFormPriority] = useState<"low" | "medium" | "high">("medium");
  const [creating, setCreating] = useState(false);
  const [dragTask, setDragTask] = useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiFetch<{ tasks: Task[] }>(
        `/api/projects/${projectId}/tasks`
      );
      setTasks(data.tasks);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formTitle.trim()) return;
    setCreating(true);
    try {
      await apiFetch(`/api/projects/${projectId}/tasks`, {
        method: "POST",
        body: JSON.stringify({ title: formTitle, priority: formPriority }),
      });
      setShowCreate(false);
      setFormTitle("");
      setFormPriority("medium");
      loadTasks();
    } catch (err) {
      alert(err instanceof Error ? err.message : "创建失败");
    } finally {
      setCreating(false);
    }
  }

  async function moveTask(taskId: string, newStatus: string) {
    try {
      await apiFetch(`/api/projects/${projectId}/tasks`, {
        method: "PATCH",
        body: JSON.stringify({ taskId, status: newStatus }),
      });
      loadTasks();
    } catch {
      // ignore
    }
  }

  function handleDragStart(taskId: string) {
    setDragTask(taskId);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
  }

  function handleDrop(e: React.DragEvent, status: string) {
    e.preventDefault();
    if (dragTask) {
      moveTask(dragTask, status);
      setDragTask(null);
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
        <h3 className="font-semibold text-sm">任务看板</h3>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90"
        >
          <Plus className="h-3 w-3" />
          新建任务
        </button>
      </div>

      {/* Board */}
      <div className="grid grid-cols-3 gap-4">
        {COLUMNS.map((col) => {
          const columnTasks = tasks.filter((t) => t.status === col.status);
          return (
            <div
              key={col.status}
              className={`bg-[var(--secondary)]/50 rounded-lg border-t-2 ${col.color} min-h-[300px]`}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, col.status)}
            >
              <div className="px-3 py-2 flex items-center justify-between">
                <span className="text-xs font-medium">{col.label}</span>
                <span className="text-xs text-[var(--muted-foreground)]">
                  {columnTasks.length}
                </span>
              </div>
              <div className="px-2 pb-2 space-y-2">
                {columnTasks.map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={() => handleDragStart(task.id)}
                    className={`bg-[var(--card)] border border-[var(--border)] rounded-lg p-3 cursor-grab active:cursor-grabbing hover:shadow-sm transition-shadow ${
                      dragTask === task.id ? "opacity-50" : ""
                    }`}
                  >
                    <div className="flex items-start gap-1.5">
                      <GripVertical className="h-3.5 w-3.5 text-[var(--muted-foreground)] mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium">{task.title}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className={`text-xs px-1.5 py-0.5 rounded ${PRIORITY_STYLES[task.priority]}`}>
                            <Flag className="h-2.5 w-2.5 inline mr-0.5" />
                            {PRIORITY_LABELS[task.priority]}
                          </span>
                          {task.assigneeName && (
                            <span className="text-xs text-[var(--muted-foreground)]">
                              {task.assigneeName}
                            </span>
                          )}
                          {task.dueDate && (
                            <span className="text-xs text-[var(--muted-foreground)] flex items-center gap-0.5">
                              <Calendar className="h-2.5 w-2.5" />
                              {task.dueDate.slice(5, 10)}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-semibold mb-4">新建任务</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="text-xs font-medium mb-1 block">任务标题 *</label>
                <input
                  type="text"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  placeholder="描述需要完成的工作"
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  autoFocus
                />
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">优先级</label>
                <div className="flex gap-2">
                  {(["low", "medium", "high"] as const).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setFormPriority(p)}
                      className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                        formPriority === p
                          ? PRIORITY_STYLES[p] + " ring-1 ring-current"
                          : "bg-[var(--secondary)] hover:bg-[var(--accent)]"
                      }`}
                    >
                      {PRIORITY_LABELS[p]}
                    </button>
                  ))}
                </div>
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
                  disabled={creating || !formTitle.trim()}
                  className="px-4 py-2 text-sm font-medium rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50"
                >
                  {creating ? "创建中..." : "创建"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
