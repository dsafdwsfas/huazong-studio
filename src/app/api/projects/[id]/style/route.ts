import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";
import { extractStyleFromImages } from "@/lib/style-extractor";

/** Get project style guide */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const db = getDb();
    const project = db.get<{ style_guide_json: string | null }>(
      "SELECT style_guide_json FROM projects WHERE id = ?",
      projectId
    );
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    const styleGuide = project.style_guide_json
      ? JSON.parse(project.style_guide_json)
      : null;

    return NextResponse.json({ styleGuide });
  } catch (error) {
    console.error("Get style error:", error);
    return NextResponse.json({ error: "获取风格指南失败" }, { status: 500 });
  }
}

/** Extract style from images and save to project */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    if (payload.role !== "admin" && payload.role !== "director") {
      return NextResponse.json({ error: "需要导演或管理员权限" }, { status: 403 });
    }

    const { images, manualKeywords } = await request.json();

    const db = getDb();
    const project = db.get<{ id: string; style_guide_json: string | null }>(
      "SELECT id, style_guide_json FROM projects WHERE id = ?",
      projectId
    );
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    let styleGuide;

    if (images && images.length > 0) {
      const apiKey = process.env.GEMINI_API_KEY;
      const result = await extractStyleFromImages(images, apiKey);
      styleGuide = {
        referenceImages: images.map((img: any) => ({
          base64Preview: img.base64.substring(0, 100) + "...",
          mimeType: img.mimeType,
        })),
        analysis: result.analysis,
        keywords: result.keywords,
        manualKeywords: manualKeywords || [],
        extractedAt: new Date().toISOString(),
      };
    } else if (manualKeywords) {
      const existing = project.style_guide_json
        ? JSON.parse(project.style_guide_json)
        : {};
      styleGuide = {
        ...existing,
        manualKeywords,
        updatedAt: new Date().toISOString(),
      };
    } else {
      return NextResponse.json({ error: "请上传参考图或输入关键词" }, { status: 400 });
    }

    const now = new Date().toISOString();
    db.run(
      "UPDATE projects SET style_guide_json = ?, updated_at = ? WHERE id = ?",
      JSON.stringify(styleGuide),
      now,
      projectId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "extract_style",
      JSON.stringify({ hasImages: !!(images && images.length > 0), hasManualKeywords: !!manualKeywords }),
      now
    );

    return NextResponse.json({ styleGuide });
  } catch (error) {
    console.error("Extract style error:", error);
    return NextResponse.json({ error: "风格提取失败" }, { status: 500 });
  }
}

/** Update style guide manually (edit keywords) */
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const updates = await request.json();
    const db = getDb();
    const project = db.get<{ id: string; style_guide_json: string | null }>(
      "SELECT id, style_guide_json FROM projects WHERE id = ?",
      projectId
    );
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    const existing = project.style_guide_json
      ? JSON.parse(project.style_guide_json)
      : {};

    const merged = { ...existing, ...updates, updatedAt: new Date().toISOString() };
    const now = new Date().toISOString();
    db.run(
      "UPDATE projects SET style_guide_json = ?, updated_at = ? WHERE id = ?",
      JSON.stringify(merged),
      now,
      projectId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "update_style",
      JSON.stringify({ updatedKeys: Object.keys(updates) }),
      now
    );

    return NextResponse.json({ styleGuide: merged });
  } catch (error) {
    console.error("Update style error:", error);
    return NextResponse.json({ error: "更新风格指南失败" }, { status: 500 });
  }
}
