"""
风格元数据服务

验证、归一化 Gemini 分析结果，并提取图片技术元数据。
"""

import logging
import math
import os
import re

logger = logging.getLogger(__name__)

# --- 有效枚举值 ---

VALID_ART_STYLES = [
    "写实", "扁平", "赛博朋克", "水彩", "油画", "素描", "动漫",
    "像素", "3D渲染", "混合媒体", "极简", "波普艺术", "印象派", "其他",
]

VALID_MOODS = [
    "温暖", "冷峻", "神秘", "欢快", "紧张", "平静", "忧郁",
    "史诗", "浪漫", "恐怖", "幽默", "其他",
]

VALID_LIGHTING = [
    "自然光", "硬光", "逆光", "伦勃朗光", "环境光", "顶光",
    "侧光", "柔光", "霓虹光", "烛光", "其他",
]

VALID_COMPOSITIONS = [
    "三分法", "中心构图", "对角线", "黄金比例", "框架构图",
    "对称", "引导线", "极简留白", "满构图", "其他",
]

VALID_CAMERA_ANGLES = [
    "平视", "俯视", "仰视", "鸟瞰", "荷兰角", "特写",
    "中景", "全景", "其他",
]

_ENUM_FIELDS = {
    "art_style": VALID_ART_STYLES,
    "mood": VALID_MOODS,
    "lighting": VALID_LIGHTING,
    "composition": VALID_COMPOSITIONS,
    "camera_angle": VALID_CAMERA_ANGLES,
}

_BRIGHTNESS_LEVELS = {"高", "中", "低"}
_CONTRAST_LEVELS = {"高", "中", "低"}
_SATURATION_LEVELS = {"高", "中", "低"}


# --- 颜色归一化 ---

def _normalize_color(color_str):
    """确保颜色为 #rrggbb 小写格式。"""
    if not color_str or not isinstance(color_str, str):
        return None
    color = color_str.strip().lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    if len(color) == 6 and all(c in "0123456789abcdefABCDEF" for c in color):
        return f"#{color.lower()}"
    return None


def _human_size(size_bytes):
    """将字节数转为人类可读格式。"""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# --- 枚举值匹配 ---

def _match_enum(value, valid_values):
    """
    将值匹配到最接近的有效枚举值。

    精确匹配优先，否则按子串包含匹配，最终回退到 "其他"。
    """
    if not value or not isinstance(value, str):
        return "其他"
    value = value.strip()
    # 精确匹配
    if value in valid_values:
        return value
    # 子串匹配（双向）
    for v in valid_values:
        if v in value or value in v:
            return v
    return "其他"


# --- Schema 验证 + 归一化 ---

def validate_and_normalize(raw_result):
    """
    验证并归一化 Gemini 分析结果。

    - 确保所有字段存在（缺失用默认值填充）
    - 颜色值归一化（确保 #rrggbb 格式，去重）
    - 关键词去重、去空串
    - 枚举值归一化（匹配最近的有效值）
    - 返回干净的结构化数据
    """
    if not raw_result or not isinstance(raw_result, dict):
        raw_result = {}

    result = {}

    # metadata 子对象
    raw_meta = raw_result.get("metadata", {})
    if not isinstance(raw_meta, dict):
        raw_meta = {}

    # 颜色归一化：去重、去无效值
    raw_colors = raw_meta.get("dominant_colors", [])
    if not isinstance(raw_colors, list):
        raw_colors = []
    normalized_colors = []
    seen_colors = set()
    for c in raw_colors:
        nc = _normalize_color(c)
        if nc and nc not in seen_colors:
            normalized_colors.append(nc)
            seen_colors.add(nc)

    result["metadata"] = {
        "dominant_colors": normalized_colors,
        "brightness": raw_meta.get("brightness", "中")
            if raw_meta.get("brightness") in _BRIGHTNESS_LEVELS else "中",
        "contrast": raw_meta.get("contrast", "中")
            if raw_meta.get("contrast") in _CONTRAST_LEVELS else "中",
        "saturation": raw_meta.get("saturation", "中")
            if raw_meta.get("saturation") in _SATURATION_LEVELS else "中",
    }

    # 关键词：去重、去空串
    for key in ("style_keywords_en", "style_keywords_cn"):
        raw_kw = raw_result.get(key, [])
        if not isinstance(raw_kw, list):
            raw_kw = []
        cleaned = []
        seen = set()
        for kw in raw_kw:
            if isinstance(kw, str):
                kw = kw.strip()
                if kw and kw not in seen:
                    cleaned.append(kw)
                    seen.add(kw)
        result[key] = cleaned

    # 枚举字段归一化
    for field, valid_values in _ENUM_FIELDS.items():
        result[field] = _match_enum(raw_result.get(field), valid_values)

    # reference_artists：去重、去空串
    raw_artists = raw_result.get("reference_artists", [])
    if not isinstance(raw_artists, list):
        raw_artists = []
    artists = []
    seen_artists = set()
    for a in raw_artists:
        if isinstance(a, str):
            a = a.strip()
            if a and a not in seen_artists:
                artists.append(a)
                seen_artists.add(a)
    result["reference_artists"] = artists

    # description_cn
    desc = raw_result.get("description_cn", "")
    result["description_cn"] = desc.strip() if isinstance(desc, str) else ""

    return result


# --- 图片技术元数据提取 ---

def extract_image_metadata(image_path):
    """
    提取图片技术元数据（不依赖 AI）。

    使用 PIL/Pillow 读取图片基本信息和 EXIF 数据。

    Returns:
        dict: 包含 resolution, width, height, aspect_ratio, file_size,
              format, color_mode, bit_depth, has_alpha, dpi, exif 等字段。
    """
    result = {}
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img = Image.open(image_path)

        result["width"] = img.width
        result["height"] = img.height
        result["resolution"] = f"{img.width}x{img.height}"
        result["format"] = img.format or "Unknown"
        result["color_mode"] = img.mode
        result["has_alpha"] = img.mode in ("RGBA", "LA", "PA")

        # Aspect ratio
        gcd = math.gcd(img.width, img.height)
        result["aspect_ratio"] = f"{img.width // gcd}:{img.height // gcd}"

        # File size
        file_size = os.path.getsize(image_path)
        result["file_size_bytes"] = file_size
        result["file_size_human"] = _human_size(file_size)

        # DPI
        dpi = img.info.get("dpi", (72, 72))
        result["dpi"] = int(dpi[0]) if isinstance(dpi, tuple) else 72

        # Bit depth
        mode_bits = {
            "1": 1, "L": 8, "P": 8, "RGB": 8, "RGBA": 8,
            "CMYK": 8, "I": 32, "F": 32,
        }
        result["bit_depth"] = mode_bits.get(img.mode, 8)

        # EXIF (primarily JPEG)
        exif_data = {}
        if hasattr(img, "_getexif") and img._getexif():
            raw_exif = img._getexif()
            exif_tag_names = {
                "Make": "camera_make",
                "Model": "camera",
                "LensModel": "lens",
                "ISOSpeedRatings": "iso",
                "ExposureTime": "shutter_speed",
                "FNumber": "aperture",
                "FocalLength": "focal_length",
                "DateTimeOriginal": "date_taken",
            }
            for tag_id, tag_value in raw_exif.items():
                tag_name = TAGS.get(tag_id, "")
                if tag_name in exif_tag_names:
                    field = exif_tag_names[tag_name]
                    # Format specific fields
                    if tag_name == "ExposureTime" and hasattr(tag_value, "numerator"):
                        exif_data[field] = (
                            f"{tag_value.numerator}/{tag_value.denominator}"
                        )
                    elif tag_name == "FNumber" and hasattr(tag_value, "numerator"):
                        f_val = tag_value.numerator / tag_value.denominator
                        exif_data[field] = f"f/{f_val:.1f}"
                    elif tag_name == "FocalLength" and hasattr(tag_value, "numerator"):
                        fl_val = tag_value.numerator / tag_value.denominator
                        exif_data[field] = f"{fl_val:.0f}mm"
                    elif tag_name == "DateTimeOriginal" and isinstance(tag_value, str):
                        # Convert "2024:03:20 10:30:00" to ISO format
                        exif_data[field] = tag_value.replace(
                            ":", "-", 2
                        ).replace(" ", "T", 1)
                    else:
                        exif_data[field] = (
                            str(tag_value) if not isinstance(tag_value, (str, int, float)) else tag_value
                        )

        result["exif"] = exif_data if exif_data else None

        img.close()
    except ImportError:
        logger.warning("PIL/Pillow not available, skipping image metadata extraction")
        result["error"] = "PIL/Pillow not installed"
    except Exception as e:
        logger.error("Failed to extract image metadata from %s: %s", image_path, e)
        result["error"] = str(e)

    return result


# --- 合并 AI 分析 + 技术元数据 ---

def build_complete_metadata(ai_result, image_path=None):
    """
    合并 AI 分析结果和技术元数据，返回完整的风格元数据。

    Args:
        ai_result: Gemini 分析返回的完整 dict（含 result/status 等字段）
        image_path: 图片文件路径（可选，用于提取技术元数据）

    Returns:
        dict: 包含 style（归一化后的 AI 结果）、technical（技术元数据）、version
    """
    normalized = validate_and_normalize(ai_result.get("result", {}))
    tech_meta = extract_image_metadata(image_path) if image_path else {}

    return {
        "style": normalized,
        "technical": tech_meta,
        "version": "1.0",
    }
