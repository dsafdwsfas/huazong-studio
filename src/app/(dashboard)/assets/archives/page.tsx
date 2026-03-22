"use client";

import { useEffect, useState } from "react";
import { Search, User, Box, MapPin, Database } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface ArchiveItem {
  id: string;
  name: string;
  description: string | null;
  archiveType: "character" | "prop" | "scene";
  projectName: string;
  refCount: number;
  createdAt: string;
}

const TYPE_CONFIG = {
  character: { label: "角色", icon: User, color: "bg-blue-50 text-blue-600" },
  prop: { label: "道具", icon: Box, color: "bg-amber-50 text-amber-600" },
  scene: { label: "场景", icon: MapPin, color: "bg-green-50 text-green-600" },
};

export default function GlobalArchivesPage() {
  const [items, setItems] = useState<ArchiveItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  async function loadItems() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (typeFilter) params.set("type", typeFilter);
      if (search) params.set("q", search);
      const data = await apiFetch<{ items: ArchiveItem[] }>(
        `/api/archives?${params}`
      );
      setItems(data.items);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadItems();
  }, [typeFilter]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadItems();
  }

  return (
    <div className="p-6 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Database className="h-5 w-5 text-[var(--primary)]" />
          全局档案库
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] mt-1">
          跨项目搜索和复用角色、道具、场景档案
        </p>
      </div>

      {/* Search + Filter */}
      <div className="mb-4 space-y-3">
        <form onSubmit={handleSearch} className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索名称或描述..."
            className="w-full pl-9 pr-4 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </form>
        <div className="flex gap-1.5">
          <button
            onClick={() => setTypeFilter(null)}
            className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
              !typeFilter
                ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                : "bg-[var(--secondary)] hover:bg-[var(--accent)]"
            }`}
          >
            全部
          </button>
          {(["characters", "props", "scenes"] as const).map((t) => {
            const key = t === "characters" ? "character" : t === "props" ? "prop" : "scene";
            const config = TYPE_CONFIG[key];
            return (
              <button
                key={t}
                onClick={() => setTypeFilter(typeFilter === t ? null : t)}
                className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                  typeFilter === t
                    ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                    : "bg-[var(--secondary)] hover:bg-[var(--accent)]"
                }`}
              >
                {config.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Items */}
      {loading ? (
        <div className="flex justify-center py-20">
          <span className="animate-spin h-6 w-6 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20 text-[var(--muted-foreground)]">
          <Database className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">暂无档案</p>
          <p className="text-xs mt-1">在项目中创建角色、道具或场景后，这里会自动汇总</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const config = TYPE_CONFIG[item.archiveType];
            const Icon = config.icon;
            return (
              <div
                key={item.id}
                className="flex items-center gap-3 px-4 py-3 bg-[var(--card)] border border-[var(--border)] rounded-lg hover:border-[var(--primary)] transition-colors"
              >
                <div className={`p-2 rounded-lg ${config.color}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm">{item.name}</p>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${config.color}`}>
                      {config.label}
                    </span>
                  </div>
                  {item.description && (
                    <p className="text-xs text-[var(--muted-foreground)] mt-0.5 truncate">
                      {item.description}
                    </p>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-[var(--muted-foreground)]">{item.projectName}</p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    {item.refCount} 张参考图
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
