import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List shots for a project */
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
    const project = db.projects.find((p) => p.id === projectId);
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    const shots = db.shots
      .filter((s) => s.projectId === projectId)
      .sort((a, b) => a.sortOrder - b.sortOrder);

    // Enrich with assets and annotation counts
    const enriched = shots.map((shot) => {
      const assets = db.assets.filter((a) => a.shotId === shot.id);
      const latestAsset = assets.sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      )[0];
      const unresolvedAnnotations = db.annotations.filter(
        (a) =>
          assets.some((asset) => asset.id === a.assetId) &&
          a.status !== "resolved"
      ).length;

      const assignee = shot.assigneeId
        ? db.users.find((u) => u.id === shot.assigneeId)
        : null;

      return {
        ...shot,
        latestAsset: latestAsset || null,
        assetCount: assets.length,
        unresolvedAnnotations,
        assigneeName: assignee?.nickname || null,
      };
    });

    return NextResponse.json({ shots: enriched, project });
  } catch (error) {
    console.error("List shots error:", error);
    return NextResponse.json({ error: "获取镜头失败" }, { status: 500 });
  }
}

/** Create a single shot */
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

    const db = getDb();
    const { sceneDescription, dialogue, durationSeconds, cameraAngle } =
      await request.json();

    const existingShots = db.shots.filter((s) => s.projectId === projectId);
    const nextNumber = existingShots.length + 1;
    const now = new Date().toISOString();

    const shot = {
      id: generateId("sht"),
      projectId,
      shotNumber: nextNumber,
      sceneDescription: sceneDescription || "",
      dialogue: dialogue || null,
      durationSeconds: durationSeconds || null,
      cameraAngle: cameraAngle || null,
      status: "pending_upload",
      assigneeId: null,
      sortOrder: nextNumber,
      createdAt: now,
      updatedAt: now,
    };

    db.shots.push(shot);

    // Update project updatedAt
    const project = db.projects.find((p) => p.id === projectId);
    if (project) project.updatedAt = now;

    return NextResponse.json({ shot }, { status: 201 });
  } catch (error) {
    console.error("Create shot error:", error);
    return NextResponse.json({ error: "创建镜头失败" }, { status: 500 });
  }
}
