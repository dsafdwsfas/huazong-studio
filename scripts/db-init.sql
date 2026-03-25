-- =============================================
-- 画宗制片中枢 — PostgreSQL 初始化脚本
-- 由 docker-compose 的 db 容器在首次启动时自动执行
-- 放置于 docker-entrypoint-initdb.d/ 目录下
-- =============================================

-- 创建常用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 设置中文排序规则（腾讯云 PostgreSQL 兼容）
-- 注意: 实际排序取决于服务器 locale 设置，容器默认使用 en_US.UTF-8
-- 如需中文排序，需在 Dockerfile 中安装 zh_CN.UTF-8 locale

-- 数据库由 docker-compose 环境变量 POSTGRES_DB 自动创建
-- 以下为备用手动创建语句（正常情况下无需取消注释）
-- CREATE DATABASE huazong_studio ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8';
-- GRANT ALL PRIVILEGES ON DATABASE huazong_studio TO huazong;
