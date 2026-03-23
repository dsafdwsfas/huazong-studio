import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List scenes for a project */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const db = getDb();
    const scenesList = db.all<Record<string, unknown>>(
      "SELECT * FROM scenes WHERE project_id = ?",
      projectId
    );

    const result = scenesList.map((s) => ({
      ...s,
      refs: db.all<Record<string, unknown>>(
        "SELECT * FROM scene_refs WHERE scene_id = ?",
        s.id
      ),
    }));

    return NextResponse.json({ scenes: result });
  } catch (error) {
    console.error("List scenes error:", error);
    return NextResponse.json({ error: "获取场景列表失败" }, { status: 500 });
  }
}

/** Create scene */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { name, description, timeOfDay, refImages } = await request.json();
    if (!name) return NextResponse.json({ error: "场景名称不能为空" }, { status: 400 });

    const db = getDb();
    const now = new Date().toISOString();
    const sceneId = generateId("scn");

    db.run(
      "INSERT INTO scenes (id, project_id, name, description, time_of_day, is_global, created_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
      sceneId,
      projectId,
      name,
      description || null,
      timeOfDay || null,
      now
    );

    const refs: Record<string, unknown>[] = [];
    if (refImages && Array.isArray(refImages)) {
      for (const img of refImages) {
        const refId = generateId("srf");
        db.run(
          "INSERT INTO scene_refs (id, scene_id, ref_image_url, created_at) VALUES (?, ?, ?, ?)",
          refId,
          sceneId,
          img.url || img.base64 || "",
          now
        );
        const ref = db.get<Record<string, unknown>>(
          "SELECT * FROM scene_refs WHERE id = ?",
          refId
        );
        if (ref) refs.push(ref);
      }
    }

    const scene = db.get<Record<string, unknown>>(
      "SELECT * FROM scenes WHERE id = ?",
      sceneId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "create_scene",
      JSON.stringify({ sceneId, name }),
      now
    );

    return NextResponse.json({ scene: { ...scene, refs } }, { status: 201 });
  } catch (error) {
    console.error("Create scene error:", error);
    return NextResponse.json({ error: "创建场景失败" }, { status: 500 });
  }
}

/** Delete scene */
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
    const sceneId = searchParams.get("sceneId");
    if (!sceneId) return NextResponse.json({ error: "缺少场景ID" }, { status: 400 });

    const db = getDb();
    const scene = db.get<{ id: string; name: string }>(
      "SELECT id, name FROM scenes WHERE id = ?",
      sceneId
    );
    if (!scene) return NextResponse.json({ error: "场景不存在" }, { status: 404 });

    db.run("DELETE FROM scene_refs WHERE scene_id = ?", sceneId);
    db.run(
      "DELETE FROM shot_relations WHERE relation_type = 'scene' AND relation_id = ?",
      sceneId
    );
    db.run("DELETE FROM scenes WHERE id = ?", sceneId);

    // Activity log
    const now = new Date().toISOString();
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "delete_scene",
      JSON.stringify({ sceneId, name: scene.name }),
      now
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Delete scene error:", error);
    return NextResponse.json({ error: "删除场景失败" }, { status: 500 });
  }
}
