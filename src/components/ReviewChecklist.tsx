"use client";

import { useState } from "react";
import { CheckSquare, Square, Plus, X } from "lucide-react";

const DEFAULT_ITEMS = [
  "构图合理",
  "色调与风格指南一致",
  "角色一致性",
  "道具准确性",
  "场景匹配",
  "光影效果",
  "画面质量",
];

interface Props {
  onComplete: (passed: boolean, checklist: Record<string, boolean>) => void;
  onClose: () => void;
}

export function ReviewChecklist({ onComplete, onClose }: Props) {
  const [items, setItems] = useState<string[]>(DEFAULT_ITEMS);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [newItem, setNewItem] = useState("");

  function toggle(item: string) {
    setChecked((prev) => ({ ...prev, [item]: !prev[item] }));
  }

  function addItem() {
    if (!newItem.trim() || items.includes(newItem.trim())) return;
    setItems([...items, newItem.trim()]);
    setNewItem("");
  }

  function removeItem(item: string) {
    setItems(items.filter((i) => i !== item));
    const next = { ...checked };
    delete next[item];
    setChecked(next);
  }

  const checkedCount = items.filter((i) => checked[i]).length;
  const allChecked = checkedCount === items.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">审查检查清单</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-[var(--accent)]">
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-xs text-[var(--muted-foreground)] mb-3">
          逐项检查后决定通过或打回 ({checkedCount}/{items.length})
        </p>

        {/* Progress bar */}
        <div className="h-1.5 bg-[var(--secondary)] rounded-full mb-4 overflow-hidden">
          <div
            className="h-full bg-[var(--primary)] rounded-full transition-all"
            style={{ width: `${items.length > 0 ? (checkedCount / items.length) * 100 : 0}%` }}
          />
        </div>

        {/* Checklist items */}
        <div className="space-y-1.5 mb-4 max-h-[300px] overflow-auto">
          {items.map((item) => (
            <div
              key={item}
              className="flex items-center gap-2 group"
            >
              <button
                onClick={() => toggle(item)}
                className="flex items-center gap-2 flex-1 px-2 py-1.5 rounded-lg hover:bg-[var(--accent)] transition-colors text-left"
              >
                {checked[item] ? (
                  <CheckSquare className="h-4 w-4 text-green-500 shrink-0" />
                ) : (
                  <Square className="h-4 w-4 text-[var(--muted-foreground)] shrink-0" />
                )}
                <span className={`text-sm ${checked[item] ? "line-through text-[var(--muted-foreground)]" : ""}`}>
                  {item}
                </span>
              </button>
              <button
                onClick={() => removeItem(item)}
                className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-50 text-red-400"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>

        {/* Add custom item */}
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addItem())}
            placeholder="添加自定义检查项..."
            className="flex-1 px-3 py-1.5 border border-[var(--border)] rounded-lg bg-[var(--background)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
          <button
            onClick={addItem}
            className="px-2 py-1.5 rounded-lg bg-[var(--secondary)] hover:bg-[var(--accent)]"
          >
            <Plus className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => onComplete(false, checked)}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-lg border border-red-200 text-red-600 hover:bg-red-50"
          >
            需修改
          </button>
          <button
            onClick={() => onComplete(true, checked)}
            disabled={!allChecked}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-lg bg-green-500 text-white hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {allChecked ? "通过" : `还有 ${items.length - checkedCount} 项未检查`}
          </button>
        </div>
      </div>
    </div>
  );
}
