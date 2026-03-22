import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List annotations for an asset */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: assetId } = await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const db = getDb();
    const annotations = db.annotations
      .filter((a) => a.assetId === assetId)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    const enriched = annotations.map((ann) => {
      const annotator = db.users.find((u) => u.id === ann.annotatorId);
      const replies = db.annotationReplies
        .filter((r) => r.annotationId === ann.id)
        .map((r) => {
          const replyUser = db.users.find((u) => u.id === r.userId);
          return { ...r, userName: replyUser?.nickname || "未知" };
        })
        .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());

      return {
        ...ann,
        annotatorName: annotator?.nickname || "未知",
        replies,
      };
    });

    return NextResponse.json({ annotations: enriched });
  } catch (error) {
    console.error("List annotations error:", error);
    return NextResponse.json({ error: "获取批注失败" }, { status: 500 });
  }
}

/** Create annotation */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: assetId } = await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    // Only admin and director can annotate
    if (payload.role !== "admin" && payload.role !== "director") {
      return NextResponse.json({ error: "需要导演或管理员权限" }, { status: 403 });
    }

    const { canvasDataJson, textComment, frameTimestampMs } = await request.json();

    if (!textComment && !canvasDataJson) {
      return NextResponse.json({ error: "请输入批注内容" }, { status: 400 });
    }

    const db = getDb();
    const now = new Date().toISOString();

    const annotation = {
      id: generateId("ann"),
      assetId,
      canvasDataJson: canvasDataJson || null,
      textComment: textComment || "",
      annotatorId: payload.sub,
      status: "unresolved" as const,
      frameTimestampMs: frameTimestampMs || null,
      createdAt: now,
      updatedAt: now,
    };

    db.annotations.push(annotation);

    return NextResponse.json({ annotation }, { status: 201 });
  } catch (error) {
    console.error("Create annotation error:", error);
    return NextResponse.json({ error: "创建批注失败" }, { status: 500 });
  }
}
