import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List assets for a shot */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: shotId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const db = getDb();
    const assets = db.all<Record<string, unknown>>(
      "SELECT * FROM assets WHERE shot_id = ? ORDER BY version_number DESC",
      shotId
    );

    // Enrich with uploader info and annotations
    const enriched = assets.map((asset) => {
      const uploader = db.get<{ nickname: string }>(
        "SELECT nickname FROM users WHERE id = ?",
        asset.uploaded_by
      );

      const annotationCount =
        db.get<{ cnt: number }>(
          "SELECT COUNT(*) as cnt FROM annotations WHERE asset_id = ?",
          asset.id
        )?.cnt ?? 0;

      const unresolvedCount =
        db.get<{ cnt: number }>(
          "SELECT COUNT(*) as cnt FROM annotations WHERE asset_id = ? AND status != 'resolved'",
          asset.id
        )?.cnt ?? 0;

      return {
        ...asset,
        uploaderName: uploader?.nickname || "未知",
        annotationCount,
        unresolvedCount,
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
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const db = getDb();
    const shot = db.get<{ id: string; status: string; project_id: string }>(
      "SELECT id, status, project_id FROM shots WHERE id = ?",
      shotId
    );
    if (!shot) return NextResponse.json({ error: "镜头不存在" }, { status: 404 });

    const { fileUrl, fileType, thumbnailUrl } = await request.json();

    if (!fileUrl || !fileType) {
      return NextResponse.json({ error: "缺少文件信息" }, { status: 400 });
    }
    if (!["image", "video"].includes(fileType)) {
      return NextResponse.json({ error: "无效的文件类型，仅支持 image 或 video" }, { status: 400 });
    }

    // Calculate version number
    const versionNumber =
      (db.get<{ cnt: number }>(
        "SELECT COUNT(*) as cnt FROM assets WHERE shot_id = ?",
        shotId
      )?.cnt ?? 0) + 1;

    const now = new Date().toISOString();
    const assetId = generateId("ast");

    db.run(
      "INSERT INTO assets (id, shot_id, file_url, file_type, version_number, thumbnail_url, uploaded_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
      assetId,
      shotId,
      fileUrl,
      fileType,
      versionNumber,
      thumbnailUrl || null,
      payload.sub,
      now
    );

    // Update shot status if it was pending_upload
    if (shot.status === "pending_upload") {
      db.run(
        "UPDATE shots SET status = 'pending_review', updated_at = ? WHERE id = ?",
        now,
        shotId
      );
    }

    const asset = db.get<Record<string, unknown>>(
      "SELECT * FROM assets WHERE id = ?",
      assetId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      shot.project_id,
      "upload_asset",
      JSON.stringify({ assetId, shotId, fileType, versionNumber }),
      now
    );

    return NextResponse.json({ asset }, { status: 201 });
  } catch (error) {
    console.error("Upload asset error:", error);
    return NextResponse.json({ error: "上传失败" }, { status: 500 });
  }
}
