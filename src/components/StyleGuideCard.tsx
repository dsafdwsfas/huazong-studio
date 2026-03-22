"use client";

import { useState } from "react";
import { Palette, Upload, Edit3, Save, X, Sparkles, Plus, Bookmark, Check } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface StyleKeywords {
  color_tone: string[];
  lighting: string[];
  texture: string[];
  atmosphere: string[];
  reference: string[];
  summary: string;
}

interface StyleGuide {
  keywords?: StyleKeywords;
  manualKeywords?: string[];
  extractedAt?: string;
}

interface Props {
  projectId: string;
  styleGuide: StyleGuide | null;
  onUpdate: () => void;
}

const DIMENSION_LABELS: Record<string, { label: string; color: string }> = {
  color_tone: { label: "色调", color: "bg-rose-100 text-rose-700" },
  lighting: { label: "光影", color: "bg-amber-100 text-amber-700" },
  texture: { label: "质感", color: "bg-emerald-100 text-emerald-700" },
  atmosphere: { label: "氛围", color: "bg-violet-100 text-violet-700" },
  reference: { label: "参考", color: "bg-sky-100 text-sky-700" },
};

interface TemplateItem {
  id: string;
  name: string;
  keywordsJson: string;
  description: string;
}

export function StyleGuideCard({ projectId, styleGuide, onUpdate }: Props) {
  const [uploading, setUploading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showTemplatePicker, setShowTemplatePicker] = useState(false);
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [applying, setApplying] = useState(false);
  const [manualInput, setManualInput] = useState("");
  const [manualKeywords, setManualKeywords] = useState<string[]>(
    styleGuide?.manualKeywords || []
  );

  async function handleImageUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      const images = await Promise.all(
        Array.from(files).slice(0, 5).map(async (file) => {
          const base64 = await fileToBase64(file);
          return { base64, mimeType: file.type };
        })
      );

      await apiFetch(`/api/projects/${projectId}/style`, {
        method: "POST",
        body: JSON.stringify({ images, manualKeywords }),
      });

      onUpdate();
    } catch (err) {
      alert(err instanceof Error ? err.message : "提取失败");
    } finally {
      setUploading(false);
    }
  }

  async function handleSaveManual() {
    try {
      await apiFetch(`/api/projects/${projectId}/style`, {
        method: "PATCH",
        body: JSON.stringify({ manualKeywords }),
      });
      setEditing(false);
      onUpdate();
    } catch (err) {
      alert(err instanceof Error ? err.message : "保存失败");
    }
  }

  async function openTemplatePicker() {
    setShowTemplatePicker(true);
    setLoadingTemplates(true);
    try {
      const data = await apiFetch<{ templates: TemplateItem[] }>("/api/style-templates");
      setTemplates(data.templates);
    } catch {
      setTemplates([]);
    } finally {
      setLoadingTemplates(false);
    }
  }

  async function applyTemplate(template: TemplateItem) {
    setApplying(true);
    try {
      const keywords = JSON.parse(template.keywordsJson || "{}");
      await apiFetch(`/api/projects/${projectId}/style`, {
        method: "PATCH",
        body: JSON.stringify({
          keywords,
          manualKeywords,
          appliedTemplate: template.name,
          appliedAt: new Date().toISOString(),
        }),
      });
      setShowTemplatePicker(false);
      onUpdate();
    } catch (err) {
      alert(err instanceof Error ? err.message : "应用模板失败");
    } finally {
      setApplying(false);
    }
  }

  async function handleSaveAsTemplate() {
    if (!styleGuide?.keywords) return;
    setSaving(true);
    try {
      const name = prompt("模板名称：");
      if (!name) {
        setSaving(false);
        return;
      }
      await apiFetch("/api/style-templates", {
        method: "POST",
        body: JSON.stringify({
          name,
          description: styleGuide.keywords.summary || "",
          tags: [],
          keywords: styleGuide.keywords,
          projectId,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : "保存模板失败");
    } finally {
      setSaving(false);
    }
  }

  function addManualKeyword() {
    if (!manualInput.trim()) return;
    setManualKeywords([...manualKeywords, manualInput.trim()]);
    setManualInput("");
  }

  function removeManualKeyword(idx: number) {
    setManualKeywords(manualKeywords.filter((_, i) => i !== idx));
  }

  const hasStyle = styleGuide?.keywords;

  return (
    <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Palette className="h-4 w-4 text-[var(--primary)]" />
          <h3 className="font-semibold text-sm">风格指南</h3>
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={openTemplatePicker}
            className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-[var(--secondary)] hover:bg-[var(--accent)]"
          >
            <Sparkles className="h-3 w-3" />
            应用模板
          </button>
          <label className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-[var(--secondary)] hover:bg-[var(--accent)] cursor-pointer transition-colors">
            <Upload className="h-3 w-3" />
            {uploading ? "提取中..." : "上传参考图"}
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              className="hidden"
              disabled={uploading}
            />
          </label>
          {hasStyle && (
            <button
              onClick={handleSaveAsTemplate}
              disabled={saving || saved}
              className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-[var(--secondary)] hover:bg-[var(--accent)] disabled:opacity-50"
            >
              {saved ? <Check className="h-3 w-3 text-green-500" /> : <Bookmark className="h-3 w-3" />}
              {saved ? "已保存" : saving ? "保存中..." : "存为模板"}
            </button>
          )}
          <button
            onClick={() => setEditing(!editing)}
            className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-[var(--secondary)] hover:bg-[var(--accent)]"
          >
            <Edit3 className="h-3 w-3" />
            编辑
          </button>
        </div>
      </div>

      {!hasStyle && manualKeywords.length === 0 ? (
        <p className="text-xs text-[var(--muted-foreground)] py-4 text-center">
          上传 1-5 张参考图，AI 自动提取风格关键词。也可以手动添加。
        </p>
      ) : (
        <div className="space-y-2">
          {/* Summary */}
          {hasStyle && (
            <p className="text-sm font-medium text-[var(--foreground)]">
              {styleGuide.keywords!.summary}
            </p>
          )}

          {/* AI Keywords by dimension */}
          {hasStyle &&
            Object.entries(DIMENSION_LABELS).map(([key, def]) => {
              const words = (styleGuide.keywords as any)?.[key] as string[] | undefined;
              if (!words || words.length === 0) return null;
              return (
                <div key={key} className="flex items-start gap-2">
                  <span className={`shrink-0 text-xs px-1.5 py-0.5 rounded ${def.color}`}>
                    {def.label}
                  </span>
                  <div className="flex gap-1 flex-wrap">
                    {words.map((w, i) => (
                      <span
                        key={i}
                        className="text-xs px-1.5 py-0.5 rounded bg-[var(--secondary)] text-[var(--foreground)]"
                      >
                        {w}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}

          {/* Manual keywords */}
          {manualKeywords.length > 0 && (
            <div className="flex items-start gap-2">
              <span className="shrink-0 text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-700">
                手动
              </span>
              <div className="flex gap-1 flex-wrap">
                {manualKeywords.map((w, i) => (
                  <span
                    key={i}
                    className="text-xs px-1.5 py-0.5 rounded bg-[var(--secondary)] text-[var(--foreground)] group"
                  >
                    {w}
                    {editing && (
                      <button
                        onClick={() => removeManualKeyword(i)}
                        className="ml-1 text-red-400 hover:text-red-600"
                      >
                        ×
                      </button>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Edit mode */}
      {editing && (
        <div className="mt-3 pt-3 border-t border-[var(--border)]">
          <div className="flex gap-2">
            <input
              type="text"
              value={manualInput}
              onChange={(e) => setManualInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addManualKeyword())}
              placeholder="输入关键词，回车添加"
              className="flex-1 px-3 py-1.5 border border-[var(--border)] rounded-lg bg-[var(--background)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
            />
            <button
              onClick={addManualKeyword}
              className="px-2 py-1.5 text-xs rounded-lg bg-[var(--secondary)] hover:bg-[var(--accent)]"
            >
              <Plus className="h-3 w-3" />
            </button>
            <button
              onClick={handleSaveManual}
              className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)]"
            >
              <Save className="h-3 w-3" />
              保存
            </button>
          </div>
        </div>
      )}

      {/* Template Picker Modal */}
      {showTemplatePicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-md shadow-xl max-h-[70vh] flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">选择风格模板</h2>
              <button
                onClick={() => setShowTemplatePicker(false)}
                className="p-1 rounded hover:bg-[var(--accent)]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex-1 overflow-auto space-y-2">
              {loadingTemplates ? (
                <div className="flex justify-center py-8">
                  <span className="animate-spin h-5 w-5 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
                </div>
              ) : templates.length === 0 ? (
                <p className="text-sm text-[var(--muted-foreground)] text-center py-8">
                  还没有风格模板，先在项目中提取风格后保存为模板
                </p>
              ) : (
                templates.map((t) => {
                  const kw = JSON.parse(t.keywordsJson || "{}");
                  const preview = Object.values(kw).flat().slice(0, 6) as string[];
                  return (
                    <button
                      key={t.id}
                      onClick={() => applyTemplate(t)}
                      disabled={applying}
                      className="w-full text-left p-3 rounded-lg border border-[var(--border)] hover:border-[var(--primary)] hover:bg-[var(--accent)] transition-all disabled:opacity-50"
                    >
                      <p className="font-medium text-sm">{t.name}</p>
                      {t.description && (
                        <p className="text-xs text-[var(--muted-foreground)] mt-0.5 line-clamp-1">
                          {t.description}
                        </p>
                      )}
                      {preview.length > 0 && (
                        <div className="flex gap-1 flex-wrap mt-1.5">
                          {preview.map((w, i) => (
                            <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-[var(--secondary)]">
                              {w}
                            </span>
                          ))}
                        </div>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(",")[1]); // Remove data:image/...;base64, prefix
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
