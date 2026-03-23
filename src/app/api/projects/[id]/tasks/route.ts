import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List tasks for a project */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status");
    const assignee = searchParams.get("assignee");

    const db = getDb();

    let sql = "SELECT * FROM tasks WHERE project_id = ?";
    const params_arr: unknown[] = [projectId];

    if (status) {
      sql += " AND status = ?";
      params_arr.push(status);
    }
    if (assignee) {
      sql += " AND assignee_id = ?";
      params_arr.push(assignee);
    }

    sql += " ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 WHEN 'low' THEN 2 END ASC, created_at DESC";

    const taskList = db.all<Record<string, unknown>>(sql, ...params_arr);

    // Enrich with assignee name
    const result = taskList.map((t) => {
      const user = t.assignee_id
        ? db.get<{ nickname: string }>(
            "SELECT nickname FROM users WHERE id = ?",
            t.assignee_id
          )
        : null;
      return { ...t, assigneeName: user?.nickname || null };
    });

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
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { title, assigneeId, shotId, annotationId, priority, dueDate } =
      await request.json();
    if (!title) return NextResponse.json({ error: "任务标题不能为空" }, { status: 400 });

    const validPriority = priority || "medium";
    if (!["low", "medium", "high"].includes(validPriority)) {
      return NextResponse.json({ error: "无效的优先级" }, { status: 400 });
    }

    const db = getDb();
    const now = new Date().toISOString();
    const taskId = generateId("tsk");

    db.run(
      `INSERT INTO tasks (id, project_id, shot_id, annotation_id, title, assignee_id, status, priority, due_date, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)`,
      taskId,
      projectId,
      shotId || null,
      annotationId || null,
      title,
      assigneeId || null,
      validPriority,
      dueDate || null,
      now,
      now
    );

    const task = db.get<Record<string, unknown>>(
      "SELECT * FROM tasks WHERE id = ?",
      taskId
    );

    const user = assigneeId
      ? db.get<{ nickname: string }>(
          "SELECT nickname FROM users WHERE id = ?",
          assigneeId
        )
      : null;

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "create_task",
      JSON.stringify({ taskId, title }),
      now
    );

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
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { taskId, status, assigneeId, priority, dueDate, title } =
      await request.json();
    if (!taskId) return NextResponse.json({ error: "缺少任务ID" }, { status: 400 });

    const db = getDb();
    const task = db.get<Record<string, unknown>>(
      "SELECT * FROM tasks WHERE id = ?",
      taskId
    );
    if (!task) return NextResponse.json({ error: "任务不存在" }, { status: 404 });

    if (status) {
      const VALID_STATUSES = ["pending", "in_progress", "completed"];
      if (!VALID_STATUSES.includes(status)) {
        return NextResponse.json({ error: "无效的任务状态" }, { status: 400 });
      }
    }
    if (priority) {
      const VALID_PRIORITIES = ["low", "medium", "high"];
      if (!VALID_PRIORITIES.includes(priority)) {
        return NextResponse.json({ error: "无效的优先级" }, { status: 400 });
      }
    }

    const now = new Date().toISOString();
    const sets: string[] = ["updated_at = ?"];
    const params_arr: unknown[] = [now];

    if (status) {
      sets.push("status = ?");
      params_arr.push(status);
    }
    if (assigneeId !== undefined) {
      sets.push("assignee_id = ?");
      params_arr.push(assigneeId);
    }
    if (priority) {
      sets.push("priority = ?");
      params_arr.push(priority);
    }
    if (dueDate !== undefined) {
      sets.push("due_date = ?");
      params_arr.push(dueDate);
    }
    if (title) {
      sets.push("title = ?");
      params_arr.push(title);
    }

    params_arr.push(taskId);
    db.run(`UPDATE tasks SET ${sets.join(", ")} WHERE id = ?`, ...params_arr);

    const updated = db.get<Record<string, unknown>>(
      "SELECT * FROM tasks WHERE id = ?",
      taskId
    );
    const user = updated?.assignee_id
      ? db.get<{ nickname: string }>(
          "SELECT nickname FROM users WHERE id = ?",
          updated.assignee_id
        )
      : null;

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "update_task",
      JSON.stringify({ taskId, status, assigneeId, priority }),
      now
    );

    return NextResponse.json({ task: { ...updated, assigneeName: user?.nickname || null } });
  } catch (error) {
    console.error("Update task error:", error);
    return NextResponse.json({ error: "更新任务失败" }, { status: 500 });
  }
}
