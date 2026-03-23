import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List characters for a project */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const db = getDb();
    const characters = db.all<Record<string, unknown>>(
      "SELECT * FROM characters WHERE project_id = ?",
      projectId
    );

    const result = characters.map((c) => ({
      ...c,
      refs: db.all<Record<string, unknown>>(
        "SELECT * FROM character_refs WHERE character_id = ?",
        c.id
      ),
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
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { name, description, refImages } = await request.json();
    if (!name) return NextResponse.json({ error: "角色名称不能为空" }, { status: 400 });

    const db = getDb();
    const now = new Date().toISOString();
    const characterId = generateId("chr");

    db.run(
      "INSERT INTO characters (id, project_id, name, description, is_global, created_at) VALUES (?, ?, ?, ?, 0, ?)",
      characterId,
      projectId,
      name,
      description || null,
      now
    );

    // Add reference images if provided
    const refs: Record<string, unknown>[] = [];
    if (refImages && Array.isArray(refImages)) {
      for (const img of refImages) {
        const refId = generateId("crf");
        db.run(
          "INSERT INTO character_refs (id, character_id, ref_image_url, ref_type, created_at) VALUES (?, ?, ?, ?, ?)",
          refId,
          characterId,
          img.url || img.base64 || "",
          img.type || "front",
          now
        );
        const ref = db.get<Record<string, unknown>>(
          "SELECT * FROM character_refs WHERE id = ?",
          refId
        );
        if (ref) refs.push(ref);
      }
    }

    const character = db.get<Record<string, unknown>>(
      "SELECT * FROM characters WHERE id = ?",
      characterId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "create_character",
      JSON.stringify({ characterId, name }),
      now
    );

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
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { searchParams } = new URL(request.url);
    const characterId = searchParams.get("characterId");
    if (!characterId) return NextResponse.json({ error: "缺少角色ID" }, { status: 400 });

    const db = getDb();
    const character = db.get<{ id: string; name: string }>(
      "SELECT id, name FROM characters WHERE id = ?",
      characterId
    );
    if (!character) return NextResponse.json({ error: "角色不存在" }, { status: 404 });

    // Delete character (cascade deletes refs)
    db.run("DELETE FROM character_refs WHERE character_id = ?", characterId);
    db.run(
      "DELETE FROM shot_relations WHERE relation_type = 'character' AND relation_id = ?",
      characterId
    );
    db.run("DELETE FROM characters WHERE id = ?", characterId);

    // Activity log
    const now = new Date().toISOString();
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "delete_character",
      JSON.stringify({ characterId, name: character.name }),
      now
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Delete character error:", error);
    return NextResponse.json({ error: "删除角色失败" }, { status: 500 });
  }
}
