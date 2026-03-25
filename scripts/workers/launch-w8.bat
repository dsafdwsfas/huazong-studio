@echo off
chcp 65001 >/dev/null 2>&1
title Worker w8 - Chinese Status Terms
color 0A
echo.
echo =============================================
echo   Worker w8 - Chinese Status Terms
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w8
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w8-prompt.txt
echo.
echo Worker w8 DONE!
pause
