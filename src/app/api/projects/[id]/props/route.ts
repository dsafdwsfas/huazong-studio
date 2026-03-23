import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List props for a project */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const db = getDb();
    const propsList = db.all<Record<string, unknown>>(
      "SELECT * FROM props WHERE project_id = ?",
      projectId
    );

    const result = propsList.map((p) => ({
      ...p,
      refs: db.all<Record<string, unknown>>(
        "SELECT * FROM prop_refs WHERE prop_id = ?",
        p.id
      ),
    }));

    return NextResponse.json({ props: result });
  } catch (error) {
    console.error("List props error:", error);
    return NextResponse.json({ error: "获取道具列表失败" }, { status: 500 });
  }
}

/** Create prop */
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
    if (!name) return NextResponse.json({ error: "道具名称不能为空" }, { status: 400 });

    const db = getDb();
    const now = new Date().toISOString();
    const propId = generateId("prp");

    db.run(
      "INSERT INTO props (id, project_id, name, description, is_global, created_at) VALUES (?, ?, ?, ?, 0, ?)",
      propId,
      projectId,
      name,
      description || null,
      now
    );

    const refs: Record<string, unknown>[] = [];
    if (refImages && Array.isArray(refImages)) {
      for (const img of refImages) {
        const refId = generateId("prf");
        db.run(
          "INSERT INTO prop_refs (id, prop_id, ref_image_url, created_at) VALUES (?, ?, ?, ?)",
          refId,
          propId,
          img.url || img.base64 || "",
          now
        );
        const ref = db.get<Record<string, unknown>>(
          "SELECT * FROM prop_refs WHERE id = ?",
          refId
        );
        if (ref) refs.push(ref);
      }
    }

    const prop = db.get<Record<string, unknown>>(
      "SELECT * FROM props WHERE id = ?",
      propId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "create_prop",
      JSON.stringify({ propId, name }),
      now
    );

    return NextResponse.json({ prop: { ...prop, refs } }, { status: 201 });
  } catch (error) {
    console.error("Create prop error:", error);
    return NextResponse.json({ error: "创建道具失败" }, { status: 500 });
  }
}

/** Delete prop */
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
    const propId = searchParams.get("propId");
    if (!propId) return NextResponse.json({ error: "缺少道具ID" }, { status: 400 });

    const db = getDb();
    const prop = db.get<{ id: string; name: string }>(
      "SELECT id, name FROM props WHERE id = ?",
      propId
    );
    if (!prop) return NextResponse.json({ error: "道具不存在" }, { status: 404 });

    db.run("DELETE FROM prop_refs WHERE prop_id = ?", propId);
    db.run(
      "DELETE FROM shot_relations WHERE relation_type = 'prop' AND relation_id = ?",
      propId
    );
    db.run("DELETE FROM props WHERE id = ?", propId);

    // Activity log
    const now = new Date().toISOString();
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "delete_prop",
      JSON.stringify({ propId, name: prop.name }),
      now
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Delete prop error:", error);
    return NextResponse.json({ error: "删除道具失败" }, { status: 500 });
  }
}
