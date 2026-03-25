"""
AI 图片风格分析服务

使用 Google Gemini API 分析图片，提取风格元数据。
"""

import json
import logging
import os
import re
import tempfile
import time

from zou.app import config

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """
分析这张图片，以 JSON 格式返回以下信息。请确保返回有效的 JSON，不要包含额外的说明文字：
{
  "metadata": {
    "dominant_colors": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
    "brightness": "高/中/低",
    "contrast": "高/中/低",
    "saturation": "高/中/低"
  },
  "style_keywords_en": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "style_keywords_cn": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "art_style": "写实/扁平/赛博朋克/水彩/油画/素描/动漫/像素/其他",
  "mood": "温暖/冷峻/神秘/欢快/紧张/平静/忧郁/其他",
  "lighting": "自然光/硬光/逆光/伦勃朗光/环境光/顶光/侧光/其他",
  "composition": "三分法/中心构图/对角线/黄金比例/框架构图/对称/引导线/其他",
  "camera_angle": "平视/俯视/仰视/鸟瞰/荷兰角/特写/其他",
  "reference_artists": ["参考艺术家1", "参考艺术家2"],
  "description_cn": "一句话中文描述这张图的整体风格和氛围"
}
""".strip()


def _parse_gemini_response(text):
    """从 Gemini 响应中提取 JSON，容错处理 markdown 代码块。"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    return json.loads(text)


def analyze_image(image_path, project_id=None):
    """
    用 Gemini API 分析图片，返回结构化风格数据。

    Args:
        image_path: 图片文件的本地路径
        project_id: 可选，关联项目 ID（用于日志）

    Returns:
        dict: 分析结果，包含 result/status/analyzed_at/model 字段
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return {
            "status": "error",
            "error": "GEMINI_API_KEY not configured",
            "result": None,
        }

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")

        uploaded_file = genai.upload_file(image_path)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    [ANALYSIS_PROMPT, uploaded_file],
                    generation_config={"temperature": 0.2},
                )
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(
                        "Gemini API retry %d/%d after %ds: %s",
                        attempt + 1,
                        max_retries,
                        wait_time,
                        e,
                    )
                    time.sleep(wait_time)
                else:
                    raise

        response_text = response.text
        result = _parse_gemini_response(response_text)

        return {
            "status": "success",
            "result": result,
            "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "model": "gemini-2.5-pro",
            "preview_file_id": None,
        }

    except json.JSONDecodeError as e:
        logger.error("Gemini response JSON parse error: %s", e)
        return {
            "status": "error",
            "error": f"JSON parse error: {str(e)}",
            "raw_response": response_text[:500] if "response_text" in dir() else "",
            "result": None,
        }
    except ImportError:
        logger.error("google-generativeai package not installed")
        return {
            "status": "error",
            "error": "google-generativeai package not installed. Run: pip install google-generativeai",
            "result": None,
        }
    except Exception as e:
        logger.error("Gemini analysis failed: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "result": None,
        }


def get_analysis_from_entity(entity):
    """从 Entity.data 中读取已缓存的分析结果。"""
    data = entity.data or {}
    return data.get("ai_analysis")


def save_analysis_to_entity(entity, analysis_result, preview_file_id=None):
    """将分析结果保存到 Entity.data JSONB 中。"""
    from zou.app import db

    data = dict(entity.data) if entity.data else {}
    analysis_result["preview_file_id"] = str(preview_file_id) if preview_file_id else None
    data["ai_analysis"] = analysis_result
    entity.data = data
    entity.save()
    db.session.commit()
