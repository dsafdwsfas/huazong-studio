"use client";

import { useEffect, useState } from "react";
import { Palette, Search, Plus, Copy, Check } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface StyleTemplate {
  id: string;
  name: string;
  tagsJson: string;
  keywordsJson: string;
  description: string;
  createdAt: string;
}

const PRESET_TAGS = ["赛博朋克", "水墨", "写实", "动漫", "复古", "科幻", "奇幻", "极简"];

export default function StyleTemplatesPage() {
  const [templates, setTemplates] = useState<StyleTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Create form state
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formTags, setFormTags] = useState<string[]>([]);
  const [formKeywords, setFormKeywords] = useState("");
  const [creating, setCreating] = useState(false);

  async function loadTemplates() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (activeTag) params.set("tag", activeTag);
      const data = await apiFetch<{ templates: StyleTemplate[] }>(
        `/api/style-templates?${params}`
      );
      setTemplates(data.templates);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTemplates();
  }, [activeTag]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadTemplates();
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formName.trim()) return;
    setCreating(true);
    try {
      let keywords = {};
      if (formKeywords.trim()) {
        try {
          keywords = JSON.parse(formKeywords);
        } catch {
          keywords = { manual: formKeywords.split(/[,，\s]+/).filter(Boolean) };
        }
      }
      await apiFetch("/api/style-templates", {
        method: "POST",
        body: JSON.stringify({
          name: formName,
          description: formDesc,
          tags: formTags,
          keywords,
        }),
      });
      setShowCreate(false);
      setFormName("");
      setFormDesc("");
      setFormTags([]);
      setFormKeywords("");
      loadTemplates();
    } catch (err) {
      alert(err instanceof Error ? err.message : "创建失败");
    } finally {
      setCreating(false);
    }
  }

  function toggleTag(tag: string) {
    setFormTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  async function copyKeywords(template: StyleTemplate) {
    try {
      const kw = JSON.parse(template.keywordsJson);
      await navigator.clipboard.writeText(JSON.stringify(kw, null, 2));
      setCopiedId(template.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      // ignore
    }
  }

  return (
    <div className="p-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Palette className="h-5 w-5 text-violet-500" />
            风格模板库
          </h1>
          <p className="text-sm text-[var(--muted-foreground)] mt-1">
            保存和复用项目风格定调
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90"
        >
          <Plus className="h-4 w-4" />
          新建模板
        </button>
      </div>

      {/* Search + Tags */}
      <div className="mb-4 space-y-3">
        <form onSubmit={handleSearch} className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索模板名称、关键词..."
            className="w-full pl-9 pr-4 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </form>
        <div className="flex gap-1.5 flex-wrap">
          <button
            onClick={() => setActiveTag(null)}
            className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
              !activeTag
                ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                : "bg-[var(--secondary)] text-[var(--foreground)] hover:bg-[var(--accent)]"
            }`}
          >
            全部
          </button>
          {PRESET_TAGS.map((tag) => (
            <button
              key={tag}
              onClick={() => setActiveTag(activeTag === tag ? null : tag)}
              className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                activeTag === tag
                  ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                  : "bg-[var(--secondary)] text-[var(--foreground)] hover:bg-[var(--accent)]"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* Template Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <span className="animate-spin h-6 w-6 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
        </div>
      ) : templates.length === 0 ? (
        <div className="text-center py-20 text-[var(--muted-foreground)]">
          <Palette className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">还没有风格模板</p>
          <p className="text-xs mt-1">在项目风格指南中点击"保存为模板"，或手动创建</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((t) => {
            const tags: string[] = JSON.parse(t.tagsJson || "[]");
            const keywords = JSON.parse(t.keywordsJson || "{}");
            const kwPreview = Object.values(keywords)
              .flat()
              .slice(0, 8) as string[];

            return (
              <div
                key={t.id}
                className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 hover:border-[var(--primary)] transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-sm">{t.name}</h3>
                  <button
                    onClick={() => copyKeywords(t)}
                    className="p-1 rounded hover:bg-[var(--accent)] text-[var(--muted-foreground)]"
                    title="复制关键词"
                  >
                    {copiedId === t.id ? (
                      <Check className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
                {t.description && (
                  <p className="text-xs text-[var(--muted-foreground)] mb-2 line-clamp-2">
                    {t.description}
                  </p>
                )}
                {tags.length > 0 && (
                  <div className="flex gap-1 flex-wrap mb-2">
                    {tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs px-1.5 py-0.5 rounded bg-violet-50 text-violet-600"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                {kwPreview.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {kwPreview.map((kw, i) => (
                      <span
                        key={i}
                        className="text-xs px-1.5 py-0.5 rounded bg-[var(--secondary)] text-[var(--foreground)]"
                      >
                        {kw}
                      </span>
                    ))}
                    {Object.values(keywords).flat().length > 8 && (
                      <span className="text-xs text-[var(--muted-foreground)]">...</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-lg shadow-xl">
            <h2 className="text-lg font-semibold mb-4">新建风格模板</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-xs font-medium mb-1 block">模板名称 *</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="如：赛博朋克霓虹城市"
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  autoFocus
                />
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">描述</label>
                <input
                  type="text"
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  placeholder="简要描述风格特点"
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                />
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">标签</label>
                <div className="flex gap-1.5 flex-wrap">
                  {PRESET_TAGS.map((tag) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleTag(tag)}
                      className={`px-2 py-1 text-xs rounded-full transition-colors ${
                        formTags.includes(tag)
                          ? "bg-violet-500 text-white"
                          : "bg-[var(--secondary)] text-[var(--foreground)] hover:bg-[var(--accent)]"
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">关键词</label>
                <textarea
                  value={formKeywords}
                  onChange={(e) => setFormKeywords(e.target.value)}
                  placeholder="用逗号分隔：霓虹灯, 深蓝色调, 雨夜, 高对比度"
                  rows={3}
                  className="w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none"
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
                  disabled={creating || !formName.trim()}
                  className="px-4 py-2 text-sm font-medium rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50"
                >
                  {creating ? "创建中..." : "创建模板"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
