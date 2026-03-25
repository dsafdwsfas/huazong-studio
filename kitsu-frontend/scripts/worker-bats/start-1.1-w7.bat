@echo off
chcp 65001 >nul
title w7 前端辅助 ^| 1.1 品牌重塑与汉化
color 0A
cd /d "D:\claude\bot-01\workspace\.worktrees\1.1-w7"

echo.
echo =========================================
echo   Worker: w7 - 前端辅助
echo   Feature: 1.1 - 品牌重塑与汉化
echo   Worktree: D:\claude\bot-01\workspace\.worktrees\1.1-w7
echo   Task: 全量中文翻译、i18n文件补全、翻译覆盖率>95%
echo =========================================
echo.
echo Starting claude...
echo.

type "D:\claude\bot-01\workspace\kitsu-frontend\scripts\worker-bats\1.1-w7-prompt.txt" | claude -p - --output-format text --max-turns 50 --model sonnet

echo.
echo =========================================
echo   Worker w7 DONE!
echo =========================================
echo.
pause
