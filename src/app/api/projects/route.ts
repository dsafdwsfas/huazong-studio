import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List projects */
export async function GET(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const db = getDb();
    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status");

    interface ProjectRow {
      id: string;
      name: string;
      description: string;
      cover_url: string | null;
      status: string;
      style_guide_json: string | null;
      created_by: string;
      created_at: string;
      updated_at: string;
    }

    let projects: ProjectRow[];
    if (status && status !== "all") {
      projects = db.all<ProjectRow>(
        "SELECT * FROM projects WHERE status = ?",
        status
      );
    } else {
      projects = db.all<ProjectRow>("SELECT * FROM projects");
    }

    // Enrich with stats
    const enriched = projects.map((p) => {
      const totalShots =
        db.get<{ cnt: number }>(
          "SELECT COUNT(*) as cnt FROM shots WHERE project_id = ?",
          p.id
        )?.cnt ?? 0;

      const approvedShots =
        db.get<{ cnt: number }>(
          "SELECT COUNT(*) as cnt FROM shots WHERE project_id = ? AND status IN ('approved', 'delivered')",
          p.id
        )?.cnt ?? 0;

      return {
        ...p,
        totalShots,
        approvedShots,
        progress: totalShots > 0 ? Math.round((approvedShots / totalShots) * 100) : 0,
      };
    });

    // Sort by updated_at desc
    enriched.sort(
      (a, b) =>
        new Date(b.updated_at).getTime() -
        new Date(a.updated_at).getTime()
    );

    return NextResponse.json({ projects: enriched });
  } catch (error) {
    console.error("List projects error:", error);
    return NextResponse.json({ error: "获取项目失败" }, { status: 500 });
  }
}

/** Update project (status change, archive/unarchive) */
export async function PATCH(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    if (payload.role !== "admin" && payload.role !== "director") {
      return NextResponse.json({ error: "没有权限" }, { status: 403 });
    }

    const { projectId, status, name, description } = await request.json();
    if (!projectId) return NextResponse.json({ error: "缺少项目ID" }, { status: 400 });

    const db = getDb();
    const project = db.get<Record<string, unknown>>(
      "SELECT * FROM projects WHERE id = ?",
      projectId
    );
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    if (status) {
      const VALID_STATUSES = ["active", "completed", "archived"];
      if (!VALID_STATUSES.includes(status)) {
        return NextResponse.json({ error: "无效的项目状态" }, { status: 400 });
      }
    }

    const now = new Date().toISOString();
    const sets: string[] = ["updated_at = ?"];
    const params: unknown[] = [now];

    if (status) {
      sets.push("status = ?");
      params.push(status);
    }
    if (name) {
      sets.push("name = ?");
      params.push(name);
    }
    if (description !== undefined) {
      sets.push("description = ?");
      params.push(description);
    }

    params.push(projectId);
    db.run(`UPDATE projects SET ${sets.join(", ")} WHERE id = ?`, ...params);

    const updated = db.get<Record<string, unknown>>(
      "SELECT * FROM projects WHERE id = ?",
      projectId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "update_project",
      JSON.stringify({ status, name, description }),
      now
    );

    return NextResponse.json({ project: updated });
  } catch (error) {
    console.error("Update project error:", error);
    return NextResponse.json({ error: "更新项目失败" }, { status: 500 });
  }
}

/** Create project */
export async function POST(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    if (payload.role !== "admin" && payload.role !== "director") {
      return NextResponse.json({ error: "没有创建项目的权限" }, { status: 403 });
    }

    const { name, description } = await request.json();
    if (!name) {
      return NextResponse.json({ error: "项目名称不能为空" }, { status: 400 });
    }

    const db = getDb();
    const now = new Date().toISOString();
    const projectId = generateId("prj");

    db.run(
      `INSERT INTO projects (id, name, description, cover_url, status, style_guide_json, created_by, created_at, updated_at)
       VALUES (?, ?, ?, NULL, 'active', NULL, ?, ?, ?)`,
      projectId,
      name,
      description || "",
      payload.sub,
      now,
      now
    );

    // Add creator as project member
    db.run(
      "INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
      projectId,
      payload.sub,
      payload.role,
      now
    );

    const project = db.get<Record<string, unknown>>(
      "SELECT * FROM projects WHERE id = ?",
      projectId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "create_project",
      JSON.stringify({ name }),
      now
    );

    return NextResponse.json({ project }, { status: 201 });
  } catch (error) {
    console.error("Create project error:", error);
    return NextResponse.json({ error: "创建项目失败" }, { status: 500 });
  }
}
