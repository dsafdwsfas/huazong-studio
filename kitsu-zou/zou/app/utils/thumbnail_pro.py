"""
专业格式缩略图生成模块

支持 PSD/AI/EXR/视频/音频/3D 模型的预览和缩略图生成。
所有外部依赖通过 try-except 导入，缺失时优雅降级。

依赖清单：
- psd-tools: PSD 文件解析（pip install psd-tools）
- OpenCV: EXR/HDR 色调映射（pip install opencv-python-headless）
- Pillow: 基础图片处理（已安装）
- FFmpeg: 视频帧提取/音频波形（系统依赖）
- ImageMagick: PSD/AI 后备方案（系统依赖）
- Ghostscript: AI 文件渲染（系统依赖）
"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ---- 可选依赖检测 ----

try:
    from psd_tools import PSDImage
    HAS_PSD_TOOLS = True
except ImportError:
    HAS_PSD_TOOLS = False

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

HAS_FFMPEG = shutil.which("ffmpeg") is not None
HAS_IMAGEMAGICK = shutil.which("convert") is not None or shutil.which("magick") is not None
HAS_GHOSTSCRIPT = shutil.which("gs") is not None or shutil.which("gswin64c") is not None

# ImageMagick v7 用 magick，v6 用 convert
IMAGEMAGICK_CMD = "magick" if shutil.which("magick") else "convert"
GHOSTSCRIPT_CMD = "gswin64c" if shutil.which("gswin64c") else "gs"

# ---- 格式检测 ----

# 扩展名 → 格式类别映射
FORMAT_MAP = {
    # 图片
    ".psd": "psd",
    ".psb": "psd",
    ".ai": "ai",
    ".eps": "ai",
    ".exr": "exr",
    ".hdr": "hdr",
    # 视频
    ".mp4": "video",
    ".mov": "video",
    ".avi": "video",
    ".mkv": "video",
    ".webm": "video",
    ".wmv": "video",
    # 音频
    ".wav": "audio",
    ".mp3": "audio",
    ".flac": "audio",
    ".aac": "audio",
    ".ogg": "audio",
    # 3D
    ".obj": "3d",
    ".fbx": "3d",
    ".glb": "3d",
    ".gltf": "3d",
    ".stl": "3d",
}


def detect_format(file_path):
    """检测文件格式类别"""
    ext = Path(file_path).suffix.lower()
    return FORMAT_MAP.get(ext)


# ---- 统一入口 ----


def create_thumbnail(file_path, output_path, size=(300, 200)):
    """
    为任意专业格式文件生成缩略图。

    Args:
        file_path: 源文件路径
        output_path: 输出 PNG 路径
        size: 目标尺寸 (width, height)

    Returns:
        str: 成功时返回 output_path，失败返回 None
    """
    fmt = detect_format(file_path)
    if not fmt:
        return None

    handlers = {
        "psd": _create_psd_thumbnail,
        "ai": _create_ai_thumbnail,
        "exr": _create_exr_thumbnail,
        "hdr": _create_hdr_thumbnail,
        "video": _create_video_thumbnail,
        "audio": _create_audio_thumbnail,
        "3d": _create_3d_thumbnail,
    }

    handler = handlers.get(fmt)
    if not handler:
        return None

    try:
        result = handler(file_path, output_path, size)
        if result and os.path.exists(output_path):
            logger.info("缩略图生成成功: %s → %s", file_path, output_path)
            return output_path
    except Exception as e:
        logger.warning("缩略图生成失败 (%s): %s", fmt, e)

    # 降级：生成占位图
    return _create_placeholder(file_path, output_path, size, fmt)


# ---- PSD ----


def _create_psd_thumbnail(file_path, output_path, size):
    """PSD 缩略图：psd-tools → ImageMagick 降级"""
    if HAS_PSD_TOOLS:
        try:
            psd = PSDImage.open(file_path)
            img = psd.composite()
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path, "PNG")
            return output_path
        except Exception as e:
            logger.debug("psd-tools 失败，尝试 ImageMagick: %s", e)

    if HAS_IMAGEMAGICK:
        return _imagemagick_convert(file_path, output_path, size)

    return None


# ---- AI/EPS ----


def _create_ai_thumbnail(file_path, output_path, size):
    """AI/EPS 缩略图：Ghostscript → ImageMagick 降级"""
    if HAS_GHOSTSCRIPT:
        try:
            width, height = size
            dpi = max(72, int(width / 4))  # 粗略 DPI 估算
            subprocess.run(
                [
                    GHOSTSCRIPT_CMD,
                    "-dBATCH",
                    "-dNOPAUSE",
                    "-dSAFER",
                    "-sDEVICE=pngalpha",
                    f"-r{dpi}",
                    f"-sOutputFile={output_path}",
                    file_path,
                ],
                timeout=30,
                capture_output=True,
                check=True,
            )
            # 调整尺寸
            _resize_to_fit(output_path, size)
            return output_path
        except Exception as e:
            logger.debug("Ghostscript 失败，尝试 ImageMagick: %s", e)

    if HAS_IMAGEMAGICK:
        return _imagemagick_convert(file_path, output_path, size)

    return None


# ---- EXR ----


def _create_exr_thumbnail(file_path, output_path, size):
    """EXR 缩略图：OpenCV 色调映射"""
    if not HAS_OPENCV:
        return None

    img = cv2.imread(
        file_path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH
    )
    if img is None:
        return None

    # Reinhard 色调映射
    tonemap = cv2.createTonemapReinhard(gamma=2.2)
    ldr = tonemap.process(img.astype(np.float32))
    ldr = np.clip(ldr * 255, 0, 255).astype(np.uint8)

    # 缩放
    h, w = ldr.shape[:2]
    tw, th = size
    scale = min(tw / w, th / h)
    new_w, new_h = int(w * scale), int(h * scale)
    ldr = cv2.resize(ldr, (new_w, new_h), interpolation=cv2.INTER_AREA)

    cv2.imwrite(output_path, ldr)
    return output_path


# ---- HDR ----


def _create_hdr_thumbnail(file_path, output_path, size):
    """HDR 缩略图：OpenCV 色调映射（与 EXR 相同流程）"""
    return _create_exr_thumbnail(file_path, output_path, size)


# ---- 视频 ----


def _create_video_thumbnail(file_path, output_path, size):
    """视频缩略图：FFmpeg 提取 10% 位置的帧"""
    if not HAS_FFMPEG:
        return None

    width, height = size

    # 先获取视频时长
    duration = _get_video_duration(file_path)
    seek_time = max(0, duration * 0.1) if duration > 0 else 1

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-ss", str(seek_time),
                "-i", file_path,
                "-vframes", "1",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease",
                "-y",
                output_path,
            ],
            timeout=30,
            capture_output=True,
            check=True,
        )
        return output_path
    except Exception as e:
        logger.debug("FFmpeg 视频帧提取失败: %s", e)
        return None


def _get_video_duration(file_path):
    """获取视频时长（秒）"""
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", file_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # 从 stderr 中提取 Duration
        import re
        match = re.search(
            r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)",
            result.stderr
        )
        if match:
            h, m, s, _ = match.groups()
            return int(h) * 3600 + int(m) * 60 + int(s)
    except Exception:
        pass
    return 0


# ---- 音频 ----


def _create_audio_thumbnail(file_path, output_path, size):
    """音频缩略图：FFmpeg 生成波形图"""
    if not HAS_FFMPEG:
        return None

    width, height = size

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", file_path,
                "-filter_complex",
                f"showwavespic=s={width}x{height}:colors=#00b242",
                "-frames:v", "1",
                "-y",
                output_path,
            ],
            timeout=30,
            capture_output=True,
            check=True,
        )
        return output_path
    except Exception as e:
        logger.debug("FFmpeg 波形图生成失败: %s", e)
        return None


# ---- 3D 模型 ----


def _create_3d_thumbnail(file_path, output_path, size):
    """3D 模型缩略图：生成占位图（trimesh 渲染需要 OpenGL，不适合服务端）"""
    # 3D 模型在服务端无法简单渲染，直接生成信息占位图
    return None


# ---- 工具函数 ----


def _imagemagick_convert(file_path, output_path, size):
    """使用 ImageMagick 转换文件"""
    width, height = size
    try:
        # [0] 只取第一页/第一帧
        subprocess.run(
            [
                IMAGEMAGICK_CMD,
                f"{file_path}[0]",
                "-thumbnail", f"{width}x{height}",
                "-background", "none",
                "-flatten",
                output_path,
            ],
            timeout=30,
            capture_output=True,
            check=True,
        )
        return output_path
    except Exception as e:
        logger.debug("ImageMagick 转换失败: %s", e)
        return None


def _resize_to_fit(image_path, size):
    """将图片调整到目标尺寸内"""
    try:
        img = Image.open(image_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(image_path, "PNG")
    except Exception:
        pass


def _create_placeholder(file_path, output_path, size, format_name):
    """
    生成占位缩略图：显示文件名、格式和大小信息。
    当专业格式解析失败时使用。
    """
    width, height = size
    img = Image.new("RGB", (width, height), (45, 45, 55))
    draw = ImageDraw.Draw(img)

    filename = Path(file_path).name
    ext = Path(file_path).suffix.upper()
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    size_text = _format_bytes(file_size)

    # 用默认字体绘制
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_small = font_large

    # 绘制格式标签
    draw.text(
        (width // 2, height // 3),
        ext,
        fill=(0, 178, 66),
        font=font_large,
        anchor="mm",
    )

    # 绘制文件名（截断）
    display_name = filename if len(filename) <= 25 else filename[:22] + "..."
    draw.text(
        (width // 2, height // 2 + 10),
        display_name,
        fill=(180, 180, 190),
        font=font_small,
        anchor="mm",
    )

    # 绘制文件大小
    draw.text(
        (width // 2, height // 2 + 30),
        size_text,
        fill=(120, 120, 130),
        font=font_small,
        anchor="mm",
    )

    img.save(output_path, "PNG")
    logger.info("生成占位缩略图: %s", output_path)
    return output_path


def _format_bytes(size):
    """格式化文件大小"""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ---- 依赖检测报告 ----


def get_capabilities():
    """返回当前可用的缩略图生成能力"""
    return {
        "psd": HAS_PSD_TOOLS or HAS_IMAGEMAGICK,
        "ai": HAS_GHOSTSCRIPT or HAS_IMAGEMAGICK,
        "exr": HAS_OPENCV,
        "hdr": HAS_OPENCV,
        "video": HAS_FFMPEG,
        "audio": HAS_FFMPEG,
        "3d": False,  # 服务端不支持，前端用 Three.js
        "dependencies": {
            "psd_tools": HAS_PSD_TOOLS,
            "opencv": HAS_OPENCV,
            "ffmpeg": HAS_FFMPEG,
            "imagemagick": HAS_IMAGEMAGICK,
            "ghostscript": HAS_GHOSTSCRIPT,
        },
    }
