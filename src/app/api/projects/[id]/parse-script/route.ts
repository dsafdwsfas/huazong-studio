import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/**
 * Parse a script/storyboard text and auto-split into shot cards.
 * Uses simple heuristic parsing (can be upgraded to Gemini API later).
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { scriptText, useAI = false } = await request.json();

    if (!scriptText || !scriptText.trim()) {
      return NextResponse.json({ error: "请输入剧本内容" }, { status: 400 });
    }

    let parsedShots: Array<{
      shotNumber: number;
      sceneDescription: string;
      dialogue: string | null;
      durationSeconds: number | null;
      cameraAngle: string | null;
    }>;

    if (useAI && process.env.GEMINI_API_KEY) {
      parsedShots = await parseScriptWithGemini(scriptText, process.env.GEMINI_API_KEY);
    } else {
      parsedShots = parseScriptRuleBased(scriptText);
    }

    // Save to database
    const db = getDb();
    const now = new Date().toISOString();
    const savedShots: Record<string, unknown>[] = [];

    for (const parsed of parsedShots) {
      const shotId = generateId("sht");
      db.run(
        `INSERT INTO shots (id, project_id, shot_number, scene_description, dialogue, duration_seconds, camera_angle, status, assignee_id, sort_order, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_upload', NULL, ?, ?, ?)`,
        shotId,
        projectId,
        parsed.shotNumber,
        parsed.sceneDescription,
        parsed.dialogue,
        parsed.durationSeconds,
        parsed.cameraAngle,
        parsed.shotNumber,
        now,
        now
      );
      const shot = db.get<Record<string, unknown>>(
        "SELECT * FROM shots WHERE id = ?",
        shotId
      );
      if (shot) savedShots.push(shot);
    }

    // Update project updated_at
    db.run("UPDATE projects SET updated_at = ? WHERE id = ?", now, projectId);

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "parse_script",
      JSON.stringify({ shotCount: savedShots.length }),
      now
    );

    return NextResponse.json({
      shots: savedShots,
      count: savedShots.length,
    });
  } catch (error) {
    console.error("Parse script error:", error);
    return NextResponse.json({ error: "解析剧本失败" }, { status: 500 });
  }
}

/**
 * Rule-based script parser.
 * Supports common Chinese storyboard formats:
 * - "镜头1：..." / "镜头 1：..."
 * - "1. ..." / "1、..."
 * - "场次1 ..." / "场景1 ..."
 * - "S1:" / "Shot 1:"
 * - Lines separated by blank lines
 */
function parseScriptRuleBased(text: string) {
  const lines = text.split("\n").map((l) => l.trim());
  const shots: Array<{
    shotNumber: number;
    sceneDescription: string;
    dialogue: string | null;
    durationSeconds: number | null;
    cameraAngle: string | null;
  }> = [];

  const shotPattern =
    /^(?:镜头|shot|s|场次|场景|sc)\s*(\d+)\s*[：:.\-、]/i;
  const numberedPattern = /^(\d+)\s*[.、：:)\]\-]/;

  let currentShot: (typeof shots)[0] | null = null;
  let shotCounter = 0;

  for (const line of lines) {
    if (!line) {
      if (currentShot && currentShot.sceneDescription) {
        continue;
      }
      continue;
    }

    const shotMatch = line.match(shotPattern);
    const numMatch = line.match(numberedPattern);

    if (shotMatch || numMatch) {
      if (currentShot) {
        shots.push(currentShot);
      }

      shotCounter++;
      const description = shotMatch
        ? line.replace(shotPattern, "").trim()
        : line.replace(numberedPattern, "").trim();

      const cameraMatch = description.match(
        /[（(](.*?(?:全景|中景|近景|特写|远景|俯拍|仰拍|跟拍|推|拉|摇|移|航拍).*?)[）)]/
      );

      const durationMatch = description.match(
        /(\d+)\s*(?:秒|s|sec)/i
      );

      currentShot = {
        shotNumber: shotCounter,
        sceneDescription: description,
        dialogue: null,
        durationSeconds: durationMatch ? parseInt(durationMatch[1]) : null,
        cameraAngle: cameraMatch ? cameraMatch[1] : null,
      };
    } else if (currentShot) {
      if (
        line.startsWith('"') ||
        line.startsWith('\u201c') ||
        line.startsWith("\u300c") ||
        line.match(/^[\u4e00-\u9fa5]{1,4}[：:]/)
      ) {
        currentShot.dialogue = currentShot.dialogue
          ? currentShot.dialogue + "\n" + line
          : line;
      } else {
        currentShot.sceneDescription += " " + line;
      }
    } else {
      shotCounter++;
      currentShot = {
        shotNumber: shotCounter,
        sceneDescription: line,
        dialogue: null,
        durationSeconds: null,
        cameraAngle: null,
      };
    }
  }

  if (currentShot) {
    shots.push(currentShot);
  }

  if (shots.length === 0) {
    const paragraphs = text
      .split(/\n\s*\n/)
      .map((p) => p.trim())
      .filter(Boolean);

    return paragraphs.map((p, i) => ({
      shotNumber: i + 1,
      sceneDescription: p,
      dialogue: null,
      durationSeconds: null,
      cameraAngle: null,
    }));
  }

  return shots;
}

/**
 * AI-powered script parser using Gemini API.
 */
async function parseScriptWithGemini(
  text: string,
  apiKey: string,
): Promise<Array<{
  shotNumber: number;
  sceneDescription: string;
  dialogue: string | null;
  durationSeconds: number | null;
  cameraAngle: string | null;
}>> {
  const prompt = `你是一位专业的影视分镜师。请将以下剧本/分镜脚本拆解为独立的镜头卡片。

对每个镜头提取：
- shotNumber: 镜头编号（从1开始）
- sceneDescription: 场景画面描述
- dialogue: 台词/旁白（没有则为null）
- durationSeconds: 预估时长秒数（没有则为null）
- cameraAngle: 机位/景别建议（如：全景、中景、近景、特写、俯拍等，没有则为null）

输出严格 JSON 数组格式，不要其他文字：
[{"shotNumber":1,"sceneDescription":"...","dialogue":"...","durationSeconds":5,"cameraAngle":"中景"}, ...]

剧本内容：
${text}`;

  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { responseMimeType: "application/json" },
        }),
      },
    );

    if (!res.ok) throw new Error(`Gemini API error: ${res.status}`);

    const data = await res.json();
    const content = data.candidates?.[0]?.content?.parts?.[0]?.text || "[]";
    const parsed = JSON.parse(content);

    if (Array.isArray(parsed) && parsed.length > 0) {
      return parsed.map((s: Record<string, unknown>, i: number) => ({
        shotNumber: (s.shotNumber as number) || i + 1,
        sceneDescription: (s.sceneDescription as string) || "",
        dialogue: (s.dialogue as string) || null,
        durationSeconds: (s.durationSeconds as number) || null,
        cameraAngle: (s.cameraAngle as string) || null,
      }));
    }

    // Fallback to rule-based if AI returns empty
    return parseScriptRuleBased(text);
  } catch (error) {
    console.error("Gemini script parsing failed, falling back to rule-based:", error);
    return parseScriptRuleBased(text);
  }
}
