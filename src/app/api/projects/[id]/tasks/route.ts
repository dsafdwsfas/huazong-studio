import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List tasks for a project */
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

    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status");
    const assignee = searchParams.get("assignee");

    const db = getDb();
    let taskList = db.tasks.filter((t) => t.projectId === projectId);

    if (status) taskList = taskList.filter((t) => t.status === status);
    if (assignee) taskList = taskList.filter((t) => t.assigneeId === assignee);

    // Enrich with assignee name
    const result = taskList.map((t) => {
      const user = db.users.find((u) => u.id === t.assigneeId);
      return { ...t, assigneeName: user?.nickname || null };
    });

    // Sort by priority (high first), then by creation date
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    result.sort(
      (a, b) =>
        priorityOrder[a.priority] - priorityOrder[b.priority] ||
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );

    return NextResponse.json({ tasks: result });
  } catch (error) {
    console.error("List tasks error:", error);
    return NextResponse.json({ error: "获取任务列表失败" }, { status: 500 });
  }
}

/** Create task */
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

    const { title, assigneeId, shotId, annotationId, priority, dueDate } =
      await request.json();
    if (!title) return NextResponse.json({ error: "任务标题不能为空" }, { status: 400 });

    const db = getDb();
    const now = new Date().toISOString();
    const task = {
      id: generateId("tsk"),
      projectId,
      shotId: shotId || null,
      annotationId: annotationId || null,
      title,
      assigneeId: assigneeId || null,
      status: "pending" as const,
      priority: priority || "medium",
      dueDate: dueDate || null,
      createdAt: now,
      updatedAt: now,
    };
    db.tasks.push(task);

    const user = db.users.find((u) => u.id === task.assigneeId);
    return NextResponse.json(
      { task: { ...task, assigneeName: user?.nickname || null } },
      { status: 201 }
    );
  } catch (error) {
    console.error("Create task error:", error);
    return NextResponse.json({ error: "创建任务失败" }, { status: 500 });
  }
}

/** Update task (status, assignee, etc.) */
export async function PATCH(
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

    const { taskId, status, assigneeId, priority, dueDate, title } =
      await request.json();
    if (!taskId) return NextResponse.json({ error: "缺少任务ID" }, { status: 400 });

    const db = getDb();
    const task = db.tasks.find((t) => t.id === taskId);
    if (!task) return NextResponse.json({ error: "任务不存在" }, { status: 404 });

    if (status) task.status = status;
    if (assigneeId !== undefined) task.assigneeId = assigneeId;
    if (priority) task.priority = priority;
    if (dueDate !== undefined) task.dueDate = dueDate;
    if (title) task.title = title;
    task.updatedAt = new Date().toISOString();

    const user = db.users.find((u) => u.id === task.assigneeId);
    return NextResponse.json({ task: { ...task, assigneeName: user?.nickname || null } });
  } catch (error) {
    console.error("Update task error:", error);
    return NextResponse.json({ error: "更新任务失败" }, { status: 500 });
  }
}
