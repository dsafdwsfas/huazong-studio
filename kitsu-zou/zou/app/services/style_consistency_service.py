"""
风格一致性检查服务

对比新上传图片的分析结果与项目锁定风格，生成一致性评分和差异报告。
"""

import logging

from zou.app.services import style_lock_service

logger = logging.getLogger(__name__)


def check_consistency(project_id, shot_analysis):
    """
    检查 shot 分析结果与项目锁定风格的一致性。

    Args:
        project_id: 项目 ID
        shot_analysis: shot 的 AI 分析结果（result 字段）

    Returns:
        {
            "score": 85,  # 0-100 一致性评分
            "matches": ["art_style", "mood"],  # 匹配的维度
            "mismatches": [
                {"dimension": "lighting", "locked": "硬光", "actual": "柔光", "severity": "medium"}
            ],
            "color_similarity": 72,  # 色彩相似度 0-100
            "keyword_overlap": 0.6,  # 关键词重叠率 0-1
        }
    """
    locked = style_lock_service.get_locked_style(project_id)
    if not locked or not locked.get("locked"):
        return {
            "score": -1,
            "message": "项目未锁定风格，无法检查一致性",
            "matches": [],
            "mismatches": [],
        }

    locked_style = locked.get("style", {})
    if not locked_style:
        return {"score": -1, "message": "锁定风格数据为空", "matches": [], "mismatches": []}

    if not shot_analysis:
        return {"score": -1, "message": "shot 无分析数据", "matches": [], "mismatches": []}

    matches = []
    mismatches = []

    # Compare enum dimensions
    dimensions = [
        ("art_style", "艺术风格", "high"),
        ("mood", "氛围", "medium"),
        ("lighting", "光影", "medium"),
        ("composition", "构图", "low"),
        ("camera_angle", "镜头角度", "low"),
    ]

    for key, label, severity in dimensions:
        locked_val = locked_style.get(key, "")
        actual_val = shot_analysis.get(key, "")
        if locked_val and actual_val:
            if locked_val == actual_val:
                matches.append(key)
            else:
                mismatches.append({
                    "dimension": key,
                    "label": label,
                    "locked": locked_val,
                    "actual": actual_val,
                    "severity": severity,
                })
        elif locked_val:
            mismatches.append({
                "dimension": key,
                "label": label,
                "locked": locked_val,
                "actual": "(未检测到)",
                "severity": "low",
            })

    # Color similarity
    locked_colors = set(locked_style.get("dominant_colors", []))
    actual_colors = set(
        (shot_analysis.get("metadata", {}) or {}).get("dominant_colors", [])
    )
    color_sim = 0
    if locked_colors and actual_colors:
        overlap = len(locked_colors & actual_colors)
        total = max(len(locked_colors), len(actual_colors))
        color_sim = int(overlap / total * 100) if total > 0 else 0

    # Keyword overlap
    locked_kw = set(locked_style.get("style_keywords_cn", []))
    actual_kw = set(shot_analysis.get("style_keywords_cn", []))
    kw_overlap = 0.0
    if locked_kw and actual_kw:
        overlap = len(locked_kw & actual_kw)
        total = max(len(locked_kw), len(actual_kw))
        kw_overlap = round(overlap / total, 2) if total > 0 else 0.0

    # Calculate overall score
    dim_score = len(matches) / max(len(matches) + len(mismatches), 1) * 50
    color_score = color_sim * 0.25
    kw_score = kw_overlap * 25
    total_score = int(min(dim_score + color_score + kw_score, 100))

    return {
        "score": total_score,
        "matches": matches,
        "mismatches": mismatches,
        "color_similarity": color_sim,
        "keyword_overlap": kw_overlap,
        "matched_keywords": list(locked_kw & actual_kw) if locked_kw and actual_kw else [],
    }
