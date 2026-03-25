"""
手机验证码服务 — 腾讯云 SMS

提供验证码的发送和验证功能，使用 Redis 存储验证码和防刷状态。
当 SMS 配置为空时，退化为控制台打印验证码（开发模式）。

安全特性:
- 60 秒发送间隔（防刷）
- 验证码 5 分钟有效期
- 最多 5 次错误尝试后锁定 15 分钟
- 验证成功后立即删除（一次性使用）
"""
import hashlib
import hmac
import json
import logging
import random
import time

import requests

from zou.app import config_oauth
from zou.app.stores.auth_tokens_store import revoked_tokens_store as redis_store

logger = logging.getLogger(__name__)

# =============================================================================
# Redis Key 前缀定义
# =============================================================================
SMS_CODE_PREFIX = "sms_code:"          # 验证码存储
SMS_COOLDOWN_PREFIX = "sms_cooldown:"  # 发送冷却期
SMS_ATTEMPTS_PREFIX = "sms_attempts:"  # 错误尝试次数
SMS_LOCKOUT_PREFIX = "sms_lockout:"    # 锁定标记

# =============================================================================
# 时间常量（秒）
# =============================================================================
CODE_EXPIRE_SECONDS = 300       # 验证码有效期: 5 分钟
COOLDOWN_SECONDS = 60           # 发送冷却期: 60 秒
MAX_VERIFY_ATTEMPTS = 5         # 最大错误尝试次数
LOCKOUT_SECONDS = 900           # 锁定时间: 15 分钟


def send_sms_code(phone):
    """
    发送 6 位数字验证码到指定手机号

    流程:
    1. 检查是否在冷却期内（60 秒内不允许重复发送）
    2. 生成 6 位随机验证码
    3. 存入 Redis（5 分钟过期）
    4. 设置冷却期标记
    5. 调用腾讯云 SMS API 发送（或开发模式打印到控制台）

    参数:
        phone: 手机号码字符串

    返回:
        True: 发送成功
        False: 发送失败（冷却期内或API错误）

    异常:
        不抛出异常，错误通过返回值和日志反映
    """
    if not phone or not phone.strip():
        logger.warning("手机号为空，无法发送验证码")
        return False

    phone = phone.strip()

    # 检查 Redis 是否可用
    if redis_store is None:
        logger.error("Redis 不可用，无法发送验证码")
        return False

    # 检查冷却期 — 防止 60 秒内重复发送
    cooldown_key = f"{SMS_COOLDOWN_PREFIX}{phone}"
    if redis_store.get(cooldown_key):
        logger.info("手机号 %s 在冷却期内，拒绝发送", phone)
        return False

    # 检查是否被锁定
    lockout_key = f"{SMS_LOCKOUT_PREFIX}{phone}"
    if redis_store.get(lockout_key):
        logger.info("手机号 %s 已被锁定，拒绝发送", phone)
        return False

    # 生成 6 位随机验证码
    code = f"{random.randint(100000, 999999)}"

    # 存入 Redis: key=sms_code:{phone}, value=code, expire=300s
    code_key = f"{SMS_CODE_PREFIX}{phone}"
    redis_store.set(code_key, code, ex=CODE_EXPIRE_SECONDS)

    # 设置冷却期标记
    redis_store.set(cooldown_key, "1", ex=COOLDOWN_SECONDS)

    # 重置错误尝试计数
    attempts_key = f"{SMS_ATTEMPTS_PREFIX}{phone}"
    redis_store.delete(attempts_key)

    # 发送短信
    if not config_oauth.SMS_ENABLED or not config_oauth.SMS_SECRET_ID:
        # 开发模式 — 打印验证码到控制台
        logger.info(
            "[开发模式] 手机号 %s 的验证码: %s（有效期 %d 秒）",
            phone,
            code,
            CODE_EXPIRE_SECONDS,
        )
        print(
            f"\n{'='*50}\n"
            f"[SMS 开发模式] 手机: {phone} 验证码: {code}\n"
            f"{'='*50}\n"
        )
        return True

    # 生产模式 — 调用腾讯云 SMS API
    success = _send_via_tencent_cloud(phone, code)
    if not success:
        # 发送失败时清理验证码和冷却期
        redis_store.delete(code_key)
        redis_store.delete(cooldown_key)
        return False

    logger.info("验证码已发送到手机号 %s", phone)
    return True


def verify_sms_code(phone, code):
    """
    验证手机验证码

    流程:
    1. 检查手机号是否被锁定（错误次数过多）
    2. 从 Redis 读取存储的验证码
    3. 比对验证码
    4. 成功: 删除验证码和错误计数
    5. 失败: 错误计数 +1，达到阈值则锁定

    参数:
        phone: 手机号码字符串
        code: 用户输入的验证码字符串

    返回:
        True: 验证通过
        False: 验证失败（验证码错误、过期、被锁定）
    """
    if not phone or not code:
        return False

    phone = phone.strip()
    code = code.strip()

    if redis_store is None:
        logger.error("Redis 不可用，无法验证")
        return False

    # 检查是否被锁定
    lockout_key = f"{SMS_LOCKOUT_PREFIX}{phone}"
    if redis_store.get(lockout_key):
        logger.info("手机号 %s 已锁定，拒绝验证", phone)
        return False

    # 从 Redis 读取验证码
    code_key = f"{SMS_CODE_PREFIX}{phone}"
    stored_code = redis_store.get(code_key)

    if stored_code is None:
        logger.info("手机号 %s 无有效验证码（已过期或未发送）", phone)
        return False

    # 比对验证码（使用恒定时间比较防止时序攻击）
    if not hmac.compare_digest(stored_code, code):
        # 验证失败 — 记录错误次数
        attempts_key = f"{SMS_ATTEMPTS_PREFIX}{phone}"
        attempts = redis_store.incr(attempts_key)
        redis_store.expire(attempts_key, CODE_EXPIRE_SECONDS)

        if attempts >= MAX_VERIFY_ATTEMPTS:
            # 达到最大错误次数 — 锁定 15 分钟
            redis_store.set(lockout_key, "1", ex=LOCKOUT_SECONDS)
            redis_store.delete(code_key)
            redis_store.delete(attempts_key)
            logger.warning(
                "手机号 %s 验证错误 %d 次，已锁定 %d 秒",
                phone,
                attempts,
                LOCKOUT_SECONDS,
            )
        else:
            logger.info(
                "手机号 %s 验证码错误（第 %d/%d 次）",
                phone,
                attempts,
                MAX_VERIFY_ATTEMPTS,
            )

        return False

    # 验证成功 — 删除验证码（一次性使用）
    redis_store.delete(code_key)
    redis_store.delete(f"{SMS_ATTEMPTS_PREFIX}{phone}")
    logger.info("手机号 %s 验证码验证成功", phone)
    return True


def get_cooldown_remaining(phone):
    """
    获取指定手机号的冷却剩余时间（秒）

    参数:
        phone: 手机号码字符串

    返回:
        剩余冷却秒数，0 表示可以发送
    """
    if redis_store is None:
        return 0

    cooldown_key = f"{SMS_COOLDOWN_PREFIX}{phone}"
    ttl = redis_store.ttl(cooldown_key)
    return max(0, ttl)


# =============================================================================
# 腾讯云 SMS API 调用（使用 requests + HMAC 签名，避免新依赖）
# =============================================================================

def _send_via_tencent_cloud(phone, code):
    """
    通过腾讯云 SMS API 发送验证码

    使用 TC3-HMAC-SHA256 签名方式调用 API，避免引入额外 SDK 依赖。
    文档: https://cloud.tencent.com/document/product/382/55981

    参数:
        phone: 手机号（需要带国际区号前缀，如 +86）
        code: 6 位验证码

    返回:
        True: 发送成功
        False: 发送失败
    """
    # 确保手机号带有国际区号前缀
    if not phone.startswith("+"):
        phone = f"+86{phone}"

    secret_id = config_oauth.SMS_SECRET_ID
    secret_key = config_oauth.SMS_SECRET_KEY
    app_id = config_oauth.SMS_APP_ID
    sign_name = config_oauth.SMS_SIGN_NAME
    template_id = config_oauth.SMS_TEMPLATE_ID

    # 请求体
    payload = {
        "SmsSdkAppId": app_id,
        "SignName": sign_name,
        "TemplateId": template_id,
        "TemplateParamSet": [code],
        "PhoneNumberSet": [phone],
    }

    # 构造 TC3 签名
    service = "sms"
    host = "sms.tencentcloudapi.com"
    action = "SendSms"
    version = "2021-01-11"
    region = "ap-guangzhou"
    timestamp = int(time.time())
    date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))

    # CanonicalRequest
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    payload_str = json.dumps(payload)
    content_type = "application/json; charset=utf-8"
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-tc-action:{action.lower()}\n"
    )
    signed_headers = "content-type;host;x-tc-action"
    hashed_payload = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    canonical_request = (
        f"{http_request_method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{hashed_payload}"
    )

    # StringToSign
    algorithm = "TC3-HMAC-SHA256"
    credential_scope = f"{date}/{service}/tc3_request"
    hashed_canonical = hashlib.sha256(
        canonical_request.encode("utf-8")
    ).hexdigest()
    string_to_sign = (
        f"{algorithm}\n"
        f"{timestamp}\n"
        f"{credential_scope}\n"
        f"{hashed_canonical}"
    )

    # 签名
    def _hmac_sha256(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    secret_date = _hmac_sha256(
        f"TC3{secret_key}".encode("utf-8"), date
    )
    secret_service = _hmac_sha256(secret_date, service)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    signature = hmac.new(
        secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # Authorization
    authorization = (
        f"{algorithm} "
        f"Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    headers = {
        "Authorization": authorization,
        "Content-Type": content_type,
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": version,
        "X-TC-Region": region,
    }

    try:
        response = requests.post(
            f"https://{host}",
            headers=headers,
            data=payload_str,
            timeout=10,
        )
        result = response.json()

        # 检查响应
        send_status = (
            result.get("Response", {})
            .get("SendStatusSet", [{}])[0]
        )

        if send_status.get("Code") == "Ok":
            logger.info("腾讯云 SMS 发送成功: %s", phone)
            return True
        else:
            error = result.get("Response", {}).get("Error", {})
            logger.error(
                "腾讯云 SMS 发送失败: Code=%s, Message=%s",
                error.get("Code") or send_status.get("Code"),
                error.get("Message") or send_status.get("Message"),
            )
            return False

    except Exception as e:
        logger.error("腾讯云 SMS API 调用异常: %s", e)
        return False
