"use client";

import { useState, useEffect } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { apiFetch } from "@/lib/api-client";

interface Asset {
  id: string;
  fileUrl: string;
  fileType: "image" | "video";
  versionNumber: number;
  createdAt: string;
}

interface Props {
  shotId: string;
  shotNumber: number;
  onClose: () => void;
}

export function VersionCompare({ shotId, shotNumber, onClose }: Props) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [leftIdx, setLeftIdx] = useState(0);
  const [rightIdx, setRightIdx] = useState(1);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<{ assets: Asset[] }>(
          `/api/shots/${shotId}/assets`
        );
        const sorted = (data.assets || []).sort(
          (a, b) => a.versionNumber - b.versionNumber
        );
        setAssets(sorted);
        if (sorted.length >= 2) {
          setLeftIdx(sorted.length - 2);
          setRightIdx(sorted.length - 1);
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [shotId]);

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <span className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full" />
      </div>
    );
  }

  if (assets.length < 2) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-sm shadow-xl text-center">
          <p className="text-sm mb-4">镜头 #{shotNumber} 需要至少 2 个版本才能对比</p>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)]"
          >
            关闭
          </button>
        </div>
      </div>
    );
  }

  const leftAsset = assets[leftIdx];
  const rightAsset = assets[rightIdx];

  function renderAsset(asset: Asset) {
    if (asset.fileType === "video") {
      return (
        <video
          src={asset.fileUrl}
          className="w-full h-full object-contain bg-black"
          controls
          muted
        />
      );
    }
    return (
      <img
        src={asset.fileUrl}
        alt={`V${asset.versionNumber}`}
        className="w-full h-full object-contain bg-black"
      />
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/90">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 bg-black/50">
        <h2 className="text-white font-semibold text-sm">
          镜头 #{shotNumber} — 版本对比
        </h2>
        <button onClick={onClose} className="p-1.5 rounded hover:bg-white/10">
          <X className="h-5 w-5 text-white" />
        </button>
      </div>

      {/* Compare view */}
      <div className="flex-1 flex">
        {/* Left */}
        <div className="flex-1 flex flex-col border-r border-white/10">
          <div className="flex items-center justify-between px-4 py-2 bg-black/30">
            <button
              onClick={() => setLeftIdx(Math.max(0, leftIdx - 1))}
              disabled={leftIdx === 0}
              className="p-1 rounded hover:bg-white/10 disabled:opacity-30 text-white"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-white text-sm font-mono">
              V{leftAsset.versionNumber}
            </span>
            <button
              onClick={() => setLeftIdx(Math.min(assets.length - 1, leftIdx + 1))}
              disabled={leftIdx >= assets.length - 1}
              className="p-1 rounded hover:bg-white/10 disabled:opacity-30 text-white"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          <div className="flex-1 flex items-center justify-center p-2">
            {renderAsset(leftAsset)}
          </div>
        </div>

        {/* Right */}
        <div className="flex-1 flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 bg-black/30">
            <button
              onClick={() => setRightIdx(Math.max(0, rightIdx - 1))}
              disabled={rightIdx === 0}
              className="p-1 rounded hover:bg-white/10 disabled:opacity-30 text-white"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-white text-sm font-mono">
              V{rightAsset.versionNumber}
            </span>
            <button
              onClick={() => setRightIdx(Math.min(assets.length - 1, rightIdx + 1))}
              disabled={rightIdx >= assets.length - 1}
              className="p-1 rounded hover:bg-white/10 disabled:opacity-30 text-white"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          <div className="flex-1 flex items-center justify-center p-2">
            {renderAsset(rightAsset)}
          </div>
        </div>
      </div>
    </div>
  );
}
