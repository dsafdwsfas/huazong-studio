import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List scenes for a project */
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
    const scenesList = db.scenes.filter((s) => s.projectId === projectId);
    const result = scenesList.map((s) => ({
      ...s,
      refs: db.sceneRefs.filter((r) => r.sceneId === s.id),
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
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { name, description, timeOfDay, refImages } = await request.json();
    if (!name) return NextResponse.json({ error: "场景名称不能为空" }, { status: 400 });

    const db = getDb();
    const scene = {
      id: generateId("scn"),
      projectId,
      name,
      description: description || null,
      timeOfDay: timeOfDay || null,
      isGlobal: false,
      createdAt: new Date().toISOString(),
    };
    db.scenes.push(scene);

    const refs: any[] = [];
    if (refImages && Array.isArray(refImages)) {
      for (const img of refImages) {
        const ref = {
          id: generateId("srf"),
          sceneId: scene.id,
          refImageUrl: img.url || img.base64 || "",
          createdAt: new Date().toISOString(),
        };
        db.sceneRefs.push(ref);
        refs.push(ref);
      }
    }

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
    await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const sceneId = searchParams.get("sceneId");
    if (!sceneId) return NextResponse.json({ error: "缺少场景ID" }, { status: 400 });

    const db = getDb();
    const idx = db.scenes.findIndex((s) => s.id === sceneId);
    if (idx === -1) return NextResponse.json({ error: "场景不存在" }, { status: 404 });

    db.scenes.splice(idx, 1);
    db.sceneRefs = db.sceneRefs.filter((r) => r.sceneId !== sceneId) as any;
    db.shotRelations = db.shotRelations.filter(
      (r) => !(r.relationType === "scene" && r.relationId === sceneId)
    ) as any;

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Delete scene error:", error);
    return NextResponse.json({ error: "删除场景失败" }, { status: 500 });
  }
}
