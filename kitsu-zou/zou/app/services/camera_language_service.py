"""
镜头语言库服务

将项目级镜头语言术语存储在 Project.data["camera_language_library"] 数组中。
支持 CRUD、分类筛选、搜索、预置术语初始化。
"""

import logging
import time
import uuid

from zou.app import db
from zou.app.models.project import Project
from zou.app.services import persons_service

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "shot_size",
    "camera_movement",
    "composition",
    "angle",
    "transition",
    "other",
}

DEFAULT_TERMS = [
    # 景别 (shot_size)
    {
        "term_cn": "大全景",
        "term_en": "Extreme Wide Shot",
        "category": "shot_size",
        "description": "展示广阔的环境全貌，人物在画面中非常渺小，用于建立场景氛围",
        "example_usage": "开场建立地理环境，如荒漠、城市天际线",
        "tags": ["环境", "建立镜头"],
    },
    {
        "term_cn": "全景",
        "term_en": "Wide Shot",
        "category": "shot_size",
        "description": "展示人物全身及周围环境，交代人物与空间的关系",
        "example_usage": "角色进入新场景时，展示其在环境中的位置",
        "tags": ["环境", "人物"],
    },
    {
        "term_cn": "中全景",
        "term_en": "Medium Wide Shot",
        "category": "shot_size",
        "description": "拍摄人物膝盖以上，兼顾人物动作与环境信息",
        "example_usage": "角色走动或与环境互动时使用",
        "tags": ["人物", "动作"],
    },
    {
        "term_cn": "中景",
        "term_en": "Medium Shot",
        "category": "shot_size",
        "description": "拍摄人物腰部以上，最常用的叙事景别，平衡人物与环境",
        "example_usage": "日常对话场景，展示角色的手势和表情",
        "tags": ["人物", "叙事"],
    },
    {
        "term_cn": "中近景",
        "term_en": "Medium Close-up",
        "category": "shot_size",
        "description": "拍摄人物胸部以上，强调面部表情同时保留部分肢体语言",
        "example_usage": "重要对话中捕捉角色的情感反应",
        "tags": ["人物", "情感"],
    },
    {
        "term_cn": "近景",
        "term_en": "Close-up",
        "category": "shot_size",
        "description": "拍摄人物肩部以上或物体细节，聚焦表情或重要道具",
        "example_usage": "角色独白、情感高潮、关键道具特写",
        "tags": ["人物", "情感", "细节"],
    },
    {
        "term_cn": "特写",
        "term_en": "Big Close-up",
        "category": "shot_size",
        "description": "拍摄人物面部或物体局部细节，营造强烈的亲密感或紧张感",
        "example_usage": "眼神交流、泪滴滑落、按下按钮的手指",
        "tags": ["情感", "细节", "紧张"],
    },
    {
        "term_cn": "大特写",
        "term_en": "Extreme Close-up",
        "category": "shot_size",
        "description": "极度放大的局部细节，如眼睛、嘴唇、指尖，制造强烈视觉冲击",
        "example_usage": "恐惧时瞳孔放大、关键线索的微观展示",
        "tags": ["细节", "冲击"],
    },
    # 运镜 (camera_movement)
    {
        "term_cn": "推",
        "term_en": "Push In / Dolly In",
        "category": "camera_movement",
        "description": "摄影机向被摄体靠近，逐渐强调主体，增强紧迫感或聚焦注意力",
        "example_usage": "角色做出重要决定时缓慢推进",
        "tags": ["强调", "紧迫"],
    },
    {
        "term_cn": "拉",
        "term_en": "Pull Out / Dolly Out",
        "category": "camera_movement",
        "description": "摄影机远离被摄体，揭示更多环境信息或制造疏离感",
        "example_usage": "结尾拉远展示角色的孤独，或揭示场景全貌",
        "tags": ["揭示", "疏离"],
    },
    {
        "term_cn": "摇",
        "term_en": "Pan",
        "category": "camera_movement",
        "description": "摄影机在固定位置水平旋转，跟随动作或展示空间横向范围",
        "example_usage": "跟随角色视线从左到右扫过房间",
        "tags": ["跟随", "展示"],
    },
    {
        "term_cn": "移",
        "term_en": "Tracking Shot",
        "category": "camera_movement",
        "description": "摄影机在轨道或滑轨上平移，与被摄体保持恒定距离和角度",
        "example_usage": "角色行走时的侧面跟拍，保持画面稳定流畅",
        "tags": ["跟随", "流畅"],
    },
    {
        "term_cn": "跟",
        "term_en": "Follow Shot",
        "category": "camera_movement",
        "description": "摄影机跟随被摄体移动，通常从后方或侧方，营造临场感",
        "example_usage": "跟随角色穿越走廊或人群",
        "tags": ["跟随", "临场"],
    },
    {
        "term_cn": "升降",
        "term_en": "Crane / Jib",
        "category": "camera_movement",
        "description": "摄影机垂直升起或降落，改变视角高度，制造宏大或亲密感",
        "example_usage": "从地面升起俯瞰战场，或从高处降落到角色面前",
        "tags": ["宏大", "视角变化"],
    },
    {
        "term_cn": "环绕",
        "term_en": "Orbit / Arc Shot",
        "category": "camera_movement",
        "description": "摄影机围绕被摄体做弧形运动，强化主体存在感或制造戏剧效果",
        "example_usage": "英雄觉醒时刻的 360 度环绕",
        "tags": ["戏剧", "强调"],
    },
    {
        "term_cn": "手持",
        "term_en": "Handheld",
        "category": "camera_movement",
        "description": "手持摄影机拍摄，画面带有自然晃动，增加真实感和紧张感",
        "example_usage": "追逐场景、战争场面、纪实风格",
        "tags": ["真实", "紧张", "纪实"],
    },
    {
        "term_cn": "Steadicam",
        "term_en": "Steadicam",
        "category": "camera_movement",
        "description": "使用稳定器跟拍，兼顾手持的灵活性和轨道的稳定性",
        "example_usage": "长镜头跟随角色穿越复杂场景",
        "tags": ["稳定", "长镜头"],
    },
    {
        "term_cn": "无人机",
        "term_en": "Drone Shot",
        "category": "camera_movement",
        "description": "使用无人机进行航拍，提供独特的高空视角和自由运动轨迹",
        "example_usage": "建立镜头展示地貌，或跟拍高速追逐",
        "tags": ["航拍", "宏大"],
    },
    # 构图 (composition)
    {
        "term_cn": "三分法",
        "term_en": "Rule of Thirds",
        "category": "composition",
        "description": "将画面分为九宫格，主体置于交叉点或分割线上，创造平衡而有张力的构图",
        "example_usage": "人物面部置于上三分之一交叉点",
        "tags": ["基础", "平衡"],
    },
    {
        "term_cn": "中心构图",
        "term_en": "Center Composition",
        "category": "composition",
        "description": "主体居中放置，营造对称、庄重或压迫感",
        "example_usage": "韦斯·安德森式对称构图，强调秩序感",
        "tags": ["对称", "庄重"],
    },
    {
        "term_cn": "对角线",
        "term_en": "Diagonal Composition",
        "category": "composition",
        "description": "利用画面对角线引导视线，增加动态感和不稳定感",
        "example_usage": "倾斜的楼梯、蜿蜒的道路作为视觉引导",
        "tags": ["动态", "引导"],
    },
    {
        "term_cn": "黄金比例",
        "term_en": "Golden Ratio",
        "category": "composition",
        "description": "基于 1:1.618 比例的构图法则，创造自然和谐的视觉效果",
        "example_usage": "风景摄影中地平线的精确定位",
        "tags": ["和谐", "高级"],
    },
    {
        "term_cn": "框架构图",
        "term_en": "Frame within Frame",
        "category": "composition",
        "description": "利用门框、窗户、拱门等元素在画面内创建二次框架，聚焦主体",
        "example_usage": "透过门框看到房间内的角色",
        "tags": ["聚焦", "层次"],
    },
    {
        "term_cn": "对称",
        "term_en": "Symmetry",
        "category": "composition",
        "description": "画面左右或上下对称，营造秩序感、仪式感或超现实氛围",
        "example_usage": "走廊、建筑物正面、镜面倒影",
        "tags": ["秩序", "仪式"],
    },
    {
        "term_cn": "引导线",
        "term_en": "Leading Lines",
        "category": "composition",
        "description": "利用画面中的线条引导观众视线至主体，增强画面深度",
        "example_usage": "铁轨、公路、河流指向远方的主体",
        "tags": ["引导", "深度"],
    },
    {
        "term_cn": "负空间",
        "term_en": "Negative Space",
        "category": "composition",
        "description": "大面积留白或空旷区域包围主体，突出孤独、渺小或极简美感",
        "example_usage": "广阔天空下的孤独人影",
        "tags": ["极简", "孤独"],
    },
    # 角度 (angle)
    {
        "term_cn": "平视",
        "term_en": "Eye Level",
        "category": "angle",
        "description": "摄影机与被摄体视线平齐，最自然中性的视角，不带倾向性",
        "example_usage": "日常对话场景，客观叙事",
        "tags": ["中性", "自然"],
    },
    {
        "term_cn": "俯视",
        "term_en": "High Angle",
        "category": "angle",
        "description": "摄影机从上方向下拍摄，使主体显得渺小、脆弱或处于劣势",
        "example_usage": "表现角色的无助或被审判感",
        "tags": ["弱势", "渺小"],
    },
    {
        "term_cn": "仰视",
        "term_en": "Low Angle",
        "category": "angle",
        "description": "摄影机从下方向上拍摄，使主体显得高大、威严或具有威胁性",
        "example_usage": "反派登场、英雄站立时的仰拍",
        "tags": ["威严", "力量"],
    },
    {
        "term_cn": "鸟瞰",
        "term_en": "Bird's Eye View",
        "category": "angle",
        "description": "从正上方垂直向下拍摄，提供上帝视角，展示空间布局或渺小感",
        "example_usage": "俯瞰城市街道、战场布局、迷宫",
        "tags": ["全局", "上帝视角"],
    },
    {
        "term_cn": "荷兰角",
        "term_en": "Dutch Angle",
        "category": "angle",
        "description": "摄影机倾斜拍摄，画面不水平，制造不安、混乱或心理扭曲感",
        "example_usage": "角色精神崩溃、噩梦场景、恐怖片",
        "tags": ["不安", "扭曲"],
    },
    {
        "term_cn": "过肩",
        "term_en": "Over the Shoulder",
        "category": "angle",
        "description": "从一个角色的肩膀后方拍摄另一个角色，建立对话空间关系",
        "example_usage": "正反打对话场景中的标准角度",
        "tags": ["对话", "关系"],
    },
    {
        "term_cn": "主观",
        "term_en": "POV (Point of View)",
        "category": "angle",
        "description": "模拟角色第一人称视角，让观众直接体验角色所见",
        "example_usage": "角色看手机屏幕、透过望远镜观察",
        "tags": ["沉浸", "第一人称"],
    },
    # 转场 (transition)
    {
        "term_cn": "切",
        "term_en": "Cut",
        "category": "transition",
        "description": "最基础的转场方式，直接从一个镜头切换到下一个，干净利落",
        "example_usage": "正反打对话中的镜头切换",
        "tags": ["基础", "快速"],
    },
    {
        "term_cn": "叠化",
        "term_en": "Dissolve",
        "category": "transition",
        "description": "前一个镜头渐隐的同时下一个镜头渐现，表示时间流逝或场景过渡",
        "example_usage": "回忆闪回、梦境过渡、时间蒙太奇",
        "tags": ["柔和", "时间"],
    },
    {
        "term_cn": "淡入淡出",
        "term_en": "Fade In / Fade Out",
        "category": "transition",
        "description": "画面从黑/白渐现或渐隐至黑/白，标志段落的开始或结束",
        "example_usage": "电影开场淡入、章节结束淡出至黑",
        "tags": ["段落", "开始", "结束"],
    },
    {
        "term_cn": "擦除",
        "term_en": "Wipe",
        "category": "transition",
        "description": "一个画面从边缘推开另一个画面，风格化的场景转换",
        "example_usage": "星球大战标志性的横向擦除转场",
        "tags": ["风格化", "复古"],
    },
    {
        "term_cn": "匹配剪辑",
        "term_en": "Match Cut",
        "category": "transition",
        "description": "利用前后镜头中相似的形状、动作或声音进行无缝衔接",
        "example_usage": "扔骨头匹配切到太空站（2001太空漫游）",
        "tags": ["创意", "无缝"],
    },
    {
        "term_cn": "跳切",
        "term_en": "Jump Cut",
        "category": "transition",
        "description": "同一镜头内跳过部分时间，制造时间压缩或焦虑不安的节奏",
        "example_usage": "角色等待时的跳切蒙太奇，Vlog 风格剪辑",
        "tags": ["节奏", "现代"],
    },
    {
        "term_cn": "L-cut",
        "term_en": "L-cut",
        "category": "transition",
        "description": "音频延续到下一个画面，前一场景的声音跨越到新画面上",
        "example_usage": "角色还在说话时画面已切到听者的反应",
        "tags": ["音频", "流畅"],
    },
    {
        "term_cn": "J-cut",
        "term_en": "J-cut",
        "category": "transition",
        "description": "下一个场景的音频提前于画面出现，创造期待感和流畅过渡",
        "example_usage": "听到下一场景的对话声，画面随后切过去",
        "tags": ["音频", "期待"],
    },
]


def _get_library(project):
    """从 project.data 中提取镜头语言术语列表。"""
    data = project.data or {}
    return data.get("camera_language_library", [])


def _save_library(project, terms):
    """将术语列表写回 project.data。"""
    data = dict(project.data) if project.data else {}
    data["camera_language_library"] = terms
    project.data = data
    project.save()
    db.session.commit()


def _find_term(terms, term_id):
    """在列表中查找指定术语，返回 (index, term) 或 (None, None)。"""
    for i, t in enumerate(terms):
        if t.get("id") == term_id:
            return i, t
    return None, None


def list_terms(project_id, category=None, search=None):
    """列出术语，支持分类/搜索筛选。"""
    project = Project.get(project_id)
    terms = _get_library(project)

    if category:
        terms = [t for t in terms if t["category"] == category]
    if search:
        q = search.lower()
        terms = [
            t
            for t in terms
            if q in t.get("term_cn", "").lower()
            or q in t.get("term_en", "").lower()
            or q in t.get("description", "").lower()
        ]

    # 计算分类统计（基于未筛选数据）
    all_terms = _get_library(project)
    categories = {}
    for t in all_terms:
        cat = t.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "terms": terms,
        "total": len(terms),
        "categories": categories,
        "initialized": len(all_terms) > 0,
    }


def create_term(
    project_id,
    person_id,
    term_cn,
    term_en,
    category="other",
    description="",
    example_usage="",
    tags=None,
):
    """创建术语。"""
    project = Project.get(project_id)
    person = persons_service.get_person(person_id)

    if category not in VALID_CATEGORIES:
        category = "other"

    terms = _get_library(project)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    term = {
        "id": str(uuid.uuid4()),
        "term_cn": term_cn,
        "term_en": term_en,
        "category": category,
        "description": description,
        "example_usage": example_usage,
        "tags": tags or [],
        "created_at": now,
        "created_by": str(person_id),
        "created_by_name": person.get("full_name", ""),
    }
    terms.append(term)
    _save_library(project, terms)
    return term


def update_term(project_id, term_id, **kwargs):
    """更新术语。"""
    project = Project.get(project_id)
    terms = _get_library(project)
    idx, term = _find_term(terms, term_id)
    if term is None:
        return None

    for field in (
        "term_cn",
        "term_en",
        "category",
        "description",
        "example_usage",
        "tags",
    ):
        if field in kwargs and kwargs[field] is not None:
            value = kwargs[field]
            if field == "category" and value not in VALID_CATEGORIES:
                value = "other"
            term[field] = value

    terms[idx] = term
    _save_library(project, terms)
    return term


def delete_term(project_id, term_id):
    """删除术语。"""
    project = Project.get(project_id)
    terms = _get_library(project)
    original_len = len(terms)

    terms = [t for t in terms if t.get("id") != term_id]
    if len(terms) == original_len:
        return False

    _save_library(project, terms)
    return True


def get_default_terms():
    """返回预置术语列表。"""
    return DEFAULT_TERMS


def init_default_terms(project_id, person_id):
    """首次初始化：将预置术语写入项目。若已有术语则跳过。"""
    project = Project.get(project_id)
    existing = _get_library(project)
    if len(existing) > 0:
        return {
            "terms": existing,
            "total": len(existing),
            "initialized": True,
            "message": "Already initialized.",
        }

    person = persons_service.get_person(person_id)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    terms = []
    for default in DEFAULT_TERMS:
        term = {
            "id": str(uuid.uuid4()),
            "term_cn": default["term_cn"],
            "term_en": default["term_en"],
            "category": default["category"],
            "description": default["description"],
            "example_usage": default["example_usage"],
            "tags": list(default["tags"]),
            "created_at": now,
            "created_by": str(person_id),
            "created_by_name": person.get("full_name", ""),
        }
        terms.append(term)

    _save_library(project, terms)
    return {
        "terms": terms,
        "total": len(terms),
        "initialized": True,
        "message": "Default terms initialized.",
    }
