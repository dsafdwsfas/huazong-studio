import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { getDb } from "@/lib/db-store";

/** List all archives across projects (characters, props, scenes) */
export async function GET(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const { searchParams } = new URL(request.url);
    const type = searchParams.get("type"); // characters | props | scenes
    const search = searchParams.get("q");

    const db = getDb();

    if (type === "characters") {
      let chars = db.all<Record<string, unknown>>(
        `SELECT c.*, COALESCE(p.name, '全局') as project_name
         FROM characters c
         LEFT JOIN projects p ON c.project_id = p.id`
      );
      if (search) {
        const q = search;
        chars = chars.filter(
          (c) =>
            (c.name as string).includes(q) ||
            ((c.description as string) || "").includes(q)
        );
      }
      const items = chars.map((c) => ({
        ...c,
        refs: db.all<Record<string, unknown>>(
          "SELECT * FROM character_refs WHERE character_id = ?",
          c.id
        ),
        archiveType: "character",
      }));
      return NextResponse.json({ items });
    }

    if (type === "props") {
      let propsList = db.all<Record<string, unknown>>(
        `SELECT pr.*, COALESCE(p.name, '全局') as project_name
         FROM props pr
         LEFT JOIN projects p ON pr.project_id = p.id`
      );
      if (search) {
        const q = search;
        propsList = propsList.filter(
          (p) =>
            (p.name as string).includes(q) ||
            ((p.description as string) || "").includes(q)
        );
      }
      const items = propsList.map((p) => ({
        ...p,
        refs: db.all<Record<string, unknown>>(
          "SELECT * FROM prop_refs WHERE prop_id = ?",
          p.id
        ),
        archiveType: "prop",
      }));
      return NextResponse.json({ items });
    }

    if (type === "scenes") {
      let scenesList = db.all<Record<string, unknown>>(
        `SELECT s.*, COALESCE(p.name, '全局') as project_name
         FROM scenes s
         LEFT JOIN projects p ON s.project_id = p.id`
      );
      if (search) {
        const q = search;
        scenesList = scenesList.filter(
          (s) =>
            (s.name as string).includes(q) ||
            ((s.description as string) || "").includes(q)
        );
      }
      const items = scenesList.map((s) => ({
        ...s,
        refs: db.all<Record<string, unknown>>(
          "SELECT * FROM scene_refs WHERE scene_id = ?",
          s.id
        ),
        archiveType: "scene",
      }));
      return NextResponse.json({ items });
    }

    // Return all types combined
    interface ArchiveItem {
      id: string;
      name: string;
      description: string | null;
      created_at: string;
      project_id: string | null;
      project_name: string;
      ref_count: number;
      archiveType: string;
    }

    const characters: ArchiveItem[] = db.all<ArchiveItem>(
      `SELECT c.id, c.name, c.description, c.created_at, c.project_id,
              COALESCE(p.name, '全局') as project_name,
              (SELECT COUNT(*) FROM character_refs WHERE character_id = c.id) as ref_count
       FROM characters c
       LEFT JOIN projects p ON c.project_id = p.id`
    ).map((c) => ({ ...c, archiveType: "character" }));

    const props: ArchiveItem[] = db.all<ArchiveItem>(
      `SELECT pr.id, pr.name, pr.description, pr.created_at, pr.project_id,
              COALESCE(p.name, '全局') as project_name,
              (SELECT COUNT(*) FROM prop_refs WHERE prop_id = pr.id) as ref_count
       FROM props pr
       LEFT JOIN projects p ON pr.project_id = p.id`
    ).map((p) => ({ ...p, archiveType: "prop" }));

    const scenes: ArchiveItem[] = db.all<ArchiveItem>(
      `SELECT s.id, s.name, s.description, s.created_at, s.project_id,
              COALESCE(p.name, '全局') as project_name,
              (SELECT COUNT(*) FROM scene_refs WHERE scene_id = s.id) as ref_count
       FROM scenes s
       LEFT JOIN projects p ON s.project_id = p.id`
    ).map((s) => ({ ...s, archiveType: "scene" }));

    let all: ArchiveItem[] = [...characters, ...props, ...scenes];

    if (search) {
      const q = search;
      all = all.filter(
        (a) =>
          a.name.includes(q) ||
          (a.description || "").includes(q)
      );
    }

    all.sort(
      (a, b) =>
        new Date(b.created_at).getTime() -
        new Date(a.created_at).getTime()
    );

    return NextResponse.json({ items: all });
  } catch (error) {
    console.error("List archives error:", error);
    return NextResponse.json({ error: "获取档案失败" }, { status: 500 });
  }
}
