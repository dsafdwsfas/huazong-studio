import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List characters for a project */
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
    const characters = db.characters.filter((c) => c.projectId === projectId);
    const result = characters.map((c) => ({
      ...c,
      refs: db.characterRefs.filter((r) => r.characterId === c.id),
    }));

    return NextResponse.json({ characters: result });
  } catch (error) {
    console.error("List characters error:", error);
    return NextResponse.json({ error: "获取角色列表失败" }, { status: 500 });
  }
}

/** Create character */
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

    const { name, description, refImages } = await request.json();
    if (!name) return NextResponse.json({ error: "角色名称不能为空" }, { status: 400 });

    const db = getDb();
    const character = {
      id: generateId("chr"),
      projectId,
      name,
      description: description || null,
      isGlobal: false,
      createdAt: new Date().toISOString(),
    };
    db.characters.push(character);

    // Add reference images if provided
    const refs: any[] = [];
    if (refImages && Array.isArray(refImages)) {
      for (const img of refImages) {
        const ref = {
          id: generateId("crf"),
          characterId: character.id,
          refImageUrl: img.url || img.base64 || "",
          refType: img.type || "front",
          createdAt: new Date().toISOString(),
        };
        db.characterRefs.push(ref);
        refs.push(ref);
      }
    }

    return NextResponse.json({ character: { ...character, refs } }, { status: 201 });
  } catch (error) {
    console.error("Create character error:", error);
    return NextResponse.json({ error: "创建角色失败" }, { status: 500 });
  }
}

/** Delete character */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const characterId = searchParams.get("characterId");
    if (!characterId) return NextResponse.json({ error: "缺少角色ID" }, { status: 400 });

    const db = getDb();
    const idx = db.characters.findIndex((c) => c.id === characterId);
    if (idx === -1) return NextResponse.json({ error: "角色不存在" }, { status: 404 });

    db.characters.splice(idx, 1);
    // Clean up refs and relations
    db.characterRefs = db.characterRefs.filter((r) => r.characterId !== characterId) as any;
    db.shotRelations = db.shotRelations.filter(
      (r) => !(r.relationType === "character" && r.relationId === characterId)
    ) as any;

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Delete character error:", error);
    return NextResponse.json({ error: "删除角色失败" }, { status: 500 });
  }
}
