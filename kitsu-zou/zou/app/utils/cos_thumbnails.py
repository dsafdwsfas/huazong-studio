"""
COS Cloud Infinite (CI) thumbnail generation utility.

COS CI generates thumbnails by appending processing parameters to the object URL.
No separate API call needed — just construct the URL with style parameters.

Supported operations:
- Thumbnail: imageView2/1/w/{width}/h/{height}
- Scale: imageMogr2/thumbnail/{percent}%
- Format conversion: imageMogr2/format/webp
- Quality: imageMogr2/quality/80

Reference: https://cloud.tencent.com/document/product/460/6924
"""

import os
from urllib.parse import urlencode, urlparse, urlunparse


def _get_env(key, default=None):
    """Read environment variable with optional default."""
    return os.environ.get(key, default)


def _is_ci_enabled():
    """Check if COS Cloud Infinite is enabled."""
    return _get_env("COS_CI_ENABLED", "false").lower() in ("true", "1", "yes")


def _strip_existing_params(url):
    """Remove any existing CI processing parameters from URL."""
    parsed = urlparse(url)
    # CI params are appended after '?' on COS URLs
    # Keep only the path, strip query that starts with CI operations
    clean_path = parsed.path.split("?")[0]
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        clean_path,
        "",
        "",
        "",
    ))


def get_thumbnail_url(cos_url, width=200, height=200, format=None):
    """
    Generate thumbnail URL by appending CI parameters.

    Uses imageView2 mode 1 (center-crop to exact dimensions).

    Args:
        cos_url: Full COS object URL.
        width: Target width in pixels (default 200).
        height: Target height in pixels (default 200).
        format: Optional output format (e.g., 'webp', 'png').

    Returns:
        URL with CI thumbnail parameters appended, or original URL
        if CI is disabled.
    """
    if not _is_ci_enabled() or not cos_url:
        return cos_url

    base_url = _strip_existing_params(cos_url)
    params = f"imageView2/1/w/{width}/h/{height}"

    if format:
        params += f"/format/{format}"

    return f"{base_url}?{params}"


def get_preview_url(cos_url, max_width=800):
    """
    Generate preview URL with max width constraint.

    Uses imageMogr2 to scale image proportionally so width does not
    exceed max_width. Height adjusts automatically.

    Args:
        cos_url: Full COS object URL.
        max_width: Maximum width in pixels (default 800).

    Returns:
        URL with CI preview parameters appended, or original URL
        if CI is disabled.
    """
    if not _is_ci_enabled() or not cos_url:
        return cos_url

    base_url = _strip_existing_params(cos_url)
    params = f"imageMogr2/thumbnail/{max_width}x"

    return f"{base_url}?{params}"


def get_cdn_url(key, bucket_type, cdn_domain=None):
    """
    Convert COS object key to CDN URL if CDN is enabled.

    When CDN is not enabled or not configured, falls back to
    constructing a standard COS URL.

    Args:
        key: Object key in the bucket (e.g., 'previews/abc123.png').
        bucket_type: One of 'pictures', 'movies', 'files'.
        cdn_domain: Override CDN domain. If None, reads from env.

    Returns:
        CDN URL if enabled, otherwise standard COS URL.
    """
    if cdn_domain is None:
        cdn_domain = _get_env("COS_CDN_DOMAIN", "")

    cdn_enabled = _get_env("COS_CDN_ENABLED", "false").lower() in (
        "true", "1", "yes",
    )

    if cdn_enabled and cdn_domain:
        # CDN domain should not have trailing slash
        domain = cdn_domain.rstrip("/")
        # Ensure https
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        return f"{domain}/{key.lstrip('/')}"

    # Fallback: construct standard COS URL
    region = _get_env("COS_REGION", "ap-beijing")
    bucket_map = {
        "pictures": _get_env("COS_BUCKET_PICTURES", ""),
        "movies": _get_env("COS_BUCKET_MOVIES", ""),
        "files": _get_env("COS_BUCKET_FILES", ""),
    }
    bucket = bucket_map.get(bucket_type, "")
    if not bucket:
        return key  # Cannot construct URL without bucket name

    return f"https://{bucket}.cos.{region}.myqcloud.com/{key.lstrip('/')}"


def get_ci_style_url(cos_url, style=None):
    """
    Apply a named CI style to a COS URL.

    Styles are predefined image processing pipelines configured in the
    COS console. Falls back to the COS_CI_THUMBNAIL_STYLE env var.

    Args:
        cos_url: Full COS object URL.
        style: CI style string (e.g., 'imageView2/1/w/200/h/200').
               If None, reads COS_CI_THUMBNAIL_STYLE from env.

    Returns:
        URL with CI style appended, or original URL if CI is disabled.
    """
    if not _is_ci_enabled() or not cos_url:
        return cos_url

    if style is None:
        style = _get_env(
            "COS_CI_THUMBNAIL_STYLE", "imageView2/1/w/200/h/200"
        )

    base_url = _strip_existing_params(cos_url)
    return f"{base_url}?{style}"
