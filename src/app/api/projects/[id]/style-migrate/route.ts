import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { getDb } from "@/lib/db-store";

const MIGRATION_PROMPT = `你是一位专业的 AI 影视提示词工程师。

已有风格关键词（JSON 格式）：
{style_json}

用户想要将这个风格应用到以下新内容：
{content_description}

请生成一段融合后的提示词，保持原有风格特征，但适配新内容。
输出格式：
1. 一段完整的中文生成提示词（适用于即梦/可灵等 AI 视频平台）
2. 一段完整的英文生成提示词（适用于 Midjourney/Flux 等平台）

用 JSON 格式返回：
{
  "zh_prompt": "中文提示词",
  "en_prompt": "English prompt",
  "style_notes": "风格迁移说明（简短描述如何融合）"
}`;

/** Generate style migration prompt */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const { contentDescription } = await request.json();
    if (!contentDescription) {
      return NextResponse.json({ error: "请输入内容描述" }, { status: 400 });
    }

    const db = getDb();
    const project = db.get<{ id: string; style_guide_json: string | null }>(
      "SELECT id, style_guide_json FROM projects WHERE id = ?",
      projectId
    );
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    const styleGuide = project.style_guide_json
      ? JSON.parse(project.style_guide_json)
      : null;

    if (!styleGuide?.keywords) {
      return NextResponse.json({ error: "项目还没有风格指南，请先提取风格" }, { status: 400 });
    }

    const apiKey = process.env.GEMINI_API_KEY;

    if (apiKey) {
      const prompt = MIGRATION_PROMPT
        .replace("{style_json}", JSON.stringify(styleGuide.keywords, null, 2))
        .replace("{content_description}", contentDescription);

      try {
        const response = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              contents: [{ parts: [{ text: prompt }] }],
              generationConfig: { temperature: 0.7 },
            }),
          }
        );

        if (response.ok) {
          const data = await response.json();
          const text = data.candidates?.[0]?.content?.parts?.[0]?.text || "";
          const jsonMatch = text.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            const result = JSON.parse(jsonMatch[0]);
            return NextResponse.json({ migration: result });
          }
        }
      } catch {
        // Fall through to placeholder
      }
    }

    // Placeholder response when API is unavailable
    const kwSummary = styleGuide.keywords.summary || "风格未定义";
    const colorTone = (styleGuide.keywords.color_tone || []).join("、");
    const atmosphere = (styleGuide.keywords.atmosphere || []).join("、");

    return NextResponse.json({
      migration: {
        zh_prompt: `${contentDescription}，${kwSummary}，色调：${colorTone}，氛围：${atmosphere}，高质量，电影级画面`,
        en_prompt: `${contentDescription}, ${kwSummary}, color tone: ${colorTone}, atmosphere: ${atmosphere}, high quality, cinematic`,
        style_notes: `将「${kwSummary}」风格应用到「${contentDescription}」场景（占位符模式，设置 GEMINI_API_KEY 以获得更好结果）`,
      },
    });
  } catch (error) {
    console.error("Style migration error:", error);
    return NextResponse.json({ error: "风格迁移失败" }, { status: 500 });
  }
}
