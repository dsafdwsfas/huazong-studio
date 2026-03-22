import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

// Extend db-store for style templates
interface StyleTemplate {
  id: string;
  name: string;
  tagsJson: string;
  keywordsJson: string;
  description: string;
  refImagesJson: string | null;
  projectId: string | null;
  createdBy: string;
  createdAt: string;
}

// Add style templates to store if not exists
function getStyleTemplates(): StyleTemplate[] {
  const db = getDb() as any;
  if (!db.styleTemplates) db.styleTemplates = [];
  return db.styleTemplates;
}

/** List style templates */
export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const tag = searchParams.get("tag");
    const search = searchParams.get("q");

    let templates = getStyleTemplates();

    if (tag) {
      templates = templates.filter((t) => {
        const tags = JSON.parse(t.tagsJson || "[]");
        return tags.includes(tag);
      });
    }

    if (search) {
      templates = templates.filter(
        (t) =>
          t.name.includes(search) ||
          t.description.includes(search) ||
          t.keywordsJson.includes(search)
      );
    }

    // Sort by newest first
    templates.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );

    return NextResponse.json({ templates });
  } catch (error) {
    console.error("List style templates error:", error);
    return NextResponse.json({ error: "获取风格模板失败" }, { status: 500 });
  }
}

/** Create style template */
export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { name, tags, keywords, description, refImages, projectId } =
      await request.json();

    if (!name) {
      return NextResponse.json({ error: "模板名称不能为空" }, { status: 400 });
    }

    const templates = getStyleTemplates();
    const template: StyleTemplate = {
      id: generateId("stl"),
      name,
      tagsJson: JSON.stringify(tags || []),
      keywordsJson: JSON.stringify(keywords || {}),
      description: description || "",
      refImagesJson: refImages ? JSON.stringify(refImages) : null,
      projectId: projectId || null,
      createdBy: payload.sub,
      createdAt: new Date().toISOString(),
    };

    templates.push(template);

    return NextResponse.json({ template }, { status: 201 });
  } catch (error) {
    console.error("Create style template error:", error);
    return NextResponse.json({ error: "创建模板失败" }, { status: 500 });
  }
}
