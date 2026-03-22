# 画宗制片中枢 — 开发进度

## 日期：2026-03-22

## 已完成文件

### 配置
- `package.json` — 依赖定义
- `tsconfig.json` — TypeScript 配置
- `next.config.ts` — Next.js 配置
- `postcss.config.mjs` — Tailwind v4
- `wrangler.toml` — Cloudflare Workers 配置
- `.gitignore`

### 核心库
- `src/lib/utils.ts` — cn() 工具函数
- `src/lib/constants.ts` — 状态/角色/平台常量
- `src/lib/auth.ts` — JWT 创建/验证
- `src/lib/id.ts` — nanoid 生成器
- `src/lib/db-store.ts` — 开发用内存数据库（含种子管理员）
- `src/lib/api-client.ts` — 前端 API 客户端

### 认证 API
- `src/app/api/auth/register/route.ts` — 邀请码注册
- `src/app/api/auth/login/route.ts` — 密码登录
- `src/app/api/auth/invite/route.ts` — 生成/列出邀请码

### 项目 API
- `src/app/api/projects/route.ts` — 项目 CRUD
- `src/app/api/projects/[id]/shots/route.ts` — 镜头 CRUD
- `src/app/api/projects/[id]/parse-script/route.ts` — 剧本拆解
- `src/app/api/shots/[id]/assets/route.ts` — 资产上传

### 页面
- `src/app/layout.tsx` — 根布局
- `src/app/page.tsx` — 首页重定向
- `src/app/globals.css` — 全局样式 + CSS 变量
- `src/app/(auth)/layout.tsx` — 认证布局
- `src/app/(auth)/login/page.tsx` — 登录/注册页
- `src/app/(dashboard)/layout.tsx` — Dashboard 侧边栏布局
- `src/app/(dashboard)/projects/page.tsx` — 项目列表页
- `src/app/(dashboard)/projects/[id]/page.tsx` — 项目详情/分镜板

## 待完成

### Task 2: 数据库 Schema（子代理已派发）
- Drizzle ORM schema 定义
- D1 迁移文件

### Task 7: 画笔批注系统
- 需要 Fabric.js 或 Konva.js
- 自由画笔/矩形/箭头/文字批注
- 批注状态管理和回复线程
- 视频帧定位批注

### Task 8: 状态流转
- 镜头状态变更 API
- 权限中间件（admin/director/artist）
- 批量操作

### 后续功能（Phase 2-5）
- 风格定调系统
- 提示词资产库
- 角色/道具/场景档案
- 任务看板
- 积分台账
- 全局搜索

## 默认账号
- 管理员：13800000000 / admin123
- 邀请码：HUAZONG2026

## 技术决策
- 开发阶段使用内存数据库（db-store.ts），生产环境切换 D1 + Drizzle
- 登录：邀请码注册 + 密码（非微信/短信）
- 部署目标：Cloudflare Pages + Workers
