import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List style templates */
export async function GET(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const { searchParams } = new URL(request.url);
    const tag = searchParams.get("tag");
    const search = searchParams.get("q");

    const db = getDb();

    let templates = db.all<Record<string, unknown>>("SELECT * FROM style_templates");

    if (tag) {
      templates = templates.filter((t) => {
        const tags = JSON.parse((t.tags_json as string) || "[]");
        return tags.includes(tag);
      });
    }

    if (search) {
      templates = templates.filter(
        (t) =>
          (t.name as string).includes(search) ||
          ((t.description as string) || "").includes(search) ||
          ((t.keywords_json as string) || "").includes(search)
      );
    }

    // Sort by newest first
    templates.sort(
      (a, b) =>
        new Date(b.created_at as string).getTime() -
        new Date(a.created_at as string).getTime()
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
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { name, tags, keywords, description, refImages, projectId } =
      await request.json();

    if (!name) {
      return NextResponse.json({ error: "模板名称不能为空" }, { status: 400 });
    }

    const db = getDb();
    const now = new Date().toISOString();
    const templateId = generateId("stl");

    db.run(
      `INSERT INTO style_templates (id, name, tags_json, keywords_json, description, ref_images_json, project_id, created_by, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      templateId,
      name,
      JSON.stringify(tags || []),
      JSON.stringify(keywords || {}),
      description || "",
      refImages ? JSON.stringify(refImages) : null,
      projectId || null,
      payload.sub,
      now
    );

    const template = db.get<Record<string, unknown>>(
      "SELECT * FROM style_templates WHERE id = ?",
      templateId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId || null,
      "create_style_template",
      JSON.stringify({ templateId, name }),
      now
    );

    return NextResponse.json({ template }, { status: 201 });
  } catch (error) {
    console.error("Create style template error:", error);
    return NextResponse.json({ error: "创建模板失败" }, { status: 500 });
  }
}
