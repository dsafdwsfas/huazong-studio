"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Plus,
  Upload,
  FileText,
  MessageSquare,
  ChevronLeft,
  Image as ImageIcon,
  Video,
  AlertCircle,
  Clapperboard,
  User,
  KanbanSquare,
  Coins,
  LayoutDashboard,
  CheckSquare,
  SplitSquareHorizontal,
} from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import { SHOT_STATUS, type ShotStatus } from "@/lib/constants";
import { StyleGuideCard } from "@/components/StyleGuideCard";
import { ArchivePanel } from "@/components/ArchivePanel";
import { TaskBoard } from "@/components/TaskBoard";
import { CreditLedger } from "@/components/CreditLedger";
import { ProjectDashboard } from "@/components/ProjectDashboard";
import { ReviewChecklist } from "@/components/ReviewChecklist";
import { VersionCompare } from "@/components/VersionCompare";

type TabKey = "dashboard" | "shots" | "archives" | "tasks" | "credits";

interface Shot {
  id: string;
  shotNumber: number;
  sceneDescription: string;
  dialogue: string | null;
  durationSeconds: number | null;
  cameraAngle: string | null;
  status: ShotStatus;
  assigneeName: string | null;
  latestAsset: {
    id: string;
    fileUrl: string;
    fileType: "image" | "video";
    versionNumber: number;
  } | null;
  assetCount: number;
  unresolvedAnnotations: number;
  sortOrder: number;
}

interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [shots, setShots] = useState<Shot[]>([]);
  const [loading, setLoading] = useState(true);
  const [showScript, setShowScript] = useState(false);
  const [scriptText, setScriptText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [hoveredShot, setHoveredShot] = useState<string | null>(null);
  const [styleGuide, setStyleGuide] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [selectedShots, setSelectedShots] = useState<Set<string>>(new Set());
  const [showReview, setShowReview] = useState(false);
  const [compareShot, setCompareShot] = useState<{ id: string; number: number } | null>(null);

  const loadStyleGuide = useCallback(async () => {
    try {
      const data = await apiFetch<{ styleGuide: any }>(`/api/projects/${id}/style`);
      setStyleGuide(data.styleGuide);
    } catch {
      // ignore - style guide is optional
    }
  }, [id]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiFetch<{ shots: Shot[]; project: Project }>(
        `/api/projects/${id}/shots`
      );
      setProject(data.project);
      setShots(data.shots);
    } catch (err) {
      if (err instanceof Error && "status" in err && (err as any).status === 401) {
        router.push("/login");
      }
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  useEffect(() => {
    loadData();
    loadStyleGuide();
  }, [loadData, loadStyleGuide]);

  async function handleParseScript(e: React.FormEvent) {
    e.preventDefault();
    if (!scriptText.trim()) return;
    setParsing(true);
    try {
      const data = await apiFetch<{ count: number }>(
        `/api/projects/${id}/parse-script`,
        {
          method: "POST",
          body: JSON.stringify({ scriptText }),
        }
      );
      setShowScript(false);
      setScriptText("");
      loadData();
      alert(`成功拆解 ${data.count} 个镜头`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "解析失败");
    } finally {
      setParsing(false);
    }
  }

  async function handleAddShot() {
    try {
      await apiFetch(`/api/projects/${id}/shots`, {
        method: "POST",
        body: JSON.stringify({ sceneDescription: "新镜头" }),
      });
      loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "添加失败");
    }
  }

  function toggleSelect(shotId: string) {
    setSelectedShots((prev) => {
      const next = new Set(prev);
      if (next.has(shotId)) next.delete(shotId);
      else next.add(shotId);
      return next;
    });
  }

  function selectAll() {
    if (selectedShots.size === filteredShots.length) {
      setSelectedShots(new Set());
    } else {
      setSelectedShots(new Set(filteredShots.map((s) => s.id)));
    }
  }

  async function batchUpdateStatus(newStatus: string) {
    try {
      await Promise.all(
        Array.from(selectedShots).map((shotId) =>
          apiFetch(`/api/shots/${shotId}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status: newStatus }),
          })
        )
      );
      setSelectedShots(new Set());
      loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "批量操作失败");
    }
  }

  function handleReviewComplete(passed: boolean) {
    setShowReview(false);
    batchUpdateStatus(passed ? "approved" : "needs_revision");
  }

  const filteredShots =
    statusFilter === "all"
      ? shots
      : shots.filter((s) => s.status === statusFilter);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="animate-spin h-6 w-6 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-[var(--border)] bg-[var(--card)] px-6 py-4">
        <div className="flex items-center gap-3 mb-2">
          <button
            onClick={() => router.push("/projects")}
            className="p-1 rounded hover:bg-[var(--accent)]"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <h1 className="text-xl font-bold">{project?.name}</h1>
        </div>
        {/* Tab Navigation */}
        <div className="flex gap-1 mt-3">
          {([
            { key: "dashboard", label: "概览", icon: LayoutDashboard },
            { key: "shots", label: "分镜板", icon: Clapperboard },
            { key: "archives", label: "档案管理", icon: User },
            { key: "tasks", label: "任务看板", icon: KanbanSquare },
            { key: "credits", label: "积分台账", icon: Coins },
          ] as const).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-t-lg transition-colors ${
                activeTab === tab.key
                  ? "bg-[var(--background)] text-[var(--foreground)] font-medium border border-[var(--border)] border-b-transparent -mb-px"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              }`}
            >
              <tab.icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "dashboard" && (
        <div className="flex-1 overflow-auto p-6">
          <StyleGuideCard
            projectId={id}
            styleGuide={styleGuide}
            onUpdate={loadStyleGuide}
          />
          <ProjectDashboard projectId={id} />
        </div>
      )}

      {activeTab === "shots" && (
        <>
          {/* Shot toolbar */}
          <div className="px-6 pt-4 flex items-center justify-between">
            <div className="flex gap-2">
              <button
                onClick={() => setShowScript(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-[var(--border)] rounded-lg hover:bg-[var(--accent)]"
              >
                <FileText className="h-3.5 w-3.5" />
                导入剧本
              </button>
              <button
                onClick={handleAddShot}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-[var(--border)] rounded-lg hover:bg-[var(--accent)]"
              >
                <Plus className="h-3.5 w-3.5" />
                添加镜头
              </button>
              <button
                onClick={selectAll}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-[var(--border)] rounded-lg hover:bg-[var(--accent)]"
              >
                <CheckSquare className="h-3.5 w-3.5" />
                {selectedShots.size === filteredShots.length && filteredShots.length > 0 ? "取消全选" : "全选"}
              </button>
              {selectedShots.size > 0 && (
                <>
                  <button
                    onClick={() => setShowReview(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-green-500 text-white hover:bg-green-600"
                  >
                    批量审查 ({selectedShots.size})
                  </button>
                  <button
                    onClick={() => batchUpdateStatus("needs_revision")}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-red-200 text-red-600 hover:bg-red-50"
                  >
                    批量打回
                  </button>
                </>
              )}
            </div>
            <div className="flex gap-1 text-xs">
              <FilterBtn label="全部" value="all" current={statusFilter} onClick={setStatusFilter} count={shots.length} />
              <FilterBtn label="待上传" value="pending_upload" current={statusFilter} onClick={setStatusFilter} count={shots.filter((s) => s.status === "pending_upload").length} />
              <FilterBtn label="待审查" value="pending_review" current={statusFilter} onClick={setStatusFilter} count={shots.filter((s) => s.status === "pending_review").length} />
              <FilterBtn label="需修改" value="needs_revision" current={statusFilter} onClick={setStatusFilter} count={shots.filter((s) => s.status === "needs_revision").length} />
              <FilterBtn label="通过" value="approved" current={statusFilter} onClick={setStatusFilter} count={shots.filter((s) => s.status === "approved").length} />
            </div>
          </div>

          {/* Shot Grid (Waterfall) */}
          <div className="flex-1 overflow-auto px-6 pb-6 pt-3">
        {filteredShots.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-[var(--muted-foreground)]">
            <FileText className="h-12 w-12 mb-3 opacity-30" />
            <p className="text-sm mb-2">
              {shots.length === 0
                ? "还没有镜头，导入剧本或手动添加"
                : "没有匹配的镜头"}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
            {filteredShots.map((shot) => (
              <ShotCard
                key={shot.id}
                shot={shot}
                isHovered={hoveredShot === shot.id}
                isSelected={selectedShots.has(shot.id)}
                onMouseEnter={() => setHoveredShot(shot.id)}
                onMouseLeave={() => setHoveredShot(null)}
                onSelect={() => toggleSelect(shot.id)}
                onCompare={() => setCompareShot({ id: shot.id, number: shot.shotNumber })}
              />
            ))}
          </div>
        )}
      </div>

        </>
      )}

      {activeTab === "archives" && (
        <div className="flex-1 overflow-auto p-6 space-y-6">
          <ArchivePanel projectId={id} type="characters" />
          <ArchivePanel projectId={id} type="props" />
          <ArchivePanel projectId={id} type="scenes" />
        </div>
      )}

      {activeTab === "tasks" && (
        <div className="flex-1 overflow-auto p-6">
          <TaskBoard projectId={id} />
        </div>
      )}

      {activeTab === "credits" && (
        <div className="flex-1 overflow-auto p-6">
          <CreditLedger projectId={id} />
        </div>
      )}

      {/* Review Checklist */}
      {showReview && (
        <ReviewChecklist
          onComplete={handleReviewComplete}
          onClose={() => setShowReview(false)}
        />
      )}

      {/* Version Compare */}
      {compareShot && (
        <VersionCompare
          shotId={compareShot.id}
          shotNumber={compareShot.number}
          onClose={() => setCompareShot(null)}
        />
      )}

      {/* Script Import Dialog */}
      {showScript && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-[var(--card)] rounded-xl border border-[var(--border)] p-6 w-full max-w-2xl shadow-xl max-h-[80vh] flex flex-col">
            <h2 className="text-lg font-semibold mb-1">导入剧本 / 分镜脚本</h2>
            <p className="text-sm text-[var(--muted-foreground)] mb-4">
              粘贴剧本内容，系统会自动识别并拆分为镜头卡片。支持格式：「镜头1：...」「1. ...」「场景1：...」等。
            </p>
            <form onSubmit={handleParseScript} className="flex-1 flex flex-col">
              <textarea
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                placeholder={`示例格式：

镜头1：深邃的黑色背景中，零星的蓝色光点缓缓漂浮（全景，3秒）
旁白："在这个世界的尽头..."

镜头2：女主角站在废墟中，风吹动她的头发（中景，5秒）
女主角："我们还有希望吗？"

镜头3：俯拍城市全景，建筑物上闪烁着霓虹灯（航拍，4秒）`}
                className="flex-1 min-h-[300px] w-full px-3 py-2 border border-[var(--border)] rounded-lg bg-[var(--background)] text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[var(--ring)] resize-none"
                autoFocus
              />
              <div className="flex gap-2 justify-end mt-4">
                <button
                  type="button"
                  onClick={() => setShowScript(false)}
                  className="px-4 py-2 text-sm rounded-lg border border-[var(--border)] hover:bg-[var(--accent)]"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={parsing || !scriptText.trim()}
                  className="px-4 py-2 text-sm font-medium rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50"
                >
                  {parsing ? "解析中..." : "开始拆解"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function ShotCard({
  shot,
  isHovered,
  isSelected,
  onMouseEnter,
  onMouseLeave,
  onSelect,
  onCompare,
}: {
  shot: Shot;
  isHovered: boolean;
  isSelected: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  onSelect: () => void;
  onCompare: () => void;
}) {
  const statusDef = SHOT_STATUS[shot.status];
  const videoRef = useRef<HTMLVideoElement>(null);

  // Auto-play video on hover
  useEffect(() => {
    if (!videoRef.current) return;
    if (isHovered) {
      videoRef.current.play().catch(() => {});
    } else {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  }, [isHovered]);

  return (
    <div
      className={`group bg-[var(--card)] border rounded-lg overflow-hidden hover:border-[var(--primary)] hover:shadow-lg transition-all cursor-pointer relative ${
        isSelected ? "border-[var(--primary)] ring-2 ring-[var(--primary)]/30" : "border-[var(--border)]"
      }`}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Thumbnail / Preview */}
      <div className="aspect-video bg-[var(--secondary)] relative overflow-hidden">
        {shot.latestAsset ? (
          shot.latestAsset.fileType === "video" ? (
            <video
              ref={videoRef}
              src={shot.latestAsset.fileUrl}
              className="w-full h-full object-cover"
              muted
              loop
              playsInline
              preload="metadata"
            />
          ) : (
            <img
              src={shot.latestAsset.fileUrl}
              alt={`镜头 ${shot.shotNumber}`}
              className={`w-full h-full object-cover transition-transform duration-300 ${
                isHovered ? "scale-110" : "scale-100"
              }`}
            />
          )
        ) : (
          <div className="flex items-center justify-center h-full">
            <Upload className="h-6 w-6 text-[var(--muted-foreground)] opacity-30" />
          </div>
        )}

        {/* Select checkbox */}
        <button
          onClick={(e) => { e.stopPropagation(); onSelect(); }}
          className={`absolute top-1.5 left-1.5 z-10 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
            isSelected
              ? "bg-[var(--primary)] border-[var(--primary)] text-white"
              : "bg-black/40 border-white/60 opacity-0 group-hover:opacity-100"
          }`}
        >
          {isSelected && <span className="text-xs">✓</span>}
        </button>

        {/* Shot number badge */}
        <div className="absolute top-1.5 left-8 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded font-mono">
          #{shot.shotNumber}
        </div>

        {/* Compare button */}
        {shot.assetCount > 1 && (
          <button
            onClick={(e) => { e.stopPropagation(); onCompare(); }}
            className="absolute bottom-1.5 left-1.5 p-1 rounded bg-black/40 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/60"
            title="版本对比"
          >
            <SplitSquareHorizontal className="h-3 w-3" />
          </button>
        )}

        {/* Asset type indicator */}
        {shot.latestAsset && (
          <div className="absolute top-1.5 right-1.5">
            {shot.latestAsset.fileType === "video" ? (
              <Video className="h-3.5 w-3.5 text-white drop-shadow" />
            ) : (
              <ImageIcon className="h-3.5 w-3.5 text-white drop-shadow" />
            )}
          </div>
        )}

        {/* Unresolved annotations badge */}
        {shot.unresolvedAnnotations > 0 && (
          <div className="absolute bottom-1.5 right-1.5 bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
            <MessageSquare className="h-3 w-3" />
            {shot.unresolvedAnnotations}
          </div>
        )}

        {/* Hover: enlarged preview */}
        {isHovered && shot.latestAsset && shot.latestAsset.fileType === "image" && (
          <div className="fixed z-50 pointer-events-none" style={{
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
          }}>
            <img
              src={shot.latestAsset.fileUrl}
              alt={`镜头 ${shot.shotNumber} 放大`}
              className="max-w-lg max-h-96 rounded-xl shadow-2xl border-2 border-white/20"
            />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-2 space-y-1">
        <div className="flex items-center justify-between gap-1">
          <span className={`text-xs px-1.5 py-0.5 rounded ${statusDef.color}`}>
            {statusDef.label}
          </span>
          {shot.assetCount > 0 && (
            <span className="text-xs text-[var(--muted-foreground)]">
              V{shot.assetCount}
            </span>
          )}
        </div>
        <p className="text-xs text-[var(--foreground)] line-clamp-2 leading-relaxed">
          {shot.sceneDescription}
        </p>
        {shot.assigneeName && (
          <p className="text-xs text-[var(--muted-foreground)]">
            {shot.assigneeName}
          </p>
        )}
      </div>
    </div>
  );
}

function FilterBtn({
  label,
  value,
  current,
  onClick,
  count,
}: {
  label: string;
  value: string;
  current: string;
  onClick: (v: string) => void;
  count: number;
}) {
  if (count === 0 && value !== "all") return null;
  return (
    <button
      onClick={() => onClick(value)}
      className={`px-2 py-1 rounded transition-colors ${
        current === value
          ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
          : "hover:bg-[var(--accent)] text-[var(--muted-foreground)]"
      }`}
    >
      {label} {count > 0 && `(${count})`}
    </button>
  );
}
