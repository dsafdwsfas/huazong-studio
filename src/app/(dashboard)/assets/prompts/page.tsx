"use client";

import { useEffect, useState } from "react";
import { Plus, Search, Copy, Check, Tag, Sparkles, Code2 } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface Prompt {
  id: string;
  title: string;
  content: string;
  format: "text" | "json";
  tags: string[];
  usageCount: number;
  creatorName: string;
  createdAt: string;
}

const PRESET_TAGS = ["风格", "人物", "场景", "道具", "氛围", "光影", "特效"];

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [sort, setSort] = useState<"newest" | "popular">("newest");
  const [showCreate, setShowCreate] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Create form
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newTags, setNewTags] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadPrompts();
  }, [activeTag, sort]);

  async function loadPrompts() {
    try {
      setLoading(true);
      let url = `/api/prompts?sort=${sort}`;
      if (activeTag) url += `&tag=${activeTag}`;
      if (search) url += `&q=${encodeURIComponent(search)}`;
      const data = await apiFetch<{ prompts: Prompt[] }>(url);
      setPrompts(data.prompts);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;
    setCreating(true);
    try {
      await apiFetch("/api/prompts", {
        method: "POST",
        body: JSON.stringify({
          title: newTitle,
          content: newContent,
          tags: newTags,
        }),
      });
      setShowCreate(false);
      setNewTitle("");
      setNewContent("");
      setNewTags([]);
      loadPrompts();
    } catch (err) {
      alert(err instanceof Error ? err.message : "创建失败");
    } finally {
      setCreating(false);
    }
  }

  function handleCopy(prompt: Prompt) {
    navigator.clipboard.writeText(prompt.content);
    setCopiedId(prompt.id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadPrompts();
  }

  function toggleTag(tag: string) {
    if (newTags.includes(tag)) {
      setNewTags(newTags.filter((t) => t !== tag));
    } else {
      setNewTags([...newTags, tag]);
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">提示词资产库</h1>
          <p className="text-sm text-[var(--muted-foreground)] mt-1">
            团队共享提示词，一键复制复用
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-lg text-sm font-medium hover:opacity-90"
        >
          <Plus className="h-4 w-4" />
          添加提示词
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-3 mb-4">
        <form onSubmit={handleSearch} className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索提示词..."
            className="w-full pl-9 pr-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </form>

        <div className="flex gap-1">
          <button
            onClick={() => setSort("newest")}
            className={`px-3 py-1.5 text-xs rounded-md ${sort === "newest" ? "bg-[var(--primary)] text-[var(--primary-foreground)]" : "bg-[var(--secondary)] text-[var(--muted-foreground)]"}`}
          >
            最新
          </button>
          <button
            onClick={() => setSort("popular")}
            className={`px-3 py-1.5 text-xs rounded-md ${sort === "popular" ? "bg-[var(--primary)] text-[var(--primary-foreground)]" : "bg-[var(--secondary)] text-[var(--muted-foreground)]"}`}
          >
            热门
          </button>
        </div>
      </div>

      {/* Tag filters */}
      <div className="flex gap-1.5 mb-6 flex-wrap">
        <button
          onClick={() => setActiveTag(null)}
          className={`px-2.5 py-1 text-xs rounded-full border ${!activeTag ? "border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-foreground)]" : "border-[var(--border)] hover:bg-[var(--accent)]"}`}
        >
          全部
        </button>
        {PRESET_TAGS.map((tag) => (
          <button
            key={tag}
            onClick={() => setActiveTag(activeTag === tag ? null : tag)}
            className={`px-2.5 py-1 text-xs rounded-full border ${activeTag === tag ? "border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-foreground)]" : "border-[var(--border)] hover:bg-[var(--accent)]"}`}
          >
            {tag}
          </button>
        ))}
      </div>

      {/* Prompt Cards */}
      {loading ? (
        <div className="flex justify-center py-20">
          <span className="animate-spin h-6 w-6 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
        </div>
      ) : prompts.length === 0 ? (
        <div className="text-center py-20 text-[var(--muted-foreground)]">
          <Sparkles className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">还没有提示词，点击「添加提示词」开始</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {prompts.map((prompt) => (
            <div
              key={prompt.id}
              className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {prompt.format === "json" ? (
                    <Code2 className="h-4 w-4 text-[var(--primary)]" />
                  ) : (
                    <Sparkles className="h-4 w-4 text-[var(--primary)]" />
                  )}
                  <h3 className="font-medium text-sm">{prompt.title}</h3>
                </div>
                <button
                  onClick={() => handleCopy(prompt)}
                  className="flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-[var(--secondary)] hover:bg-[var(--accent)] transition-colors"
                >
                  {copiedId === prompt.id ? (
                    <>
                      <Check className="h-3 w-3 text-green-500" />
                      已复制
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      复制
                    </>
                  )}
                </button>
              </div>

              <pre className="text-xs text-[var(--muted-foreground)] bg-[var(--secondary)] rounded-lg p-3 overflow-x-auto max-h-32 mb-2 whitespace-pre-wrap font-mono">
                {prompt.content.length > 300
                  ? prompt.content.substring(0, 300) + "..."
                  : prompt.content}
              </pre>

              <div className="flex items-center justify-between">
                <div className="flex gap-1 flex-wrap">
                  {prompt.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs px-1.5 py-0.5 rounded bg-[var(--accent)] text-[var(--muted-foreground)]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <span className="text-xs text-[var(--muted-foreground)]">
                  {prompt.creatorName} · 使用 {prompt.usageCount} 次
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-lg shadow-xl max-h-[85vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">添加提示词</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-sm font-medium">标题 *</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="例：赛博朋克夜景风格"
                  required
                  className="mt-1 w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                />
              </div>
              <div>
                <label className="text-sm font-medium">
                  提示词内容 *（文本或 JSON）
                </label>
                <textarea
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="输入提示词内容..."
                  required
                  rows={8}
                  className="mt-1 w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">标签</label>
                <div className="flex gap-1.5 flex-wrap">
                  {PRESET_TAGS.map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleTag(tag)}
                      className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                        newTags.includes(tag)
                          ? "border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-foreground)]"
                          : "border-[var(--border)] hover:bg-[var(--accent)]"
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
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
                  {creating ? "保存中..." : "保存"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
