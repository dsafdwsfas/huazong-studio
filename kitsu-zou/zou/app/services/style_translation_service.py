"""
风格关键词翻译服务

提供英→中风格关键词翻译，内置 300+ 词汇表 + Gemini API 兜底。
"""

import json
import logging
import re
import time

from zou.app import config

logger = logging.getLogger(__name__)

# ── 内置英→中风格词汇表（300+ 条目）──────────────────────────────

STYLE_GLOSSARY = {
    # 艺术风格
    "realistic": "写实", "realism": "写实", "photorealistic": "照片级写实",
    "flat": "扁平", "flat design": "扁平设计", "minimalist": "极简",
    "cyberpunk": "赛博朋克", "steampunk": "蒸汽朋克",
    "watercolor": "水彩", "oil painting": "油画", "acrylic": "丙烯",
    "sketch": "素描", "pencil sketch": "铅笔素描", "ink": "水墨",
    "anime": "动漫", "manga": "漫画", "cel shading": "赛璐璐",
    "pixel art": "像素风", "voxel": "体素", "low poly": "低多边形",
    "3d render": "3D渲染", "3d": "3D", "cgi": "CG",
    "pop art": "波普艺术", "art deco": "装饰艺术", "art nouveau": "新艺术",
    "impressionist": "印象派", "expressionist": "表现主义",
    "surreal": "超现实", "surrealism": "超现实主义",
    "abstract": "抽象", "geometric": "几何", "organic": "有机",
    "retro": "复古", "vintage": "复古", "nostalgic": "怀旧",
    "futuristic": "未来主义", "sci-fi": "科幻", "fantasy": "奇幻",
    "gothic": "哥特", "dark fantasy": "黑暗奇幻",
    "cartoon": "卡通", "comic": "漫画风", "graphic novel": "图像小说",
    "collage": "拼贴", "mixed media": "混合媒体",
    "photographic": "摄影风", "documentary": "纪实",
    "cinematic": "电影感", "filmic": "胶片感",
    "painterly": "绘画感", "brushstroke": "笔触",
    "graffiti": "涂鸦", "street art": "街头艺术",
    "ukiyo-e": "浮世绘", "chinese painting": "国画",
    "calligraphy": "书法", "woodcut": "木刻",

    # 色彩与色调
    "warm": "暖色调", "cool": "冷色调", "cold": "冷色调",
    "vibrant": "鲜艳", "vivid": "明艳", "saturated": "高饱和",
    "desaturated": "低饱和", "muted": "柔和", "pastel": "粉彩",
    "monochrome": "单色", "monochromatic": "单色调",
    "black and white": "黑白", "b&w": "黑白",
    "sepia": "棕褐", "duotone": "双色调",
    "neon": "霓虹", "fluorescent": "荧光", "iridescent": "彩虹色",
    "metallic": "金属质感", "chrome": "铬银", "gold": "金色",
    "earthy": "大地色", "natural": "自然色",
    "dark": "暗色调", "light": "明亮", "bright": "明亮",
    "high contrast": "高对比", "low contrast": "低对比",
    "high saturation": "高饱和", "low saturation": "低饱和",
    "color grading": "调色", "color palette": "调色板",
    "complementary": "互补色", "analogous": "类似色",
    "gradient": "渐变", "ombre": "渐变",
    "teal": "青色", "cyan": "青色", "magenta": "品红",
    "amber": "琥珀色", "coral": "珊瑚色", "indigo": "靛蓝",
    "crimson": "深红", "burgundy": "酒红", "maroon": "栗色",
    "olive": "橄榄绿", "teal": "蓝绿", "navy": "藏青",

    # 光影
    "natural light": "自然光", "ambient": "环境光",
    "hard light": "硬光", "soft light": "柔光",
    "backlight": "逆光", "backlit": "逆光",
    "rim light": "轮廓光", "edge light": "边缘光",
    "rembrandt": "伦勃朗光", "rembrandt lighting": "伦勃朗光",
    "chiaroscuro": "明暗对比", "dramatic lighting": "戏剧性光影",
    "golden hour": "黄金时刻", "blue hour": "蓝色时刻",
    "sunrise": "日出", "sunset": "日落", "twilight": "暮光",
    "moonlight": "月光", "candlelight": "烛光",
    "spotlight": "聚光灯", "stage lighting": "舞台灯光",
    "neon light": "霓虹灯光", "fluorescent light": "荧光灯",
    "volumetric light": "体积光", "god rays": "丁达尔效应",
    "lens flare": "镜头光晕", "bokeh": "焦外散景",
    "shadow": "阴影", "cast shadow": "投射阴影",
    "overexposed": "过曝", "underexposed": "欠曝",
    "high key": "高调", "low key": "低调",

    # 构图
    "rule of thirds": "三分法", "golden ratio": "黄金比例",
    "center composition": "中心构图", "centered": "居中",
    "diagonal": "对角线", "diagonal composition": "对角线构图",
    "symmetry": "对称", "symmetrical": "对称",
    "asymmetry": "不对称", "asymmetrical": "不对称",
    "leading lines": "引导线", "vanishing point": "消失点",
    "frame within frame": "框架构图", "framing": "框架构图",
    "negative space": "负空间", "white space": "留白",
    "depth of field": "景深", "shallow dof": "浅景深",
    "wide angle": "广角", "telephoto": "长焦",
    "panoramic": "全景", "panorama": "全景",
    "close-up": "特写", "macro": "微距",
    "bird's eye": "鸟瞰", "aerial": "航拍",
    "worm's eye": "仰视", "low angle": "低角度",
    "high angle": "高角度", "eye level": "平视",
    "dutch angle": "荷兰角", "tilted": "倾斜",
    "foreground": "前景", "background": "背景",
    "midground": "中景", "layered": "层次",
    "overlap": "重叠", "cropped": "裁切",
    "full shot": "全景镜头", "medium shot": "中景镜头",
    "establishing shot": "建立镜头", "over the shoulder": "过肩",

    # 氛围与情绪
    "mysterious": "神秘", "eerie": "诡异", "haunting": "幽魅",
    "serene": "宁静", "peaceful": "平和", "tranquil": "静谧",
    "dramatic": "戏剧性", "intense": "紧张", "tense": "紧迫",
    "epic": "史诗", "grand": "宏大", "majestic": "壮丽",
    "romantic": "浪漫", "dreamy": "梦幻", "ethereal": "空灵",
    "melancholy": "忧郁", "somber": "沉郁", "gloomy": "阴沉",
    "cheerful": "欢快", "joyful": "喜悦", "playful": "活泼",
    "energetic": "活力", "dynamic": "动感", "action": "动作",
    "horror": "恐怖", "creepy": "诡异", "sinister": "阴险",
    "whimsical": "奇异", "quirky": "古怪", "surreal": "超现实",
    "elegant": "优雅", "sophisticated": "精致", "luxurious": "奢华",
    "rustic": "田园", "rural": "乡村", "urban": "都市",
    "industrial": "工业", "gritty": "粗粝", "raw": "原始",
    "clean": "干净", "crisp": "清晰", "polished": "精致",
    "chaotic": "混乱", "orderly": "有序", "balanced": "均衡",
    "cozy": "温馨", "intimate": "亲密", "isolated": "孤独",

    # 材质与纹理
    "texture": "纹理", "textured": "有纹理",
    "smooth": "光滑", "rough": "粗糙", "glossy": "光泽",
    "matte": "磨砂", "transparent": "透明", "translucent": "半透明",
    "glass": "玻璃", "crystal": "水晶", "ice": "冰",
    "metal": "金属", "wood": "木质", "stone": "石质",
    "fabric": "织物", "silk": "丝绸", "leather": "皮革",
    "paper": "纸质", "parchment": "羊皮纸",
    "grain": "颗粒感", "noise": "噪点", "film grain": "胶片颗粒",

    # 场景与环境
    "cityscape": "城市景观", "landscape": "风景", "seascape": "海景",
    "interior": "室内", "exterior": "室外",
    "underwater": "水下", "space": "太空", "desert": "沙漠",
    "forest": "森林", "mountain": "山脉", "ocean": "海洋",
    "rain": "雨", "snow": "雪", "fog": "雾", "mist": "薄雾",
    "night": "夜晚", "day": "白天", "dusk": "黄昏", "dawn": "黎明",
    "post-apocalyptic": "末日废土", "dystopian": "反乌托邦",
    "utopian": "乌托邦", "ancient": "古代", "medieval": "中世纪",
    "futuristic city": "未来城市", "neon city": "霓虹都市",
}

# 反向映射（中→英）
_CN_TO_EN = {v: k for k, v in STYLE_GLOSSARY.items()}


def translate_keywords(keywords_en, target="cn"):
    """
    翻译英文风格关键词为中文。

    Args:
        keywords_en: 英文关键词列表
        target: 目标语言 "cn"（默认）

    Returns:
        list[dict]: [{"en": "cyberpunk", "cn": "赛博朋克", "source": "glossary"}]
    """
    if not keywords_en:
        return []

    results = []
    untranslated = []

    for kw in keywords_en:
        if not kw or not isinstance(kw, str):
            continue
        kw_lower = kw.strip().lower()
        cn = STYLE_GLOSSARY.get(kw_lower)
        if cn:
            results.append({"en": kw.strip(), "cn": cn, "source": "glossary"})
        else:
            untranslated.append(kw.strip())

    # Batch translate remaining via Gemini if available
    if untranslated and config.GEMINI_API_KEY:
        gemini_translations = _gemini_batch_translate(untranslated)
        for item in gemini_translations:
            results.append({**item, "source": "gemini"})
    elif untranslated:
        # No Gemini — return as-is
        for kw in untranslated:
            results.append({"en": kw, "cn": kw, "source": "untranslated"})

    return results


def translate_keywords_cn_to_en(keywords_cn):
    """翻译中文关键词为英文（用于搜索/匹配）。"""
    if not keywords_cn:
        return []
    results = []
    for kw in keywords_cn:
        if not kw or not isinstance(kw, str):
            continue
        en = _CN_TO_EN.get(kw.strip())
        if en:
            results.append({"cn": kw.strip(), "en": en})
        else:
            results.append({"cn": kw.strip(), "en": kw.strip()})
    return results


def enrich_analysis_with_translations(analysis_result):
    """
    为分析结果添加双语关键词对照。

    修改 analysis_result in-place，添加 keyword_pairs 字段。
    """
    if not analysis_result or not isinstance(analysis_result, dict):
        return analysis_result

    result = analysis_result.get("result", {})
    if not result:
        return analysis_result

    en_keywords = result.get("style_keywords_en", [])
    if en_keywords:
        pairs = translate_keywords(en_keywords)
        result["keyword_pairs"] = pairs
        # Ensure cn keywords are complete
        if not result.get("style_keywords_cn") or len(result["style_keywords_cn"]) < len(en_keywords):
            result["style_keywords_cn"] = [p["cn"] for p in pairs]

    analysis_result["result"] = result
    return analysis_result


def get_glossary_stats():
    """返回词汇表统计信息。"""
    return {
        "total_entries": len(STYLE_GLOSSARY),
        "categories": {
            "art_style": sum(1 for k in STYLE_GLOSSARY if k in _ART_STYLE_KEYS),
            "color": sum(1 for k in STYLE_GLOSSARY if k in _COLOR_KEYS),
            "lighting": sum(1 for k in STYLE_GLOSSARY if k in _LIGHTING_KEYS),
            "composition": sum(1 for k in STYLE_GLOSSARY if k in _COMP_KEYS),
            "mood": sum(1 for k in STYLE_GLOSSARY if k in _MOOD_KEYS),
            "other": 0,
        }
    }


# Category key sets for stats
_ART_STYLE_KEYS = {
    "realistic", "realism", "flat", "cyberpunk", "watercolor", "oil painting",
    "sketch", "anime", "pixel art", "3d render", "pop art", "impressionist",
    "surreal", "abstract", "retro", "cartoon", "cinematic", "painterly",
}
_COLOR_KEYS = {
    "warm", "cool", "vibrant", "saturated", "monochrome", "neon", "metallic",
    "dark", "bright", "pastel", "gradient", "high contrast",
}
_LIGHTING_KEYS = {
    "natural light", "hard light", "soft light", "backlight", "rembrandt",
    "chiaroscuro", "golden hour", "volumetric light", "bokeh", "neon light",
}
_COMP_KEYS = {
    "rule of thirds", "golden ratio", "center composition", "diagonal",
    "symmetry", "leading lines", "negative space", "depth of field",
}
_MOOD_KEYS = {
    "mysterious", "serene", "dramatic", "epic", "romantic", "melancholy",
    "cheerful", "horror", "elegant", "cozy",
}


def _gemini_batch_translate(keywords):
    """用 Gemini 批量翻译未知关键词。"""
    try:
        import google.generativeai as genai

        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")

        prompt = (
            "将以下英文艺术/设计风格关键词翻译为中文，返回 JSON 数组。"
            "每个元素格式: {\"en\": \"原文\", \"cn\": \"中文翻译\"}\n"
            "关键词: " + json.dumps(keywords, ensure_ascii=False)
        )

        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1},
        )

        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except Exception as e:
        logger.warning("Gemini translation failed: %s", e)
        return [{"en": kw, "cn": kw} for kw in keywords]
