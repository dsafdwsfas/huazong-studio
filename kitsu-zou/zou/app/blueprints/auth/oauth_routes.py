"""
OAuth 2.0 & 手机验证码路由定义

本文件定义所有 OAuth 和 SMS 认证端点的路由映射。
集成方式: 在 zou/app/blueprints/auth/__init__.py 中添加以下两行即可启用:

    from zou.app.blueprints.auth.oauth_routes import oauth_routes
    routes = routes + oauth_routes

路由列表:
    GET  /auth/oauth/wecom/login       — 企业微信 OAuth 登录入口
    GET  /auth/oauth/wecom/callback    — 企业微信 OAuth 回调处理
    GET  /auth/oauth/dingtalk/login    — 钉钉 OAuth 登录入口
    GET  /auth/oauth/dingtalk/callback — 钉钉 OAuth 回调处理
    POST /auth/sms/send                — 发送手机验证码
    POST /auth/sms/login               — 手机验证码登录
"""
from zou.app.blueprints.auth.oauth_resources import (
    WeComLoginResource,
    WeComCallbackResource,
    DingtalkLoginResource,
    DingtalkCallbackResource,
    SMSSendResource,
    SMSLoginResource,
)


# OAuth 2.0 路由 — 企业微信
wecom_routes = [
    ("/auth/oauth/wecom/login", WeComLoginResource),
    ("/auth/oauth/wecom/callback", WeComCallbackResource),
]

# OAuth 2.0 路由 — 钉钉
dingtalk_routes = [
    ("/auth/oauth/dingtalk/login", DingtalkLoginResource),
    ("/auth/oauth/dingtalk/callback", DingtalkCallbackResource),
]

# 手机验证码路由
sms_routes = [
    ("/auth/sms/send", SMSSendResource),
    ("/auth/sms/login", SMSLoginResource),
]

# 完整 OAuth + SMS 路由列表（合并导出）
oauth_routes = wecom_routes + dingtalk_routes + sms_routes
