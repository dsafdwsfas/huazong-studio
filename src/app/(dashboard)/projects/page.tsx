"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, FolderOpen, Search } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import { PROJECT_STATUS, type ProjectStatus } from "@/lib/constants";

interface Project {
  id: string;
  name: string;
  description: string;
  coverUrl: string | null;
  status: ProjectStatus;
  createdAt: string;
  updatedAt: string;
  totalShots: number;
  approvedShots: number;
  progress: number;
}

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  // Create form
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadProjects();
  }, [filter]);

  async function loadProjects() {
    try {
      setLoading(true);
      const data = await apiFetch<{ projects: Project[] }>(
        `/api/projects?status=${filter}`
      );
      setProjects(data.projects);
    } catch (err) {
      if (err instanceof Error && "status" in err && (err as any).status === 401) {
        router.push("/login");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);

    try {
      await apiFetch("/api/projects", {
        method: "POST",
        body: JSON.stringify({ name: newName, description: newDesc }),
      });
      setNewName("");
      setNewDesc("");
      setShowCreate(false);
      loadProjects();
    } catch (err) {
      alert(err instanceof Error ? err.message : "创建失败");
    } finally {
      setCreating(false);
    }
  }

  const filtered = search
    ? projects.filter(
        (p) =>
          p.name.includes(search) || p.description.includes(search)
      )
    : projects;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">项目中心</h1>
          <p className="text-sm text-[var(--muted-foreground)] mt-1">
            管理所有制片项目
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
        >
          <Plus className="h-4 w-4" />
          新建项目
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex gap-1 bg-[var(--secondary)] rounded-lg p-1">
          {[
            { key: "all", label: "全部" },
            { key: "active", label: "进行中" },
            { key: "completed", label: "已完成" },
            { key: "archived", label: "已归档" },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                filter === f.key
                  ? "bg-[var(--card)] shadow-sm text-[var(--foreground)]"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索项目..."
            className="w-full pl-9 pr-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>
      </div>

      {/* Project Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <span className="animate-spin h-6 w-6 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-[var(--muted-foreground)]">
          <FolderOpen className="h-12 w-12 mb-3 opacity-30" />
          <p className="text-sm">
            {projects.length === 0 ? "还没有项目，点击「新建项目」开始" : "没有匹配的项目"}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => router.push(`/projects/${project.id}`)}
            />
          ))}
        </div>
      )}

      {/* Create Dialog */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-semibold mb-4">新建项目</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-sm font-medium">项目名称 *</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="例：隔壁小区 TVC"
                  required
                  autoFocus
                  className="mt-1 w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                />
              </div>
              <div>
                <label className="text-sm font-medium">项目描述</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="简要描述项目内容..."
                  rows={3}
                  className="mt-1 w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-sm rounded-lg border border-[var(--border)] hover:bg-[var(--accent)]"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={creating}
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

function ProjectCard({
  project,
  onClick,
}: {
  project: Project;
  onClick: () => void;
}) {
  const statusDef = PROJECT_STATUS[project.status];

  return (
    <button
      onClick={onClick}
      className="text-left bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 hover:border-[var(--primary)] hover:shadow-md transition-all group"
    >
      {/* Cover */}
      <div className="aspect-video bg-[var(--secondary)] rounded-lg mb-3 flex items-center justify-center overflow-hidden">
        {project.coverUrl ? (
          <img
            src={project.coverUrl}
            alt={project.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <FolderOpen className="h-8 w-8 text-[var(--muted-foreground)] opacity-30" />
        )}
      </div>

      {/* Info */}
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-sm group-hover:text-[var(--primary)] transition-colors line-clamp-1">
            {project.name}
          </h3>
          <span
            className={`shrink-0 text-xs px-2 py-0.5 rounded-full ${statusDef.color}`}
          >
            {statusDef.label}
          </span>
        </div>

        {project.description && (
          <p className="text-xs text-[var(--muted-foreground)] line-clamp-2">
            {project.description}
          </p>
        )}

        {/* Progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-[var(--muted-foreground)]">
            <span>{project.approvedShots}/{project.totalShots} 镜头</span>
            <span>{project.progress}%</span>
          </div>
          <div className="h-1.5 bg-[var(--secondary)] rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--primary)] rounded-full transition-all"
              style={{ width: `${project.progress}%` }}
            />
          </div>
        </div>

        <p className="text-xs text-[var(--muted-foreground)]">
          更新于 {new Date(project.updatedAt).toLocaleDateString("zh-CN")}
        </p>
      </div>
    </button>
  );
}
