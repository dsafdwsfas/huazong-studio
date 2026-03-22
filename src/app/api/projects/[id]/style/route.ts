import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { getDb } from "@/lib/db-store";
import { extractStyleFromImages } from "@/lib/style-extractor";

/** Get project style guide */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const db = getDb();
    const project = db.projects.find((p) => p.id === projectId);
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    const styleGuide = project.styleGuideJson
      ? JSON.parse(project.styleGuideJson)
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
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    if (payload.role !== "admin" && payload.role !== "director") {
      return NextResponse.json({ error: "需要导演或管理员权限" }, { status: 403 });
    }

    const { images, manualKeywords } = await request.json();

    const db = getDb();
    const project = db.projects.find((p) => p.id === projectId);
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    let styleGuide;

    if (images && images.length > 0) {
      // AI extraction from images
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
      // Manual keywords only
      const existing = project.styleGuideJson
        ? JSON.parse(project.styleGuideJson)
        : {};
      styleGuide = {
        ...existing,
        manualKeywords,
        updatedAt: new Date().toISOString(),
      };
    } else {
      return NextResponse.json({ error: "请上传参考图或输入关键词" }, { status: 400 });
    }

    project.styleGuideJson = JSON.stringify(styleGuide);
    project.updatedAt = new Date().toISOString();

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
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const updates = await request.json();
    const db = getDb();
    const project = db.projects.find((p) => p.id === projectId);
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    const existing = project.styleGuideJson
      ? JSON.parse(project.styleGuideJson)
      : {};

    const merged = { ...existing, ...updates, updatedAt: new Date().toISOString() };
    project.styleGuideJson = JSON.stringify(merged);
    project.updatedAt = new Date().toISOString();

    return NextResponse.json({ styleGuide: merged });
  } catch (error) {
    console.error("Update style error:", error);
    return NextResponse.json({ error: "更新风格指南失败" }, { status: 500 });
  }
}
