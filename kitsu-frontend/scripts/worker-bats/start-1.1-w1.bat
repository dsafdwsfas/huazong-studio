@echo off
chcp 65001 >nul
title w1 前端主力A ^| 1.1 品牌重塑与汉化
color 0A
cd /d "D:\claude\bot-01\workspace\.worktrees\1.1-w1"

echo.
echo =========================================
echo   Worker: w1 - 前端主力A
echo   Feature: 1.1 - 品牌重塑与汉化
echo   Worktree: D:\claude\bot-01\workspace\.worktrees\1.1-w1
echo   Task: 替换Logo、Favicon、品牌色、登录页重设计
echo =========================================
echo.
echo Starting claude...
echo.

type "D:\claude\bot-01\workspace\kitsu-frontend\scripts\worker-bats\1.1-w1-prompt.txt" | claude -p - --output-format text --max-turns 50 --model sonnet

echo.
echo =========================================
echo   Worker w1 DONE!
echo =========================================
echo.
pause
