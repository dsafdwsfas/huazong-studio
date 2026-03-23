import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List prompts */
export async function GET(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const { searchParams } = new URL(request.url);
    const tag = searchParams.get("tag");
    const search = searchParams.get("q");
    const sort = searchParams.get("sort") || "newest";

    const db = getDb();

    let prompts = db.all<Record<string, unknown>>("SELECT * FROM prompts");

    // Filter by tag
    if (tag) {
      prompts = prompts.filter((p) => {
        const tags = JSON.parse((p.tags_json as string) || "[]");
        return tags.includes(tag);
      });
    }

    // Search
    if (search) {
      const q = search.toLowerCase();
      prompts = prompts.filter(
        (p) =>
          (p.title as string).toLowerCase().includes(q) ||
          (p.content as string).toLowerCase().includes(q) ||
          ((p.tags_json as string) || "").toLowerCase().includes(q)
      );
    }

    // Sort
    if (sort === "popular") {
      prompts.sort((a, b) => (b.usage_count as number) - (a.usage_count as number));
    } else {
      prompts.sort(
        (a, b) =>
          new Date(b.created_at as string).getTime() -
          new Date(a.created_at as string).getTime()
      );
    }

    // Enrich with creator name
    const enriched = prompts.map((p) => {
      const creator = db.get<{ nickname: string }>(
        "SELECT nickname FROM users WHERE id = ?",
        p.created_by
      );
      return {
        ...p,
        tags: JSON.parse((p.tags_json as string) || "[]"),
        creatorName: creator?.nickname || "未知",
      };
    });

    return NextResponse.json({ prompts: enriched });
  } catch (error) {
    console.error("List prompts error:", error);
    return NextResponse.json({ error: "获取提示词失败" }, { status: 500 });
  }
}

/** Create prompt */
export async function POST(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { title, content, format, tags, previewImageUrl } = await request.json();

    if (!title || !content) {
      return NextResponse.json({ error: "标题和内容不能为空" }, { status: 400 });
    }

    // Auto-detect format
    let detectedFormat = format || "text";
    if (!format) {
      try {
        JSON.parse(content);
        detectedFormat = "json";
      } catch {
        detectedFormat = "text";
      }
    }

    const db = getDb();
    const now = new Date().toISOString();
    const promptId = generateId("pmt");

    db.run(
      `INSERT INTO prompts (id, title, content, format, tags_json, preview_image_url, usage_count, created_by, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)`,
      promptId,
      title,
      content,
      detectedFormat,
      JSON.stringify(tags || []),
      previewImageUrl || null,
      payload.sub,
      now,
      now
    );

    const prompt = db.get<Record<string, unknown>>(
      "SELECT * FROM prompts WHERE id = ?",
      promptId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      null,
      "create_prompt",
      JSON.stringify({ promptId, title }),
      now
    );

    return NextResponse.json({ prompt }, { status: 201 });
  } catch (error) {
    console.error("Create prompt error:", error);
    return NextResponse.json({ error: "创建提示词失败" }, { status: 500 });
  }
}
