import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List assets for a shot */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: shotId } = await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const db = getDb();
    const assets = db.assets
      .filter((a) => a.shotId === shotId)
      .sort((a, b) => b.versionNumber - a.versionNumber);

    // Enrich with uploader info and annotations
    const enriched = assets.map((asset) => {
      const uploader = db.users.find((u) => u.id === asset.uploadedBy);
      const annotations = db.annotations.filter((a) => a.assetId === asset.id);
      return {
        ...asset,
        uploaderName: uploader?.nickname || "未知",
        annotationCount: annotations.length,
        unresolvedCount: annotations.filter((a) => a.status !== "resolved").length,
      };
    });

    return NextResponse.json({ assets: enriched });
  } catch (error) {
    console.error("List assets error:", error);
    return NextResponse.json({ error: "获取资产失败" }, { status: 500 });
  }
}

/** Upload asset to a shot (stores base64 for dev, R2 in production) */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: shotId } = await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const db = getDb();
    const shot = db.shots.find((s) => s.id === shotId);
    if (!shot) return NextResponse.json({ error: "镜头不存在" }, { status: 404 });

    const { fileUrl, fileType, thumbnailUrl } = await request.json();

    if (!fileUrl || !fileType) {
      return NextResponse.json({ error: "缺少文件信息" }, { status: 400 });
    }

    // Calculate version number
    const existingAssets = db.assets.filter((a) => a.shotId === shotId);
    const versionNumber = existingAssets.length + 1;
    const now = new Date().toISOString();

    const asset = {
      id: generateId("ast"),
      shotId,
      fileUrl,
      fileType: fileType as "image" | "video",
      versionNumber,
      thumbnailUrl: thumbnailUrl || null,
      uploadedBy: payload.sub,
      createdAt: now,
    };

    db.assets.push(asset);

    // Update shot status if it was pending_upload
    if (shot.status === "pending_upload") {
      shot.status = "pending_review";
      shot.updatedAt = now;
    }

    return NextResponse.json({ asset }, { status: 201 });
  } catch (error) {
    console.error("Upload asset error:", error);
    return NextResponse.json({ error: "上传失败" }, { status: 500 });
  }
}
