import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
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
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

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

    if (useAI) {
      // TODO: Call Gemini API for intelligent parsing
      // For now, fall back to rule-based parsing
      parsedShots = parseScriptRuleBased(scriptText);
    } else {
      parsedShots = parseScriptRuleBased(scriptText);
    }

    // Save to database
    const db = getDb();
    const now = new Date().toISOString();
    const savedShots = [];

    for (const parsed of parsedShots) {
      const shot = {
        id: generateId("sht"),
        projectId,
        shotNumber: parsed.shotNumber,
        sceneDescription: parsed.sceneDescription,
        dialogue: parsed.dialogue,
        durationSeconds: parsed.durationSeconds,
        cameraAngle: parsed.cameraAngle,
        status: "pending_upload",
        assigneeId: null,
        sortOrder: parsed.shotNumber,
        createdAt: now,
        updatedAt: now,
      };
      db.shots.push(shot);
      savedShots.push(shot);
    }

    // Update project
    const project = db.projects.find((p) => p.id === projectId);
    if (project) project.updatedAt = now;

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

  // Try pattern matching first
  const shotPattern =
    /^(?:镜头|shot|s|场次|场景|sc)\s*(\d+)\s*[：:.\-、]/i;
  const numberedPattern = /^(\d+)\s*[.、：:)\]\-]/;

  let currentShot: (typeof shots)[0] | null = null;
  let shotCounter = 0;

  for (const line of lines) {
    if (!line) {
      // Blank line might separate shots
      if (currentShot && currentShot.sceneDescription) {
        // Check if next content looks like a new shot
        continue;
      }
      continue;
    }

    const shotMatch = line.match(shotPattern);
    const numMatch = line.match(numberedPattern);

    if (shotMatch || numMatch) {
      // Save previous shot
      if (currentShot) {
        shots.push(currentShot);
      }

      shotCounter++;
      const description = shotMatch
        ? line.replace(shotPattern, "").trim()
        : line.replace(numberedPattern, "").trim();

      // Extract camera angle hints
      const cameraMatch = description.match(
        /[（(](.*?(?:全景|中景|近景|特写|远景|俯拍|仰拍|跟拍|推|拉|摇|移|航拍).*?)[）)]/
      );

      // Extract duration hints
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
      // Check if it's dialogue
      if (
        line.startsWith('"') ||
        line.startsWith('"') ||
        line.startsWith("「") ||
        line.match(/^[\u4e00-\u9fa5]{1,4}[：:]/)
      ) {
        currentShot.dialogue = currentShot.dialogue
          ? currentShot.dialogue + "\n" + line
          : line;
      } else {
        // Append to description
        currentShot.sceneDescription += " " + line;
      }
    } else {
      // First content without a shot marker — create shot
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

  // Don't forget the last shot
  if (currentShot) {
    shots.push(currentShot);
  }

  // If no shots were found, split by blank lines
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
