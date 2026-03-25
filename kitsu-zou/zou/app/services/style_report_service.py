"""
风格报告导出服务

从项目锁定风格和分析数据生成 Markdown 风格报告。
"""

import time


def generate_report(project_name, locked_style, reference_analyses=None):
    """
    生成项目风格报告（Markdown 格式）。

    Args:
        project_name: 项目名称
        locked_style: 锁定的风格数据
        reference_analyses: 参考图分析结果列表

    Returns:
        str: Markdown 格式报告
    """
    style = locked_style.get("style", {}) if locked_style else {}
    now = time.strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append(f"# 风格报告 — {project_name}")
    lines.append(f"")
    lines.append(f"> 生成时间: {now}")
    if locked_style and locked_style.get("locked_at"):
        lines.append(f"> 锁定时间: {locked_style['locked_at']}")
    if locked_style and locked_style.get("locked_by_name"):
        lines.append(f"> 锁定人: {locked_style['locked_by_name']}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Core style attributes
    lines.append(f"## 核心风格定义")
    lines.append(f"")
    attrs = [
        ("艺术风格", style.get("art_style", "")),
        ("氛围", style.get("mood", "")),
        ("光影", style.get("lighting", "")),
        ("构图", style.get("composition", "")),
        ("镜头角度", style.get("camera_angle", "")),
    ]
    lines.append(f"| 维度 | 设定 |")
    lines.append(f"|------|------|")
    for label, val in attrs:
        if val:
            lines.append(f"| {label} | {val} |")
    lines.append(f"")

    # Colors
    colors = style.get("dominant_colors", [])
    if colors:
        lines.append(f"## 主色调")
        lines.append(f"")
        lines.append(f"| 色值 |")
        lines.append(f"|------|")
        for c in colors:
            lines.append(f"| `{c}` |")
        lines.append(f"")

    # Keywords
    cn_kw = style.get("style_keywords_cn", [])
    en_kw = style.get("style_keywords_en", [])
    if cn_kw:
        lines.append(f"## 风格关键词")
        lines.append(f"")
        lines.append(f"**中文**: {', '.join(cn_kw)}")
        if en_kw:
            lines.append(f"")
            lines.append(f"**英文**: {', '.join(en_kw)}")
        lines.append(f"")

    # Description
    desc = style.get("description", "") or style.get("description_cn", "")
    if desc:
        lines.append(f"## 风格描述")
        lines.append(f"")
        lines.append(f"{desc}")
        lines.append(f"")

    # Reference artists
    artists = style.get("reference_artists", [])
    if artists:
        lines.append(f"## 参考艺术家")
        lines.append(f"")
        for a in artists:
            lines.append(f"- {a}")
        lines.append(f"")

    # Reference images count
    ref_ids = locked_style.get("reference_image_ids", []) if locked_style else []
    if ref_ids:
        lines.append(f"## 参考图")
        lines.append(f"")
        lines.append(f"共 {len(ref_ids)} 张参考图")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*本报告由画宗制片中枢 AI 风格引擎自动生成*")

    return "\n".join(lines)
