@echo off
chcp 65001 >/dev/null 2>&1
title Worker w1 - Brand Frontend Text
color 0A
echo.
echo =============================================
echo   Worker w1 - Brand Frontend Text
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w1
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w1-prompt.txt
echo.
echo Worker w1 DONE!
pause
