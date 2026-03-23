import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List projects */
export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) {
      return NextResponse.json({ error: "未登录" }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload) {
      return NextResponse.json({ error: "登录已过期" }, { status: 401 });
    }

    const db = getDb();
    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status");

    let projects = db.projects;

    // Filter by status
    if (status && status !== "all") {
      projects = projects.filter((p) => p.status === status);
    }

    // Enrich with stats
    const enriched = projects.map((p) => {
      const shots = db.shots.filter((s) => s.projectId === p.id);
      const totalShots = shots.length;
      const approvedShots = shots.filter((s) => s.status === "approved" || s.status === "delivered").length;

      return {
        ...p,
        totalShots,
        approvedShots,
        progress: totalShots > 0 ? Math.round((approvedShots / totalShots) * 100) : 0,
      };
    });

    // Sort by updatedAt desc
    enriched.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());

    return NextResponse.json({ projects: enriched });
  } catch (error) {
    console.error("List projects error:", error);
    return NextResponse.json({ error: "获取项目失败" }, { status: 500 });
  }
}

/** Update project (status change, archive/unarchive) */
export async function PATCH(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    if (payload.role !== "admin" && payload.role !== "director") {
      return NextResponse.json({ error: "没有权限" }, { status: 403 });
    }

    const { projectId, status, name, description } = await request.json();
    if (!projectId) return NextResponse.json({ error: "缺少项目ID" }, { status: 400 });

    const db = getDb();
    const project = db.projects.find((p) => p.id === projectId);
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    if (status) {
      const VALID_STATUSES = ["active", "completed", "archived"];
      if (!VALID_STATUSES.includes(status)) {
        return NextResponse.json({ error: "无效的项目状态" }, { status: 400 });
      }
      project.status = status;
    }
    if (name) project.name = name;
    if (description !== undefined) project.description = description;
    project.updatedAt = new Date().toISOString();

    return NextResponse.json({ project });
  } catch (error) {
    console.error("Update project error:", error);
    return NextResponse.json({ error: "更新项目失败" }, { status: 500 });
  }
}

/** Create project */
export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) {
      return NextResponse.json({ error: "未登录" }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload) {
      return NextResponse.json({ error: "登录已过期" }, { status: 401 });
    }

    // Only admin and director can create projects
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

    const project = {
      id: projectId,
      name,
      description: description || "",
      coverUrl: null,
      status: "active" as const,
      styleGuideJson: null,
      createdBy: payload.sub,
      createdAt: now,
      updatedAt: now,
    };

    db.projects.push(project);

    // Add creator as project member
    db.projectMembers.push({
      projectId,
      userId: payload.sub,
      role: payload.role,
      joinedAt: now,
    });

    return NextResponse.json({ project }, { status: 201 });
  } catch (error) {
    console.error("Create project error:", error);
    return NextResponse.json({ error: "创建项目失败" }, { status: 500 });
  }
}
