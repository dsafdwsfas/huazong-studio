/**
 * Style extraction service using Gemini API.
 * Analyzes reference images and extracts style keywords in JSON format,
 * then converts to human-readable style guide.
 */

const STYLE_EXTRACTION_PROMPT = `你是一位专业的影视美术指导和色彩顾问。
分析提供的参考图片，提取影响画面风格、色调、质感的所有视觉特征。

输出严格的 JSON 格式，包含以下维度：

{
  "color_palette": {
    "dominant_colors": ["主色1", "主色2", "主色3"],
    "accent_colors": ["点缀色1"],
    "overall_tone": "整体色调描述（如：冷色调偏蓝、暖色调金黄、低饱和度莫兰迪）",
    "contrast": "高/中/低",
    "saturation": "高饱和/中等/低饱和/去饱和"
  },
  "lighting": {
    "type": "自然光/人工光/混合",
    "direction": "顶光/侧光/逆光/平光/伦勃朗光",
    "quality": "硬光/柔光/漫射",
    "mood": "光影营造的氛围",
    "time_of_day": "如适用（黄金时段/蓝调时刻/正午等）"
  },
  "texture_and_quality": {
    "surface": "画面质感描述（胶片颗粒/数码清晰/油画质感等）",
    "grain": "无/轻微/明显/强烈",
    "sharpness": "锐利/适中/柔焦",
    "post_processing": "后期风格（电影调色/VSCO滤镜/无后期等）"
  },
  "composition_style": {
    "framing": "构图特点",
    "depth": "浅景深/深景深/平面化",
    "perspective": "透视特点"
  },
  "atmosphere": {
    "mood": "整体情绪（神秘/温暖/压迫/梦幻等）",
    "era": "时代感（现代/复古/未来/古典）",
    "genre": "风格流派（赛博朋克/新黑色/田园/极简等）"
  },
  "art_reference": {
    "similar_artists": ["风格接近的艺术家/导演"],
    "similar_works": ["风格接近的作品"],
    "medium": "最接近的媒介（电影/摄影/插画/3D渲染等）"
  }
}

只返回 JSON，不要其他文字。`;

const STYLE_TO_KEYWORDS_PROMPT = `将以下 JSON 风格分析转换为简洁的中英文风格关键词列表。

要求：
1. 每个关键词简短有力（2-6个字）
2. 中英文都要有
3. 按维度分组：色调、光影、质感、氛围、风格参考
4. 只保留对"指导团队统一风格"有用的关键词
5. 总数控制在 15-25 个

输出格式：
{
  "color_tone": ["关键词1", "keyword1", ...],
  "lighting": ["关键词2", "keyword2", ...],
  "texture": ["关键词3", "keyword3", ...],
  "atmosphere": ["关键词4", "keyword4", ...],
  "reference": ["关键词5", "keyword5", ...],
  "summary": "一句话风格描述（中文，30字以内）"
}

只返回 JSON。`;

export interface StyleAnalysis {
  color_palette: {
    dominant_colors: string[];
    accent_colors: string[];
    overall_tone: string;
    contrast: string;
    saturation: string;
  };
  lighting: {
    type: string;
    direction: string;
    quality: string;
    mood: string;
    time_of_day?: string;
  };
  texture_and_quality: {
    surface: string;
    grain: string;
    sharpness: string;
    post_processing: string;
  };
  composition_style: {
    framing: string;
    depth: string;
    perspective: string;
  };
  atmosphere: {
    mood: string;
    era: string;
    genre: string;
  };
  art_reference: {
    similar_artists: string[];
    similar_works: string[];
    medium: string;
  };
}

export interface StyleKeywords {
  color_tone: string[];
  lighting: string[];
  texture: string[];
  atmosphere: string[];
  reference: string[];
  summary: string;
}

/**
 * Extract style from images using Gemini API.
 * Falls back to a placeholder if API is unavailable.
 */
export async function extractStyleFromImages(
  imageBase64List: Array<{ base64: string; mimeType: string }>,
  apiKey?: string
): Promise<{ analysis: StyleAnalysis; keywords: StyleKeywords }> {
  if (!apiKey) {
    // Return placeholder for development
    return getPlaceholderStyle();
  }

  try {
    // Step 1: Extract detailed JSON analysis
    const parts: any[] = imageBase64List.map((img) => ({
      inlineData: { mimeType: img.mimeType, data: img.base64 },
    }));
    parts.push({ text: STYLE_EXTRACTION_PROMPT });

    const analysisResponse = await callGemini(apiKey, parts);
    const analysis: StyleAnalysis = JSON.parse(analysisResponse);

    // Step 2: Convert to keywords
    const keywordParts = [
      { text: `${STYLE_TO_KEYWORDS_PROMPT}\n\nJSON 风格分析：\n${JSON.stringify(analysis, null, 2)}` },
    ];
    const keywordsResponse = await callGemini(apiKey, keywordParts);
    const keywords: StyleKeywords = JSON.parse(keywordsResponse);

    return { analysis, keywords };
  } catch (error) {
    console.error("Style extraction failed:", error);
    return getPlaceholderStyle();
  }
}

async function callGemini(apiKey: string, parts: any[]): Promise<string> {
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts }],
        generationConfig: { responseMimeType: "application/json" },
      }),
    }
  );

  if (!res.ok) {
    throw new Error(`Gemini API error: ${res.status}`);
  }

  const data = await res.json();
  return data.candidates?.[0]?.content?.parts?.[0]?.text || "{}";
}

function getPlaceholderStyle(): { analysis: StyleAnalysis; keywords: StyleKeywords } {
  return {
    analysis: {
      color_palette: {
        dominant_colors: ["深蓝", "暗灰", "金色"],
        accent_colors: ["霓虹粉"],
        overall_tone: "冷色调偏蓝，带暖色点缀",
        contrast: "高",
        saturation: "中等",
      },
      lighting: {
        type: "人工光",
        direction: "侧光",
        quality: "硬光",
        mood: "神秘而紧张",
        time_of_day: "夜晚",
      },
      texture_and_quality: {
        surface: "电影胶片质感",
        grain: "轻微",
        sharpness: "锐利",
        post_processing: "电影调色 Teal & Orange",
      },
      composition_style: {
        framing: "对称构图",
        depth: "浅景深",
        perspective: "低角度",
      },
      atmosphere: {
        mood: "紧张悬疑",
        era: "现代",
        genre: "赛博朋克",
      },
      art_reference: {
        similar_artists: ["Roger Deakins", "Denis Villeneuve"],
        similar_works: ["银翼杀手2049", "攻壳机动队"],
        medium: "电影",
      },
    },
    keywords: {
      color_tone: ["冷色调", "Teal & Orange", "深蓝主调", "低饱和"],
      lighting: ["硬光侧打", "rim light", "霓虹光晕", "夜景"],
      texture: ["胶片颗粒", "film grain", "锐利", "电影调色"],
      atmosphere: ["赛博朋克", "cyberpunk", "神秘紧张", "未来感"],
      reference: ["银翼杀手", "Blade Runner", "Deakins打光"],
      summary: "赛博朋克夜景风格，冷蓝色调配霓虹暖光，电影胶片质感",
    },
  };
}
