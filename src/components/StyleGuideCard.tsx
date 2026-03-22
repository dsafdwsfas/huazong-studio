"use client";

import { useState } from "react";
import { Palette, Upload, Edit3, Save, X, Sparkles, Plus } from "lucide-react";
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

export function StyleGuideCard({ projectId, styleGuide, onUpdate }: Props) {
  const [uploading, setUploading] = useState(false);
  const [editing, setEditing] = useState(false);
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
