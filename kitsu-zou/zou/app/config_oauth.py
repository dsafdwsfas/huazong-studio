"""
OAuth 2.0 和手机验证码配置 — 从环境变量读取

画宗制片中枢扩展认证配置，独立于主 config.py 以避免修改现有代码。
支持企业微信 OAuth、钉钉 OAuth、腾讯云短信验证码。
"""
import os


# =============================================================================
# 企业微信 OAuth 2.0
# 文档: https://developer.work.weixin.qq.com/document/path/91022
# =============================================================================
WECOM_ENABLED = os.getenv("WECOM_ENABLED", "false").lower() == "true"
WECOM_CORP_ID = os.getenv("WECOM_CORP_ID", "")
WECOM_AGENT_ID = os.getenv("WECOM_AGENT_ID", "")
WECOM_SECRET = os.getenv("WECOM_SECRET", "")
WECOM_REDIRECT_URI = os.getenv("WECOM_REDIRECT_URI", "")

# =============================================================================
# 钉钉 OAuth 2.0
# 文档: https://open.dingtalk.com/document/orgapp/tutorial-obtaining-user-personal-information
# =============================================================================
DINGTALK_ENABLED = os.getenv("DINGTALK_ENABLED", "false").lower() == "true"
DINGTALK_APP_KEY = os.getenv("DINGTALK_APP_KEY", "")
DINGTALK_APP_SECRET = os.getenv("DINGTALK_APP_SECRET", "")
DINGTALK_REDIRECT_URI = os.getenv("DINGTALK_REDIRECT_URI", "")

# =============================================================================
# 手机验证码 — 腾讯云 SMS
# 文档: https://cloud.tencent.com/document/product/382
# =============================================================================
SMS_ENABLED = os.getenv("SMS_ENABLED", "false").lower() == "true"
SMS_SECRET_ID = os.getenv("SMS_SECRET_ID", "")
SMS_SECRET_KEY = os.getenv("SMS_SECRET_KEY", "")
SMS_APP_ID = os.getenv("SMS_APP_ID", "")
SMS_SIGN_NAME = os.getenv("SMS_SIGN_NAME", "画宗科技")
SMS_TEMPLATE_ID = os.getenv("SMS_TEMPLATE_ID", "")

# =============================================================================
# 自动注册 — OAuth/SMS 登录时自动创建用户
# =============================================================================
AUTO_REGISTER_ENABLED = (
    os.getenv("AUTO_REGISTER_ENABLED", "true").lower() == "true"
)

# =============================================================================
# 前端回调地址（OAuth 登录成功后重定向）
# =============================================================================
OAUTH_SUCCESS_REDIRECT = os.getenv("OAUTH_SUCCESS_REDIRECT", "/")
