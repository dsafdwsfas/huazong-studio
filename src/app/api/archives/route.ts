import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { getDb } from "@/lib/db-store";

/** List all archives across projects (characters, props, scenes) */
export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const type = searchParams.get("type"); // characters | props | scenes
    const search = searchParams.get("q");

    const db = getDb();

    const projectMap = new Map(db.projects.map((p) => [p.id, p.name]));

    if (type === "characters" || !type) {
      let chars = db.characters.map((c) => ({
        ...c,
        projectName: c.projectId ? projectMap.get(c.projectId) || "未知项目" : "全局",
        refs: db.characterRefs.filter((r) => r.characterId === c.id),
        archiveType: "character" as const,
      }));
      if (search) {
        chars = chars.filter((c) => c.name.includes(search) || c.description?.includes(search));
      }
      if (type === "characters") return NextResponse.json({ items: chars });
    }

    if (type === "props" || !type) {
      let propsList = db.props.map((p) => ({
        ...p,
        projectName: p.projectId ? projectMap.get(p.projectId) || "未知项目" : "全局",
        refs: db.propRefs.filter((r) => r.propId === p.id),
        archiveType: "prop" as const,
      }));
      if (search) {
        propsList = propsList.filter((p) => p.name.includes(search) || p.description?.includes(search));
      }
      if (type === "props") return NextResponse.json({ items: propsList });
    }

    if (type === "scenes" || !type) {
      let scenesList = db.scenes.map((s) => ({
        ...s,
        projectName: s.projectId ? projectMap.get(s.projectId) || "未知项目" : "全局",
        refs: db.sceneRefs.filter((r) => r.sceneId === s.id),
        archiveType: "scene" as const,
      }));
      if (search) {
        scenesList = scenesList.filter((s) => s.name.includes(search) || s.description?.includes(search));
      }
      if (type === "scenes") return NextResponse.json({ items: scenesList });
    }

    // Return all types combined
    const all = [
      ...db.characters.map((c) => ({
        id: c.id, name: c.name, description: c.description, archiveType: "character" as const,
        projectName: c.projectId ? projectMap.get(c.projectId) || "未知" : "全局",
        refCount: db.characterRefs.filter((r) => r.characterId === c.id).length,
        createdAt: c.createdAt,
      })),
      ...db.props.map((p) => ({
        id: p.id, name: p.name, description: p.description, archiveType: "prop" as const,
        projectName: p.projectId ? projectMap.get(p.projectId) || "未知" : "全局",
        refCount: db.propRefs.filter((r) => r.propId === p.id).length,
        createdAt: p.createdAt,
      })),
      ...db.scenes.map((s) => ({
        id: s.id, name: s.name, description: s.description, archiveType: "scene" as const,
        projectName: s.projectId ? projectMap.get(s.projectId) || "未知" : "全局",
        refCount: db.sceneRefs.filter((r) => r.sceneId === s.id).length,
        createdAt: s.createdAt,
      })),
    ];

    const filtered = search
      ? all.filter((a) => a.name.includes(search) || a.description?.includes(search))
      : all;

    filtered.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    return NextResponse.json({ items: filtered });
  } catch (error) {
    console.error("List archives error:", error);
    return NextResponse.json({ error: "获取档案失败" }, { status: 500 });
  }
}
