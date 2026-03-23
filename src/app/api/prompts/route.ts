import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

function getPrompts() {
  return getDb().prompts;
}

/** List prompts */
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
    const sort = searchParams.get("sort") || "newest";

    let prompts = getPrompts();

    // Filter by tag
    if (tag) {
      prompts = prompts.filter((p) => {
        const tags = JSON.parse(p.tagsJson || "[]");
        return tags.includes(tag);
      });
    }

    // Search
    if (search) {
      const q = search.toLowerCase();
      prompts = prompts.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.content.toLowerCase().includes(q) ||
          p.tagsJson.toLowerCase().includes(q)
      );
    }

    // Sort
    if (sort === "popular") {
      prompts.sort((a, b) => b.usageCount - a.usageCount);
    } else {
      prompts.sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
    }

    // Enrich with creator name
    const db = getDb();
    const enriched = prompts.map((p) => {
      const creator = db.users.find((u) => u.id === p.createdBy);
      return {
        ...p,
        tags: JSON.parse(p.tagsJson || "[]"),
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
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

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

    const now = new Date().toISOString();
    const prompt = {
      id: generateId("pmt"),
      title,
      content,
      format: detectedFormat as "text" | "json",
      tagsJson: JSON.stringify(tags || []),
      previewImageUrl: previewImageUrl || null,
      usageCount: 0,
      createdBy: payload.sub,
      createdAt: now,
      updatedAt: now,
    };

    getPrompts().push(prompt);

    return NextResponse.json({ prompt }, { status: 201 });
  } catch (error) {
    console.error("Create prompt error:", error);
    return NextResponse.json({ error: "创建提示词失败" }, { status: 500 });
  }
}
