@echo off
chcp 65001 >/dev/null 2>&1
title Worker w4 - Brand Logo Visual
color 0A
echo.
echo =============================================
echo   Worker w4 - Brand Logo Visual
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w4
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w4-prompt.txt
echo.
echo Worker w4 DONE!
pause
