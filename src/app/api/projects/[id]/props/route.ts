import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List props for a project */
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
    const propsList = db.props.filter((p) => p.projectId === projectId);
    const result = propsList.map((p) => ({
      ...p,
      refs: db.propRefs.filter((r) => r.propId === p.id),
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
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { name, description, refImages } = await request.json();
    if (!name) return NextResponse.json({ error: "道具名称不能为空" }, { status: 400 });

    const db = getDb();
    const prop = {
      id: generateId("prp"),
      projectId,
      name,
      description: description || null,
      isGlobal: false,
      createdAt: new Date().toISOString(),
    };
    db.props.push(prop);

    const refs: any[] = [];
    if (refImages && Array.isArray(refImages)) {
      for (const img of refImages) {
        const ref = {
          id: generateId("prf"),
          propId: prop.id,
          refImageUrl: img.url || img.base64 || "",
          createdAt: new Date().toISOString(),
        };
        db.propRefs.push(ref);
        refs.push(ref);
      }
    }

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
    await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const propId = searchParams.get("propId");
    if (!propId) return NextResponse.json({ error: "缺少道具ID" }, { status: 400 });

    const db = getDb();
    const idx = db.props.findIndex((p) => p.id === propId);
    if (idx === -1) return NextResponse.json({ error: "道具不存在" }, { status: 404 });

    db.props.splice(idx, 1);
    db.propRefs = db.propRefs.filter((r) => r.propId !== propId) as any;
    db.shotRelations = db.shotRelations.filter(
      (r) => !(r.relationType === "prop" && r.relationId === propId)
    ) as any;

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Delete prop error:", error);
    return NextResponse.json({ error: "删除道具失败" }, { status: 500 });
  }
}
