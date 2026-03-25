@echo off
chcp 65001 >nul
title w3 后端主力A ^| 1.1 品牌重塑与汉化
color 0A
cd /d "D:\claude\bot-01\workspace\.worktrees\1.1-w3"

echo.
echo =========================================
echo   Worker: w3 - 后端主力A
echo   Feature: 1.1 - 品牌重塑与汉化
echo   Worktree: D:\claude\bot-01\workspace\.worktrees\1.1-w3
echo   Task: 邮件模板汉化、API返回文案替换
echo =========================================
echo.
echo Starting claude...
echo.

type "D:\claude\bot-01\workspace\kitsu-frontend\scripts\worker-bats\1.1-w3-prompt.txt" | claude -p - --output-format text --max-turns 50 --model sonnet

echo.
echo =========================================
echo   Worker w3 DONE!
echo =========================================
echo.
pause
