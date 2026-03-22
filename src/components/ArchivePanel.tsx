"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2, User, Box, MapPin, Sun, Moon, Sunset } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

type ArchiveType = "characters" | "props" | "scenes";

interface Ref {
  id: string;
  refImageUrl: string;
  refType?: string;
}

interface ArchiveItem {
  id: string;
  name: string;
  description: string | null;
  timeOfDay?: string | null;
  refs: Ref[];
  createdAt: string;
}

const TYPE_CONFIG: Record<ArchiveType, { label: string; icon: typeof User; idParam: string; apiName: string }> = {
  characters: { label: "角色", icon: User, idParam: "characterId", apiName: "characters" },
  props: { label: "道具", icon: Box, idParam: "propId", apiName: "props" },
  scenes: { label: "场景", icon: MapPin, idParam: "sceneId", apiName: "scenes" },
};

const TIME_ICONS: Record<string, typeof Sun> = {
  "白天": Sun,
  "夜晚": Moon,
  "黄昏": Sunset,
};

interface Props {
  projectId: string;
  type: ArchiveType;
}

export function ArchivePanel({ projectId, type }: Props) {
  const config = TYPE_CONFIG[type];
  const Icon = config.icon;

  const [items, setItems] = useState<ArchiveItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formTimeOfDay, setFormTimeOfDay] = useState("");
  const [creating, setCreating] = useState(false);

  async function loadItems() {
    try {
      setLoading(true);
      const data = await apiFetch<Record<string, ArchiveItem[]>>(
        `/api/projects/${projectId}/${config.apiName}`
      );
      setItems(data[config.apiName] || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadItems();
  }, [projectId, type]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim()) return;
    setCreating(true);
    try {
      const body: any = { name: formName, description: formDesc };
      if (type === "scenes" && formTimeOfDay) body.timeOfDay = formTimeOfDay;
      await apiFetch(`/api/projects/${projectId}/${config.apiName}`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setShowCreate(false);
      setFormName("");
      setFormDesc("");
      setFormTimeOfDay("");
      loadItems();
    } catch (err) {
      alert(err instanceof Error ? err.message : "创建失败");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(itemId: string) {
    if (!confirm(`确认删除此${config.label}？`)) return;
    try {
      await apiFetch(
        `/api/projects/${projectId}/${config.apiName}?${config.idParam}=${itemId}`,
        { method: "DELETE" }
      );
      loadItems();
    } catch (err) {
      alert(err instanceof Error ? err.message : "删除失败");
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
          <Icon className="h-4 w-4 text-[var(--primary)]" />
          {config.label}档案 ({items.length})
        </h3>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90"
        >
          <Plus className="h-3 w-3" />
          添加{config.label}
        </button>
      </div>

      {/* Items Grid */}
      {items.length === 0 ? (
        <div className="text-center py-12 text-[var(--muted-foreground)]">
          <Icon className="h-10 w-10 mx-auto mb-2 opacity-30" />
          <p className="text-sm">暂无{config.label}档案</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-[var(--card)] border border-[var(--border)] rounded-lg overflow-hidden hover:border-[var(--primary)] transition-colors group"
            >
              {/* Thumbnail or placeholder */}
              <div className="aspect-square bg-[var(--secondary)] relative flex items-center justify-center">
                {item.refs.length > 0 ? (
                  <img
                    src={item.refs[0].refImageUrl}
                    alt={item.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <Icon className="h-8 w-8 text-[var(--muted-foreground)] opacity-30" />
                )}
                {/* Ref count badge */}
                {item.refs.length > 1 && (
                  <span className="absolute top-1.5 right-1.5 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded">
                    {item.refs.length} 张
                  </span>
                )}
                {/* Delete button */}
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }}
                  className="absolute top-1.5 left-1.5 p-1 rounded bg-black/40 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
              <div className="p-2">
                <div className="flex items-center gap-1">
                  <p className="font-medium text-xs truncate flex-1">{item.name}</p>
                  {type === "scenes" && item.timeOfDay && (() => {
                    const TimeIcon = TIME_ICONS[item.timeOfDay] || Sun;
                    return <TimeIcon className="h-3 w-3 text-[var(--muted-foreground)]" />;
                  })()}
                </div>
                {item.description && (
                  <p className="text-xs text-[var(--muted-foreground)] line-clamp-1 mt-0.5">
                    {item.description}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-semibold mb-4">添加{config.label}</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="text-xs font-medium mb-1 block">{config.label}名称 *</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder={`输入${config.label}名称`}
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  autoFocus
                />
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">描述</label>
                <textarea
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  placeholder={`${config.label}的详细描述`}
                  rows={3}
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none"
                />
              </div>
              {type === "scenes" && (
                <div>
                  <label className="text-xs font-medium mb-1 block">时间</label>
                  <div className="flex gap-2">
                    {["白天", "夜晚", "黄昏"].map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setFormTimeOfDay(formTimeOfDay === t ? "" : t)}
                        className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                          formTimeOfDay === t
                            ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                            : "bg-[var(--secondary)] hover:bg-[var(--accent)]"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
              )}
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
                  disabled={creating || !formName.trim()}
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
